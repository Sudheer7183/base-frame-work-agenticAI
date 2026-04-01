

# """
# Database Persistence Node  (v3 — aligned to actual ORM models)
# ==============================================================
# Persists completed WCAuditState into all 9 WC tables using the
# exact column names, FK structure and enum values from wc_models.py
# and the create_wc_tables.py migration.

# Key design facts from the models:
#   • wc_policies.id        is the INTEGER PK (not policy_number)
#   • wc_audit_cases.id     is the INTEGER PK (not audit_case_id from state)
#   • wc_audit_cases.audit_reference  is NOT NULL UNIQUE  → we generate it
#   • wc_audit_cases.policy_id        is FK → wc_policies.id
#   • wc_payroll_records.audit_case_id is FK → wc_audit_cases.id (NOT NULL)
#   • wc_payroll_records.source        is NOT NULL enum
#   • audit_status_enum values: pending,ingesting,processing,review,approved,completed,rejected
#     (NO hitl_pending, NO error)
#   • agent findings use: agent_name, finding_type, summary, detail (JSONB), evidence_ref
#   • wc_hitl_reviews has NO status/risk_level columns

# Flow:
#   1. UPSERT wc_policies            → capture policy_db_id
#   2. INSERT  wc_policy_officers     (FK: policy_db_id)
#   3. INSERT  wc_policy_class_codes  (FK: policy_db_id)
#   4. UPSERT  wc_audit_cases         (FK: policy_db_id) → capture case_db_id
#   5. INSERT  wc_payroll_records     (FK: case_db_id)
#   6. INSERT  wc_variance_lines      (FK: case_db_id)
#   7. INSERT  wc_agent_findings      (FK: case_db_id)
#   8. INSERT  wc_hitl_reviews        (FK: case_db_id)
#   9. UPSERT  wc_audit_reports       (FK: case_db_id, UNIQUE on audit_case_id)
# """

# import json
# import logging
# from datetime import datetime, date
# from typing import Any, Optional

# from sqlalchemy import text
# from sqlalchemy.exc import SQLAlchemyError

# from app.core.database import SessionLocal
# from app.agent_langgraph.wc_state import WCAuditState

# logger = logging.getLogger(__name__)


# # ─────────────────────────────────────────────
# # Helpers
# # ─────────────────────────────────────────────

# def _safe(v: Any, default=None):
#     """Return None for empty / NaN-like / pandas NaT values."""
#     if v is None:
#         return default
#     tn = type(v).__name__
#     if tn in ("NaTType", "NAType"):
#         return default
#     if isinstance(v, float) and (v != v):
#         return default
#     if isinstance(v, str) and v.strip() in ("", "nan", "None", "NaT", "NaN", "nat"):
#         return default
#     return v


# def _date(v: Any) -> Optional[str]:
#     """Convert date/datetime/string → ISO date string, or None."""
#     if not v:
#         return None
#     tn = type(v).__name__
#     if tn in ("NaTType", "NAType"):
#         return None
#     if isinstance(v, (datetime, date)):
#         return v.strftime("%Y-%m-%d")
#     s = str(v).strip()
#     if s in ("NaT", "NaN", "", "None"):
#         return None
#     for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y/%m/%d"):
#         try:
#             return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
#         except ValueError:
#             pass
#     return None


# def _jsonb(v: Any) -> Optional[str]:
#     if v is None:
#         return None
#     try:
#         return json.dumps(v, default=str)
#     except Exception:
#         return None


# # audit_status_enum valid values (from migration DDL)
# _STAGE_TO_STATUS = {
#     "init":          "pending",
#     "pending":       "pending",
#     "processing":    "ingesting",
#     "running":       "ingesting",
#     "hitl_pending":  "review",
#     "hitl_approved": "approved",
#     "review":        "review",
#     "approved":      "approved",
#     "rejected":      "rejected",
#     "completed":     "completed",
#     "error":         "completed",
# }

# # hitl_decision values from hitl_checkpoint node
# _HITL_DECISION_TO_STATUS = {
#     "approve":  "approved",
#     "approved": "approved",
#     "reject":   "rejected",
#     "rejected": "rejected",
# }

# def _status(state: dict) -> str:
#     """
#     Determine the correct DB status from the full state dict.
#     Priority:
#       1. hitl_decision (set by hitl_checkpoint after human review)
#       2. errors in state → completed (persisted with errors noted in findings)
#       3. current_stage fallback
#     """
#     # 1. HITL decision takes highest priority — this is the definitive outcome
#     hitl = str(state.get("hitl_decision") or "").strip().lower()
#     if hitl in _HITL_DECISION_TO_STATUS:
#         return _HITL_DECISION_TO_STATUS[hitl]

#     # 2. Check for errors
#     if state.get("errors"):
#         return "completed"

#     # 3. Fall back to current_stage
#     stage = str(state.get("current_stage") or "").strip().lower()
#     return _STAGE_TO_STATUS.get(stage, "completed")


# def _fetchone(db, sql: str, params: dict):
#     try:
#         return db.execute(text(sql), params).fetchone()
#     except Exception:
#         return None


# # ─────────────────────────────────────────────
# # Node entry point
# # ─────────────────────────────────────────────

# def persist_to_database(state: WCAuditState) -> dict:
#     audit_case_id = state.get("audit_case_id")
#     tenant_id     = state.get("tenant_id", "default")
#     policy_cfg    = state.get("policy_config") or {}
#     policy_number = state.get("policy_number") or policy_cfg.get("policy_number", "")
#     schema        = f"tenant_{tenant_id}" if tenant_id != "default" else "public"
#     overall       = state.get("overall_variance") or {}
#     errors        = []
#     now           = datetime.utcnow().isoformat()

#     db = SessionLocal()
#     policy_db_id = None
#     case_db_id   = None

#     try:
#         db.execute(text(f'SET search_path TO "{schema}", public'))

#         # ── 1. wc_policies ────────────────────────────────────────────────
#         try:
#             xml_recs = state.get("xml_records") or [{}]
#             state_code = _safe(
#                 policy_cfg.get("governing_state")
#                 or policy_cfg.get("state")
#                 or xml_recs[0].get("StateCode"),
#                 "FL"
#             )
#             db.execute(text(f"""
#                 INSERT INTO {schema}.wc_policies
#                     (policy_number, insured_name, effective_date, expiration_date,
#                      estimated_premium, payroll_frequency, state_code, created_at, updated_at)
#                 VALUES
#                     (:policy_number, :insured_name, :effective_date, :expiration_date,
#                      :estimated_premium, :payroll_frequency, :state_code, :created_at, :updated_at)
#                 ON CONFLICT (policy_number) DO UPDATE SET
#                     insured_name      = EXCLUDED.insured_name,
#                     effective_date    = EXCLUDED.effective_date,
#                     expiration_date   = EXCLUDED.expiration_date,
#                     estimated_premium = EXCLUDED.estimated_premium,
#                     payroll_frequency = EXCLUDED.payroll_frequency,
#                     state_code        = EXCLUDED.state_code,
#                     updated_at        = EXCLUDED.updated_at
#             """), {
#                 "policy_number":    policy_number,
#                 "insured_name":     _safe(policy_cfg.get("insured_name"), "Unknown"),
#                 "effective_date":   _date(policy_cfg.get("effective_date")),
#                 "expiration_date":  _date(policy_cfg.get("expiration_date")),
#                 "estimated_premium":_safe(policy_cfg.get("est_premium"), 0),
#                 "payroll_frequency":_safe(policy_cfg.get("payroll_freq"), "1W"),
#                 "state_code":       state_code,
#                 "created_at":       now,
#                 "updated_at":       now,
#             })
#             row = _fetchone(db,
#                 f"SELECT id FROM {schema}.wc_policies WHERE policy_number = :pn",
#                 {"pn": policy_number})
#             policy_db_id = row[0] if row else None
#             logger.info(f"[DBPersist] wc_policies: id={policy_db_id} for {policy_number}")
#         except SQLAlchemyError as e:
#             logger.error(f"[DBPersist] wc_policies failed: {e}")
#             errors.append(f"wc_policies: {e}")
#             db.rollback()

#         # ── 2. wc_policy_officers ─────────────────────────────────────────
#         if policy_db_id:
#             officers = policy_cfg.get("officers") or []
#             if officers:
#                 try:
#                     db.execute(text(
#                         f"DELETE FROM {schema}.wc_policy_officers WHERE policy_id = :pid"
#                     ), {"pid": policy_db_id})
#                     for off in officers:
#                         db.execute(text(f"""
#                             INSERT INTO {schema}.wc_policy_officers
#                                 (policy_id, officer_name, title, is_on_payroll,
#                                  ownership_pct, state_code, created_at)
#                             VALUES
#                                 (:policy_id, :officer_name, :title, :is_on_payroll,
#                                  :ownership_pct, :state_code, :created_at)
#                         """), {
#                             "policy_id":    policy_db_id,
#                             "officer_name": _safe(off.get("name"), "Unknown"),
#                             "title":        _safe(off.get("title")),
#                             "is_on_payroll":bool(off.get("is_on_payroll", True)),
#                             "ownership_pct":_safe(off.get("ownership_pct"), 0),
#                             "state_code":   _safe(off.get("state_code")),
#                             "created_at":   now,
#                         })
#                 except SQLAlchemyError as e:
#                     logger.error(f"[DBPersist] wc_policy_officers failed: {e}")
#                     errors.append(f"wc_policy_officers: {e}")
#                     db.rollback()

#         # ── 3. wc_policy_class_codes ──────────────────────────────────────
#         if policy_db_id:
#             try:
#                 for xrec in (state.get("xml_records") or []):
#                     db.execute(text(f"""
#                         INSERT INTO {schema}.wc_policy_class_codes
#                             (policy_id, class_code, state_code, composite_rate,
#                              exposure, est_premium, est_cc_premium,
#                              endorsement_version, created_at)
#                         VALUES
#                             (:policy_id, :class_code, :state_code, :composite_rate,
#                              :exposure, :est_premium, :est_cc_premium,
#                              :endorsement_version, :created_at)
#                         ON CONFLICT DO NOTHING
#                     """), {
#                         "policy_id":          policy_db_id,
#                         "class_code":         _safe(str(xrec.get("classCode", ""))),
#                         "state_code":         _safe(xrec.get("StateCode")),
#                         "composite_rate":     _safe(xrec.get("CompositeRate"), 0),
#                         "exposure":           _safe(xrec.get("Exposure"), 0),
#                         "est_premium":        _safe(xrec.get("EstPremium"), 0),
#                         "est_cc_premium":     _safe(xrec.get("EstCCpremium"), 0),
#                         "endorsement_version":_safe(xrec.get("endorsement_version"), "V1"),
#                         "created_at":         now,
#                     })
#                 logger.info(f"[DBPersist] wc_policy_class_codes: {len(state.get('xml_records') or [])} rows")
#             except SQLAlchemyError as e:
#                 logger.error(f"[DBPersist] wc_policy_class_codes failed: {e}")
#                 errors.append(f"wc_policy_class_codes: {e}")
#                 db.rollback()

#         # ── 4. wc_audit_cases ─────────────────────────────────────────────
#         if policy_db_id:
#             audit_ref     = f"WCA-{policy_number}-{audit_case_id}"
#             mapped_status = _status(dict(state))   # reads hitl_decision + current_stage
#             try:
#                 db.execute(text(f"""
#                     INSERT INTO {schema}.wc_audit_cases
#                         (policy_id, audit_reference, status,
#                          first_check_date, last_check_date,
#                          expected_submissions, actual_submissions, submitted_count,
#                          total_earned_exposure, total_earned_premium,
#                          total_est_exposure, total_est_ytd_premium,
#                          total_variance, total_variance_pct,
#                          ai_narrative, risk_level, recommendation, hitl_required,
#                          payroll_file_path, policy_xml_path, audit_meta_file_path,
#                          created_at, updated_at, completed_at)
#                     VALUES
#                         (:policy_id, :audit_reference, :status,
#                          :first_check_date, :last_check_date,
#                          :expected_submissions, :actual_submissions, :submitted_count,
#                          :total_earned_exposure, :total_earned_premium,
#                          :total_est_exposure, :total_est_ytd_premium,
#                          :total_variance, :total_variance_pct,
#                          :ai_narrative, :risk_level, :recommendation, :hitl_required,
#                          :payroll_file_path, :policy_xml_path, :audit_meta_file_path,
#                          :created_at, :updated_at, :completed_at)
#                     ON CONFLICT (audit_reference) DO UPDATE SET
#                         status                = EXCLUDED.status,
#                         first_check_date      = EXCLUDED.first_check_date,
#                         last_check_date       = EXCLUDED.last_check_date,
#                         submitted_count       = EXCLUDED.submitted_count,
#                         total_earned_exposure = EXCLUDED.total_earned_exposure,
#                         total_earned_premium  = EXCLUDED.total_earned_premium,
#                         total_est_exposure    = EXCLUDED.total_est_exposure,
#                         total_est_ytd_premium = EXCLUDED.total_est_ytd_premium,
#                         total_variance        = EXCLUDED.total_variance,
#                         total_variance_pct    = EXCLUDED.total_variance_pct,
#                         ai_narrative          = EXCLUDED.ai_narrative,
#                         risk_level            = EXCLUDED.risk_level,
#                         recommendation        = EXCLUDED.recommendation,
#                         hitl_required         = EXCLUDED.hitl_required,
#                         updated_at            = EXCLUDED.updated_at,
#                         completed_at          = EXCLUDED.completed_at
#                 """), {
#                     "policy_id":            policy_db_id,
#                     "audit_reference":      audit_ref,
#                     "status":               mapped_status,
#                     "first_check_date":     _date(state.get("first_check_date")),
#                     "last_check_date":      _date(state.get("last_check_date")),
#                     "expected_submissions": _safe(state.get("expected_submissions"), 0),
#                     "actual_submissions":   _safe(state.get("actual_submissions"), 0),
#                     "submitted_count":      _safe(state.get("submitted_count"), 0),
#                     "total_earned_exposure":_safe(overall.get("earned_exposure"), 0),
#                     "total_earned_premium": _safe(overall.get("earned_premium"), 0),
#                     "total_est_exposure":   _safe(overall.get("est_exposure"), 0),
#                     "total_est_ytd_premium":_safe(overall.get("est_ytd_premium"), 0),
#                     "total_variance":       _safe(overall.get("variance"), 0),
#                     "total_variance_pct":   _safe(overall.get("variance_pct"), 0),
#                     "ai_narrative":         _safe(state.get("ai_narrative")),
#                     "risk_level":           _safe(state.get("risk_level"), "low"),
#                     "recommendation":       _safe(state.get("recommendation")),
#                     "hitl_required":        bool(state.get("hitl_required", False)),
#                     "payroll_file_path":    _safe(state.get("payroll_file_path")),
#                     "policy_xml_path":      _safe(state.get("policy_xml_path")),
#                     "audit_meta_file_path": _safe(state.get("audit_meta_file_path")),
#                     "created_at":           now,
#                     "updated_at":           now,
#                     "completed_at":         now,
#                 })
#                 row = _fetchone(db,
#                     f"SELECT id FROM {schema}.wc_audit_cases WHERE audit_reference = :ref",
#                     {"ref": audit_ref})
#                 case_db_id = row[0] if row else None
#                 logger.info(f"[DBPersist] wc_audit_cases: id={case_db_id}, ref={audit_ref}, status={mapped_status}")
#             except SQLAlchemyError as e:
#                 logger.error(f"[DBPersist] wc_audit_cases failed: {e}")
#                 errors.append(f"wc_audit_cases: {e}")
#                 db.rollback()

#         # ── 5. wc_payroll_records ─────────────────────────────────────────
#         if case_db_id:
#             try:
#                 inserted = 0
#                 for prec in (state.get("excel_records") or []):
#                     check_date = _date(prec.get("check_date"))
#                     if not check_date or not _safe(prec.get("policy_number")):
#                         continue
#                     db.execute(text(f"""
#                         INSERT INTO {schema}.wc_payroll_records
#                             (audit_case_id, source, client_name, policy_number,
#                              check_date, ee_no, employee_name, state_code, class_code,
#                              wages, overtime_pay, double_time, tips, net_pay,
#                              exposure, net_rate, earned_premium,
#                              census_rate, census_premium,
#                              pol_eff_date, process_date, created_at)
#                         VALUES
#                             (:audit_case_id, :source, :client_name, :policy_number,
#                              :check_date, :ee_no, :employee_name, :state_code, :class_code,
#                              :wages, :overtime_pay, :double_time, :tips, :net_pay,
#                              :exposure, :net_rate, :earned_premium,
#                              :census_rate, :census_premium,
#                              :pol_eff_date, :process_date, :created_at)
#                         ON CONFLICT DO NOTHING
#                     """), {
#                         "audit_case_id":  case_db_id,
#                         "source":         "insured",
#                         "client_name":    _safe(prec.get("client_name")),
#                         "policy_number":  _safe(prec.get("policy_number")),
#                         "check_date":     check_date,
#                         "ee_no":          _safe(prec.get("ee_no")),
#                         "employee_name":  _safe(prec.get("employee_name")),
#                         "state_code":     _safe(prec.get("state_code")),
#                         "class_code":     _safe(str(prec.get("class_code", ""))),
#                         "wages":          _safe(prec.get("wages"), 0),
#                         "overtime_pay":   _safe(prec.get("overtime_pay"), 0),
#                         "double_time":    _safe(prec.get("double_time"), 0),
#                         "tips":           _safe(prec.get("tips"), 0),
#                         "net_pay":        _safe(prec.get("net_pay"), 0),
#                         "exposure":       _safe(prec.get("exposure"), 0),
#                         "net_rate":       _safe(prec.get("net_rate"), 0),
#                         "earned_premium": _safe(prec.get("earned_premium"), 0),
#                         "census_rate":    _safe(prec.get("census_rate"), 0),
#                         "census_premium": _safe(prec.get("census_premium"), 0),
#                         "pol_eff_date":   _date(prec.get("pol_eff_date")),
#                         "process_date":   _date(prec.get("process_date")),
#                         "created_at":     now,
#                     })
#                     inserted += 1
#                 logger.info(f"[DBPersist] wc_payroll_records: {inserted} rows")
#             except SQLAlchemyError as e:
#                 logger.error(f"[DBPersist] wc_payroll_records failed: {e}")
#                 errors.append(f"wc_payroll_records: {e}")
#                 db.rollback()

#         # ── 6. wc_variance_lines ──────────────────────────────────────────
#         if case_db_id:
#             try:
#                 db.execute(text(
#                     f"DELETE FROM {schema}.wc_variance_lines WHERE audit_case_id = :cid"
#                 ), {"cid": case_db_id})
#                 for vrow in (state.get("class_code_variance") or []):
#                     db.execute(text(f"""
#                         INSERT INTO {schema}.wc_variance_lines
#                             (audit_case_id, policy_number, state_code, class_code,
#                              earned_exposure, earned_premium, est_exposure, est_ytd_premium,
#                              variance, variance_pct, root_cause, is_flagged, created_at)
#                         VALUES
#                             (:audit_case_id, :policy_number, :state_code, :class_code,
#                              :earned_exposure, :earned_premium, :est_exposure, :est_ytd_premium,
#                              :variance, :variance_pct, :root_cause, :is_flagged, :created_at)
#                         ON CONFLICT DO NOTHING
#                     """), {
#                         "audit_case_id":  case_db_id,
#                         "policy_number":  _safe(vrow.get("PolicyNumber")),
#                         "state_code":     _safe(vrow.get("StateCode")),
#                         "class_code":     _safe(str(vrow.get("ClassCode", ""))),
#                         "earned_exposure":_safe(vrow.get("earned_exposure"), 0),
#                         "earned_premium": _safe(vrow.get("earned_premium"), 0),
#                         "est_exposure":   _safe(vrow.get("est_exposure"), 0),
#                         "est_ytd_premium":_safe(vrow.get("est_ytd_premium"), 0),
#                         "variance":       _safe(vrow.get("variance"), 0),
#                         "variance_pct":   _safe(vrow.get("variance_pct"), 0),
#                         "root_cause":     _safe(vrow.get("root_cause"), "none"),
#                         "is_flagged":     bool(vrow.get("is_flagged", False)),
#                         "created_at":     now,
#                     })
#                 logger.info(f"[DBPersist] wc_variance_lines: {len(state.get('class_code_variance') or [])} rows")
#             except SQLAlchemyError as e:
#                 logger.error(f"[DBPersist] wc_variance_lines failed: {e}")
#                 errors.append(f"wc_variance_lines: {e}")
#                 db.rollback()

#         # ── 7. wc_agent_findings ──────────────────────────────────────────
#         if case_db_id:
#             try:
#                 db.execute(text(
#                     f"DELETE FROM {schema}.wc_agent_findings WHERE audit_case_id = :cid"
#                 ), {"cid": case_db_id})
#                 agent_name_map = {
#                     "officer":    "OfficerAgent",
#                     "class_code": "ClassCodeAgent",
#                     "frequency":  "FrequencyAgent",
#                 }
#                 all_findings = [
#                     *[{**f, "_type": "officer"}     for f in (state.get("officer_findings")    or [])],
#                     *[{**f, "_type": "class_code"}  for f in (state.get("class_code_findings") or [])],
#                     *[{**f, "_type": "frequency"}   for f in (state.get("frequency_findings")  or [])],
#                 ]
#                 for finding in all_findings:
#                     ftype      = finding.get("_type", "system")
#                     agent_name = agent_name_map.get(ftype, "WCAuditAgent")
#                     detail_data = {k: v for k, v in finding.items() if k != "_type"}
#                     db.execute(text(f"""
#                         INSERT INTO {schema}.wc_agent_findings
#                             (audit_case_id, agent_name, finding_type,
#                              severity, summary, detail, created_at)
#                         VALUES
#                             (:audit_case_id, :agent_name, :finding_type,
#                              :severity, :summary, :detail, :created_at)
#                         ON CONFLICT DO NOTHING
#                     """), {
#                         "audit_case_id": case_db_id,
#                         "agent_name":    agent_name,
#                         "finding_type":  _safe(finding.get("issue") or finding.get("finding_type")),
#                         "severity":      _safe(finding.get("severity"), "info"),
#                         "summary":       _safe(finding.get("description")),
#                         "detail":        _jsonb(detail_data),
#                         "created_at":    now,
#                     })
#                 logger.info(f"[DBPersist] wc_agent_findings: {len(all_findings)} findings")
#             except SQLAlchemyError as e:
#                 logger.error(f"[DBPersist] wc_agent_findings failed: {e}")
#                 errors.append(f"wc_agent_findings: {e}")
#                 db.rollback()

#         # ── 8. wc_hitl_reviews ────────────────────────────────────────────
#         if case_db_id and state.get("hitl_required"):
#             try:
#                 db.execute(text(f"""
#                     INSERT INTO {schema}.wc_hitl_reviews
#                         (audit_case_id, reviewer_id, action, notes, override_data, reviewed_at)
#                     VALUES
#                         (:audit_case_id, :reviewer_id, :action, :notes, :override_data, :reviewed_at)
#                     ON CONFLICT DO NOTHING
#                 """), {
#                     "audit_case_id": case_db_id,
#                     "reviewer_id":   _safe(state.get("hitl_reviewer"), "system"),
#                     "action":        _safe(state.get("hitl_decision"), "pending"),
#                     "notes":         _safe(state.get("hitl_notes")),
#                     "override_data": None,
#                     "reviewed_at":   now,
#                 })
#                 logger.info(f"[DBPersist] wc_hitl_reviews: inserted for case {case_db_id}")
#             except SQLAlchemyError as e:
#                 logger.error(f"[DBPersist] wc_hitl_reviews failed: {e}")
#                 errors.append(f"wc_hitl_reviews: {e}")
#                 db.rollback()

#         # ── 9. wc_audit_reports ───────────────────────────────────────────
#         if case_db_id:
#             report_file = (
#                 _safe(state.get("report_file_path"))
#                 or _safe((state.get("report_data") or {}).get("report_file_path"))
#             )
#             try:
#                 db.execute(text(f"""
#                     INSERT INTO {schema}.wc_audit_reports
#                         (audit_case_id, report_ref, report_file, summary, is_final, generated_at)
#                     VALUES
#                         (:audit_case_id, :report_ref, :report_file, :summary, :is_final, :generated_at)
#                     ON CONFLICT (audit_case_id) DO UPDATE SET
#                         report_file  = EXCLUDED.report_file,
#                         summary      = EXCLUDED.summary,
#                         is_final     = EXCLUDED.is_final,
#                         generated_at = EXCLUDED.generated_at
#                 """), {
#                     "audit_case_id": case_db_id,
#                     "report_ref":    f"WCA-{policy_number}-{audit_case_id}-REPORT",
#                     "report_file":   report_file,
#                     "summary":       _safe(state.get("ai_narrative")),
#                     "is_final":      bool(state.get("hitl_decision") == "approve"
#                                           or not state.get("hitl_required")),
#                     "generated_at":  now,
#                 })
#                 logger.info(f"[DBPersist] wc_audit_reports: upserted for case {case_db_id}")
#             except SQLAlchemyError as e:
#                 logger.error(f"[DBPersist] wc_audit_reports failed: {e}")
#                 errors.append(f"wc_audit_reports: {e}")
#                 db.rollback()

#         db.commit()
#         logger.info(
#             f"[DBPersist] Case {audit_case_id} ({policy_number}) committed. "
#             f"policy_db_id={policy_db_id}, case_db_id={case_db_id}, errors={len(errors)}"
#         )

#     except Exception as exc:
#         logger.error(f"[DBPersist] Fatal: {exc}", exc_info=True)
#         db.rollback()
#         errors.append(f"fatal: {exc}")
#     finally:
#         db.close()

#     return {
#         "errors": errors,
#         "agent_logs": [{
#             "agent":        "db_persistence",
#             "status":       "error" if errors else "success",
#             "policy_db_id": policy_db_id,
#             "case_db_id":   case_db_id,
#             "errors":       errors,
#             "timestamp":    datetime.utcnow().isoformat(),
#         }],
#     }

"""
Database Persistence Node  (v4 — Full SQLAlchemy ORM)
======================================================
Persists completed WCAuditState into all 9 WC tables using ONLY
SQLAlchemy ORM model operations.  Zero raw SQL / text() calls.

ORM pattern used per table:
  • wc_policies        → query-then-update or add (upsert via Python)
  • wc_policy_officers → delete-all + bulk add
  • wc_policy_class_codes → exists-check + conditional add
  • wc_audit_cases     → query-then-update or add (upsert via Python)
  • wc_payroll_records → bulk add (append-only)
  • wc_variance_lines  → delete-all + bulk add
  • wc_agent_findings  → delete-all + bulk add
  • wc_hitl_reviews    → conditional add
  • wc_audit_reports   → query-then-update or add (upsert via Python)

File: backend/app/agent_langgraph/wc_nodes/db_persistence.py
"""

import logging
from datetime import datetime, date
from typing import Any, Optional

from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.agent_langgraph.wc_state import WCAuditState
from app.models.wc_audit import (
    Policy, PolicyClassCode, PolicyOfficer,
    AuditCase, PayrollRecord, VarianceLine,
    AgentFinding, HITLReview, AuditReport,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _safe(v: Any, default=None):
    """Return `default` for empty / NaN-like / pandas NaT values."""
    if v is None:
        return default
    tn = type(v).__name__
    if tn in ("NaTType", "NAType"):
        return default
    if isinstance(v, float) and (v != v):          # NaN check
        return default
    if isinstance(v, str) and v.strip() in ("", "nan", "None", "NaT", "NaN", "nat"):
        return default
    return v


def _date(v: Any) -> Optional[date]:
    """Convert date / datetime / string → Python date, or None."""
    if not v:
        return None
    tn = type(v).__name__
    if tn in ("NaTType", "NAType"):
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v).strip()
    if s in ("NaT", "NaN", "", "None"):
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


# ── Status mapping ────────────────────────────────────────────────────────────
# Maps internal agent-stage strings → DB enum values (plain VARCHAR columns).
_STAGE_TO_STATUS = {
    "init":          "pending",
    "pending":       "pending",
    "processing":    "ingesting",
    "running":       "ingesting",
    "hitl_pending":  "review",
    "hitl_approved": "approved",
    "review":        "review",
    "approved":      "approved",
    "rejected":      "rejected",
    "completed":     "completed",
    "error":         "completed",
}


def _status(state: dict) -> str:
    """Derive the DB status string from the audit state dict."""
    if state.get("hitl_decision") == "approve":
        return "approved"
    if state.get("hitl_decision") == "reject":
        return "rejected"
    if state.get("errors"):
        return "completed"
    stage = str(state.get("current_stage") or "").strip().lower()
    return _STAGE_TO_STATUS.get(stage, "completed")


# ─────────────────────────────────────────────
# Node entry point
# ─────────────────────────────────────────────
def _clean_state_code(officer: dict) -> str | None:
    """
    Safely extract a VARCHAR(5)-safe state code from an officer dict.
 
    The Mock API sometimes puts a check date ("03/30/2025") in state_code
    and the real 2-letter state abbreviation in title ("CA").
    Detection rule: if state_code contains "/" or "-" or is longer than 5 chars,
    it's a date — use title[:5] instead.
    Always hard-caps the result to 5 characters.
    """
    raw = str(officer.get("state_code") or "").strip()
    title = str(officer.get("title") or "").strip()
 
    is_date_like = "/" in raw or "-" in raw or len(raw) > 5
 
    if is_date_like or not raw:
        # Use title as fallback — it usually holds the state abbreviation
        return title[:5] if title else None
 
    return raw[:5]   # hard-cap even for seemingly valid values

def persist_to_database(state: WCAuditState) -> dict:
    """
    LangGraph node — persists the final WCAuditState to all 9 WC tables
    using pure SQLAlchemy ORM (no raw SQL).
    """
    audit_case_id = state.get("audit_case_id")
    tenant_id     = state.get("tenant_id", "default")
    policy_cfg    = state.get("policy_config") or {}
    policy_number = state.get("policy_number") or policy_cfg.get("policy_number", "")
    overall       = state.get("overall_variance") or {}
    errors:  list = []
    now           = datetime.utcnow()

    db = SessionLocal()
    policy_db_id: Optional[int] = None
    case_db_id:   Optional[int] = None

    # ── Set tenant schema search path (driver-level config, not a data query)
    schema = f"tenant_{tenant_id}" if tenant_id != "default" else "public"
    db.connection().exec_driver_sql(f'SET search_path TO "{schema}", public')

    try:

        # ══════════════════════════════════════════════════════════════════
        # 1. wc_policies  — upsert by policy_number
        # ══════════════════════════════════════════════════════════════════
        try:
            xml_recs   = state.get("xml_records") or [{}]
            state_code = _safe(
                policy_cfg.get("governing_state")
                or policy_cfg.get("state")
                or xml_recs[0].get("StateCode"),
                "FL",
            )

            policy_obj = (
                db.query(Policy)
                .filter(Policy.policy_number == policy_number)
                .first()
            )

            if policy_obj is None:
                policy_obj = Policy(
                    policy_number     = policy_number,
                    insured_name      = _safe(policy_cfg.get("insured_name"), "Unknown"),
                    effective_date    = _date(policy_cfg.get("effective_date")),
                    expiration_date   = _date(policy_cfg.get("expiration_date")),
                    estimated_premium = _safe(policy_cfg.get("est_premium"), 0),
                    payroll_frequency = _safe(policy_cfg.get("payroll_freq"), "1W"),
                    state_code        = state_code,
                    created_at        = now,
                    updated_at        = now,
                )
                db.add(policy_obj)
            else:
                policy_obj.insured_name      = _safe(policy_cfg.get("insured_name"), "Unknown")
                policy_obj.effective_date    = _date(policy_cfg.get("effective_date"))
                policy_obj.expiration_date   = _date(policy_cfg.get("expiration_date"))
                policy_obj.estimated_premium = _safe(policy_cfg.get("est_premium"), 0)
                policy_obj.payroll_frequency = _safe(policy_cfg.get("payroll_freq"), "1W")
                policy_obj.state_code        = state_code
                policy_obj.updated_at        = now

            db.flush()    # generates policy_obj.id without committing
            policy_db_id = policy_obj.id
            logger.info(f"[DBPersist] wc_policies: id={policy_db_id} for {policy_number}")

        except SQLAlchemyError as e:
            logger.error(f"[DBPersist] wc_policies failed: {e}")
            errors.append(f"wc_policies: {e}")
            db.rollback()

        # ══════════════════════════════════════════════════════════════════
        # 2. wc_policy_officers  — delete-and-replace
        # ══════════════════════════════════════════════════════════════════
        if policy_db_id:
            officers = policy_cfg.get("officers") or []
            if officers:
                try:
                    # Delete existing officers for this policy
                    db.query(PolicyOfficer).filter(
                        PolicyOfficer.policy_id == policy_db_id
                    ).delete(synchronize_session=False)

                    # for off in officers:
                    #     db.add(PolicyOfficer(
                    #         policy_id     = policy_db_id,
                    #         officer_name  = _safe(off.get("name"), "Unknown"),
                    #         title         = _safe(off.get("title")),
                    #         is_on_payroll = bool(off.get("is_on_payroll", True)),
                    #         ownership_pct = _safe(off.get("ownership_pct"), 0),
                    #         state_code    = _safe(off.get("state_code")),
                    #         created_at    = now,
                    #     ))

                    for off in officers:
                        db.add(PolicyOfficer(
                            policy_id     = policy_db_id,
                            officer_name  = _safe(off.get("officer_name") or off.get("name"), "Unknown"),
                            title         = _safe(off.get("title")),
                            is_on_payroll = bool(off.get("is_on_payroll", True)),
                            ownership_pct = _safe(off.get("ownership_pct"), 0),
                            state_code    = _clean_state_code(off),   
                            created_at    = now,
                        ))
                    db.flush()
                    logger.info(f"[DBPersist] wc_policy_officers: {len(officers)} rows")

                except SQLAlchemyError as e:
                    logger.error(f"[DBPersist] wc_policy_officers failed: {e}")
                    errors.append(f"wc_policy_officers: {e}")
                    db.rollback()

        # ══════════════════════════════════════════════════════════════════
        # 3. wc_policy_class_codes  — skip if already exists (ON CONFLICT DO NOTHING)
        # ══════════════════════════════════════════════════════════════════
        if policy_db_id:
            try:
                for xrec in (state.get("xml_records") or []):
                    cc = _safe(str(xrec.get("classCode", "")))
                    sc = _safe(xrec.get("StateCode"))

                    already_exists = (
                        db.query(PolicyClassCode)
                        .filter(
                            PolicyClassCode.policy_id  == policy_db_id,
                            PolicyClassCode.class_code == cc,
                            PolicyClassCode.state_code == sc,
                        )
                        .first()
                    )
                    if not already_exists:
                        db.add(PolicyClassCode(
                            policy_id           = policy_db_id,
                            class_code          = cc,
                            class_desc          = _safe(xrec.get("ClassDesc")),
                            state_code          = sc,
                            composite_rate      = _safe(xrec.get("CompositeRate"), 0),
                            exposure            = _safe(xrec.get("Exposure"), 0),
                            est_premium         = _safe(xrec.get("EstPremium"), 0),
                            est_cc_premium      = _safe(xrec.get("EstCCpremium"), 0),
                            endorsement_version = _safe(xrec.get("endorsement_version"), "V1"),
                            created_at          = now,
                        ))

                db.flush()
                logger.info(
                    f"[DBPersist] wc_policy_class_codes: "
                    f"{len(state.get('xml_records') or [])} processed"
                )
            except SQLAlchemyError as e:
                logger.error(f"[DBPersist] wc_policy_class_codes failed: {e}")
                errors.append(f"wc_policy_class_codes: {e}")
                db.rollback()

        # ══════════════════════════════════════════════════════════════════
        # 4. wc_audit_cases  — upsert by audit_reference
        # ══════════════════════════════════════════════════════════════════
        if policy_db_id:
            audit_ref     = f"WCA-{policy_number}-{audit_case_id}"
            mapped_status = _status(dict(state))
            try:
                case_obj = (
                    db.query(AuditCase)
                    .filter(AuditCase.audit_reference == audit_ref)
                    .first()
                )

                # Build a dict of all writeable fields so we update & create the same way
                case_fields = dict(
                    policy_id             = policy_db_id,
                    audit_reference       = audit_ref,
                    status                = mapped_status,
                    first_check_date      = _date(state.get("first_check_date")),
                    last_check_date       = _date(state.get("last_check_date")),
                    expected_submissions  = _safe(state.get("expected_submissions"), 0),
                    actual_submissions    = _safe(state.get("actual_submissions"), 0),
                    submitted_count       = _safe(state.get("submitted_count"), 0),
                    total_earned_exposure = _safe(overall.get("earned_exposure"), 0),
                    total_earned_premium  = _safe(overall.get("earned_premium"), 0),
                    total_est_exposure    = _safe(overall.get("est_exposure"), 0),
                    total_est_ytd_premium = _safe(overall.get("est_ytd_premium"), 0),
                    total_variance        = _safe(overall.get("variance"), 0),
                    total_variance_pct    = _safe(overall.get("variance_pct"), 0),
                    ai_narrative          = _safe(state.get("ai_narrative")),
                    risk_level            = _safe(state.get("risk_level"), "low"),
                    recommendation        = _safe(state.get("recommendation")),
                    hitl_required         = bool(state.get("hitl_required", False)),
                    payroll_file_path     = _safe(state.get("payroll_file_path")),
                    policy_xml_path       = _safe(state.get("policy_xml_path")),
                    audit_meta_file_path  = _safe(state.get("audit_meta_file_path")),
                    updated_at            = now,
                    completed_at          = now,
                )

                if case_obj is None:
                    case_obj = AuditCase(**case_fields, created_at=now)
                    db.add(case_obj)
                else:
                    for field, value in case_fields.items():
                        setattr(case_obj, field, value)

                db.flush()
                case_db_id = case_obj.id
                logger.info(
                    f"[DBPersist] wc_audit_cases: "
                    f"id={case_db_id}, ref={audit_ref}, status={mapped_status}"
                )

            except SQLAlchemyError as e:
                logger.error(f"[DBPersist] wc_audit_cases failed: {e}")
                errors.append(f"wc_audit_cases: {e}")
                db.rollback()

        # ══════════════════════════════════════════════════════════════════
        # 5. wc_payroll_records  — append-only (skip invalid rows)
        # ══════════════════════════════════════════════════════════════════
        if case_db_id:
            try:
                inserted = 0
                for prec in (state.get("excel_records") or []):
                    check_date = _date(prec.get("check_date"))
                    if not check_date or not _safe(prec.get("policy_number")):
                        continue

                    db.add(PayrollRecord(
                        audit_case_id  = case_db_id,
                        source         = "insured",
                        client_name    = _safe(prec.get("client_name")),
                        policy_number  = _safe(prec.get("policy_number")),
                        check_date     = check_date,
                        ee_no          = _safe(prec.get("ee_no")),
                        employee_name  = _safe(prec.get("employee_name")),
                        state_code     = _safe(prec.get("state_code")),
                        class_code     = _safe(str(prec.get("class_code", ""))),
                        wages          = _safe(prec.get("wages"), 0),
                        overtime_pay   = _safe(prec.get("overtime_pay"), 0),
                        double_time    = _safe(prec.get("double_time"), 0),
                        tips           = _safe(prec.get("tips"), 0),
                        net_pay        = _safe(prec.get("net_pay"), 0),
                        exposure       = _safe(prec.get("exposure"), 0),
                        net_rate       = _safe(prec.get("net_rate"), 0),
                        earned_premium = _safe(prec.get("earned_premium"), 0),
                        census_rate    = _safe(prec.get("census_rate"), 0),
                        census_premium = _safe(prec.get("census_premium"), 0),
                        pol_eff_date   = _date(prec.get("pol_eff_date")),
                        process_date   = _date(prec.get("process_date")),
                        created_at     = now,
                    ))
                    inserted += 1

                db.flush()
                logger.info(f"[DBPersist] wc_payroll_records: {inserted} rows")

            except SQLAlchemyError as e:
                logger.error(f"[DBPersist] wc_payroll_records failed: {e}")
                errors.append(f"wc_payroll_records: {e}")
                db.rollback()

        # ══════════════════════════════════════════════════════════════════
        # 6. wc_variance_lines  — delete-and-replace
        # ══════════════════════════════════════════════════════════════════
        if case_db_id:
            try:
                db.query(VarianceLine).filter(
                    VarianceLine.audit_case_id == case_db_id
                ).delete(synchronize_session=False)

                for vrow in (state.get("class_code_variance") or []):
                    db.add(VarianceLine(
                        audit_case_id  = case_db_id,
                        policy_number  = _safe(vrow.get("PolicyNumber")),
                        state_code     = _safe(vrow.get("StateCode")),
                        class_code     = _safe(str(vrow.get("ClassCode", ""))),
                        earned_exposure= _safe(vrow.get("earned_exposure"), 0),
                        earned_premium = _safe(vrow.get("earned_premium"), 0),
                        est_exposure   = _safe(vrow.get("est_exposure"), 0),
                        est_ytd_premium= _safe(vrow.get("est_ytd_premium"), 0),
                        variance       = _safe(vrow.get("variance"), 0),
                        variance_pct   = _safe(vrow.get("variance_pct"), 0),
                        root_cause     = _safe(vrow.get("root_cause"), "none"),
                        is_flagged     = bool(vrow.get("is_flagged", False)),
                        created_at     = now,
                    ))

                db.flush()
                logger.info(
                    f"[DBPersist] wc_variance_lines: "
                    f"{len(state.get('class_code_variance') or [])} rows"
                )
            except SQLAlchemyError as e:
                logger.error(f"[DBPersist] wc_variance_lines failed: {e}")
                errors.append(f"wc_variance_lines: {e}")
                db.rollback()

        # ══════════════════════════════════════════════════════════════════
        # 7. wc_agent_findings  — delete-and-replace
        # ══════════════════════════════════════════════════════════════════
        if case_db_id:
            try:
                db.query(AgentFinding).filter(
                    AgentFinding.audit_case_id == case_db_id
                ).delete(synchronize_session=False)

                agent_name_map = {
                    "officer":    "OfficerAgent",
                    "class_code": "ClassCodeAgent",
                    "frequency":  "FrequencyAgent",
                }
                all_findings = [
                    *[{**f, "_type": "officer"}    for f in (state.get("officer_findings")    or [])],
                    *[{**f, "_type": "class_code"} for f in (state.get("class_code_findings") or [])],
                    *[{**f, "_type": "frequency"}  for f in (state.get("frequency_findings")  or [])],
                ]

                for finding in all_findings:
                    ftype       = finding.get("_type", "system")
                    agent_name  = agent_name_map.get(ftype, "WCAuditAgent")
                    detail_data = {k: v for k, v in finding.items() if k != "_type"}

                    db.add(AgentFinding(
                        audit_case_id = case_db_id,
                        agent_name    = agent_name,
                        finding_type  = _safe(finding.get("issue") or finding.get("finding_type")),
                        severity      = _safe(finding.get("severity"), "info"),
                        summary       = _safe(finding.get("description")),
                        detail        = detail_data,      # JSON column — ORM handles serialisation
                        created_at    = now,
                    ))

                db.flush()
                logger.info(f"[DBPersist] wc_agent_findings: {len(all_findings)} findings")

            except SQLAlchemyError as e:
                logger.error(f"[DBPersist] wc_agent_findings failed: {e}")
                errors.append(f"wc_agent_findings: {e}")
                db.rollback()

        # ══════════════════════════════════════════════════════════════════
        # 8. wc_hitl_reviews  — insert only when HITL is required
        # ══════════════════════════════════════════════════════════════════
        if case_db_id and state.get("hitl_required"):
            try:
                db.add(HITLReview(
                    audit_case_id = case_db_id,
                    reviewer_id   = _safe(state.get("hitl_reviewer"), "system"),
                    action        = _safe(state.get("hitl_decision"), "pending"),
                    notes         = _safe(state.get("hitl_notes")),
                    override_data = None,
                    reviewed_at   = now,
                ))
                db.flush()
                logger.info(f"[DBPersist] wc_hitl_reviews: inserted for case {case_db_id}")

            except SQLAlchemyError as e:
                logger.error(f"[DBPersist] wc_hitl_reviews failed: {e}")
                errors.append(f"wc_hitl_reviews: {e}")
                db.rollback()

        # ══════════════════════════════════════════════════════════════════
        # 9. wc_audit_reports  — upsert by audit_case_id (unique constraint)
        # ══════════════════════════════════════════════════════════════════
        if case_db_id:
            report_file = (
                _safe(state.get("report_file_path"))
                or _safe((state.get("report_data") or {}).get("report_file_path"))
            )
            try:
                report_obj = (
                    db.query(AuditReport)
                    .filter(AuditReport.audit_case_id == case_db_id)
                    .first()
                )
                is_final = bool(
                    state.get("hitl_decision") == "approve"
                    or not state.get("hitl_required")
                )

                if report_obj is None:
                    report_obj = AuditReport(
                        audit_case_id = case_db_id,
                        report_ref    = f"WCA-{policy_number}-{audit_case_id}-REPORT",
                        report_file   = report_file,
                        summary       = _safe(state.get("ai_narrative")),
                        is_final      = is_final,
                        generated_at  = now,
                    )
                    db.add(report_obj)
                else:
                    report_obj.report_file  = report_file
                    report_obj.summary      = _safe(state.get("ai_narrative"))
                    report_obj.is_final     = is_final
                    report_obj.generated_at = now

                db.flush()
                logger.info(f"[DBPersist] wc_audit_reports: upserted for case {case_db_id}")

            except SQLAlchemyError as e:
                logger.error(f"[DBPersist] wc_audit_reports failed: {e}")
                errors.append(f"wc_audit_reports: {e}")
                db.rollback()

        # ── Final commit ──────────────────────────────────────────────────
        db.commit()
        logger.info(
            f"[DBPersist] Case {audit_case_id} ({policy_number}) committed. "
            f"policy_db_id={policy_db_id}, case_db_id={case_db_id}, "
            f"errors={len(errors)}"
        )

    except Exception as exc:
        logger.error(f"[DBPersist] Fatal: {exc}", exc_info=True)
        db.rollback()
        errors.append(f"fatal: {exc}")

    finally:
        db.close()

    return {
        "errors": errors,
        "agent_logs": [{
            "agent":        "db_persistence",
            "status":       "error" if errors else "success",
            "policy_db_id": policy_db_id,
            "case_db_id":   case_db_id,
            "errors":       errors,
            "timestamp":    datetime.utcnow().isoformat(),
        }],
    }