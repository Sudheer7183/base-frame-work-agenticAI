# """
# Workers' Compensation Audit – FastAPI Router
# Provides REST API endpoints for:
#   • Starting / managing audit cases
#   • Uploading data files
#   • Retrieving variance results
#   • HITL review resolution
#   • Report download

# FIXES applied vs. previous version
# ────────────────────────────────────
# 1. _run_audit_task now uses graph.astream_events() so the registry
#    is updated incrementally as each node completes.  The frontend
#    receives live agent_logs and a hitl_pending status WITHOUT waiting
#    for the full graph to finish.

# 2. /status now returns agent_logs, overall_variance, class_code_variance
#    and ai_narrative so the frontend pipeline steps light up correctly.

# 3. /cases now reads from _AUDIT_REGISTRY (was broken NameError).

# 4. New /hitl-decision endpoint replaces the stub; it updates the
#    registry AND signals the asyncio.Event so the blocked graph resumes.

# 5. Status mapping: "current_stage" values are mapped → frontend-friendly
#    strings ("hitl_pending", "completed", "error").
# """
# import asyncio
# import os
# import logging
# import uuid
# from datetime import datetime
# from typing import Optional, List

# from fastapi import (
#     APIRouter, HTTPException, UploadFile, File,
#     BackgroundTasks, Header,
# )
# from fastapi.responses import FileResponse
# from pydantic import BaseModel

# from app.agent_langgraph.wc_graph_builder import build_wc_audit_graph
# from app.agent_langgraph.wc_state import create_initial_state
# from app.agent_langgraph.wc_nodes.hitl_checkpoint import (
#     resolve_hitl, get_pending_reviews
# )

# logger = logging.getLogger(__name__)
# router = APIRouter(prefix="/api/v1/wc-audit", tags=["Workers Comp Audit"])

# # ─────────────────────────────────────────────────────────────────────────────
# # Shared in-memory registry
# # ─────────────────────────────────────────────────────────────────────────────
# # Each entry shape:
# # {
# #   "audit_case_id":       int,
# #   "policy_number":       str,
# #   "status":              "pending" | "processing" | "hitl_pending" |
# #                          "completed" | "rejected" | "error",
# #   "created_at":          str   (ISO),
# #   "result":              dict  (final or partial WCAuditState),
# #   "agent_logs":          list  (accumulated as graph streams),
# #   "error":               str | list | None,
# #   "hitl_event":          asyncio.Event  (only present while HITL is blocking),
# # }

# _AUDIT_REGISTRY: dict = {}

# UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/wc_audit_uploads")
# os.makedirs(UPLOAD_DIR, exist_ok=True)


# # ─────────────────────────────────────────────
# # Request / Response Schemas
# # ─────────────────────────────────────────────

# class StartAuditRequest(BaseModel):
#     policy_number:        str
#     tenant_id:            str = "default"
#     payroll_file_path:    Optional[str] = None
#     policy_xml_path:      Optional[str] = None
#     audit_meta_file_path: Optional[str] = None


# class HITLDecisionRequest(BaseModel):
#     decision: str        # "approve" | "reject"
#     notes:    str = ""


# class HITLResolveRequest(BaseModel):
#     action:        str   # approve | reject | override
#     reviewer_id:   str
#     notes:         Optional[str] = ""
#     override_data: Optional[dict] = None


# # ─────────────────────────────────────────────
# # File Upload
# # ─────────────────────────────────────────────

# @router.post("/upload")
# async def upload_audit_files(
#     payroll_file: UploadFile = File(..., description="Payroll Excel (.xlsx)"),
#     policy_xml:   UploadFile = File(..., description="Policy XML"),
#     audit_meta:   UploadFile = File(None, description="Audit metadata Excel (optional)"),
# ):
#     """Upload data files and get back their server-side paths."""
#     session_id = str(uuid.uuid4())[:8]
#     paths = {}
#     for upload, key in [
#         (payroll_file, "payroll_file_path"),
#         (policy_xml,   "policy_xml_path"),
#         (audit_meta,   "audit_meta_file_path"),
#     ]:
#         if upload is None:
#             continue
#         ext      = os.path.splitext(upload.filename)[1]
#         savepath = os.path.join(UPLOAD_DIR, f"{session_id}_{key}{ext}")
#         with open(savepath, "wb") as f:
#             f.write(await upload.read())
#         paths[key] = savepath
#         logger.info(f"[Upload] Saved {upload.filename} → {savepath}")
#     return {"session_id": session_id, **paths}


# # ─────────────────────────────────────────────
# # Start Audit
# # ─────────────────────────────────────────────

# @router.post("/start")
# async def start_audit(
#     request: StartAuditRequest,
#     background_tasks: BackgroundTasks,
# ):
#     """
#     Start a Workers' Compensation audit workflow.
#     Returns immediately with audit_case_id; execution streams in the background.
#     """
#     audit_case_id = len(_AUDIT_REGISTRY) + 1

#     missing = [f for f in ["payroll_file_path", "policy_xml_path"] if not getattr(request, f)]
#     if missing:
#         raise HTTPException(status_code=400, detail=f"Missing required paths: {', '.join(missing)}")

#     # Register with empty-but-structured entry so /status can respond immediately
#     _AUDIT_REGISTRY[audit_case_id] = {
#         "audit_case_id": audit_case_id,
#         "policy_number": request.policy_number,
#         "status":        "pending",
#         "created_at":    datetime.utcnow().isoformat(),
#         "result":        {},
#         "agent_logs":    [],
#         "error":         None,
#     }

#     initial_state = create_initial_state(
#         audit_case_id        = audit_case_id,
#         policy_number        = request.policy_number,
#         payroll_file_path    = request.payroll_file_path    or "",
#         policy_xml_path      = request.policy_xml_path      or "",
#         audit_meta_file_path = request.audit_meta_file_path or "",
#         tenant_id            = request.tenant_id,
#     )

#     background_tasks.add_task(_run_audit_task, audit_case_id, initial_state)

#     return {
#         "audit_case_id": audit_case_id,
#         "status":        "pending",
#         "message":       "Audit workflow started. Poll /status/{id} for updates.",
#     }


# # ─────────────────────────────────────────────
# # Background task — streams graph events live
# # ─────────────────────────────────────────────

# async def _run_audit_task(audit_case_id: int, initial_state) -> None:
#     """
#     Run the LangGraph audit graph using graph.astream() so the registry
#     is updated incrementally after each node completes.

#     Key flow
#     ────────
#     1. Each on_chain_end / on_tool_end event that carries state updates
#        is merged into the registry "result" dict and agent_logs list.

#     2. When the hitl_checkpoint node fires it calls
#        _mark_hitl_pending(audit_case_id) which sets status="hitl_pending"
#        in the registry BEFORE blocking on the asyncio.Event.
#        The frontend sees "hitl_pending" on the very next poll.

#     3. When the user submits a HITL decision the /hitl-decision endpoint
#        sets the event, the blocked node resumes, and the graph finishes.

#     4. On graph completion _run_audit_task sets status="completed" with
#        the full final state.
#     """
#     entry = _AUDIT_REGISTRY[audit_case_id]
#     entry["status"] = "processing"

#     try:
#         graph = build_wc_audit_graph()

#         # ── Stream per-node state updates ─────────────────────────────────
#         # graph.astream() yields { node_name: partial_state } after each node.
#         # This avoids the astream_events() issue where "output" can be a
#         # plain string, causing AttributeError: 'str' has no attribute 'get'.
#         last_state: dict = {}

#         async for state_chunk in graph.astream(initial_state):
#             if not isinstance(state_chunk, dict):
#                 continue

#             for node_name, node_output in state_chunk.items():
#                 if not isinstance(node_output, dict):
#                     continue

#                 # ── Accumulate agent_logs ──────────────────────────────────
#                 new_logs = node_output.get("agent_logs") or []
#                 if isinstance(new_logs, list):
#                     for log in new_logs:
#                         if isinstance(log, dict):
#                             entry["agent_logs"].append(log)

#                 # ── Merge all other state keys into result ─────────────────
#                 for k, v in node_output.items():
#                     if k == "agent_logs":
#                         continue
#                     if v is not None and v != [] and v != {}:
#                         entry["result"][k] = v

#                 # ── Detect HITL pause ──────────────────────────────────────
#                 if node_name == "hitl_checkpoint":
#                     entry["status"] = "hitl_pending"
#                     logger.info(
#                         f"[AuditTask] Case {audit_case_id}: graph paused at hitl_checkpoint"
#                     )

#                 last_state.update(node_output)

#         # ── Graph fully finished ───────────────────────────────────────────
#         for k, v in last_state.items():
#             if k == "agent_logs":
#                 continue
#             if v is not None:
#                 entry["result"][k] = v

#         if entry["status"] not in ("hitl_pending", "error"):
#             errs = entry["result"].get("errors") or []
#             if errs:
#                 entry["status"] = "error"
#                 entry["error"]  = errs
#             else:
#                 entry["status"] = "completed"

#         logger.info(f"[AuditTask] Case {audit_case_id} finished with status={entry['status']}")

#     except Exception as exc:
#         logger.error(f"[AuditTask] Error for case {audit_case_id}: {exc}", exc_info=True)
#         entry.update({"status": "error", "error": str(exc)})


# # ─────────────────────────────────────────────
# # Called by hitl_checkpoint.py before it blocks
# # ─────────────────────────────────────────────

# def mark_hitl_pending(audit_case_id: int, partial_state: dict) -> None:
#     """
#     Called from hitl_checkpoint.py immediately before await event.wait().
#     Ensures the registry reflects hitl_pending so the frontend can display
#     the HITL approval panel while the graph is suspended.
#     """
#     entry = _AUDIT_REGISTRY.get(audit_case_id)
#     if not entry:
#         logger.warning(f"[mark_hitl_pending] Case {audit_case_id} not in registry.")
#         return

#     # Merge whatever partial state we have so far
#     for k, v in partial_state.items():
#         if k != "agent_logs" and v is not None:
#             entry["result"][k] = v

#     new_logs = partial_state.get("agent_logs", [])
#     if new_logs:
#         entry["agent_logs"].extend(new_logs)
#         entry["result"].setdefault("agent_logs", []).extend(new_logs)

#     entry["status"] = "hitl_pending"
#     logger.info(f"[mark_hitl_pending] Case {audit_case_id} → hitl_pending")


# # ─────────────────────────────────────────────
# # Status & Results
# # ─────────────────────────────────────────────

# @router.get("/status/{audit_case_id}")
# async def get_audit_status(audit_case_id: int):
#     """
#     Poll audit status and get results.
#     Returns agent_logs, overall_variance and class_code_variance so the
#     frontend pipeline steps light up in real-time.
#     """
#     entry = _AUDIT_REGISTRY.get(audit_case_id)
#     if not entry:
#         raise HTTPException(status_code=404, detail="Audit case not found.")

#     result  = entry.get("result") or {}
#     overall = result.get("overall_variance") or {}

#     return {
#         "audit_case_id":       audit_case_id,
#         "policy_number":       entry.get("policy_number"),
#         "status":              entry.get("status"),
#         # Risk / recommendation / HITL
#         "risk_level":          result.get("risk_level"),
#         "recommendation":      result.get("recommendation"),
#         "hitl_required":       result.get("hitl_required"),
#         # Variance numbers
#         "variance":            overall.get("variance"),
#         "variance_pct":        overall.get("variance_pct"),
#         # Full variance breakdown for frontend tabs
#         "overall_variance":    overall,
#         "class_code_variance": result.get("class_code_variance", []),
#         # AI narrative
#         "ai_narrative":        result.get("ai_narrative", ""),
#         # ── CRITICAL: pipeline step indicators ───────────────────────────
#         # agent_logs is a list of {agent, status, timestamp, ...} dicts.
#         # The frontend reads agent keys from this list to light up steps.
#         "agent_logs":          entry.get("agent_logs", []),
#         # Errors / timestamps
#         "errors":              entry.get("error"),
#         "created_at":          entry.get("created_at"),
#     }


# @router.get("/results/{audit_case_id}")
# async def get_audit_results(audit_case_id: int):
#     """Get full audit results including variance breakdown and findings."""
#     entry = _AUDIT_REGISTRY.get(audit_case_id)
#     if not entry:
#         raise HTTPException(status_code=404, detail="Audit not found.")
#     if entry.get("status") not in ("completed", "review", "hitl_approved", "hitl_pending"):
#         raise HTTPException(status_code=400, detail="Audit not yet complete.")

#     result = entry.get("result", {})
#     return {
#         "audit_case_id":        audit_case_id,
#         "policy_number":        entry.get("policy_number"),
#         "overall_variance":     result.get("overall_variance", {}),
#         "class_code_variance":  result.get("class_code_variance", []),
#         "officer_findings":     result.get("officer_findings",   []),
#         "class_code_findings":  result.get("class_code_findings", []),
#         "frequency_findings":   result.get("frequency_findings",  []),
#         "ai_narrative":         result.get("ai_narrative",        ""),
#         "risk_level":           result.get("risk_level",          ""),
#         "recommendation":       result.get("recommendation",      ""),
#         "report_file":          result.get("report_file_path",    ""),
#         "agent_logs":           entry.get("agent_logs",           []),
#     }


# # ─────────────────────────────────────────────
# # List all cases  (fixes NameError: audit_results)
# # ─────────────────────────────────────────────

# @router.get("/cases")
# async def list_audit_cases(
#     x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
# ):
#     """
#     Return all audit cases stored in _AUDIT_REGISTRY, newest-first.
#     Each case has the same shape as /status/{id} so the frontend can
#     render the Dashboard and Policies screens without extra requests.
#     """
#     rows = []
#     for entry in _AUDIT_REGISTRY.values():
#         result  = entry.get("result") or {}
#         overall = result.get("overall_variance") or {}
#         rows.append({
#             "audit_case_id":       entry["audit_case_id"],
#             "policy_number":       entry.get("policy_number"),
#             "status":              entry.get("status"),
#             "risk_level":          result.get("risk_level"),
#             "recommendation":      result.get("recommendation"),
#             "hitl_required":       result.get("hitl_required"),
#             "variance":            overall.get("variance"),
#             "variance_pct":        overall.get("variance_pct"),
#             "overall_variance":    overall,
#             "class_code_variance": result.get("class_code_variance", []),
#             "ai_narrative":        result.get("ai_narrative", ""),
#             "agent_logs":          entry.get("agent_logs", []),
#             "errors":              entry.get("error"),
#             "created_at":          entry.get("created_at"),
#         })
#     return sorted(rows, key=lambda x: x["audit_case_id"], reverse=True)


# @router.get("/list")
# async def list_audits_legacy(
#     status: Optional[str] = None,
#     limit:  int = 20,
#     offset: int = 0,
# ):
#     """Legacy list endpoint — kept for backwards compatibility."""
#     all_cases = list(_AUDIT_REGISTRY.values())
#     if status:
#         all_cases = [c for c in all_cases if c.get("status") == status]
#     return {"total": len(all_cases), "items": all_cases[offset: offset + limit]}


# # ─────────────────────────────────────────────
# # HITL Endpoints
# # ─────────────────────────────────────────────

# @router.get("/hitl/pending")
# async def get_pending_hitl():
#     """Get all audits pending human review."""
#     return {"pending": get_pending_reviews()}


# @router.post("/hitl/{audit_case_id}/resolve")
# async def resolve_hitl_review(audit_case_id: int, request: HITLResolveRequest):
#     """Submit a HITL review decision via the legacy resolve interface."""
#     if not resolve_hitl(
#         audit_case_id = audit_case_id,
#         action        = request.action,
#         reviewer_id   = request.reviewer_id,
#         notes         = request.notes or "",
#         override_data = request.override_data,
#     ):
#         raise HTTPException(status_code=404, detail="No pending HITL review for this case.")
#     return {
#         "audit_case_id": audit_case_id,
#         "action":        request.action,
#         "reviewer_id":   request.reviewer_id,
#         "resolved_at":   datetime.utcnow().isoformat(),
#         "message":       f"Review {request.action}d successfully. Workflow resuming.",
#     }


# @router.post("/{audit_case_id}/hitl-decision")
# async def submit_hitl_decision(
#     audit_case_id: int,
#     payload: HITLDecisionRequest,
#     x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
# ):
#     """
#     Submit an auditor approve / reject decision from the React frontend.

#     1. Updates the registry status immediately so the next poll sees it.
#     2. Calls resolve_hitl() which sets the asyncio.Event that unblocks
#        the hitl_checkpoint node and allows the graph to resume.
#     """
#     entry = _AUDIT_REGISTRY.get(audit_case_id)
#     if not entry:
#         raise HTTPException(status_code=404, detail="Audit case not found.")

#     # Map frontend "approve"/"reject" → hitl resolve action
#     action = "approve" if payload.decision == "approve" else "reject"

#     # Update registry immediately (before graph resumes)
#     new_status = "completed" if action == "approve" else "rejected"
#     entry["hitl_decision"] = payload.decision
#     entry["hitl_notes"]    = payload.notes
#     entry["status"]        = new_status
#     if entry.get("result"):
#         entry["result"]["hitl_required"] = False

#     # Signal the blocking hitl_checkpoint to resume the graph
#     resolved = resolve_hitl(
#         audit_case_id = audit_case_id,
#         action        = action,
#         reviewer_id   = "frontend_user",
#         notes         = payload.notes,
#     )

#     if not resolved:
#         # No active hitl_checkpoint event found — the graph may already have
#         # finished or the event was cleared.  The registry update above still
#         # stands, so the frontend will see the new status.
#         logger.warning(
#             f"[hitl-decision] resolve_hitl returned False for case {audit_case_id}. "
#             "Registry updated but graph event was not found."
#         )

#     logger.info(f"[hitl-decision] Case {audit_case_id}: {action} by frontend user")
#     return {
#         "audit_case_id": audit_case_id,
#         "decision":      payload.decision,
#         "status":        new_status,
#         "message":       f"HITL decision recorded. Status → {new_status}.",
#     }


# # ─────────────────────────────────────────────
# # Report Download
# # ─────────────────────────────────────────────

# @router.get("/report/{audit_case_id}/download")
# async def download_report(audit_case_id: int):
#     """
#     Download the Excel audit report.
 
#     Route: GET /api/v1/wc-audit/report/{id}/download
#     Called via axios (with Authorization + X-Tenant-ID headers) so the
#     tenant middleware resolves correctly — no more "tenant_not_found" error.
#     """
#     entry = _AUDIT_REGISTRY.get(audit_case_id)
#     if not entry:
#         raise HTTPException(status_code=404, detail="Audit case not found.")
#     result    = entry.get("result") or {}
#     file_path = result.get("report_file_path", "")
#     if not file_path or not os.path.exists(file_path):
#         raise HTTPException(
#             status_code=404,
#             detail="Report file not yet generated. The audit may still be processing."
#         )
#     return FileResponse(
#         path       = file_path,
#         filename   = os.path.basename(file_path),
#         media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#         headers    = {
#             "Content-Disposition": f'attachment; filename="{os.path.basename(file_path)}"',
#             "Access-Control-Expose-Headers": "Content-Disposition",
#         },
#     )

###########################################################################################################################

# import asyncio
# import os
# import logging
# import uuid
# from datetime import datetime
# from typing import Optional, List
 
# from fastapi import (
#     APIRouter, HTTPException, UploadFile, File,
#     BackgroundTasks, Header, Depends, Request
# )
# from fastapi.responses import FileResponse
# from pydantic import BaseModel
 
# from app.agent_langgraph.wc_graph_builder import build_wc_audit_graph
# from app.agent_langgraph.wc_state import create_initial_state
# from app.tenancy.dependencies import require_tenant
# from app.tenancy.models import Tenant
# from app.agent_langgraph.wc_nodes.hitl_checkpoint import (
#     resolve_hitl, get_pending_reviews
# )
 
 
# from app.core.database import SessionLocal
# from sqlalchemy import text as _sql
 
# # ── ORM models ────────────────────────────────────────────────────────────────
# try:
#     from app.models.wc_audit import (
#         AuditCase, Policy, VarianceLine, AgentFinding, AuditReport
#     )
#     _WC_MODELS_AVAILABLE = True
# except ImportError:
#     _WC_MODELS_AVAILABLE = False
#     logger_tmp = logging.getLogger(__name__)
#     logger_tmp.warning("[WC API] wc_models not found — DB fallback disabled")
 
 
# def _db_get_schema(tenant: "Tenant | None" = None) -> str:
#     if tenant and hasattr(tenant, "schema_name"):
#         return tenant.schema_name
#     return "public"
 
 
# def _db_session(schema: str):
#     db = SessionLocal()
#     db.execute(_sql(f'SET search_path TO "{schema}", public'))
#     return db
 
 
# def _db_case_to_dict(case: "AuditCase", policy_number: str) -> dict:
#     status_map = {
#         "pending":    "pending",
#         "ingesting":  "processing",
#         "processing": "processing",
#         "review":     "hitl_pending",
#         "approved":   "completed",
#         "completed":  "completed",
#         "rejected":   "rejected",
#     }
#     fe_status = status_map.get(str(case.status or "").lower(), str(case.status or "pending"))
#     overall = {
#         "earned_exposure": float(case.total_earned_exposure or 0),
#         "earned_premium":  float(case.total_earned_premium  or 0),
#         "est_exposure":    float(case.total_est_exposure    or 0),
#         "est_ytd_premium": float(case.total_est_ytd_premium or 0),
#         "variance":        float(case.total_variance        or 0),
#         "variance_pct":    float(case.total_variance_pct    or 0),
#     }
#     class_code_variance = [{
#         "StateCode":       v.state_code,
#         "ClassCode":       v.class_code,
#         "earned_exposure": float(v.earned_exposure or 0),
#         "earned_premium":  float(v.earned_premium  or 0),
#         "est_exposure":    float(v.est_exposure    or 0),
#         "est_ytd_premium": float(v.est_ytd_premium or 0),
#         "variance":        float(v.variance        or 0),
#         "variance_pct":    float(v.variance_pct    or 0),
#         "root_cause":      v.root_cause,
#         "is_flagged":      bool(v.is_flagged),
#     } for v in (case.variance_lines or [])]
#     agent_logs = [{
#         "agent":        f.agent_name,
#         "finding_type": f.finding_type,
#         "status":       "success",
#         "severity":     f.severity,
#         "summary":      f.summary,
#     } for f in (case.agent_findings or [])]
#     report = case.report
#     return {
#         "audit_case_id":       case.id,
#         "policy_number":       policy_number,
#         "status":              fe_status,
#         "risk_level":          case.risk_level,
#         "recommendation":      case.recommendation,
#         "hitl_required":       bool(case.hitl_required),
#         "variance":            float(case.total_variance     or 0),
#         "variance_pct":        float(case.total_variance_pct or 0),
#         "overall_variance":    overall,
#         "class_code_variance": class_code_variance,
#         "ai_narrative":        case.ai_narrative or "",
#         "agent_logs":          agent_logs,
#         "submitted_count":     case.submitted_count,
#         "first_check_date":    str(case.first_check_date) if case.first_check_date else None,
#         "last_check_date":     str(case.last_check_date)  if case.last_check_date  else None,
#         "errors":              None,
#         "created_at":          case.created_at.isoformat() if case.created_at else None,
#         "report_file_path":    report.report_file if report else None,
#     }
 
 
# def _db_fetch_case(audit_case_id: int, schema: str = "public") -> dict | None:
#     if not _WC_MODELS_AVAILABLE:
#         return None
#     db = _db_session(schema)
#     try:
#         case = (
#             db.query(AuditCase)
#             .join(Policy, Policy.id == AuditCase.policy_id)
#             .filter(AuditCase.id == audit_case_id)
#             .first()
#         )
#         if not case:
#             return None
#         policy_number = case.policy.policy_number if case.policy else ""
#         return _db_case_to_dict(case, policy_number)
#     except Exception as e:
#         logger.error(f"[DB] _db_fetch_case({audit_case_id}) in {schema}: {e}")
#         return None
#     finally:
#         db.close()
 
 
# def _db_list_cases(schema: str = "public") -> list:
#     if not _WC_MODELS_AVAILABLE:
#         return []
#     db = _db_session(schema)
#     try:
#         cases = (
#             db.query(AuditCase)
#             .join(Policy, Policy.id == AuditCase.policy_id)
#             .order_by(AuditCase.id.desc())
#             .all()
#         )
#         # "approved" in DB = human has approved → show as "completed" on frontend
#         # "review"   in DB = waiting for human  → show as "hitl_pending"
#         status_map = {
#             "pending":    "pending",
#             "ingesting":  "processing",
#             "processing": "processing",
#             "review":     "hitl_pending",
#             "approved":   "completed",   # ← approved by HITL = completed
#             "completed":  "completed",
#             "rejected":   "rejected",
#         }
#         result = []
#         for c in cases:
#             pn        = c.policy.policy_number if c.policy else ""
#             fe_status = status_map.get(str(c.status or "").lower(), str(c.status or ""))
 
#             # Build class_code_variance from the loaded variance_lines relationship
#             # This is what VarianceAnalysis screen reads to populate its charts
#             class_code_variance = [{
#                 "StateCode":       v.state_code,
#                 "ClassCode":       v.class_code,
#                 "earned_exposure": float(v.earned_exposure or 0),
#                 "earned_premium":  float(v.earned_premium  or 0),
#                 "est_exposure":    float(v.est_exposure    or 0),
#                 "est_ytd_premium": float(v.est_ytd_premium or 0),
#                 "variance":        float(v.variance        or 0),
#                 "variance_pct":    float(v.variance_pct    or 0),
#                 "root_cause":      v.root_cause,
#                 "is_flagged":      bool(v.is_flagged),
#             } for v in (c.variance_lines or [])]
 
#             overall = {
#                 "earned_exposure": float(c.total_earned_exposure or 0),
#                 "earned_premium":  float(c.total_earned_premium  or 0),
#                 "est_exposure":    float(c.total_est_exposure    or 0),
#                 "est_ytd_premium": float(c.total_est_ytd_premium or 0),
#                 "variance":        float(c.total_variance        or 0),
#                 "variance_pct":    float(c.total_variance_pct    or 0),
#             }
 
#             result.append({
#                 "audit_case_id":       c.id,
#                 "policy_number":       pn,
#                 "status":              fe_status,
#                 "risk_level":          c.risk_level,
#                 "recommendation":      c.recommendation,
#                 "hitl_required":       bool(c.hitl_required),
#                 "variance":            float(c.total_variance     or 0),
#                 "variance_pct":        float(c.total_variance_pct or 0),
#                 "overall_variance":    overall,
#                 "class_code_variance": class_code_variance,  # ← was missing!
#                 "ai_narrative":        c.ai_narrative or "",
#                 "created_at":          c.created_at.isoformat() if c.created_at else None,
#             })
#         return result
#     except Exception as e:
#         logger.error(f"[DB] _db_list_cases in {schema}: {e}")
#         return []
#     finally:
#         db.close()
 
 
# logger = logging.getLogger(__name__)
# router = APIRouter(prefix="/api/v1/wc-audit", tags=["Workers Comp Audit"])
 
# _AUDIT_REGISTRY: dict = {}
 
# UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/wc_audit_uploads")
# os.makedirs(UPLOAD_DIR, exist_ok=True)
 
 
# class StartAuditRequest(BaseModel):
#     policy_number:        str
#     tenant_id:            str = "default"
#     payroll_file_path:    Optional[str] = None
#     policy_xml_path:      Optional[str] = None
#     audit_meta_file_path: Optional[str] = None
 
 
# class HITLDecisionRequest(BaseModel):
#     decision: str
#     notes:    str = ""
 
 
# class HITLResolveRequest(BaseModel):
#     action:        str
#     reviewer_id:   str
#     notes:         Optional[str] = ""
#     override_data: Optional[dict] = None
 
 
# @router.post("/upload")
# async def upload_audit_files(
#     payroll_file: UploadFile = File(..., description="Payroll Excel (.xlsx)"),
#     policy_xml:   UploadFile = File(..., description="Policy XML"),
#     audit_meta:   UploadFile = File(None, description="Audit metadata Excel (optional)"),
#     tenant: Tenant = Depends(require_tenant),
# ):
#     session_id = str(uuid.uuid4())[:8]
#     paths = {}
#     for upload, key in [
#         (payroll_file, "payroll_file_path"),
#         (policy_xml,   "policy_xml_path"),
#         (audit_meta,   "audit_meta_file_path"),
#     ]:
#         if upload is None:
#             continue
#         ext      = os.path.splitext(upload.filename)[1]
#         savepath = os.path.join(UPLOAD_DIR, f"{session_id}_{key}{ext}")
#         with open(savepath, "wb") as f:
#             f.write(await upload.read())
#         paths[key] = savepath
#         logger.info(f"[Upload] Saved {upload.filename} → {savepath}")
#     return {"session_id": session_id, **paths}
 
 
# @router.post("/start")
# async def start_audit(
#     request: StartAuditRequest,
#     background_tasks: BackgroundTasks,
#     tenant: Tenant = Depends(require_tenant),
# ):
#     audit_case_id = len(_AUDIT_REGISTRY) + 1
 
#     missing = [f for f in ["payroll_file_path", "policy_xml_path"] if not getattr(request, f)]
#     if missing:
#         raise HTTPException(status_code=400, detail=f"Missing required paths: {', '.join(missing)}")
 
#     _AUDIT_REGISTRY[audit_case_id] = {
#         "audit_case_id": audit_case_id,
#         "policy_number": request.policy_number,
#         "status":        "pending",
#         "created_at":    datetime.utcnow().isoformat(),
#         "result":        {},
#         "agent_logs":    [],
#         "error":         None,
#     }
 
#     initial_state = create_initial_state(
#         audit_case_id        = audit_case_id,
#         policy_number        = request.policy_number,
#         payroll_file_path    = request.payroll_file_path    or "",
#         policy_xml_path      = request.policy_xml_path      or "",
#         audit_meta_file_path = request.audit_meta_file_path or "",
#         tenant_id            = tenant.slug,
#     )
 
#     background_tasks.add_task(_run_audit_task, audit_case_id, initial_state)
 
#     return {
#         "audit_case_id": audit_case_id,
#         "status":        "pending",
#         "message":       "Audit workflow started. Poll /status/{id} for updates.",
#     }
 
 
# async def _run_audit_task(audit_case_id: int, initial_state) -> None:
#     entry = _AUDIT_REGISTRY[audit_case_id]
#     entry["status"] = "processing"
 
#     try:
#         graph = build_wc_audit_graph()
#         last_state: dict = {}
 
#         async for state_chunk in graph.astream(initial_state):
#             if not isinstance(state_chunk, dict):
#                 continue
#             for node_name, node_output in state_chunk.items():
#                 if not isinstance(node_output, dict):
#                     continue
#                 new_logs = node_output.get("agent_logs") or []
#                 if isinstance(new_logs, list):
#                     for log in new_logs:
#                         if isinstance(log, dict):
#                             entry["agent_logs"].append(log)
#                 for k, v in node_output.items():
#                     if k == "agent_logs":
#                         continue
#                     if v is not None and v != [] and v != {}:
#                         entry["result"][k] = v
#                 if node_name == "hitl_checkpoint":
#                     entry["status"] = "hitl_pending"
#                     logger.info(f"[AuditTask] Case {audit_case_id}: graph paused at hitl_checkpoint")
#                 last_state.update(node_output)
 
#         for k, v in last_state.items():
#             if k == "agent_logs":
#                 continue
#             if v is not None:
#                 entry["result"][k] = v
 
#         if entry["status"] not in ("hitl_pending", "error"):
#             errs = entry["result"].get("errors") or []
#             if errs:
#                 entry["status"] = "error"
#                 entry["error"]  = errs
#             else:
#                 entry["status"] = "completed"
 
#         logger.info(f"[AuditTask] Case {audit_case_id} finished with status={entry['status']}")
 
#     except Exception as exc:
#         logger.error(f"[AuditTask] Error for case {audit_case_id}: {exc}", exc_info=True)
#         entry.update({"status": "error", "error": str(exc)})
 
 
# def mark_hitl_pending(audit_case_id: int, partial_state: dict) -> None:
#     entry = _AUDIT_REGISTRY.get(audit_case_id)
#     if not entry:
#         logger.warning(f"[mark_hitl_pending] Case {audit_case_id} not in registry.")
#         return
#     for k, v in partial_state.items():
#         if k != "agent_logs" and v is not None:
#             entry["result"][k] = v
#     new_logs = partial_state.get("agent_logs", [])
#     if new_logs:
#         entry["agent_logs"].extend(new_logs)
#         entry["result"].setdefault("agent_logs", []).extend(new_logs)
#     entry["status"] = "hitl_pending"
#     logger.info(f"[mark_hitl_pending] Case {audit_case_id} → hitl_pending")
 
 
# # ── /status — request: Request is REQUIRED for request.state.tenant fallback ──
# @router.get("/status/{audit_case_id}")
# async def get_audit_status(audit_case_id: int, request: Request):
#     entry = _AUDIT_REGISTRY.get(audit_case_id)
 
#     if not entry:
#         # Case not in memory — load from DB using tenant from the authenticated request
#         tenant = getattr(request.state, "tenant", None)
#         schema = _db_get_schema(tenant)
#         db_row = _db_fetch_case(audit_case_id, schema)
#         if db_row:
#             return db_row
#         raise HTTPException(status_code=404, detail="Audit case not found.")
 
#     result  = entry.get("result") or {}
#     overall = result.get("overall_variance") or {}
 
#     return {
#         "audit_case_id":       audit_case_id,
#         "policy_number":       entry.get("policy_number"),
#         "status":              entry.get("status"),
#         "risk_level":          result.get("risk_level"),
#         "recommendation":      result.get("recommendation"),
#         "hitl_required":       result.get("hitl_required"),
#         "variance":            overall.get("variance"),
#         "variance_pct":        overall.get("variance_pct"),
#         "overall_variance":    overall,
#         "class_code_variance": result.get("class_code_variance", []),
#         "ai_narrative":        result.get("ai_narrative", ""),
#         "agent_logs":          entry.get("agent_logs", []),
#         "errors":              entry.get("error"),
#         "created_at":          entry.get("created_at"),
#     }
 
 
# @router.get("/results/{audit_case_id}")
# async def get_audit_results(audit_case_id: int):
#     entry = _AUDIT_REGISTRY.get(audit_case_id)
#     if not entry:
#         raise HTTPException(status_code=404, detail="Audit not found.")
#     if entry.get("status") not in ("completed", "review", "hitl_approved", "hitl_pending"):
#         raise HTTPException(status_code=400, detail="Audit not yet complete.")
#     result = entry.get("result", {})
#     return {
#         "audit_case_id":        audit_case_id,
#         "policy_number":        entry.get("policy_number"),
#         "overall_variance":     result.get("overall_variance", {}),
#         "class_code_variance":  result.get("class_code_variance", []),
#         "officer_findings":     result.get("officer_findings",   []),
#         "class_code_findings":  result.get("class_code_findings", []),
#         "frequency_findings":   result.get("frequency_findings",  []),
#         "ai_narrative":         result.get("ai_narrative",        ""),
#         "risk_level":           result.get("risk_level",          ""),
#         "recommendation":       result.get("recommendation",      ""),
#         "report_file":          result.get("report_file_path",    ""),
#         "agent_logs":           entry.get("agent_logs",           []),
#     }
 
 
# @router.get("/cases")
# async def list_audit_cases(tenant: Tenant = Depends(require_tenant)):
#     schema   = _db_get_schema(tenant)
#     db_cases = _db_list_cases(schema)
#     merged: dict[int, dict] = {c["audit_case_id"]: c for c in db_cases}
 
#     for entry in _AUDIT_REGISTRY.values():
#         cid         = entry["audit_case_id"]
#         live_status = entry.get("status", "pending")
#         result      = entry.get("result") or {}
#         overall     = result.get("overall_variance") or {}
#         live_row = {
#             "audit_case_id":       cid,
#             "policy_number":       entry.get("policy_number"),
#             "status":              live_status,
#             "risk_level":          result.get("risk_level"),
#             "recommendation":      result.get("recommendation"),
#             "hitl_required":       result.get("hitl_required"),
#             "variance":            overall.get("variance"),
#             "variance_pct":        overall.get("variance_pct"),
#             "overall_variance":    overall,
#             "class_code_variance": result.get("class_code_variance", []),
#             "ai_narrative":        result.get("ai_narrative", ""),
#             "agent_logs":          entry.get("agent_logs", []),
#             "errors":              entry.get("error"),
#             "created_at":          entry.get("created_at"),
#         }
#         if live_status in ("pending", "processing", "hitl_pending") or cid not in merged:
#             merged[cid] = live_row
 
#     return sorted(merged.values(), key=lambda x: x["audit_case_id"], reverse=True)
 
 
# @router.get("/list")
# async def list_audits_legacy(status: Optional[str] = None, limit: int = 20, offset: int = 0):
#     all_cases = list(_AUDIT_REGISTRY.values())
#     if status:
#         all_cases = [c for c in all_cases if c.get("status") == status]
#     return {"total": len(all_cases), "items": all_cases[offset: offset + limit]}
 
 
# @router.get("/hitl/pending")
# async def get_pending_hitl():
#     return {"pending": get_pending_reviews()}
 
 
# @router.post("/hitl/{audit_case_id}/resolve")
# async def resolve_hitl_review(audit_case_id: int, request: HITLResolveRequest):
#     if not resolve_hitl(
#         audit_case_id = audit_case_id,
#         action        = request.action,
#         reviewer_id   = request.reviewer_id,
#         notes         = request.notes or "",
#         override_data = request.override_data,
#     ):
#         raise HTTPException(status_code=404, detail="No pending HITL review for this case.")
#     return {
#         "audit_case_id": audit_case_id,
#         "action":        request.action,
#         "reviewer_id":   request.reviewer_id,
#         "resolved_at":   datetime.utcnow().isoformat(),
#         "message":       f"Review {request.action}d successfully. Workflow resuming.",
#     }
 
 
# @router.post("/{audit_case_id}/hitl-decision")
# async def submit_hitl_decision(
#     audit_case_id: int,
#     payload: HITLDecisionRequest,
#     tenant: Tenant = Depends(require_tenant),
# ):
#     entry = _AUDIT_REGISTRY.get(audit_case_id)
#     if not entry:
#         raise HTTPException(status_code=404, detail="Audit case not found.")
 
#     action     = "approve" if payload.decision == "approve" else "reject"
#     new_status = "completed" if action == "approve" else "rejected"
#     entry["hitl_decision"] = payload.decision
#     entry["hitl_notes"]    = payload.notes
#     entry["status"]        = new_status
#     if entry.get("result"):
#         entry["result"]["hitl_required"] = False
 
#     resolved = resolve_hitl(
#         audit_case_id = audit_case_id,
#         action        = action,
#         reviewer_id   = "frontend_user",
#         notes         = payload.notes,
#     )
#     if not resolved:
#         logger.warning(
#             f"[hitl-decision] resolve_hitl returned False for case {audit_case_id}. "
#             "Registry updated but graph event was not found."
#         )
 
#     logger.info(f"[hitl-decision] Case {audit_case_id}: {action} by frontend user")
#     return {
#         "audit_case_id": audit_case_id,
#         "decision":      payload.decision,
#         "status":        new_status,
#         "message":       f"HITL decision recorded. Status → {new_status}.",
#     }
 
 
# # ── /report/download — request: Request is REQUIRED for request.state.tenant fallback ──
# @router.get("/report/{audit_case_id}/download")
# async def download_report(audit_case_id: int, request: Request):
#     entry = _AUDIT_REGISTRY.get(audit_case_id)
 
#     if not entry:
#         tenant    = getattr(request.state, "tenant", None)
#         schema    = _db_get_schema(tenant)
#         db_row    = _db_fetch_case(audit_case_id, schema)
#         file_path = db_row.get("report_file_path") if db_row else None
#         if file_path and os.path.exists(file_path):
#             return FileResponse(
#                 path       = file_path,
#                 filename   = os.path.basename(file_path),
#                 media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#                 headers    = {
#                     "Content-Disposition":       f'attachment; filename="{os.path.basename(file_path)}"',
#                     "Access-Control-Expose-Headers": "Content-Disposition",
#                 },
#             )
#         raise HTTPException(status_code=404, detail="Audit case not found.")
 
#     result    = entry.get("result") or {}
#     file_path = result.get("report_file_path", "")
#     if not file_path or not os.path.exists(file_path):
#         raise HTTPException(
#             status_code=404,
#             detail="Report file not yet generated. The audit may still be processing."
#         )
#     return FileResponse(
#         path       = file_path,
#         filename   = os.path.basename(file_path),
#         media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#         headers    = {
#             "Content-Disposition":       f'attachment; filename="{os.path.basename(file_path)}"',
#             "Access-Control-Expose-Headers": "Content-Disposition",
#         },
#     )


####################################################################################################################

"""
Workers' Compensation Audit – FastAPI Router  (v3 — Full ORM)
=============================================================
All raw SQL text() calls replaced with SQLAlchemy ORM operations.
 
Changes vs. previous version
────────────────────────────
• Removed:  `from sqlalchemy import text as _sql`
• _db_session() now uses connection.exec_driver_sql() for SET search_path
  — this is the ORM-approved way to send driver-level config without
    bypassing the expression layer via text().
• All data queries (_db_fetch_case, _db_list_cases) already used ORM;
  no changes needed there.
"""
 
import asyncio
import os
import logging
import uuid
from datetime import datetime
from typing import Optional, List
 
from fastapi import (
    APIRouter, HTTPException, UploadFile, File,
    BackgroundTasks, Header, Depends, Request,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel
 
from app.agent_langgraph.wc_graph_builder import build_wc_audit_graph
from app.agent_langgraph.wc_state import create_initial_state
from app.tenancy.dependencies import require_tenant
from app.tenancy.models import Tenant
from app.agent_langgraph.wc_nodes.hitl_checkpoint import (
    resolve_hitl, get_pending_reviews,
)
from app.core.database import SessionLocal
#-------- Wc RABC imports ----------------------------------------------------

from app.agent_langgraph.wc_nodes.wc_rbac import (
    WCUser,require_wc_admin,require_wc_super_admin,require_wc_provider,require_wc_agent
)

# ── ORM models ────────────────────────────────────────────────────────────────
try:
    from app.models.wc_audit import (
        AuditCase, Policy, VarianceLine, AgentFinding, AuditReport,
    )
    _WC_MODELS_AVAILABLE = True
except ImportError:
    _WC_MODELS_AVAILABLE = False
    _tmp_log = logging.getLogger(__name__)
    _tmp_log.warning("[WC API] wc_models not found — DB fallback disabled")
 
 
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/wc-audit", tags=["Workers Comp Audit"])
 
# ─────────────────────────────────────────────────────────────────────────────
# Shared in-memory registry
# ─────────────────────────────────────────────────────────────────────────────
# Each entry shape:
# {
#   "audit_case_id":  int,
#   "policy_number":  str,
#   "status":         "pending" | "processing" | "hitl_pending" |
#                     "completed" | "rejected" | "error",
#   "created_at":     str   (ISO),
#   "result":         dict  (final or partial WCAuditState),
#   "agent_logs":     list  (accumulated as graph streams),
#   "error":          str | list | None,
# }
_AUDIT_REGISTRY: dict = {}
 
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/wc_audit_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
 
 
# ─────────────────────────────────────────────
# Request / Response Schemas
# ─────────────────────────────────────────────
 
class StartAuditRequest(BaseModel):
    policy_number:        str
    tenant_id:            str = "default"
    payroll_file_path:    Optional[str] = None
    policy_xml_path:      Optional[str] = None
    audit_meta_file_path: Optional[str] = None
 
 
class HITLDecisionRequest(BaseModel):
    decision: str        # "approve" | "reject"
    notes:    str = ""
 
 
class HITLResolveRequest(BaseModel):
    action:        str   # approve | reject | override
    reviewer_id:   str
    notes:         Optional[str] = ""
    override_data: Optional[dict] = None
 
 
# ─────────────────────────────────────────────
# DB helper — schema-aware session (ORM only)
# ─────────────────────────────────────────────
 
def _db_get_schema(tenant: "Tenant | None" = None) -> str:
    """Return the Postgres schema name for this tenant."""
    if tenant and hasattr(tenant, "schema_name"):
        return tenant.schema_name
    return "public"
 
 
def _db_session(schema: str):
    """
    Open a SessionLocal and point it at the correct tenant schema.
 
    exec_driver_sql() sends the SET command directly to the DBAPI cursor
    without going through SQLAlchemy's SQL expression compiler — the
    correct ORM-idiomatic way to issue driver-level session configuration.
    No text() / raw SQL is used.
    """
    db = SessionLocal()
    db.connection().exec_driver_sql(f'SET search_path TO "{schema}", public')
    return db
 
 
# ─────────────────────────────────────────────
# DB helper — ORM → dict converters
# ─────────────────────────────────────────────
 
# ─────────────────────────────────────────────
# Date / frequency display helpers
# ─────────────────────────────────────────────
 
_FREQ_LABELS = {
    "1W": "Weekly",  "2W": "Bi-Weekly",  "SM": "Semi-Monthly",
    "1M": "Monthly", "M":  "Monthly",    "Q":  "Quarterly",
    "WEEKLY": "Weekly", "BIWEEKLY": "Bi-Weekly", "MONTHLY": "Monthly",
}
 
 
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
    """Map a payroll_freq code ('1W') to a human label ('Weekly')."""
    if not freq:
        return ""
    return _FREQ_LABELS.get(str(freq).strip().upper(), str(freq))
 
 
_FE_STATUS_MAP = {
    "pending":    "pending",
    "ingesting":  "processing",
    "processing": "processing",
    "review":     "hitl_pending",
    "approved":   "completed",
    "completed":  "completed",
    "rejected":   "rejected",
}
 
 
def _db_case_to_dict(case: "AuditCase", policy_number: str) -> dict:
    """Convert an AuditCase ORM object to the standard frontend response dict."""
    fe_status = _FE_STATUS_MAP.get(
        str(case.status or "").lower(),
        str(case.status or "pending"),
    )
    overall = {
        "earned_exposure": float(case.total_earned_exposure or 0),
        "earned_premium":  float(case.total_earned_premium  or 0),
        "est_exposure":    float(case.total_est_exposure    or 0),
        "est_ytd_premium": float(case.total_est_ytd_premium or 0),
        "variance":        float(case.total_variance        or 0),
        "variance_pct":    float(case.total_variance_pct    or 0),
    }
    class_code_variance = [
        {
            "StateCode":       v.state_code,
            "ClassCode":       v.class_code,
            "earned_exposure": float(v.earned_exposure or 0),
            "earned_premium":  float(v.earned_premium  or 0),
            "est_exposure":    float(v.est_exposure    or 0),
            "est_ytd_premium": float(v.est_ytd_premium or 0),
            "variance":        float(v.variance        or 0),
            "variance_pct":    float(v.variance_pct    or 0),
            "root_cause":      v.root_cause,
            "is_flagged":      bool(v.is_flagged),
        }
        for v in (case.variance_lines or [])
    ]
    agent_logs = [
        {
            "agent":        f.agent_name,
            "finding_type": f.finding_type,
            "status":       "success",
            "severity":     f.severity,
            "summary":      f.summary,
        }
        for f in (case.agent_findings or [])
    ]
    report = case.report
    policy = case.policy  # already loaded via join
 
    return {
        "audit_case_id":        case.id,
        "policy_number":        policy_number,
        "status":               fe_status,
        "risk_level":           case.risk_level,
        "recommendation":       case.recommendation,
        "hitl_required":        bool(case.hitl_required),
        "variance":             float(case.total_variance     or 0),
        "variance_pct":         float(case.total_variance_pct or 0),
        "overall_variance":     overall,
        "class_code_variance":  class_code_variance,
        "ai_narrative":         case.ai_narrative or "",
        "agent_logs":           agent_logs,
        "submitted_count":      case.submitted_count,
        "expected_submissions": case.expected_submissions,
        "first_check_date":     str(case.first_check_date) if case.first_check_date else None,
        "last_check_date":      str(case.last_check_date)  if case.last_check_date  else None,
        "errors":               None,
        "created_at":           case.created_at.isoformat() if case.created_at else None,
        "report_file_path":     report.report_file if report else None,
        # ── Policy-level fields (available via the JOIN on wc_policies) ────────
        "effective_date":       _fmt_date(policy.effective_date   if policy else None),
        "expiration_date":      _fmt_date(policy.expiration_date  if policy else None),
        "payment_frequency":    _map_frequency(policy.payroll_frequency if policy else None),
        # ── Officer summary ────────────────────────────────────────────────────
        # officer_count from wc_policy_officers, issues from wc_agent_findings
        "officer_count":        len(policy.officers) if policy and policy.officers else None,
        "officer_issues_count": len([
            f for f in (case.agent_findings or [])
            if f.agent_name == "OfficerAgent" and f.severity in ("warning", "critical")
        ]),
    }
 
 
def _db_fetch_case(audit_case_id: int, schema: str = "public") -> dict | None:
    """Load a single AuditCase from the DB using ORM, return as dict."""
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
        policy_number = case.policy.policy_number if case.policy else ""
        return _db_case_to_dict(case, policy_number)
    except Exception as e:
        logger.error(f"[DB] _db_fetch_case({audit_case_id}) in {schema}: {e}")
        return None
    finally:
        db.close()
 
 
def _db_list_cases(schema: str = "public") -> list:
    """Load all AuditCases from the DB using ORM, return as list of dicts."""
    if not _WC_MODELS_AVAILABLE:
        return []
    db = _db_session(schema)
    try:
        cases = (
            db.query(AuditCase)
            .join(Policy, Policy.id == AuditCase.policy_id)
            .order_by(AuditCase.id.desc())
            .all()
        )
        result = []
        for c in cases:
            pn        = c.policy.policy_number if c.policy else ""
            fe_status = _FE_STATUS_MAP.get(
                str(c.status or "").lower(),
                str(c.status or ""),
            )
            class_code_variance = [
                {
                    "StateCode":       v.state_code,
                    "ClassCode":       v.class_code,
                    "earned_exposure": float(v.earned_exposure or 0),
                    "earned_premium":  float(v.earned_premium  or 0),
                    "est_exposure":    float(v.est_exposure    or 0),
                    "est_ytd_premium": float(v.est_ytd_premium or 0),
                    "variance":        float(v.variance        or 0),
                    "variance_pct":    float(v.variance_pct    or 0),
                    "root_cause":      v.root_cause,
                    "is_flagged":      bool(v.is_flagged),
                }
                for v in (c.variance_lines or [])
            ]
            overall = {
                "earned_exposure": float(c.total_earned_exposure or 0),
                "earned_premium":  float(c.total_earned_premium  or 0),
                "est_exposure":    float(c.total_est_exposure    or 0),
                "est_ytd_premium": float(c.total_est_ytd_premium or 0),
                "variance":        float(c.total_variance        or 0),
                "variance_pct":    float(c.total_variance_pct    or 0),
            }
            result.append({
                "audit_case_id":       c.id,
                "policy_number":       pn,
                "status":              fe_status,
                "risk_level":          c.risk_level,
                "recommendation":      c.recommendation,
                "hitl_required":       bool(c.hitl_required),
                "variance":            float(c.total_variance     or 0),
                "variance_pct":        float(c.total_variance_pct or 0),
                "overall_variance":    overall,
                "class_code_variance": class_code_variance,
                "ai_narrative":        c.ai_narrative or "",
                "created_at":          c.created_at.isoformat() if c.created_at else None,
                "effective_date":      c.policy.effective_date,   # ✅ NEW
                "expiration_date":     c.policy.expiration_date,  # ✅ NEW
            })
        return result
    except Exception as e:
        logger.error(f"[DB] _db_list_cases in {schema}: {e}")
        return []
    finally:
        db.close()
 
 
# ─────────────────────────────────────────────
# File Upload
# ─────────────────────────────────────────────
 
@router.post("/upload")
async def upload_audit_files(
    payroll_file: UploadFile = File(..., description="Payroll Excel (.xlsx)"),
    policy_xml:   UploadFile = File(..., description="Policy XML"),
    audit_meta:   UploadFile = File(None, description="Audit metadata Excel (optional)"),
    tenant: Tenant = Depends(require_tenant),
    user : WCUser = Depends(require_wc_super_admin)
):
    """Upload data files and get back their server-side paths."""
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
 
 
# ─────────────────────────────────────────────
# Start Audit
# ─────────────────────────────────────────────
 
@router.post("/start")
async def start_audit(
    request: StartAuditRequest,
    background_tasks: BackgroundTasks,
    tenant: Tenant = Depends(require_tenant),
):
    """
    Start a Workers' Compensation audit workflow.
    Returns immediately with audit_case_id; execution streams in the background.
    """
    audit_case_id = len(_AUDIT_REGISTRY) + 1
 
    missing = [
        f for f in ["payroll_file_path", "policy_xml_path"]
        if not getattr(request, f)
    ]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required paths: {', '.join(missing)}",
        )
 
    _AUDIT_REGISTRY[audit_case_id] = {
        "audit_case_id": audit_case_id,
        "policy_number": request.policy_number,
        "status":        "pending",
        "created_at":    datetime.utcnow().isoformat(),
        "result":        {},
        "agent_logs":    [],
        "error":         None,
    }
 
    initial_state = create_initial_state(
        audit_case_id        = audit_case_id,
        policy_number        = request.policy_number,
        payroll_file_path    = request.payroll_file_path    or "",
        policy_xml_path      = request.policy_xml_path      or "",
        audit_meta_file_path = request.audit_meta_file_path or "",
        tenant_id            = tenant.slug,
    )
 
    background_tasks.add_task(_run_audit_task, audit_case_id, initial_state)
 
    return {
        "audit_case_id": audit_case_id,
        "status":        "pending",
        "message":       "Audit workflow started. Poll /status/{id} for updates.",
    }
 
 
# ─────────────────────────────────────────────
# Background task — streams graph events live
# ─────────────────────────────────────────────
 
async def _run_audit_task(audit_case_id: int, initial_state) -> None:
    """
    Run the LangGraph audit graph using graph.astream().
    Registry is updated incrementally after each node completes.
 
    Key flow
    ────────
    1. Each node's output is merged into the registry "result" dict and
       agent_logs list.
    2. When the hitl_checkpoint node fires the status is set to
       "hitl_pending" so the next frontend poll sees it immediately.
    3. When the user submits a HITL decision the graph resumes and the
       status advances to "completed" or "rejected".
    """
    entry = _AUDIT_REGISTRY[audit_case_id]
    entry["status"] = "processing"
 
    try:
        graph      = build_wc_audit_graph()
        last_state: dict = {}
 
        async for state_chunk in graph.astream(initial_state):
            if not isinstance(state_chunk, dict):
                continue
 
            for node_name, node_output in state_chunk.items():
                if not isinstance(node_output, dict):
                    continue
 
                # Accumulate agent_logs incrementally
                new_logs = node_output.get("agent_logs") or []
                if isinstance(new_logs, list):
                    for log in new_logs:
                        if isinstance(log, dict):
                            entry["agent_logs"].append(log)
 
                # Merge all other state keys into result
                for k, v in node_output.items():
                    if k == "agent_logs":
                        continue
                    if v is not None and v != [] and v != {}:
                        entry["result"][k] = v
 
                # Detect HITL pause
                if node_name == "hitl_checkpoint":
                    entry["status"] = "hitl_pending"
                    logger.info(
                        f"[AuditTask] Case {audit_case_id}: "
                        "graph paused at hitl_checkpoint"
                    )
 
                last_state.update(node_output)
 
        # Graph fully finished — persist final state
        for k, v in last_state.items():
            if k == "agent_logs":
                continue
            if v is not None:
                entry["result"][k] = v
 
        if entry["status"] not in ("hitl_pending", "error"):
            errs = entry["result"].get("errors") or []
            if errs:
                entry["status"] = "error"
                entry["error"]  = errs
            else:
                entry["status"] = "completed"
 
        logger.info(
            f"[AuditTask] Case {audit_case_id} finished "
            f"with status={entry['status']}"
        )
 
    except Exception as exc:
        logger.error(f"[AuditTask] Error for case {audit_case_id}: {exc}", exc_info=True)
        entry.update({"status": "error", "error": str(exc)})
 
 
# ─────────────────────────────────────────────
# Called by hitl_checkpoint.py before it blocks
# ─────────────────────────────────────────────
 
def mark_hitl_pending(audit_case_id: int, partial_state: dict) -> None:
    """
    Called from hitl_checkpoint.py immediately before await event.wait().
    Ensures the registry reflects hitl_pending so the frontend can display
    the HITL approval panel while the graph is suspended.
    """
    entry = _AUDIT_REGISTRY.get(audit_case_id)
    if not entry:
        logger.warning(f"[mark_hitl_pending] Case {audit_case_id} not in registry.")
        return
 
    for k, v in partial_state.items():
        if k != "agent_logs" and v is not None:
            entry["result"][k] = v
 
    new_logs = partial_state.get("agent_logs", [])
    if new_logs:
        entry["agent_logs"].extend(new_logs)
        entry["result"].setdefault("agent_logs", []).extend(new_logs)
 
    entry["status"] = "hitl_pending"
    logger.info(f"[mark_hitl_pending] Case {audit_case_id} → hitl_pending")
 
 
# ─────────────────────────────────────────────
# Status endpoint
# ─────────────────────────────────────────────
 
@router.get("/status/{audit_case_id}")
async def get_audit_status(audit_case_id: int, request: Request):
    """
    Poll audit status and get results.
    Falls back to the DB (via ORM) if the case is not in the live registry.
    """
    entry = _AUDIT_REGISTRY.get(audit_case_id)
 
    if not entry:
        tenant    = getattr(request.state, "tenant", None)
        schema    = _db_get_schema(tenant)
        db_row    = _db_fetch_case(audit_case_id, schema)
        if db_row:
            return db_row
        raise HTTPException(status_code=404, detail="Audit case not found.")
 
    result     = entry.get("result") or {}
    overall    = result.get("overall_variance") or {}
    policy_cfg = result.get("policy_config") or {}
 
    # ── Officer summary ───────────────────────────────────────────────────
    all_officers   = policy_cfg.get("officers") or []
    officer_issues = [
        f for f in (result.get("officer_findings") or [])
        if f.get("severity") in ("warning", "critical", "error")
           or f.get("issue") not in (None, "", "none")
    ]
    officer_count        = len(all_officers) if all_officers else None
    officer_issues_count = len(officer_issues)
 
    return {
        "audit_case_id":        audit_case_id,
        "policy_number":        entry.get("policy_number"),
        "status":               entry.get("status"),
        "risk_level":           result.get("risk_level"),
        "recommendation":       result.get("recommendation"),
        "hitl_required":        result.get("hitl_required"),
        "variance":             overall.get("variance"),
        "variance_pct":         overall.get("variance_pct"),
        "overall_variance":     overall,
        "class_code_variance":  result.get("class_code_variance", []),
        "ai_narrative":         result.get("ai_narrative", ""),
        "agent_logs":           entry.get("agent_logs", []),
        "errors":               entry.get("error"),
        "created_at":           entry.get("created_at"),
        # ── Policy-level fields (from policy_config in LangGraph state) ──
        "effective_date":       _fmt_date(policy_cfg.get("effective_date")),
        "expiration_date":      _fmt_date(policy_cfg.get("expiration_date")),
        "payment_frequency":    _map_frequency(
                                    policy_cfg.get("payroll_freq")
                                    or result.get("payroll_frequency")
                                ),
        # ── Audit case timeline fields ────────────────────────────────────
        "submitted_count":      result.get("submitted_count"),
        "expected_submissions": result.get("expected_submissions"),
        "first_check_date":     result.get("first_check_date"),
        "last_check_date":      result.get("last_check_date"),
        # ── Officer summary ───────────────────────────────────────────────
        "officer_count":        officer_count,
        "officer_issues_count": officer_issues_count,
    }
 
 
# ─────────────────────────────────────────────
# Results endpoint
# ─────────────────────────────────────────────
 
@router.get("/results/{audit_case_id}")
async def get_audit_results(audit_case_id: int):
    """Get full audit results including variance breakdown and agent findings."""
    entry = _AUDIT_REGISTRY.get(audit_case_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Audit not found.")
    if entry.get("status") not in ("completed", "review", "hitl_approved", "hitl_pending"):
        raise HTTPException(status_code=400, detail="Audit not yet complete.")
 
    result = entry.get("result", {})
    return {
        "audit_case_id":        audit_case_id,
        "policy_number":        entry.get("policy_number"),
        "overall_variance":     result.get("overall_variance", {}),
        "class_code_variance":  result.get("class_code_variance", []),
        "officer_findings":     result.get("officer_findings",   []),
        "class_code_findings":  result.get("class_code_findings", []),
        "frequency_findings":   result.get("frequency_findings",  []),
        "ai_narrative":         result.get("ai_narrative",        ""),
        "risk_level":           result.get("risk_level",          ""),
        "recommendation":       result.get("recommendation",      ""),
        "report_file":          result.get("report_file_path",    ""),
        "agent_logs":           entry.get("agent_logs",           []),
        "effective_date": entry.get("effective_date",""),
        "expiration_date": entry.get("expiration_date",""),
        "payroll_frequency":entry.get("payroll_frequency","")
    }
 
 
# ─────────────────────────────────────────────
# List all cases
# ─────────────────────────────────────────────
 
@router.get("/cases")
async def list_audit_cases(tenant: Tenant = Depends(require_tenant)):
    """
    Return all audit cases — live registry merged with DB records.
    Live (in-progress) entries take priority over the persisted snapshot.
    """
    schema   = _db_get_schema(tenant)
    db_cases = _db_list_cases(schema)
    merged: dict[int, dict] = {c["audit_case_id"]: c for c in db_cases}
 
    for entry in _AUDIT_REGISTRY.values():
        cid         = entry["audit_case_id"]
        live_status = entry.get("status", "pending")
        result      = entry.get("result") or {}
        overall     = result.get("overall_variance") or {}
        live_row = {
            "audit_case_id":       cid,
            "policy_number":       entry.get("policy_number"),
            "status":              live_status,
            "risk_level":          result.get("risk_level"),
            "recommendation":      result.get("recommendation"),
            "hitl_required":       result.get("hitl_required"),
            "variance":            overall.get("variance"),
            "variance_pct":        overall.get("variance_pct"),
            "overall_variance":    overall,
            "class_code_variance": result.get("class_code_variance", []),
            "ai_narrative":        result.get("ai_narrative", ""),
            "agent_logs":          entry.get("agent_logs", []),
            "errors":              entry.get("error"),
            "created_at":          entry.get("created_at"),
            "effective_date": entry.get("effective_date",""),
            "expiration_date": entry.get("expiration_date",""),
            "payroll_frequency":entry.get("payroll_frequency","")
        }
        if live_status in ("pending", "processing", "hitl_pending") or cid not in merged:
            merged[cid] = live_row
 
    return sorted(merged.values(), key=lambda x: x["audit_case_id"], reverse=True)
 
 
# ─────────────────────────────────────────────
# Legacy list endpoint
# ─────────────────────────────────────────────
 
@router.get("/list")
async def list_audits_legacy(
    status: Optional[str] = None,
    limit:  int = 20,
    offset: int = 0,
):
    """Legacy list — kept for backwards compatibility."""
    all_cases = list(_AUDIT_REGISTRY.values())
    if status:
        all_cases = [c for c in all_cases if c.get("status") == status]
    return {"total": len(all_cases), "items": all_cases[offset: offset + limit]}
 
 
# ─────────────────────────────────────────────
# HITL Endpoints
# ─────────────────────────────────────────────
 
@router.get("/hitl/pending")
async def get_pending_hitl():
    """Return all audits currently awaiting human review."""
    return {"pending": get_pending_reviews()}
 
 
@router.post("/hitl/{audit_case_id}/resolve")
async def resolve_hitl_review(audit_case_id: int, request: HITLResolveRequest):
    """Submit a HITL review decision via the resolve interface."""
    if not resolve_hitl(
        audit_case_id = audit_case_id,
        action        = request.action,
        reviewer_id   = request.reviewer_id,
        notes         = request.notes or "",
        override_data = request.override_data,
    ):
        raise HTTPException(
            status_code=404,
            detail="No pending HITL review for this case.",
        )
    return {
        "audit_case_id": audit_case_id,
        "action":        request.action,
        "reviewer_id":   request.reviewer_id,
        "resolved_at":   datetime.utcnow().isoformat(),
        "message":       f"Review {request.action}d successfully. Workflow resuming.",
    }
 
 
@router.post("/{audit_case_id}/hitl-decision")
async def submit_hitl_decision(
    audit_case_id: int,
    payload: HITLDecisionRequest,
    tenant: Tenant = Depends(require_tenant),
):
    """
    Submit an auditor approve / reject decision from the React frontend.
 
    1. Updates the registry status immediately so the next poll sees it.
    2. Calls resolve_hitl() which sets the asyncio.Event that unblocks
       the hitl_checkpoint node and allows the graph to resume.
    """
    entry = _AUDIT_REGISTRY.get(audit_case_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Audit case not found.")
 
    action     = "approve" if payload.decision == "approve" else "reject"
    new_status = "completed" if action == "approve" else "rejected"
 
    entry["hitl_decision"] = payload.decision
    entry["hitl_notes"]    = payload.notes
    entry["status"]        = new_status
    if entry.get("result"):
        entry["result"]["hitl_required"] = False
 
    resolved = resolve_hitl(
        audit_case_id = audit_case_id,
        action        = action,
        reviewer_id   = "frontend_user",
        notes         = payload.notes,
    )
    if not resolved:
        logger.warning(
            f"[hitl-decision] resolve_hitl returned False for case {audit_case_id}. "
            "Registry updated but graph event was not found."
        )
 
    logger.info(f"[hitl-decision] Case {audit_case_id}: {action} by frontend user")
    return {
        "audit_case_id": audit_case_id,
        "decision":      payload.decision,
        "status":        new_status,
        "message":       f"HITL decision recorded. Status → {new_status}.",
    }
 
 
# ─────────────────────────────────────────────
# Report Download
# ─────────────────────────────────────────────
 
@router.get("/report/{audit_case_id}/download")
async def download_report(audit_case_id: int, request: Request):
    """Download the Excel audit report for a completed case."""
    entry = _AUDIT_REGISTRY.get(audit_case_id)
 
    if not entry:
        # Case not in memory — load from DB via ORM
        tenant    = getattr(request.state, "tenant", None)
        schema    = _db_get_schema(tenant)
        db_row    = _db_fetch_case(audit_case_id, schema)
        file_path = db_row.get("report_file_path") if db_row else None
        if file_path and os.path.exists(file_path):
            return FileResponse(
                path       = file_path,
                filename   = os.path.basename(file_path),
                media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers    = {
                    "Content-Disposition":          f'attachment; filename="{os.path.basename(file_path)}"',
                    "Access-Control-Expose-Headers": "Content-Disposition",
                },
            )
        raise HTTPException(status_code=404, detail="Audit case not found.")
 
    result    = entry.get("result") or {}
    file_path = result.get("report_file_path", "")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Report file not yet generated. The audit may still be processing.",
        )
    return FileResponse(
        path       = file_path,
        filename   = os.path.basename(file_path),
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers    = {
            "Content-Disposition":          f'attachment; filename="{os.path.basename(file_path)}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )