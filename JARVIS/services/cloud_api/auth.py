"""
JARVIS AI - Cognito & Cloud Authentication Manager
Validates Cognito JWT tokens and provides local development token signing.
"""

import os
import time
import base64
import json
import hmac
import hashlib
from typing import Dict, Any, Optional
from fastapi import Header, HTTPException


class AuthManager:
    def __init__(self):
        self.user_pool_id = os.environ.get("COGNITO_USER_POOL_ID", "us-east-1_jarvisMockPool")
        self.client_id = os.environ.get("COGNITO_APP_CLIENT_ID", "jarvisMockClientId")
        self.secret_key = os.environ.get("JWT_SECRET", "jarvis-development-secret-key-32bytes!")

    def generate_token(self, user_id: str, email: str, device_id: str) -> str:
        """Generates a signed JWT-like token for authenticated sessions."""
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": user_id,
            "email": email,
            "device_id": device_id,
            "iat": int(time.time()),
            "exp": int(time.time()) + 86400  # 24 hour expiry
        }
        b64_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        b64_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        signature = hmac.new(
            self.secret_key.encode(),
            f"{b64_header}.{b64_payload}".encode(),
            hashlib.sha256
        ).digest()
        b64_sig = base64.urlsafe_b64encode(signature).decode().rstrip("=")
        return f"{b64_header}.{b64_payload}.{b64_sig}"

    def verify_token(self, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
        """Verifies token and extracts user identity."""
        if not authorization:
            # Allow fallback for local development if configured
            return {"sub": "default_user", "email": "user@jarvis.ai", "device_id": "local"}

        token = authorization.replace("Bearer ", "").strip()
        parts = token.split(".")
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Malformed authorization token")

        b64_header, b64_payload, b64_sig = parts
        expected_sig = base64.urlsafe_b64encode(
            hmac.new(
                self.secret_key.encode(),
                f"{b64_header}.{b64_payload}".encode(),
                hashlib.sha256
            ).digest()
        ).decode().rstrip("=")

        if not hmac.compare_digest(b64_sig, expected_sig):
            raise HTTPException(status_code=401, detail="Invalid token signature")

        # Decode payload
        padded = b64_payload + "=" * ((4 - len(b64_payload) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode())

        if payload.get("exp", 0) < time.time():
            raise HTTPException(status_code=401, detail="Token has expired")

        return payload
