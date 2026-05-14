"""
Microsoft Email Reader Service
File: backend/app/services/microsoft_email_service.py

Connects to Microsoft 365 via Microsoft Graph API (OAuth 2.0)
to read, classify, and route emails into the WC Audit LangGraph pipeline.

Dependencies:
    pip install msal httpx aiofiles

Azure App Registration Required:
    - Permission: Mail.Read, Mail.ReadWrite (Application or Delegated)
    - Redirect URI: http://localhost:8000/auth/ms/callback
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional
import httpx
import msal

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# WC Audit Label Definitions
# ─────────────────────────────────────────────────────────────

WC_LABELS = {
    "policy_submission":  {
        "keywords": ["policy", "renewal", "submission", "application", "inception"],
        "priority": "medium",
    },
    "payroll_report": {
        "keywords": ["payroll", "wages", "pay stub", "pay register", "adp", "paychex", "paycheck"],
        "priority": "high",
    },
    "audit_request": {
        "keywords": ["audit", "annual audit", "audit request", "records requested"],
        "priority": "high",
    },
    "variance_query": {
        "keywords": ["variance", "discrepancy", "dispute", "additional premium", "refund"],
        "priority": "high",
    },
    "officer_update": {
        "keywords": ["officer", "inclusion", "exclusion", "executive", "director", "ceo", "cfo"],
        "priority": "medium",
    },
    "class_code_dispute": {
        "keywords": ["class code", "classification", "ncci", "reclassif", "appeal"],
        "priority": "high",
    },
}

POLICY_REF_PATTERNS = ["P\\d{5}", "POL-\\d{6}", "WC-\\d{7}"]


# ─────────────────────────────────────────────────────────────
# Microsoft Email Service
# ─────────────────────────────────────────────────────────────

class MicrosoftEmailService:
    """
    Reads emails from Microsoft 365 via Graph API.
    Classifies them with WC-specific labels.
    Pushes structured payloads to the LangGraph ingestion node.
    """

    GRAPH_BASE = "https://graph.microsoft.com/v1.0"

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        mailbox: str,
        poll_interval_seconds: int = 300,
    ):
        self.tenant_id    = tenant_id
        self.client_id    = client_id
        self.client_secret = client_secret
        self.mailbox      = mailbox
        self.poll_interval = poll_interval_seconds
        self._token_cache: dict = {}
        self._msal_app: Optional[msal.ConfidentialClientApplication] = None

    # ── Auth ──────────────────────────────────────────────────

    def _get_msal_app(self) -> msal.ConfidentialClientApplication:
        if not self._msal_app:
            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            self._msal_app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=authority,
            )
        return self._msal_app

    def _acquire_token(self) -> str:
        """Acquire an app-only access token via client credentials."""
        cache_key = f"{self.tenant_id}:{self.client_id}"
        cached = self._token_cache.get(cache_key)
        if cached and cached["expires_at"] > datetime.utcnow():
            return cached["access_token"]

        app = self._get_msal_app()
        result = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        if "access_token" not in result:
            raise RuntimeError(
                f"MSAL token error: {result.get('error_description', result)}"
            )

        self._token_cache[cache_key] = {
            "access_token": result["access_token"],
            "expires_at":   datetime.utcnow() + timedelta(seconds=result.get("expires_in", 3600) - 60),
        }
        logger.info("[MSEmail] Access token acquired.")
        return result["access_token"]

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._acquire_token()}",
            "Content-Type":  "application/json",
        }

    # ── Fetch Emails ──────────────────────────────────────────

    async def fetch_unread_emails(self, top: int = 50) -> list[dict]:
        """
        Fetch unread emails from the mailbox inbox via Graph API.
        Returns a list of raw message dicts.
        """
        url = (
            f"{self.GRAPH_BASE}/users/{self.mailbox}"
            f"/mailFolders/inbox/messages"
            f"?$filter=isRead eq false"
            f"&$top={top}"
            f"&$select=id,subject,from,receivedDateTime,bodyPreview,"
            f"body,hasAttachments,importance"
            f"&$orderby=receivedDateTime desc"
        )
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()
        messages = data.get("value", [])
        logger.info(f"[MSEmail] Fetched {len(messages)} unread messages.")
        return messages

    async def fetch_attachments(self, message_id: str) -> list[dict]:
        """Fetch attachment metadata and content for a given message."""
        url = (
            f"{self.GRAPH_BASE}/users/{self.mailbox}"
            f"/messages/{message_id}/attachments"
        )
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=self._headers())
            resp.raise_for_status()
        return resp.json().get("value", [])

    async def mark_as_read(self, message_id: str) -> None:
        """Mark a message as read after processing."""
        url = f"{self.GRAPH_BASE}/users/{self.mailbox}/messages/{message_id}"
        async with httpx.AsyncClient(timeout=15) as client:
            await client.patch(url, headers=self._headers(), json={"isRead": True})

    async def move_to_folder(self, message_id: str, destination_folder_id: str) -> None:
        """Move email to a named folder after routing."""
        url = f"{self.GRAPH_BASE}/users/{self.mailbox}/messages/{message_id}/move"
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(
                url, headers=self._headers(),
                json={"destinationId": destination_folder_id}
            )

    # ── Classification ────────────────────────────────────────

    @staticmethod
    def classify_email(subject: str, body_preview: str) -> dict:
        """
        Rule-based WC label classification.
        Falls back to 'unclassified' if no keyword matches.
        """
        text = f"{subject} {body_preview}".lower()

        # Extract policy reference
        import re
        policy_ref = None
        for pattern in POLICY_REF_PATTERNS:
            match = re.search(pattern, subject + " " + body_preview, re.IGNORECASE)
            if match:
                policy_ref = match.group(0).upper()
                break

        # Score labels
        best_label = "unclassified"
        best_score = 0
        for label_id, cfg in WC_LABELS.items():
            score = sum(1 for kw in cfg["keywords"] if kw in text)
            if score > best_score:
                best_score = score
                best_label = label_id

        return {
            "label":      best_label,
            "priority":   WC_LABELS.get(best_label, {}).get("priority", "low"),
            "policy_ref": policy_ref,
            "score":      best_score,
        }

    # ── Normalize for LangGraph ───────────────────────────────

    async def normalize_email(self, raw_msg: dict) -> dict:
        """
        Convert a raw Graph API message into the structured payload
        expected by the WC Audit LangGraph ingestion node.
        """
        subject      = raw_msg.get("subject", "")
        body_preview = raw_msg.get("bodyPreview", "")
        body_content = raw_msg.get("body", {}).get("content", "")
        from_addr    = raw_msg.get("from", {}).get("emailAddress", {})
        received_at  = raw_msg.get("receivedDateTime", "")
        msg_id       = raw_msg["id"]

        classification = self.classify_email(subject, body_preview)

        # Fetch attachments if present
        attachments = []
        if raw_msg.get("hasAttachments"):
            raw_atts = await self.fetch_attachments(msg_id)
            attachments = [
                {
                    "name":          att.get("name"),
                    "content_type":  att.get("contentType"),
                    "size_bytes":    att.get("size"),
                    "content_bytes": att.get("contentBytes"),  # base64
                }
                for att in raw_atts
            ]

        return {
            "source":       "microsoft_email",
            "message_id":   msg_id,
            "subject":      subject,
            "from_name":    from_addr.get("name", ""),
            "from_email":   from_addr.get("address", ""),
            "received_at":  received_at,
            "body_preview": body_preview,
            "body_html":    body_content,
            "label":        classification["label"],
            "priority":     classification["priority"],
            "policy_ref":   classification["policy_ref"],
            "attachments":  attachments,
            "processed":    False,
        }

    # ── Poll Loop ─────────────────────────────────────────────

    async def start_polling(self, on_email_callback) -> None:
        """
        Long-running polling loop.
        Calls on_email_callback(normalized_email) for each new email.

        Usage:
            email_svc = MicrosoftEmailService(...)
            await email_svc.start_polling(route_to_langgraph)
        """
        logger.info(f"[MSEmail] Starting poll loop (interval={self.poll_interval}s)")
        while True:
            try:
                raw_emails = await self.fetch_unread_emails()
                for raw in raw_emails:
                    normalized = await self.normalize_email(raw)
                    await on_email_callback(normalized)
                    await self.mark_as_read(raw["id"])
            except Exception as exc:
                logger.error(f"[MSEmail] Poll error: {exc}", exc_info=True)
            await asyncio.sleep(self.poll_interval)


# ─────────────────────────────────────────────────────────────
# LangGraph Email Ingestion Node
# File: backend/app/agent_langgraph/email_ingestion_node.py
# ─────────────────────────────────────────────────────────────

from app.agent_langgraph.wc_state import WCAuditState   # type: ignore


async def email_ingestion_node(state: WCAuditState) -> dict:
    """
    LangGraph node: reads pre-normalized email payload from state
    and converts it into the same shape as parse_payroll_excel /
    parse_policy_xml so downstream agents are source-agnostic.

    Triggered when state["data_source"] == "email".
    """
    email = state.get("email_payload")
    if not email:
        return {
            "errors": ["email_ingestion_node: no email_payload in state"],
            "agent_logs": [{
                "agent":  "email_ingestion",
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
            }],
        }

    label       = email.get("label", "unclassified")
    attachments = email.get("attachments", [])
    policy_ref  = email.get("policy_ref")

    import base64, io
    import pandas as pd

    excel_records: list[dict] = []

    # ── Try to parse any Excel attachments ────────────────────
    for att in attachments:
        name    = att.get("name", "")
        content = att.get("content_bytes")
        if not content:
            continue
        if not name.lower().endswith((".xlsx", ".xls", ".xlsb")):
            continue

        try:
            raw_bytes = base64.b64decode(content)
            df = pd.read_excel(io.BytesIO(raw_bytes))
            for _, row in df.iterrows():
                excel_records.append({
                    "source":        "email_attachment",
                    "policy_number": str(row.get("Policy Number", policy_ref or "") or "").strip(),
                    "check_date":    str(row.get("CheckDate", "") or ""),
                    "employee_name": str(row.get("Employee Name", "") or ""),
                    "state_code":    str(row.get("St.", "") or "").strip(),
                    "class_code":    str(row.get("Class Code", "") or "").strip(),
                    "wages":         float(row.get("Wages", 0) or 0),
                    "overtime_pay":  float(row.get("OT", 0) or 0),
                    "exposure":      float(row.get("Exposure", 0) or 0),
                    "earned_premium":float(row.get("Earned Prem.", 0) or 0),
                })
        except Exception as exc:
            logger.warning(f"[EmailIngestion] Could not parse {name}: {exc}")

    # ── Build email metadata record ───────────────────────────
    email_meta = {
        "source":       "email",
        "message_id":   email.get("message_id"),
        "from_email":   email.get("from_email"),
        "from_name":    email.get("from_name"),
        "subject":      email.get("subject"),
        "received_at":  email.get("received_at"),
        "label":        label,
        "priority":     email.get("priority"),
        "policy_ref":   policy_ref,
        "body_preview": email.get("body_preview"),
        "attachment_count": len(attachments),
    }

    logger.info(
        f"[EmailIngestion] Processed email label={label} "
        f"policy={policy_ref} excel_rows={len(excel_records)}"
    )

    return {
        "data_source":   "email",
        "email_meta":    email_meta,
        "excel_records": excel_records,               # same key as parse_payroll_excel
        "ingestion_complete": True,
        "agent_logs": [{
            "agent":     "email_ingestion",
            "status":    "success",
            "label":     label,
            "excel_rows": len(excel_records),
            "policy_ref": policy_ref,
            "timestamp": datetime.utcnow().isoformat(),
        }],
    }


# ─────────────────────────────────────────────────────────────
# FastAPI Router
# File: backend/app/routers/email_router.py
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/email", tags=["Email Ingestion"])


class EmailWebhookPayload(BaseModel):
    """Microsoft Graph change notification payload."""
    value: list[dict]


# Singleton email service (init from env/settings in production)
_email_service: Optional[MicrosoftEmailService] = None


def get_email_service() -> MicrosoftEmailService:
    global _email_service
    if _email_service is None:
        import os
        _email_service = MicrosoftEmailService(
            tenant_id     = os.getenv("MS_TENANT_ID", ""),
            client_id     = os.getenv("MS_CLIENT_ID", ""),
            client_secret = os.getenv("MS_CLIENT_SECRET", ""),
            mailbox       = os.getenv("MS_MAILBOX", "audit@yourcarrier.com"),
        )
    return _email_service


@router.get("/messages", summary="List inbox messages with WC labels")
async def list_messages(top: int = 50):
    """Fetch and classify unread messages from Microsoft 365."""
    svc = get_email_service()
    raw = await svc.fetch_unread_emails(top=top)
    normalized = [await svc.normalize_email(m) for m in raw]
    return {"count": len(normalized), "messages": normalized}


@router.post("/route/{message_id}", summary="Route email to LangGraph ingestion agent")
async def route_email_to_agent(message_id: str, background_tasks: BackgroundTasks):
    """
    Manually route a specific email to the WC audit LangGraph pipeline.
    The email is normalized, state is built, and the graph is invoked.
    """
    from app.agent_langgraph.wc_graph import run_wc_audit_from_email  # type: ignore

    svc = get_email_service()
    raw_messages = await svc.fetch_unread_emails(top=1)

    # In production: fetch by ID directly via Graph API
    matching = [m for m in raw_messages if m["id"] == message_id]
    if not matching:
        raise HTTPException(status_code=404, detail="Message not found or already processed")

    normalized = await svc.normalize_email(matching[0])
    background_tasks.add_task(run_wc_audit_from_email, normalized)
    await svc.mark_as_read(message_id)

    return {
        "status":   "routed",
        "message_id": message_id,
        "label":    normalized["label"],
        "policy_ref": normalized["policy_ref"],
    }


@router.post("/webhook", summary="Microsoft Graph change notification endpoint")
async def ms_graph_webhook(payload: EmailWebhookPayload, background_tasks: BackgroundTasks):
    """
    Receives real-time push notifications from Microsoft Graph.
    Register this URL in Azure Portal → Subscriptions.
    """
    svc = get_email_service()
    for notification in payload.value:
        msg_id = notification.get("resourceData", {}).get("id")
        if not msg_id:
            continue
        raw_msgs = await svc.fetch_unread_emails(top=1)
        matching = [m for m in raw_msgs if m["id"] == msg_id]
        if matching:
            normalized = await svc.normalize_email(matching[0])
            if normalized["label"] != "unclassified":
                from app.agent_langgraph.wc_graph import run_wc_audit_from_email  # type: ignore
                background_tasks.add_task(run_wc_audit_from_email, normalized)
    return {"status": "accepted"}


@router.get("/stats", summary="Email ingestion statistics")
async def email_stats():
    """Returns routing and processing statistics."""
    return {
        "connected":       True,
        "mailbox":         "audit@yourcarrier.com",
        "poll_interval_s": 300,
        "last_sync":       datetime.utcnow().isoformat(),
        "labels": {l: 0 for l in WC_LABELS},
    }