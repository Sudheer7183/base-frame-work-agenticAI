

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
    AgentFinding, HITLReview, AuditReport,MonthlyVariance
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
                    # annual_estimated_premium = safe(overall.get("estimated_premium"),0),
                    total_cc_premium=_safe(overall.get("total_cc_premium",0)),
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
        # 6. Monthly Variance   — delete-and-replace
        # ══════════════════════════════════════════════════════════════════
        if case_db_id:
            try:
                # Delete existing
                db.query(MonthlyVariance).filter(
                    MonthlyVariance.audit_case_id == case_db_id
                ).delete(synchronize_session=False)

                monthly_trend = overall.get("monthly_trend", [])

                for m in monthly_trend:
                    db.add(MonthlyVariance(
                        audit_case_id  = case_db_id,
                        policy_number  = policy_number,
                        month          = m.get("month"),
                        earned_premium = m.get("earned"),
                        est_premium    = m.get("est"),
                        variance       = m.get("variance"),
                        variance_pct   = (
                            (m.get("variance") / m.get("est") * 100)
                            if m.get("est") else 0
                        ),
                        created_at     = now
                    ))

                db.flush()
                logger.info(f"[DBPersist] wc_monthly_variance: {len(monthly_trend)} rows")

            except SQLAlchemyError as e:
                logger.error(f"[DBPersist] wc_monthly_variance failed: {e}")
                errors.append(f"wc_monthly_variance: {e}")
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