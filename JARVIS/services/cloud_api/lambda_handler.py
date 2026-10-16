"""
JARVIS AI - AWS Lambda Entry Point Handler
Routes API Gateway HTTP API v2 events directly to the FastAPI cloud API.
"""

import json
from services.cloud_api.api import cloud_app
from fastapi.testclient import TestClient

# Pre-warmed test client to handle API Gateway events
test_client = TestClient(cloud_app)


def handler(event, context):
    """
    AWS Lambda entry point for API Gateway HTTP API (Payload format v2.0).
    """
    try:
        http_method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
        raw_path = event.get("rawPath", "/")
        headers = event.get("headers", {})
        body = event.get("body", "")

        # Route via FastAPI test client
        if http_method == "GET":
            response = test_client.get(raw_path, headers=headers)
        elif http_method == "POST":
            json_body = json.loads(body) if body else {}
            response = test_client.post(raw_path, json=json_body, headers=headers)
        elif http_method == "DELETE":
            response = test_client.delete(raw_path, headers=headers)
        else:
            response = test_client.request(http_method, raw_path, headers=headers)

        return {
            "statusCode": response.status_code,
            "headers": dict(response.headers),
            "body": response.text
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Lambda execution failed: {str(e)}"})
        }
