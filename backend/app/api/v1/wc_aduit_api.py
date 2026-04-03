

"""
Workers' Compensation Audit API  —  v5 (Redis Stream pipeline)
==============================================================
Changes from v4
───────────────
• _AUDIT_REGISTRY is GONE.  All state lives in PostgreSQL (wc_audit_cases).
• /start creates the DB row then XADD to Redis Stream — returns immediately.
• /status queries the DB directly instead of the in-memory dict.
• /cases  queries the DB directly.
• HITL endpoints use app.services.hitl_store (asyncio.Event shared with the
  background worker — same process, same event loop).
• BackgroundTasks import removed — the LangGraph graph runs in the consumer
  worker (app/workers/variance_consumer.py), not in a BackgroundTask here.
• Report download still reads the file path from the DB AuditReport row.

File: backend/app/api/v1/wc_aduit_api.py
"""

import os
import logging
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import (
    APIRouter, HTTPException, UploadFile, File,
    Depends, Request,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import text

from app.tenancy.dependencies import require_tenant
from app.tenancy.models import Tenant
from app.core.database import SessionLocal
from app.agent_langgraph.wc_nodes.wc_rbac import (
    WCUser,
    require_wc_super_admin,
    require_wc_admin,
    require_wc_agent,
)

# ── ORM models ────────────────────────────────────────────────────────────────
try:
    from app.models.wc_audit import (
        AuditCase, Policy, VarianceLine, AgentFinding, AuditReport,
    )
    _WC_MODELS_AVAILABLE = True
except ImportError:
    _WC_MODELS_AVAILABLE = False

# ── Queue / HITL services ─────────────────────────────────────────────────────
from app.services.audit_queue import get_redis, push_to_pipeline
from app.services import hitl_store
from app.agent_langgraph.wc_nodes.hitl_checkpoint import get_pending_reviews


# caches importing

from app.core.cache import get_cache_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/wc-audit", tags=["Workers Comp Audit"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/wc_audit_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic request/response schemas
# ─────────────────────────────────────────────────────────────────────────────

class StartAuditRequest(BaseModel):
    policy_number:        str
    payroll_file_path:    Optional[str] = None
    policy_xml_path:      Optional[str] = None
    audit_meta_file_path: Optional[str] = None


class HITLDecisionRequest(BaseModel):
    decision:      str                    # "approve" | "reject" | "override"
    reviewer_id:   str  = "frontend_user" # optional — old frontend doesn't send it
    notes:         str  = ""
    override_data: Optional[dict] = None


# ─────────────────────────────────────────────────────────────────────────────
# Tenant / DB helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_schema(tenant: Tenant) -> str:
    return getattr(tenant, "schema_name", "public")


def _db_session(schema: str):
    """Return a SQLAlchemy session with search_path set for the tenant schema."""
    db = SessionLocal()
    db.execute(text(f'SET search_path TO "{schema}", public'))
    return db


# ─────────────────────────────────────────────────────────────────────────────
# Cache intializing helpers
# ─────────────────────────────────────────────────────────────────────────────

def _cache_key_cases(tenant_slug: str) ->str:
    return f"wc:cases:{tenant_slug}"

def _cache_key_status(audit_case_id:int,tenant_slug: str) -> str:
    return f"wc:status:{tenant_slug}:{audit_case_id}"

def _ttl_for_status(status: str) ->int:
    if status in ("completed", "rejected", "error"):
        return 300
    
    if status == "hitl_pending":
        return 5

    return 3

async def _invalidate_case(audit_case_id: int, tenant_slug: str):
    cache =get_cache_manager()
    await cache.delete(_cache_key_status(audit_case_id,tenant_slug))
    await cache.delete(_cache_key_cases(tenant_slug))





# ─────────────────────────────────────────────────────────────────────────────
# Status / frequency display helpers  (restored from v3)
# ─────────────────────────────────────────────────────────────────────────────

_FE_STATUS_MAP = {
    "pending":    "pending",
    "ingesting":  "processing",
    "processing": "processing",
    "review":     "hitl_pending",
    "approved":   "completed",
    "completed":  "completed",
    "rejected":   "rejected",
    "error":      "error",
}

_FREQ_LABELS = {
    "1W": "Weekly",  "2W": "Bi-Weekly",  "SM": "Semi-Monthly",
    "1M": "Monthly", "M":  "Monthly",    "Q":  "Quarterly",
    "WEEKLY": "Weekly", "BIWEEKLY": "Bi-Weekly", "MONTHLY": "Monthly",
}

# ── Agent name normalisation ──────────────────────────────────────────────────
# Maps every possible agent identifier (DB agent_name, LangGraph node name,
# streaming log key) → the lowercase snake_case key the frontend reads.
#
# Frontend agentLabels in WCAuditApp.jsx:
#   ingestion_excel / ingestion_audit_meta  → Ingestion Agent
#   ingestion_xml                           → Policy Parser
#   officer_agent                           → Officer Agent
#   class_code_agent                        → Class Code Agent
#   frequency_agent                         → Frequency Agent
#   premium_agent / risk_assessor           → Premium Agent
#   explanation_agent                       → Explanation Agent
_AGENT_KEY_MAP = {
    # LangGraph node names (used in streaming agent_logs during processing)
    "parse_payroll_excel":  "ingestion_excel",
    "parse_policy_xml":     "ingestion_xml",
    "parse_audit_metadata": "ingestion_audit_meta",
    "officer_agent":        "officer_agent",
    "class_code_agent":     "class_code_agent",
    "frequency_agent":      "frequency_agent",
    "calculate_variance":   "premium_agent",
    "assess_risk":          "risk_assessor",
    "explanation_agent":    "explanation_agent",
    "generate_report":      "explanation_agent",
    "persist_to_database":  "explanation_agent",
    "hitl_checkpoint":      "hitl_checkpoint",
    # wc_agent_findings agent_name values (camelCase from DB persistence node)
    "OfficerAgent":         "officer_agent",
    "ClassCodeAgent":       "class_code_agent",
    "FrequencyAgent":       "frequency_agent",
    "PremiumAgent":         "premium_agent",
    "ExplanationAgent":     "explanation_agent",
    "RiskAssessor":         "risk_assessor",
    "IngestionAgent":       "ingestion_excel",
    "PolicyParser":         "ingestion_xml",
    # Already-correct keys pass through
    "ingestion_excel":      "ingestion_excel",
    "ingestion_xml":        "ingestion_xml",
    "ingestion_audit_meta": "ingestion_audit_meta",
    "premium_agent":        "premium_agent",
    "risk_assessor":        "risk_assessor",
}

# All frontend pipeline step keys — emitted when a case reaches "completed"
# so every step lights up green regardless of whether individual logs survived.
_ALL_PIPELINE_KEYS = [
    "ingestion_excel",
    "ingestion_xml",
    "ingestion_audit_meta",
    "officer_agent",
    "class_code_agent",
    "frequency_agent",
    "premium_agent",
    "risk_assessor",
    "explanation_agent",
]


def _normalise_agent_logs(raw_logs: list) -> list:
    """
    Normalise a list of agent_log dicts so every entry has a frontend-compatible
    'agent' key.  Entries whose agent name can't be mapped are passed through
    unchanged — the frontend simply ignores unknown keys.
    """
    out = []
    for log in raw_logs:
        if not isinstance(log, dict):
            continue
        key = log.get("agent", "")
        normalised = _AGENT_KEY_MAP.get(key, key)
        out.append({**log, "agent": normalised})
    return out


def _fmt_date(val) -> str:
    """Convert a date/datetime/string to 'Mon YYYY' display format."""
    if not val:
        return ""
    from datetime import datetime as _dt, date as _date
    try:
        if isinstance(val, (_dt, _date)):
            return val.strftime("%b %Y")
        s = str(val).strip()
        if not s or s.lower() in ("none", "nat", ""):
            return ""
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%m-%d-%Y"):
            try:
                return _dt.strptime(s, fmt).strftime("%b %Y")
            except ValueError:
                pass
    except Exception:
        pass
    return str(val)


def _map_frequency(freq) -> str:
    if not freq:
        return ""
    return _FREQ_LABELS.get(str(freq).strip().upper(), str(freq))


# ─────────────────────────────────────────────────────────────────────────────
# Core ORM → dict converter  (restored rich mapping from v3)
# ─────────────────────────────────────────────────────────────────────────────

def _db_case_to_dict(case: "AuditCase", live_hitl_check: bool = True) -> dict:
    """
    Convert an AuditCase ORM object (with relationships already loaded) into
    the standard response dict that the React frontend expects.

    Key points:
    • class_code_variance uses 'StateCode'/'ClassCode' (capital) — matches frontend
    • agent_logs built from wc_agent_findings relationship (always available)
    • Additional logs from AuditReport.report_json merged in if present
    • All policy-level fields (effective_date, payment_frequency, etc.) included
    """
    policy = case.policy
    
    # ── Status mapping ────────────────────────────────────────────────
    fe_status = _FE_STATUS_MAP.get(str(case.status or "").lower(), str(case.status or "pending"))
    if live_hitl_check and hitl_store.is_pending(case.id):
        fe_status = "hitl_pending"

    # ── Overall variance ──────────────────────────────────────────────
    overall_variance = {
        "earned_exposure": float(case.total_earned_exposure or 0),
        "earned_premium":  float(case.total_earned_premium  or 0),
        "est_exposure":    float(case.total_est_exposure    or 0),
        "est_ytd_premium": float(case.total_est_ytd_premium or 0),
        "variance":        float(case.total_variance        or 0),
        "variance_pct":    float(case.total_variance_pct    or 0),
    }

    # ── Per-class-code variance lines ─────────────────────────────────
    # NOTE: key names use 'StateCode'/'ClassCode' (capital) — this is what
    # the React VarianceAnalysis component and Policies table read.
    class_code_variance = [
        {
            "StateCode":       v.state_code,
            "ClassCode":       v.class_code,
            "earned_exposure": float(v.earned_exposure or 0),
            "earned_premium":  float(v.earned_premium  or 0),
            "est_exposure":    float(v.est_exposure    or 0) if hasattr(v, "est_exposure") else 0.0,
            "est_ytd_premium": float(v.est_ytd_premium or 0),
            "variance":        float(v.variance        or 0),
            "variance_pct":    float(v.variance_pct    or 0),
            "root_cause":      v.root_cause,
            "is_flagged":      bool(v.is_flagged) if hasattr(v, "is_flagged") else False,
        }
        for v in (case.variance_lines or [])
    ]

    # ── Agent logs — source priority ──────────────────────────────────
    #
    # Priority 1: AuditReport.report_json (written incrementally by the
    #   consumer worker as each node completes — has correct node-name keys)
    #
    # Priority 2: wc_agent_findings (written by db_persistence at the end —
    #   has camelCase names like "OfficerAgent" that need normalisation)
    #
    # Priority 3: If case is "completed"/"approved" and neither source has
    #   logs, synthesise a full "all done" list so every pipeline step lights up.
    #
    report = case.report
    report_file_path = ""
    raw_logs = []

    if report:
        report_file_path = report.report_file or ""
        if report.report_json and isinstance(report.report_json, dict):
            raw_logs = report.report_json.get("agent_logs", [])

    if not raw_logs and case.agent_findings:
        # Fall back to wc_agent_findings — normalise camelCase names
        raw_logs = [
            {
                "agent":        f.agent_name,
                "finding_type": f.finding_type,
                "status":       "success",
                "severity":     f.severity,
                "summary":      f.summary,
            }
            for f in case.agent_findings
        ]

    # Normalise all agent keys to frontend-compatible snake_case
    agent_logs = _normalise_agent_logs(raw_logs)

    # For terminal states, guarantee every pipeline step shows "complete"
    # by filling in any missing keys. This ensures the UI always shows
    # the full green pipeline after completion — even if some nodes didn't
    # write logs (e.g. the graph skipped a branch).
    if case.status in ("completed", "approved", "rejected"):
        existing_keys = {log.get("agent") for log in agent_logs}
        ts = case.completed_at.isoformat() if case.completed_at else datetime.utcnow().isoformat()
        for key in _ALL_PIPELINE_KEYS:
            if key not in existing_keys:
                agent_logs.append({
                    "agent":     key,
                    "status":    "complete",
                    "timestamp": ts,
                    "summary":   "Completed",
                })
        # Ensure all existing logs also read as "complete" (not "success")
        # because the frontend checks `log.status === "complete"` specifically
        agent_logs = [
            {**log, "status": "complete"} if log.get("status") in ("success", "skipped", "complete") else log
            for log in agent_logs
        ]

    # ── Officer summary from findings ─────────────────────────────────
    officer_issues = [
        f for f in (case.agent_findings or [])
        if f.agent_name == "OfficerAgent"
        and f.severity in ("warning", "critical")
    ]

    return {
        # ── Identity ──────────────────────────────────────────────────
        "audit_case_id":        case.id,
        "policy_number":        policy.policy_number if policy else "",
        "status":               fe_status,
        "current_stage":        case.status,
        # ── Risk / recommendation ─────────────────────────────────────
        "risk_level":           case.risk_level or "unknown",
        "recommendation":       case.recommendation or "",
        "hitl_required":        bool(case.hitl_required),
        # ── Variance numbers (also as direct top-level fields) ────────
        "variance":             float(case.total_variance     or 0),
        "variance_pct":         float(case.total_variance_pct or 0),
        "overall_variance":     overall_variance,
        "class_code_variance":  class_code_variance,
        # ── AI narrative ──────────────────────────────────────────────
        "ai_narrative":         case.ai_narrative or "",
        # ── Agent pipeline logs ───────────────────────────────────────
        "agent_logs":           agent_logs,
        # ── Policy-level fields (from wc_policies JOIN) ───────────────
        "effective_date":       _fmt_date(policy.effective_date   if policy else None),
        "expiration_date":      _fmt_date(policy.expiration_date  if policy else None),
        "payment_frequency":    _map_frequency(policy.payroll_frequency if policy else None),
        "insured_name":str(policy.insured_name if policy else None),
        # ── Audit timeline ────────────────────────────────────────────
        "submitted_count":      case.submitted_count,
        "expected_submissions": case.expected_submissions,
        "first_check_date":     str(case.first_check_date) if case.first_check_date else None,
        "last_check_date":      str(case.last_check_date)  if case.last_check_date  else None,
        # ── Officer summary ───────────────────────────────────────────
        "officer_count":        len(policy.officers) if (policy and policy.officers) else None,
        "officer_issues_count": len(officer_issues),
        # ── Timestamps & report ───────────────────────────────────────
        "created_at":           case.created_at.isoformat() if case.created_at else None,
        "completed_at":         case.completed_at.isoformat() if case.completed_at else None,
        "report_file_path":     report_file_path,
        "errors":               case.auditor_notes if case.status == "error" else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Internal DB helpers
# ─────────────────────────────────────────────────────────────────────────────

# def _db_create_case(
#     schema:               str,
#     policy_number:        str,
#     payroll_file_path:    str,
#     policy_xml_path:      str,
#     audit_meta_file_path: str,
#     tenant_id:            str,
# ) -> AuditCase:
#     """
#     Ensure wc_policies row exists and create a wc_audit_cases row with
#     status="pending".  Returns the persisted AuditCase ORM object.
#     """
#     db = _db_session(schema)
#     try:
#         policy = (
#             db.query(Policy)
#             .filter(Policy.policy_number == policy_number)
#             .first()
#         )
#         if policy is None:
#             policy = Policy(
#                 policy_number     = policy_number,
#                 insured_name      = "Pending",
#                 effective_date    = datetime.utcnow().date(),
#                 expiration_date   = datetime.utcnow().date(),
#                 state_code        = "XX",
#                 is_active         = True,
#             )
#             db.add(policy)
#             db.flush()

#         temp_ref = f"WCA-{policy_number}-{uuid.uuid4().hex[:8]}"
#         case = AuditCase(
#             policy_id             = policy.id,
#             audit_reference       = temp_ref,
#             status                = "pending",
#             payroll_file_path     = payroll_file_path,
#             policy_xml_path       = policy_xml_path,
#             audit_meta_file_path  = audit_meta_file_path,
#             created_at            = datetime.utcnow(),
#             updated_at            = datetime.utcnow(),
#         )
#         db.add(case)
#         db.commit()
#         db.refresh(case)
#         logger.info(f"[API] AuditCase created: id={case.id}  policy={policy_number}  schema={schema}")
#         return case
#     except Exception:
#         db.rollback()
#         raise
#     finally:
#         db.close()


def _db_create_case(
    schema:               str,
    policy_number:        str,
    payroll_file_path:    str,
    policy_xml_path:      str,
    audit_meta_file_path: str,
    tenant_id:            str,
) -> "AuditCase":
    """
    Ensure wc_policies row exists and create a wc_audit_cases row with
    status="pending".  Returns the persisted AuditCase ORM object.
    """
    db = _db_session(schema)
    try:
        policy = (
            db.query(Policy)
            .filter(Policy.policy_number == policy_number)
            .first()
        )
        if policy is None:
            policy = Policy(
                policy_number  = policy_number,
                insured_name   = " ",
                effective_date = datetime.utcnow().date(),
                expiration_date= datetime.utcnow().date(),
                state_code     = "XX",
                is_active      = True,
            )
            db.add(policy)
            db.flush()
 
        # ── FIX: use a placeholder reference first, then update after flush ──
        # We need case.id to build the reference, but case.id isn't assigned
        # until after db.flush(). Strategy: INSERT with a temp ref, then
        # immediately UPDATE it to the canonical format.
        case = AuditCase(
            policy_id            = policy.id,
            audit_reference      = f"WCA-{policy_number}-PENDING",  # temp placeholder
            status               = "pending",
            payroll_file_path    = payroll_file_path,
            policy_xml_path      = policy_xml_path,
            audit_meta_file_path = audit_meta_file_path,
            created_at           = datetime.utcnow(),
            updated_at           = datetime.utcnow(),
        )
        db.add(case)
        db.flush()  # case.id is now assigned by PostgreSQL SERIAL
 
        # ── FIX: update to the canonical reference format ──────────────────
        # This must match EXACTLY what persist_to_database generates:
        #   f"WCA-{policy_number}-{audit_case_id}"
        case.audit_reference = f"WCA-{policy_number}-{case.id}"
        db.commit()
        db.refresh(case)
 
        logger.info(
            f"[API] AuditCase created: id={case.id}  "
            f"ref={case.audit_reference}  policy={policy_number}  schema={schema}"
        )
        return case
 
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def _db_fetch_case(audit_case_id: int, schema: str) -> Optional[dict]:
    """
    Return the full status/result dict for the /status endpoint.
    Uses a JOIN so all relationship data (variance_lines, agent_findings,
    policy, report) is loaded in one query round-trip.
    """
    if not _WC_MODELS_AVAILABLE:
        return None

    db = _db_session(schema)
    try:
        case = (
            db.query(AuditCase)
            .join(Policy, Policy.id == AuditCase.policy_id)
            .filter(AuditCase.id == audit_case_id)
            .first()
        )
        if not case:
            return None
        return _db_case_to_dict(case, live_hitl_check=True)

    except Exception as exc:
        logger.error(f"[API] _db_fetch_case error: {exc}", exc_info=True)
        return None
    finally:
        db.close()


def _db_list_cases(schema: str) -> List[dict]:
    """
    Return summary list for the /cases endpoint.
    Joins Policy so insured_name, effective_date, expiration_date are available.
    All relationship data loaded via SQLAlchemy lazy-load within the session.
    """
    if not _WC_MODELS_AVAILABLE:
        return []

    db = _db_session(schema)
    try:
        cases = (
            db.query(AuditCase)
            .join(Policy, Policy.id == AuditCase.policy_id)
            .order_by(AuditCase.created_at.desc())
            .limit(200)
            .all()
        )
        return [_db_case_to_dict(c, live_hitl_check=False) for c in cases]

    except Exception as exc:
        logger.error(f"[API] _db_list_cases error: {exc}", exc_info=True)
        return []
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# File Upload
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_audit_files(
    payroll_file: UploadFile = File(..., description="Payroll Excel (.xlsx)"),
    policy_xml:   UploadFile = File(..., description="Policy XML (.xml)"),
    audit_meta:   UploadFile = File(None, description="Audit metadata Excel (.xlsx) — optional"),
    tenant: Tenant = Depends(require_tenant),
    user:   WCUser = Depends(require_wc_super_admin),
):
    """Upload the three source files and get back their server-side paths."""
    session_id = str(uuid.uuid4())[:8]
    paths = {}

    for upload, key in [
        (payroll_file, "payroll_file_path"),
        (policy_xml,   "policy_xml_path"),
        (audit_meta,   "audit_meta_file_path"),
    ]:
        if upload is None:
            continue
        ext      = os.path.splitext(upload.filename)[1]
        savepath = os.path.join(UPLOAD_DIR, f"{session_id}_{key}{ext}")
        with open(savepath, "wb") as f:
            f.write(await upload.read())
        paths[key] = savepath
        logger.info(f"[Upload] Saved {upload.filename} → {savepath}")

    return {"session_id": session_id, **paths}


# ─────────────────────────────────────────────────────────────────────────────
# Start Audit  ← main change: creates DB row + XADD, no BackgroundTask
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/start")
async def start_audit(
    request: StartAuditRequest,
    tenant:  Tenant = Depends(require_tenant),
):
    """
    Start a Workers' Compensation audit workflow.

    Flow
    ────
    1. Validate that the required file paths are present.
    2. Create an AuditCase row in PostgreSQL (status="pending").
    3. XADD the case onto the Redis Stream — the background worker picks it up.
    4. Return immediately with audit_case_id.

    The LangGraph graph runs asynchronously in the worker process.
    Poll /status/{audit_case_id} to track progress.
    """
    missing = [
        f for f in ["payroll_file_path", "policy_xml_path"]
        if not getattr(request, f)
    ]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required file paths: {', '.join(missing)}",
        )

    schema = _get_schema(tenant)

    # ── Step 1: Create persistent DB record ──────────────────────────
    try:
        case = _db_create_case(
            schema               = schema,
            policy_number        = request.policy_number,
            payroll_file_path    = request.payroll_file_path    or "",
            policy_xml_path      = request.policy_xml_path      or "",
            audit_meta_file_path = request.audit_meta_file_path or "",
            tenant_id            = tenant.slug,
        )
    except Exception as exc:
        logger.error(f"[API /start] DB create failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create audit case: {exc}")

    # ── Step 2: Push to Redis Stream (the belt) ───────────────────────
    try:
        redis = get_redis()
        await push_to_pipeline(
            redis                = redis,
            audit_case_id        = case.id,
            policy_number        = request.policy_number,
            tenant_id            = tenant.slug,
            schema_name          = schema,
            payroll_file_path    = request.payroll_file_path    or "",
            policy_xml_path      = request.policy_xml_path      or "",
            audit_meta_file_path = request.audit_meta_file_path or "",
        )
    except Exception as exc:
        logger.error(f"[API /start] Redis XADD failed: {exc}", exc_info=True)
        # The DB row exists — mark it as error so it's visible
        db = _db_session(schema)
        try:
            c = db.query(AuditCase).filter(AuditCase.id == case.id).first()
            if c:
                c.status = "error"
                c.auditor_notes = f"Redis push failed: {exc}"
                db.commit()
        finally:
            db.close()
        raise HTTPException(
            status_code=503,
            detail=f"Audit case created (id={case.id}) but queueing failed: {exc}",
        )

    logger.info(
        f"[API /start] Audit queued: case_id={case.id}  "
        f"policy={request.policy_number}  tenant={tenant.slug}"
    )

    await _invalidate_case(case.id, tenant.slug)

    return {
        "audit_case_id": case.id,
        "status":        "pending",
        "message":       (
            f"Audit workflow queued. "
            f"Poll /api/v1/wc-audit/status/{case.id} for progress."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Status Poll  ← reads from DB instead of _AUDIT_REGISTRY
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/status/{audit_case_id}")
async def get_audit_status(
    audit_case_id: int,
    tenant: Tenant = Depends(require_tenant),
):
    """
    Return the current status and partial results of an audit case.
    Reads directly from PostgreSQL — no in-memory registry involved.
    """
    schema = _get_schema(tenant)
    cache  = get_cache_manager()
    key    = _cache_key_status(audit_case_id, tenant.slug)

    cached = await cache.get(key)
    if cached is not None:
        return cached

    entry  = _db_fetch_case(audit_case_id, schema)

    if entry is None:
        raise HTTPException(status_code=404, detail="Audit case not found.")

    ttl = _ttl_for_status(entry["status"])
    await cache.set(key, entry, ttl=ttl)
    return entry


# ─────────────────────────────────────────────────────────────────────────────
# List Cases
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/cases")
async def list_audit_cases(
    tenant: Tenant = Depends(require_tenant),
):
    """Return a summary list of the most recent 200 audit cases for this tenant."""

    schema = _get_schema(tenant)

    cache = get_cache_manager()
    

    # --- END DIAGNOSTICS ---
    print("tenant slug while getting the tenanat",tenant.slug)
    key = _cache_key_cases(tenant.slug)

    # return _db_list_cases(schema)
    return await cache.get_or_set(
        key,
        lambda : _db_list_cases(schema),
        ttl=30
    )


# ─────────────────────────────────────────────────────────────────────────────
# HITL — list pending reviews
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/hitl/pending")
async def list_hitl_pending(
    tenant: Tenant = Depends(require_tenant),
    user:   WCUser = Depends(require_wc_admin),
):
    """
    Return all audit cases currently paused for human review.
    Combines the live asyncio event store with any DB rows in 'review' status.
    """
    live_pending_ids = hitl_store.all_pending_ids()
    schema = _get_schema(tenant)
    db_pending = []

    if _WC_MODELS_AVAILABLE:
        db = _db_session(schema)
        try:
            rows = (
                db.query(AuditCase)
                .filter(AuditCase.status.in_(["review", "approved"]))
                .all()
            )
            db_pending = [
                {
                    "audit_case_id":  r.id,
                    "policy_number":  r.policy.policy_number if r.policy else "",
                    "status":         r.status,
                    "risk_level":     r.risk_level or "unknown",
                    "hitl_required":  r.hitl_required,
                }
                for r in rows
            ]
        finally:
            db.close()

    # Merge: use DB as base, mark truly-live ones
    for item in db_pending:
        item["live"] = item["audit_case_id"] in live_pending_ids

    return {
        "pending_cases":   db_pending,
        "live_event_ids":  live_pending_ids,
    }


# ─────────────────────────────────────────────────────────────────────────────
# HITL — submit decision
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/hitl-decision/{audit_case_id}")
async def submit_hitl_decision(
    audit_case_id: int,
    body:   HITLDecisionRequest,
    tenant: Tenant = Depends(require_tenant),
    user:   WCUser = Depends(require_wc_admin),
):
    """
    Submit a human-in-the-loop decision for a paused audit case.

    The asyncio.Event shared with the background worker is set here,
    which unblocks the graph and allows it to continue.
    """
    valid_decisions = {"approve", "reject", "override"}
    if body.decision not in valid_decisions:
        raise HTTPException(
            status_code=400,
            detail=f"decision must be one of: {valid_decisions}",
        )

    # ── Signal the waiting graph via shared asyncio event ────────────
    resolved = hitl_store.resolve(
        audit_case_id  = audit_case_id,
        decision       = body.decision,
        reviewer_id    = body.reviewer_id,
        notes          = body.notes,
        override_data  = body.override_data,
    )

    if not resolved:
        # Case may have already completed or the event was never registered
        # Update DB status directly and return gracefully
        if _WC_MODELS_AVAILABLE:
            schema = _get_schema(tenant)
            db = _db_session(schema)
            try:
                c = db.query(AuditCase).filter(AuditCase.id == audit_case_id).first()
                if c:
                    c.status            = "approved" if body.decision == "approve" else "rejected"
                    c.hitl_approved_by  = body.reviewer_id
                    c.hitl_notes        = body.notes
                    c.hitl_approved_at  = datetime.utcnow()
                    c.updated_at        = datetime.utcnow()
                    db.commit()
            finally:
                db.close()

        return {
            "audit_case_id": audit_case_id,
            "decision":      body.decision,
            "resolved":      False,
            "message":       "No live HITL event found; DB status updated directly.",
        }

    # ── Also persist decision in DB for the audit trail ──────────────
    if _WC_MODELS_AVAILABLE:
        schema = _get_schema(tenant)
        db = _db_session(schema)
        try:
            c = db.query(AuditCase).filter(AuditCase.id == audit_case_id).first()
            if c:
                c.hitl_approved_by = body.reviewer_id
                c.hitl_notes       = body.notes
                c.hitl_approved_at = datetime.utcnow()
                c.updated_at       = datetime.utcnow()
                # Let the graph update status to approved/completed/rejected
                db.commit()
        finally:
            db.close()

    logger.info(
        f"[API /hitl-decision] Case {audit_case_id}: "
        f"decision={body.decision}  reviewer={body.reviewer_id}"
    )
    await _invalidate_case(audit_case_id, tenant.slug)
    return {
        "audit_case_id": audit_case_id,
        "decision":      body.decision,
        "resolved":      True,
        "message":       "Decision submitted. Graph is resuming.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# HITL backward-compatible aliases
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{audit_case_id}/hitl-decision")
async def submit_hitl_decision_legacy(
    audit_case_id: int,
    body:   HITLDecisionRequest,
    tenant: Tenant = Depends(require_tenant),
):
    """
    Backward-compatible alias for the React frontend which calls
    POST /wc-audit/{audit_case_id}/hitl-decision.
    Delegates entirely to the canonical endpoint logic.
    """
    return await submit_hitl_decision(audit_case_id, body, tenant)


class HITLResolveRequest(BaseModel):
    """Streamlit HITL UI sends this shape via POST /hitl/{id}/resolve."""
    action:        str              # approve | reject | override
    reviewer_id:   str  = "streamlit_user"
    notes:         Optional[str]  = ""
    override_data: Optional[dict] = None


@router.post("/hitl/{audit_case_id}/resolve")
async def resolve_hitl_review(
    audit_case_id: int,
    request: HITLResolveRequest,
    tenant:  Tenant = Depends(require_tenant),
):
    """
    Streamlit HITL UI calls POST /hitl/{id}/resolve with action/reviewer_id.
    Translates to the canonical hitl_store.resolve() call.
    """
    decision = "approve" if request.action == "approve" else (
        "override" if request.action == "override" else "reject"
    )
    body = HITLDecisionRequest(
        decision      = decision,
        reviewer_id   = request.reviewer_id or "streamlit_user",
        notes         = request.notes or "",
        override_data = request.override_data,
    )
    result = await submit_hitl_decision(audit_case_id, body, tenant)
    return {
        "audit_case_id": audit_case_id,
        "action":        request.action,
        "reviewer_id":   request.reviewer_id,
        "resolved_at":   datetime.utcnow().isoformat(),
        "message":       f"Review {request.action}d successfully. Workflow resuming.",
        **result,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Report Download
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/report/{audit_case_id}/download")
async def download_report(
    audit_case_id: int,
    tenant: Tenant = Depends(require_tenant),
    user:   WCUser = Depends(require_wc_agent),
):
    """Download the generated Excel audit report for a completed case."""
    if not _WC_MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="WC models not available.")

    schema = _get_schema(tenant)
    db = _db_session(schema)
    try:
        report = (
            db.query(AuditReport)
            .filter(AuditReport.audit_case_id == audit_case_id)
            .first()
        )
    finally:
        db.close()

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not yet generated. The audit may still be processing.",
        )

    file_path = report.report_file or ""
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Report file not found on disk. It may still be generating.",
        )

    return FileResponse(
        path       = file_path,
        filename   = os.path.basename(file_path),
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers    = {
            "Content-Disposition": f'attachment; filename="{os.path.basename(file_path)}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Queue health (admin / monitoring)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/queue/health")
async def queue_health(
    tenant: Tenant = Depends(require_tenant),
    user:   WCUser = Depends(require_wc_admin),
):
    """
    Return the current Redis Stream queue depth and pending (unACKed) count.
    Useful for monitoring dashboards and alerting.
    """
    from app.services.audit_queue import queue_length, pending_count
    redis = get_redis()
    return {
        "stream":          "wc:audit:pipeline",
        "total_messages":  await queue_length(redis),
        "pending_unacked": await pending_count(redis),
        "live_hitl_cases": hitl_store.all_pending_ids(),
        "checked_at":      datetime.utcnow().isoformat(),
    }



@router.get("/cases-test")
async def list_audit_cases_test():
    print(">>> NO DEPS — cases-test hit <<<", flush=True)
    return {"test": "ok"}


class StartFromAPIRequest(BaseModel):
    policy_number: str


@router.post("/start-from-api")
async def start_audit_from_api(
    request: StartFromAPIRequest,
    tenant:  Tenant = Depends(require_tenant),
    user:    WCUser = Depends(require_wc_super_admin),
):
    """
    Start an audit where data comes from the Mock API instead of uploaded files.
    Uses the exact same Redis Stream pipeline as /start.
    The worker reads data_source="api" and routes to api_ingestion_node.
    """
    schema = _get_schema(tenant)

    # Step 1 — create DB row (no file paths needed)
    try:
        case = _db_create_case(
            schema               = schema,
            policy_number        = request.policy_number,
            payroll_file_path    = "",
            policy_xml_path      = "",
            audit_meta_file_path = "",
            tenant_id            = tenant.slug,
        )
    except Exception as exc:
        logger.error(f"[API /start-from-api] DB create failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create audit case: {exc}")

    # Step 2 — push to Redis Stream with data_source="api"
    try:
        redis = get_redis()
        await push_to_pipeline(
            redis                = redis,
            audit_case_id        = case.id,
            policy_number        = request.policy_number,
            tenant_id            = tenant.slug,
            schema_name          = schema,
            payroll_file_path    = "",
            policy_xml_path      = "",
            audit_meta_file_path = "",
            data_source          = "api",      # ← the only difference vs /start
        )
    except Exception as exc:
        logger.error(f"[API /start-from-api] Redis XADD failed: {exc}", exc_info=True)
        db = _db_session(schema)
        try:
            c = db.query(AuditCase).filter(AuditCase.id == case.id).first()
            if c:
                c.status = "error"
                c.auditor_notes = f"Redis push failed: {exc}"
                db.commit()
        finally:
            db.close()
        raise HTTPException(status_code=503, detail=f"Queuing failed: {exc}")

    await _invalidate_case(case.id, tenant.slug)

    return {
        "audit_case_id": case.id,
        "status":        "pending",
        "message":       f"Audit queued from API source for policy {request.policy_number}",
    }



import os
import logging
import requests
from datetime import datetime
from typing import List, Optional
 
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
 
# (These are already imported in the real file — shown here for clarity)
# from app.tenancy.dependencies import require_tenant
# from app.tenancy.models import Tenant
# from app.services.audit_queue import get_redis, push_to_pipeline
# from app.agent_langgraph.wc_nodes.wc_rbac import WCUser, require_wc_super_admin
# from app.core.cache import get_cache_manager
 
logger = logging.getLogger(__name__)
 
MOCK_API_BASE = os.getenv("MOCK_API_BASE_URL", "http://localhost:9000/api/v1")
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Schema
# ─────────────────────────────────────────────────────────────────────────────
 
class StartBatchFromAPIRequest(BaseModel):
    """
    Optional filter: if policy_numbers is provided, only those policies are
    queued. If omitted the endpoint fetches ALL policies from the Mock API.
    """
    policy_numbers: Optional[List[str]] = None
 
 
class BatchAuditResult(BaseModel):
    policy_number:  str
    audit_case_id:  int
    status:         str
    message:        str
 
 
class StartBatchFromAPIResponse(BaseModel):
    batch_id:       str          # UUID to correlate frontend polling
    total_queued:   int
    cases:          List[BatchAuditResult]
    errors:         List[str]
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Endpoint
# ─────────────────────────────────────────────────────────────────────────────
 
# @router.post("/start-batch-from-api", response_model=StartBatchFromAPIResponse)
# async def start_batch_audit_from_api(
#     request: StartBatchFromAPIRequest,
#     tenant:  Tenant = Depends(require_tenant),
#     user:    WCUser = Depends(require_wc_super_admin),
# ):
#     """
#     Fetch ALL policies from the Mock API and enqueue each one for audit.
 
#     Flow
#     ────
#     1. GET /policies  →  list of policy_numbers (or use the provided list)
#     2. For each policy_number:
#        a. _db_create_case(...)  — creates wc_audit_cases row (status=pending)
#        b. push_to_pipeline(..., data_source="api")  — XADD to Redis Stream
#     3. Return immediately. Worker picks them up sequentially.
#        Each case runs the full LangGraph pipeline independently,
#        including HITL checkpoint when required.
#     """
#     import uuid as _uuid
 
#     schema   = _get_schema(tenant)
#     batch_id = str(_uuid.uuid4())
#     errors: List[str] = []
#     results: List[BatchAuditResult] = []
 
#     # ── Step 1: Discover policy numbers ──────────────────────────────────────
#     policy_numbers = request.policy_numbers or []
 
#     if not policy_numbers:
#         try:
#             resp = requests.get(
#                 f"{MOCK_API_BASE}/policies",
#                 # timeout=30,
#             )
#             resp.raise_for_status()
#             data           = resp.json()
#             # Mock API returns: {"policies": [{"policy_number": "...", ...}, ...]}
#             # or a plain list: [{"policy_number": "..."}, ...]
#             raw_list       = data.get("policies", data) if isinstance(data, dict) else data
#             policy_numbers = [
#                 p["policy_number"] if isinstance(p, dict) else str(p)
#                 for p in raw_list
#             ]
#             logger.info(
#                 f"[BatchAPI] Discovered {len(policy_numbers)} policies "
#                 f"from Mock API for tenant={tenant.slug}"
#             )
#         except Exception as exc:
#             logger.error(f"[BatchAPI] Failed to fetch policy list: {exc}", exc_info=True)
#             raise HTTPException(
#                 status_code=502,
#                 detail=f"Could not fetch policy list from Mock API: {exc}",
#             )
 
#     if not policy_numbers:
#         raise HTTPException(
#             status_code=404,
#             detail="Mock API returned no policies to process.",
#         )
 
#     # ── Step 2: Create DB rows + push to Redis ────────────────────────────────
#     redis = get_redis()
 
#     for policy_number in policy_numbers:
#         policy_number = str(policy_number).strip()
#         if not policy_number:
#             continue
 
#         try:
#             # a) Persist DB row (same helper used by /start and /start-from-api)
#             case = _db_create_case(
#                 schema               = schema,
#                 policy_number        = policy_number,
#                 payroll_file_path    = "",        # no files — data comes from API
#                 policy_xml_path      = "",
#                 audit_meta_file_path = "",
#                 tenant_id            = tenant.slug,
#             )
 
#             # b) Push to Redis Stream
#             await push_to_pipeline(
#                 redis                = redis,
#                 audit_case_id        = case.id,
#                 policy_number        = policy_number,
#                 tenant_id            = tenant.slug,
#                 schema_name          = schema,
#                 payroll_file_path    = "",
#                 policy_xml_path      = "",
#                 audit_meta_file_path = "",
#                 data_source          = "api",     # ← routes to api_ingestion_node
#             )
 
#             # c) Invalidate cache so /cases reflects the new pending row
#             await _invalidate_case(case.id, tenant.slug)
 
#             results.append(BatchAuditResult(
#                 policy_number = policy_number,
#                 audit_case_id = case.id,
#                 status        = "pending",
#                 message       = f"Queued successfully (case_id={case.id})",
#             ))
 
#             logger.info(
#                 f"[BatchAPI] Queued policy={policy_number} "
#                 f"case_id={case.id} tenant={tenant.slug}"
#             )
 
#         except Exception as exc:
#             err_msg = f"Failed to queue {policy_number}: {exc}"
#             logger.error(f"[BatchAPI] {err_msg}", exc_info=True)
#             errors.append(err_msg)
 
#     return StartBatchFromAPIResponse(
#         batch_id     = batch_id,
#         total_queued = len(results),
#         cases        = results,
#         errors       = errors,
#     )


import json   # add to existing imports if not already present
 
 
POLICY_CONFIG_CACHE_TTL = int(os.getenv("POLICY_CONFIG_CACHE_TTL_SECS", 86400))

@router.post("/start-batch-from-api", response_model=StartBatchFromAPIResponse)
async def start_batch_audit_from_api(
    request: StartBatchFromAPIRequest,
    tenant:  Tenant = Depends(require_tenant),
    user:    WCUser = Depends(require_wc_super_admin),
):
    """
    Fetch ALL policies from the Mock API and enqueue each one for audit.
 
    Flow
    ────
    1. GET /policies  →  list of policy numbers (or use the provided list)
    2. For each policy_number:
       a. _db_create_case(...)      — creates wc_audit_cases row (status=pending)
       b. Read config from Redis    — cached by /preview-api-policies, or fetch now
       c. _db_enrich_case_from_config() — writes real insured_name, dates,
                                          state_code, est_ytd_premium to DB so
                                          pending cards show correct values immediately
       d. push_to_pipeline(...)     — XADD to Redis Stream
    3. Return immediately. Worker reads config from Redis cache (no extra HTTP
       call for config), fetches only payroll, runs full LangGraph pipeline.
    """
    import uuid as _uuid
 
    schema   = _get_schema(tenant)
    batch_id = str(_uuid.uuid4())
    errors: List[str] = []
    results: List[BatchAuditResult] = []
 
    # ── Step 1: Discover policy numbers ──────────────────────────────────────
    policy_numbers = request.policy_numbers or []
 
    if not policy_numbers:
        try:
            resp = requests.get(
                f"{MOCK_API_BASE}/policies",
                # timeout=30,
            )
            resp.raise_for_status()
            data     = resp.json()
            # Mock API returns: {"policies": [{"policy_number": "...", ...}, ...]}
            # or a plain list: [{"policy_number": "..."}, ...]
            raw_list = data.get("policies", data) if isinstance(data, dict) else data
 
            for p in raw_list:
                if isinstance(p, dict):
                    pn = str(p.get("policy_number") or p.get("policyNumber") or "").strip()
                    if pn:
                        policy_numbers.append(pn)
                else:
                    pn = str(p).strip()
                    if pn:
                        policy_numbers.append(pn)
 
            logger.info(
                f"[BatchAPI] Discovered {len(policy_numbers)} policies "
                f"from Mock API for tenant={tenant.slug}"
            )
        except Exception as exc:
            logger.error(f"[BatchAPI] Failed to fetch policy list: {exc}", exc_info=True)
            raise HTTPException(
                status_code=502,
                detail=f"Could not fetch policy list from Mock API: {exc}",
            )
 
    if not policy_numbers:
        raise HTTPException(
            status_code=404,
            detail="Mock API returned no policies to process.",
        )
 
    # ── Step 2: Create DB rows, enrich with config, push to Redis ────────────
    redis = get_redis()
 
    for policy_number in policy_numbers:
        policy_number = str(policy_number).strip()
        if not policy_number:
            continue
 
        try:
            # a) Create the pending DB row
            case = _db_create_case(
                schema               = schema,
                policy_number        = policy_number,
                payroll_file_path    = "",        # no files — data comes from API
                policy_xml_path      = "",
                audit_meta_file_path = "",
                tenant_id            = tenant.slug,
            )
 
            # b) Get policy config — try Redis cache first (set by /preview-api-policies),
            #    fall back to fetching directly from Mock API if cache is cold.
            config      = None
            config_json = None
 
            try:
                config_json = await redis.get(f"policy_config:{policy_number}")
            except Exception as redis_exc:
                logger.debug(f"[BatchAPI] Redis read failed for {policy_number}: {redis_exc}")
 
            if config_json:
                # Cache hit — config was pre-loaded by the preview step
                try:
                    config = json.loads(config_json) if isinstance(config_json, str) else config_json
                    logger.debug(f"[BatchAPI] Config cache hit for {policy_number}")
                except Exception:
                    config = None
            else:
                # Cache miss — fetch config now and cache it for the worker
                logger.info(
                    f"[BatchAPI] Config cache miss for {policy_number} — "
                    "fetching from Mock API"
                )
                try:
                    r = requests.get(
                        f"{MOCK_API_BASE}/policies/{policy_number}/policy-config",
                        timeout=20,
                    )
                    if r.status_code == 404:
                        logger.warning(
                            f"[BatchAPI] Config 404 for {policy_number} — "
                            "case will be queued without enrichment"
                        )
                    elif r.status_code == 200:
                        config = r.json()
                        # Cache so the worker skips this call later
                        try:
                            await redis.setex(
                                f"policy_config:{policy_number}",
                                POLICY_CONFIG_CACHE_TTL,
                                json.dumps(config),
                            )
                        except Exception as cache_exc:
                            logger.debug(
                                f"[BatchAPI] Redis write failed for {policy_number}: {cache_exc}"
                            )
                    else:
                        r.raise_for_status()
                except Exception as fetch_exc:
                    # Non-fatal — case is still queued, worker will try to fetch config
                    logger.warning(
                        f"[BatchAPI] Could not fetch config for {policy_number}: {fetch_exc}. "
                        "Case queued without enrichment."
                    )
 
            # c) Enrich the pending DB row with real policy details so cards
            #    show meaningful data (insured name, dates, est premium) immediately
            if config:
                try:
                    _db_enrich_case_from_config(
                        case_id   = case.id,
                        policy_id = case.policy_id,
                        config    = config,
                        schema    = schema,
                    )
                except Exception as enrich_exc:
                    # Non-fatal — enrichment failure must never block the queue
                    logger.warning(
                        f"[BatchAPI] Enrichment failed for {policy_number} "
                        f"(non-fatal): {enrich_exc}"
                    )
 
            # d) Push to Redis Stream — worker picks this up and processes the pipeline
            await push_to_pipeline(
                redis                = redis,
                audit_case_id        = case.id,
                policy_number        = policy_number,
                tenant_id            = tenant.slug,
                schema_name          = schema,
                payroll_file_path    = "",
                policy_xml_path      = "",
                audit_meta_file_path = "",
                data_source          = "api",     # ← routes to api_ingestion_node
            )
 
            # e) Invalidate cache so /cases immediately reflects the enriched pending row
            await _invalidate_case(case.id, tenant.slug)
 
            results.append(BatchAuditResult(
                policy_number = policy_number,
                audit_case_id = case.id,
                status        = "pending",
                message       = f"Queued successfully (case_id={case.id})",
            ))
 
            logger.info(
                f"[BatchAPI] Queued policy={policy_number} "
                f"case_id={case.id} tenant={tenant.slug}"
            )
 
        except Exception as exc:
            err_msg = f"Failed to queue {policy_number}: {exc}"
            logger.error(f"[BatchAPI] {err_msg}", exc_info=True)
            errors.append(err_msg)
 
    return StartBatchFromAPIResponse(
        batch_id     = batch_id,
        total_queued = len(results),
        cases        = results,
        errors       = errors,
    )

from pydantic import BaseModel as _BaseModel   # alias avoids clash with existing import
 
 
class ClearDataResponse(_BaseModel):
    deleted_policies: int
    deleted_cases:    int
    total_deleted:    int
    message:          str
 
 
@router.delete("/admin/clear-all-data", response_model=ClearDataResponse)
async def clear_all_audit_data(
    tenant: Tenant  = Depends(require_tenant),
    user:   WCUser  = Depends(require_wc_super_admin),   # Super Admin only
):
    """
    **DESTRUCTIVE** — Permanently deletes every Policy row for this tenant.
 
    Because all child tables reference wc_policies.id with ON DELETE CASCADE,
    a single DELETE on wc_policies wipes the entire object graph:
 
        wc_policies
          └─ wc_policy_class_codes  (CASCADE)
          └─ wc_policy_officers     (CASCADE)
          └─ wc_audit_cases         (CASCADE)
               └─ wc_payroll_records   (CASCADE)
               └─ wc_variance_lines    (CASCADE)
               └─ wc_agent_findings    (CASCADE)
               └─ wc_hitl_reviews      (CASCADE)
               └─ wc_audit_reports     (CASCADE)
 
    Also flushes the tenant's Redis cache so the /cases endpoint
    immediately returns an empty list.
    """
    if not _WC_MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="WC models not available.")
 
    schema = _get_schema(tenant)
    db     = _db_session(schema)
 
    try:
        # Count before deletion so we can report back
        case_count   = db.query(AuditCase).count()
        policy_count = db.query(Policy).count()
 
        # Delete all policies — CASCADE handles everything downstream
        db.query(Policy).delete(synchronize_session=False)
        db.commit()
 
        logger.warning(
            f"[AdminClear] Tenant={tenant.slug} | "
            f"Deleted {policy_count} policies / {case_count} cases "
            f"by user={user.username}"
        )
    except Exception as exc:
        db.rollback()
        logger.error(f"[AdminClear] Failed for tenant={tenant.slug}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database wipe failed: {exc}")
    finally:
        db.close()
 
    # Flush Redis cache so the UI sees an empty list immediately
    try:
        cache = get_cache_manager()
        await cache.delete(_cache_key_cases(tenant.slug))
    except Exception as cache_exc:
        # Non-fatal — the DB rows are already gone; cache will expire naturally
        logger.warning(f"[AdminClear] Cache flush failed (non-fatal): {cache_exc}")
 
    return ClearDataResponse(
        deleted_policies = policy_count,
        deleted_cases    = case_count,
        total_deleted    = policy_count + case_count,
        message          = (
            f"Successfully deleted {policy_count} policies and "
            f"{case_count} audit cases (plus all related records) "
            f"for tenant '{tenant.slug}'."
        ),
    )



from sqlalchemy import text as _text

class AuditConfig(BaseModel):
    """Current tenant-level audit configuration."""
    hitl_enabled: bool = True
 
 
class UpdateAuditConfigRequest(BaseModel):
    """Payload for PATCH /admin/config."""
    hitl_enabled: bool
 
 
# ── Config helpers ────────────────────────────────────────────────────────────
 
_CONFIG_KEY    = "audit_config"
_CONFIG_CACHE_TTL = 60  # seconds
 
 
def _ensure_config_table(db, schema: str) -> None:
    """Create wc_tenant_config if it doesn't exist yet (idempotent)."""
    db.execute(_text(f"""
        CREATE TABLE IF NOT EXISTS {schema}.wc_tenant_config (
            key        VARCHAR(100) PRIMARY KEY,
            value      JSONB        NOT NULL DEFAULT '{{}}',
            updated_at TIMESTAMP    NOT NULL DEFAULT now()
        )
    """))
    db.commit()
 
 
def _read_config(db, schema: str) -> dict:
    """Return the raw config dict from the DB (empty dict if not yet set)."""
    row = db.execute(_text(
        f"SELECT value FROM {schema}.wc_tenant_config WHERE key = :k"
    ), {"k": _CONFIG_KEY}).fetchone()
    return dict(row[0]) if row else {}
 
 
def _write_config(db, schema: str, config: dict) -> None:
    """Upsert the config dict into the DB."""
    import json
    db.execute(_text(f"""
        INSERT INTO {schema}.wc_tenant_config (key, value, updated_at)
        VALUES (:k, CAST(:v AS jsonb), now())   -- CAST() avoids the "::" clash
        ON CONFLICT (key)
        DO UPDATE SET value = EXCLUDED.value, updated_at = now()
    """), {"k": _CONFIG_KEY, "v": json.dumps(config)})
    db.commit()
 
 
# ── Endpoints ─────────────────────────────────────────────────────────────────
 
@router.get("/admin/config", response_model=AuditConfig)
async def get_audit_config(
    tenant: Tenant = Depends(require_tenant),
    user:   WCUser = Depends(require_wc_super_admin),
):
    """
    Return the current tenant-level audit configuration.
    Requires the Wc_super_admin Keycloak role.
    """
    schema = _get_schema(tenant)
    cache  = get_cache_manager()
    key    = f"wc:config:{tenant.slug}"
 
    cached = await cache.get(key)
    if cached is not None:
        return AuditConfig(**cached)
 
    db = _db_session(schema)
    try:
        _ensure_config_table(db, schema)
        raw = _read_config(db, schema)
    finally:
        db.close()
 
    # Apply defaults for any keys not yet stored
    config = AuditConfig(
        hitl_enabled=raw.get("hitl_enabled", True),
    )
    await cache.set(key, config.dict(), ttl=_CONFIG_CACHE_TTL)
    return config
 
 
@router.patch("/admin/config", response_model=AuditConfig)
async def update_audit_config(
    body:   UpdateAuditConfigRequest,
    tenant: Tenant = Depends(require_tenant),
    user:   WCUser = Depends(require_wc_super_admin),
):
    """
    Update the tenant-level audit configuration.
    Requires the Wc_super_admin Keycloak role.
 
    Setting  hitl_enabled=false  causes  assess_risk  to force
    hitl_required=False for every subsequent audit, bypassing the
    hitl_checkpoint node in the LangGraph pipeline.
    """
    schema = _get_schema(tenant)
    db     = _db_session(schema)
    try:
        _ensure_config_table(db, schema)
        existing = _read_config(db, schema)
        existing["hitl_enabled"] = body.hitl_enabled
        _write_config(db, schema, existing)
    except Exception as exc:
        db.rollback()
        logger.error(f"[Config] Write failed for tenant={tenant.slug}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Config update failed: {exc}")
    finally:
        db.close()
 
    # Invalidate cache so workers and the GET endpoint pick up the new value
    cache = get_cache_manager()
    await cache.delete(f"wc:config:{tenant.slug}")
 
    logger.info(
        f"[Config] tenant={tenant.slug} hitl_enabled={body.hitl_enabled} "
        f"updated by user={user.username}"
    )
    return AuditConfig(hitl_enabled=body.hitl_enabled)




import json
 
POLICY_CONFIG_CACHE_TTL = int(os.getenv("POLICY_CONFIG_CACHE_TTL_SECS", 86400))  # 24 h
 
 
# ─────────────────────────────────────────────────────────────────────────────
# NEW ENDPOINT — Preview API policies (step 1 of the 2-step batch flow)
# ─────────────────────────────────────────────────────────────────────────────
 
class PolicyPreviewItem(BaseModel):
    policy_number:    str
    insured_name:     str
    effective_date:   str
    expiration_date:  str
    state_code:       str
    class_codes:      str          # comma-separated e.g. "5190, 8810"
    est_premium:      float
    payroll_frequency: str
    officer_count:    int
    available:        bool         # False if mock API returned 404
 
 
class PolicyPreviewResponse(BaseModel):
    total:    int
    policies: list[PolicyPreviewItem]
    errors:   list[str]
 
 
@router.get("/preview-api-policies", response_model=PolicyPreviewResponse)
async def preview_api_policies(
    tenant: Tenant = Depends(require_tenant),
    user:   WCUser = Depends(require_wc_super_admin),
):
    """
    Step 1 of the two-step batch flow.
 
    Fetches ALL policies from the Mock API, retrieves policy-config for each,
    caches the configs in Redis (TTL=24h), and returns an enriched preview list
    so the frontend can display a table before the user confirms the batch.
 
    The frontend shows this table → user clicks "Start Batch Audit" →
    /start-batch-from-api reads from cache (no duplicate HTTP calls).
    """
    errors: list[str] = []
    redis = get_redis()
 
    # ── Step 1: Discover policy numbers ──────────────────────────────────────
    try:
        resp = requests.get(f"{MOCK_API_BASE}/policies", timeout=30)
        resp.raise_for_status()
        data     = resp.json()
        raw_list = data.get("policies", data) if isinstance(data, dict) else data
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Mock API unreachable: {exc}")
 
    # ── Step 2: Fetch config for each policy, build preview + cache ───────────
    preview_items: list[PolicyPreviewItem] = []
 
    for entry in raw_list:
        pn = (entry.get("policy_number") or entry.get("policyNumber") or str(entry)).strip()
        if not pn:
            continue
 
        cache_key = f"policy_config:{pn}"
 
        # Check if already cached from a previous preview
        try:
            cached_raw = await redis.get(cache_key)
            if cached_raw:
                config = json.loads(cached_raw)
                logger.debug(f"[Preview] Cache hit for {pn}")
                preview_items.append(_build_preview_item(pn, config, available=True))
                continue
        except Exception:
            pass  # Redis unavailable — proceed to fetch
 
        # Check if /policies already returned inline config
        if entry.get("xml_records") or entry.get("audit_meta"):
            config = entry
        else:
            # Fetch config from Mock API
            try:
                r = requests.get(
                    f"{MOCK_API_BASE}/policies/{pn}/policy-config",
                    timeout=20,
                )
                if r.status_code == 404:
                    logger.warning(f"[Preview] Config 404 for {pn}")
                    preview_items.append(PolicyPreviewItem(
                        policy_number=pn, insured_name="—", effective_date="—",
                        expiration_date="—", state_code="—", class_codes="—",
                        est_premium=0, payroll_frequency="—", officer_count=0,
                        available=False,
                    ))
                    errors.append(f"{pn}: not found in Mock API (404)")
                    continue
                r.raise_for_status()
                config = r.json()
            except Exception as exc:
                errors.append(f"{pn}: config fetch failed — {exc}")
                preview_items.append(PolicyPreviewItem(
                    policy_number=pn, insured_name="—", effective_date="—",
                    expiration_date="—", state_code="—", class_codes="—",
                    est_premium=0, payroll_frequency="—", officer_count=0,
                    available=False,
                ))
                continue
 
        # Cache in Redis so /start-batch-from-api skips the config call
        try:
            await redis.setex(cache_key, POLICY_CONFIG_CACHE_TTL, json.dumps(config))
        except Exception as cache_exc:
            logger.warning(f"[Preview] Redis cache write failed for {pn}: {cache_exc}")
 
        preview_items.append(_build_preview_item(pn, config, available=True))
 
    logger.info(
        f"[Preview] {len(preview_items)} policies previewed, "
        f"{len(errors)} errors for tenant={tenant.slug}"
    )
 
    return PolicyPreviewResponse(
        total    = len(preview_items),
        policies = preview_items,
        errors   = errors,
    )
 
 
def _build_preview_item(policy_number: str, config: dict, available: bool) -> "PolicyPreviewItem":
    """Build a PolicyPreviewItem from a raw policy-config dict."""
    xml_records  = config.get("xml_records", [])
    audit_meta   = config.get("audit_meta", {})
    officers     = config.get("officers", [])
 
    first_xml    = xml_records[0] if xml_records else {}
 
    # Collect unique class codes
    class_codes  = ", ".join(
        sorted({str(r.get("classCode") or r.get("ClassCode") or "").split()[0]
                for r in xml_records if r.get("classCode") or r.get("ClassCode")})
    ) or "—"
 
    return PolicyPreviewItem(
        policy_number    = policy_number,
        insured_name     = first_xml.get("InsuredName", "—") or "—",
        effective_date   = first_xml.get("EffectiveDate", "—") or "—",
        expiration_date  = first_xml.get("ExpirationDate", "—") or "—",
        state_code       = first_xml.get("StateCode", "—") or "—",
        class_codes      = class_codes,
        est_premium      = float(first_xml.get("premium", 0) or 0),
        payroll_frequency= audit_meta.get("a_payroll_frequency", "—") or "—",
        officer_count    = len(officers),
        available        = available,
    )


import json
 
 
# ─────────────────────────────────────────────────────────────────────────────
# ADDITION 1 — New helper (paste below _db_create_case in wc_aduit_api.py)
# ─────────────────────────────────────────────────────────────────────────────
 
def _db_enrich_case_from_config(
    case_id:   int,
    policy_id: int,
    config:    dict,
    schema:    str,
) -> None:
    """
    Write real policy details from the pre-fetched config into the DB
    immediately after _db_create_case, before the worker picks up the job.
 
    Updates:
      wc_policies     — insured_name, effective_date, expiration_date,
                        state_code, estimated_premium, payroll_frequency
      wc_audit_cases  — total_earned_premium   ← THIS is what the card reads
                        total_est_ytd_premium  ← also set for accuracy
    """
    if not config:
        return
 
    xml_records = config.get("xml_records", [])
    audit_meta  = config.get("audit_meta", {})
 
    if not xml_records and not audit_meta:
        return
 
    first_xml = xml_records[0] if xml_records else {}
 
    def _safe_date(val):
        if not val:
            return None
        from datetime import datetime as _dt
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%Y/%m/%d"):
            try:
                return _dt.strptime(str(val).strip(), fmt).date()
            except (ValueError, TypeError):
                pass
        return None
 
    insured_name    = str(first_xml.get("InsuredName") or "").strip() or None
    effective_date  = _safe_date(first_xml.get("EffectiveDate"))
    expiration_date = _safe_date(first_xml.get("ExpirationDate"))
    state_code      = str(first_xml.get("StateCode") or "").strip()[:5] or None
    est_premium     = float(first_xml.get("premium") or 0)
    payroll_freq    = str(audit_meta.get("a_payroll_frequency") or "1W").strip()
 
    # Sum EstPremium across all class codes — this is displayed as the card premium
    total_est_ytd = sum(float(r.get("EstPremium") or 0) for r in xml_records)
 
    db = _db_session(schema)
    try:
        # ── wc_policies — replace placeholder values ──────────────────────────
        policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if policy:
            if insured_name:
                policy.insured_name = insured_name
            if effective_date:
                policy.effective_date = effective_date
            if expiration_date:
                policy.expiration_date = expiration_date
            if state_code and state_code not in ("XX", ""):
                policy.state_code = state_code
            if est_premium:
                policy.estimated_premium = est_premium
            if payroll_freq:
                policy.payroll_frequency = payroll_freq
            policy.updated_at = datetime.utcnow()
 
        # ── wc_audit_cases — set BOTH premium fields ──────────────────────────
        case = db.query(AuditCase).filter(AuditCase.id == case_id).first()
        if case and total_est_ytd:
            case.total_earned_premium  = total_est_ytd   # ← card reads this field
            case.total_est_ytd_premium = total_est_ytd   # ← also set for accuracy
            case.updated_at            = datetime.utcnow()
 
        db.commit()
        logger.info(
            f"[API] Case {case_id} enriched: insured='{insured_name}' "
            f"state={state_code} premium={total_est_ytd:.2f}"
        )
 
    except Exception as exc:
        db.rollback()
        logger.warning(
            f"[API] _db_enrich_case_from_config failed for case {case_id} "
            f"(non-fatal): {exc}"
        )
    finally:
        db.close()