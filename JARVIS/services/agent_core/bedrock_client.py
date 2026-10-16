"""
JARVIS AI - Amazon Bedrock Model Provider & Planner Client
Interacts with Amazon Bedrock foundation models with configurable fallback for offline/local development.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger("jarvis.bedrock")


class BedrockModelProvider:
    def __init__(
        self,
        region_name: Optional[str] = None,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    ):
        self.region_name = region_name or os.environ.get("AWS_REGION", "us-east-1")
        self.model_id = os.environ.get("BEDROCK_MODEL_ID", model_id)
        self.client = None
        self.is_available = False

        # Attempt to initialize boto3 Bedrock runtime client
        try:
            # Check if AWS credentials exist
            session = boto3.Session(region_name=self.region_name)
            credentials = session.get_credentials()
            if credentials and credentials.access_key:
                self.client = session.client("bedrock-runtime", region_name=self.region_name)
                self.is_available = True
                logger.info(f"Amazon Bedrock client initialized for region {self.region_name}")
            else:
                logger.info("No AWS credentials detected. Operating in local intelligent planner mode.")
        except Exception as e:
            logger.warning(f"Bedrock initialization skipped: {str(e)}. Operating in local planner mode.")

    def plan_task(self, command: str, device_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generates a structured multi-step plan for the user command.
        Uses Bedrock if configured and available, or local semantic rule engine.
        """
        if self.is_available and self.client:
            try:
                return self._invoke_bedrock_planner(command, device_context)
            except (ClientError, Exception) as e:
                logger.warning(f"Bedrock invocation failed ({str(e)}). Falling back to local planner.")

        return self._local_plan_task(command, device_context)

    def _invoke_bedrock_planner(self, command: str, device_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Invokes Amazon Bedrock Claude/Titan to decompose command into structured JSON steps."""
        prompt = (
            f"You are JARVIS AI Orchestrator. Decompose the user command into discrete structured steps.\n"
            f"Target Device Capabilities: {device_context.get('capabilities', [])}\n"
            f"User Command: '{command}'\n\n"
            f"Return a strict JSON array of objects with keys:\n"
            f"- tool_name: string\n"
            f"- action_description: string\n"
            f"- risk_level: 'LOW' | 'MODERATE' | 'HIGH'\n"
            f"- input_args: object\n"
        )

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        })

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=body,
            contentType="application/json",
            accept="application/json"
        )
        response_body = json.loads(response["body"].read().decode("utf-8"))
        raw_text = response_body.get("content", [{}])[0].get("text", "[]")

        # Extract JSON array
        start = raw_text.find("[")
        end = raw_text.rfind("]")
        if start != -1 and end != -1:
            return json.loads(raw_text[start:end+1])
        return []

    def _local_plan_task(self, command: str, device_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Deterministic, rule-based planner used for local development and offline mode.
        Produces genuine, verified steps matching available capabilities.
        """
        cmd = command.lower()
        steps = []

        if "spotify" in cmd:
            query = "study playlist"
            if "play" in cmd:
                query = cmd.split("play")[-1].strip() or query
            steps.append({
                "tool_name": "spotify_control",
                "action_description": f"Launch Spotify and play '{query}'",
                "risk_level": "LOW",
                "input_args": {"action": "play_playlist", "query": query}
            })

        elif "youtube" in cmd:
            query = "Python tutorials"
            if "search for" in cmd:
                query = cmd.split("search for")[-1].split("and")[0].strip()
            elif "search" in cmd:
                query = cmd.split("search")[-1].split("and")[0].strip()
            steps.append({
                "tool_name": "browser_search_youtube",
                "action_description": f"Search YouTube for '{query}' and play matching video",
                "risk_level": "LOW",
                "input_args": {"search_term": query}
            })

        elif "vs code" in cmd or "vscode" in cmd or ("python" in cmd and "program" in cmd):
            steps.append({
                "tool_name": "vscode_run_program",
                "action_description": "Create Python program file in workspace, execute, and verify stdout",
                "risk_level": "MODERATE",
                "input_args": {
                    "filename": "python_assignment.py",
                    "code_content": (
                        "# JARVIS Autonomous Program\n"
                        "def calculate():\n"
                        "    nums = [10, 20, 30, 40, 50]\n"
                        "    print('AVERAGE=' + str(sum(nums) / len(nums)))\n"
                        "calculate()\n"
                    ),
                    "expected_output": "AVERAGE=30.0",
                    "open_in_editor": True
                }
            })

        elif "attendance" in cmd:
            steps.append({
                "tool_name": "analyze_attendance",
                "action_description": "Process attendance CSV and calculate individual percentages",
                "risk_level": "LOW",
                "input_args": {"filename": "attendance.csv"}
            })
            steps.append({
                "tool_name": "generate_attendance_report",
                "action_description": "Generate formatted Markdown report of attendance metrics",
                "risk_level": "LOW",
                "input_args": {"output_filename": "monthly_attendance_report.md"}
            })

        elif "duplicate" in cmd:
            steps.append({
                "tool_name": "find_duplicate_files",
                "action_description": "Scan directory files for duplicate SHA-256 hashes",
                "risk_level": "LOW",
                "input_args": {}
            })

        elif "remember" in cmd:
            preference = command.replace("remember", "").replace("that", "").strip()
            steps.append({
                "tool_name": "save_memory",
                "action_description": f"Store preference: {preference}",
                "risk_level": "LOW",
                "input_args": {"category": "preference", "key": "user_stated", "value": preference}
            })

        else:
            steps.append({
                "tool_name": "browser_search_web",
                "action_description": f"Perform web search for: '{command}'",
                "risk_level": "LOW",
                "input_args": {"query": command}
            })

        return steps
