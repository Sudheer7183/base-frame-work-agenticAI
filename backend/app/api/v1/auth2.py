from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import os
from app.core.config import settings

router = APIRouter()

KEYCLOAK_URL   = os.getenv("KEYCLOAK_URL",   "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "agentic")
CLIENT_ID      = settings.KEYCLOAK_CLIENT_ID
CLIENT_SECRET  = settings.KEYCLOAK_CLIENT_SECRET


class TokenRequest(BaseModel):
    grant_type:    str                # "password" | "refresh_token"
    username:      Optional[str] = None   # grant_type=password only
    password:      Optional[str] = None   # grant_type=password only
    refresh_token: Optional[str] = None   # grant_type=refresh_token only


@router.post("/auth/token")
async def proxy_token(body: TokenRequest):
    """
    Single proxy endpoint for ALL Keycloak token operations.
    Browser never talks to Keycloak directly — no CORS issue from any subdomain.

    Supported grant types:
      grant_type=password       → login        (username + password)
      grant_type=refresh_token  → refresh      (refresh_token)
    """
    token_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"

    # ── Build form data based on grant type ───────────────────────────────────
    form_data: dict = {
        "grant_type": body.grant_type,
        "client_id":  CLIENT_ID,
        "client_secret":CLIENT_SECRET
    }

    # Only add client_secret if it is configured (confidential clients)
    if CLIENT_SECRET:
        form_data["client_secret"] = CLIENT_SECRET

    if body.grant_type == "password":
        if not body.username or not body.password:
            raise HTTPException(status_code=422, detail="username and password required for password grant")
        form_data["username"] = body.username
        form_data["password"] = body.password

    elif body.grant_type == "refresh_token":
        if not body.refresh_token:
            raise HTTPException(status_code=422, detail="refresh_token required for refresh_token grant")
        form_data["refresh_token"] = body.refresh_token

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported grant_type: {body.grant_type}")

    # ── Forward to Keycloak server-to-server (no CORS) ────────────────────────
    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if not response.is_success:
        error_body = response.json() if response.content else {}
        raise HTTPException(
            status_code=response.status_code,
            detail=error_body.get("error_description", "Keycloak token request failed"),
        )

    return response.json()  # access_token, refresh_token, expires_in etc. — same shape as Keycloak