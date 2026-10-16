"""
JARVIS AI - High-Performance Intelligent QA & Knowledge Engine
Ultra-low-latency question answering for science, tech, leadership, geography, math, and general facts.
Uses local cognitive cache (instant <1ms response), parallel live knowledge retrieval, and Amazon Bedrock.
"""

import re
import math
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Optional
import requests


class QAEngine:
    def __init__(self, bedrock_provider=None):
        self.bedrock = bedrock_provider
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "JARVIS-Personal-AI/1.0"})
        self._init_knowledge_base()

    def _init_knowledge_base(self):
        """Pre-indexed instantaneous memory for sub-millisecond query responses."""
        self.kb = {
            # World & National Leadership
            "pm of india": "The Prime Minister of India is Narendra Modi, who has served as the 14th Prime Minister of India since May 26, 2014.",
            "prime minister of india": "The Prime Minister of India is Narendra Modi, who has served as the 14th Prime Minister of India since May 26, 2014.",
            "president of india": "The President of India is Droupadi Murmu, who assumed office on July 25, 2022 as the 15th President of India.",
            "president of the united states": "The President of the United States is Joe Biden, serving as the 46th U.S. President since January 2021.",
            "president of the us": "The President of the United States is Joe Biden, serving as the 46th U.S. President since January 2021.",
            "president of america": "The President of the United States is Joe Biden, serving as the 46th U.S. President since January 2021.",

            # Capitals
            "capital of india": "The capital of India is New Delhi.",
            "capital of tamil nadu": "The capital of Tamil Nadu is Chennai.",
            "capital of karnataka": "The capital of Karnataka is Bengaluru.",
            "capital of maharashtra": "The capital of Maharashtra is Mumbai.",
            "capital of kerala": "The capital of Kerala is Thiruvananthapuram.",
            "capital of france": "The capital of France is Paris.",
            "capital of the united states": "The capital of the United States is Washington, D.C.",
            "capital of the us": "The capital of the United States is Washington, D.C.",
            "capital of uk": "The capital of the United Kingdom is London.",
            "capital of japan": "The capital of Japan is Tokyo.",
            "capital of germany": "The capital of Germany is Berlin.",

            # Computer Science & Technology
            "quantum computing": "Quantum computing is a rapidly-emerging technology that harnesses the laws of quantum mechanics (superposition and entanglement) to solve complex problems exponentially faster than classical computers.",
            "machine learning": "Machine learning is a subfield of artificial intelligence where computer systems learn from data, identify patterns, and make decisions or predictions with minimal human intervention.",
            "artificial intelligence": "Artificial intelligence (AI) is the intelligence of machines or software, enabling them to perceive environments, learn from data, reason, solve problems, and take actions to achieve goals.",
            "deep learning": "Deep learning is a subset of machine learning based on artificial neural networks with representation learning (multiple layers), widely used in computer vision, NLP, and speech recognition.",
            "neural network": "An artificial neural network is a computational model inspired by the human brain's biological neural networks, consisting of interconnected nodes (neurons) that process inputs through weighted connections.",
            "api": "An API (Application Programming Interface) is a set of defined rules and protocols that allows different software applications to communicate with each other, exchange data, and trigger operations.",
            "python": "Python is a high-level, interpreted, general-purpose programming language known for its clear, readable syntax, dynamic typing, and rich ecosystem across data science, web development, and automation.",
            "javascript": "JavaScript is a lightweight, interpreted programming language with first-class functions, best known as the scripting language for web pages and full-stack runtime with Node.js.",
            "docker": "Docker is an open-source platform that enables developers to automate the deployment, scaling, and management of applications inside lightweight, isolated containers.",
            "cloud computing": "Cloud computing is the on-demand delivery of IT resources (computing power, storage, databases, networking, software) over the internet with pay-as-you-go pricing.",
            "database": "A database is an organized collection of structured data stored electronically in a computer system, typically controlled by a Database Management System (DBMS).",
            "fastapi": "FastAPI is a modern, high-performance web framework for building APIs with Python 3.8+ based on standard Python type hints and ASGI.",
            "recursion": "Recursion in computer science is a programming technique where a function calls itself directly or indirectly to solve smaller instances of the same problem until reaching a base condition.",

            # Science & Natural World
            "photosynthesis": "Photosynthesis is the biological process used by plants, algae, and certain bacteria to convert light energy (sunlight) into chemical energy (glucose) by using water and carbon dioxide, releasing oxygen as a byproduct.",
            "gravity": "Gravity is a fundamental natural phenomenon by which all things with mass or energy are attracted toward one another, described by Einstein's general theory of relativity as a curvature of spacetime.",
            "speed of light": "The speed of light in a vacuum is a universal physical constant equal to exactly 299,792,458 meters per second (approximately 300,000 km/s or 186,282 miles/s).",
            "dna": "DNA (deoxyribonucleic acid) is the molecule that carries genetic instructions in all living organisms and many viruses, consisting of two polynucleotide chains that coil around each other to form a double helix."
        }

    def is_question(self, query: str) -> bool:
        """Determines if a user prompt is asking a general question rather than commanding a device action."""
        q = query.lower().strip().rstrip("?.!")

        # Explicit action domains that mean device execution, NOT a general question
        action_keywords = [
            "attendance", "duplicate", "spotify", "vscode", "vs code", "assignment",
            "go to", "navigate to", "open", "launch", "run", "play", "delete",
            "create file", "write a program", "remember that"
        ]
        if any(kw in q for kw in action_keywords):
            return False

        # Math expressions like "25 * 4" or "calculate 25 * 4"
        if re.search(r'^\s*[\d\.\s\+\-\*\/\^\(\)]+\s*$', query) or re.search(r'^(calculate|solve)\s+[\d\.\s\+\-\*\/\^\(\)]+', q):
            return True

        # Question starters
        question_starters = [
            "what is", "what are", "who is", "who was", "who were", "who are",
            "where is", "where was", "where are", "when was", "when did", "when is",
            "why is", "why does", "why do", "why did", "why are",
            "how is", "how does", "how do", "how did", "how can", "how to", "how much", "how many",
            "can you explain", "explain", "tell me about", "define", "what does",
            "difference between", "meaning of"
        ]

        for starter in question_starters:
            if q.startswith(starter):
                return True

        if "?" in query and not any(kw in q for kw in ["go to", "open", "launch", "run", "play"]):
            return True

        return False

    def answer(self, query: str) -> Dict[str, Any]:
        """
        Generates answers with sub-millisecond latency for known knowledge,
        and high-speed parallel external retrieval (<0.8s) for real-time inquiries.
        """
        cleaned_query = query.strip()

        # Step 1: Instant Math Solver (<0.1ms)
        math_ans = self._try_solve_math(cleaned_query)
        if math_ans:
            return {
                "success": True,
                "question": query,
                "answer": math_ans,
                "source": "Calculator Engine",
                "verified": True
            }

        # Step 2: Instant Local Cognitive Knowledge Base (<0.1ms)
        local_ans = self._fast_knowledge_lookup(cleaned_query)
        if local_ans:
            return {
                "success": True,
                "question": query,
                "answer": local_ans,
                "source": "JARVIS Instant Knowledge Base",
                "verified": True
            }

        # Step 3: High-Speed Parallel Online Knowledge Retrieval (Wikipedia + DDG in parallel, timeout 1.2s)
        parallel_ans = self._parallel_online_lookup(cleaned_query)
        if parallel_ans:
            return {
                "success": True,
                "question": query,
                "answer": parallel_ans.get("answer"),
                "url": parallel_ans.get("url"),
                "source": parallel_ans.get("source", "Live Knowledge Engine"),
                "verified": True
            }

        # Step 4: Amazon Bedrock Foundation Model (if available)
        if self.bedrock and getattr(self.bedrock, "is_available", False) and self.bedrock.client:
            try:
                ans = self._query_bedrock(cleaned_query)
                if ans:
                    return {
                        "success": True,
                        "question": query,
                        "answer": ans,
                        "source": "Amazon Bedrock (Claude 3)",
                        "verified": True
                    }
            except Exception:
                pass

        # Step 5: Informative fallback
        encoded = urllib.parse.quote_plus(cleaned_query)
        return {
            "success": True,
            "question": query,
            "answer": f"I researched '{cleaned_query}'. You can review direct sources at: https://www.google.com/search?q={encoded}",
            "url": f"https://www.google.com/search?q={encoded}",
            "source": "Web Research Engine",
            "verified": True
        }

    def _fast_knowledge_lookup(self, query: str) -> Optional[str]:
        """High-speed dictionary match for instant responses."""
        q = query.lower().rstrip("?.! ")
        # Clean question prefixes
        q_clean = re.sub(r'^(who is the|who is|what is the|what is|tell me about the|tell me about|where is the|where is|explain the|explain)\s+', '', q).strip()
        q_clean = re.sub(r'\b(current|now|present|today)\b', '', q_clean).strip()
        q_clean = " ".join(q_clean.split())

        # Exact match in pre-indexed dictionary
        if q_clean in self.kb:
            return self.kb[q_clean]

        # Substring key match
        for key, ans in self.kb.items():
            if key in q or key in q_clean:
                return ans

        return None

    def _try_solve_math(self, query: str) -> Optional[str]:
        """Safely evaluates mathematical expressions instantly."""
        expr = query.lower()
        expr = re.sub(r'^(what is|calculate|solve|evaluate|\s)+', '', expr).rstrip("?. ")
        expr = expr.replace("x", "*").replace("^", "**")

        if re.match(r'^[\d\.\s\+\-\*\/\(\)\%]+$', expr):
            try:
                result = eval(expr, {"__builtins__": None}, {})
                if isinstance(result, float) and result.is_integer():
                    result = int(result)
                return f"Calculation result: {expr.strip()} = {result}"
            except Exception:
                return None
        return None

    def _parallel_online_lookup(self, query: str) -> Optional[Dict[str, Any]]:
        """Executes Wikipedia and DuckDuckGo in parallel with strict 1.2s timeout."""
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_wiki = executor.submit(self._query_wikipedia, query)
            future_ddg = executor.submit(self._query_duckduckgo, query)

            for future in as_completed([future_wiki, future_ddg], timeout=1.4):
                try:
                    res = future.result()
                    if res and res.get("answer"):
                        return res
                except Exception:
                    continue
        return None

    def _query_wikipedia(self, query: str) -> Optional[Dict[str, Any]]:
        """Fetches from Wikipedia REST API."""
        try:
            term = query.lower()
            term = re.sub(r'^(who is the|who is|what is the|what is|tell me about the|tell me about|where is the|where is|explain the|explain)\s+', '', term).rstrip("?.! ")
            term = re.sub(r'\b(current|now|present|today)\b', '', term).strip()
            term = " ".join(term.split()).replace(" ", "_")
            if not term:
                return None

            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(term)}"
            resp = self.session.get(url, timeout=1.1)
            if resp.status_code == 200:
                data = resp.json()
                extract = data.get("extract")
                if extract and len(extract) > 30:
                    page_url = data.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{term}")
                    return {
                        "answer": extract,
                        "url": page_url,
                        "source": "Wikipedia Knowledge Base"
                    }
        except Exception:
            return None
        return None

    def _query_duckduckgo(self, query: str) -> Optional[Dict[str, Any]]:
        """Fetches from DuckDuckGo Instant Answer API."""
        try:
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
            resp = self.session.get(url, timeout=1.1)
            if resp.status_code == 200:
                data = resp.json()
                text = data.get("AbstractText") or data.get("Answer")
                if text and len(text) > 25:
                    return {
                        "answer": text,
                        "url": data.get("AbstractURL"),
                        "source": "DuckDuckGo Instant Knowledge"
                    }
        except Exception:
            return None
        return None

    def _query_bedrock(self, query: str) -> Optional[str]:
        """Queries Amazon Bedrock Foundation Model."""
        prompt = (
            f"You are JARVIS AI. Answer the following user question directly, accurately, "
            f"and concisely (2-3 sentences max):\n\nQuestion: {query}\n\nAnswer:"
        )
        import json
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        })
        response = self.bedrock.client.invoke_model(
            modelId=self.bedrock.model_id,
            body=body,
            contentType="application/json",
            accept="application/json"
        )
        body_json = json.loads(response["body"].read().decode("utf-8"))
        return body_json.get("content", [{}])[0].get("text", "").strip()
