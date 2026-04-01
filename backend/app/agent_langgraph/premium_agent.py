# """
# Premium Agent (Deterministic)
# Performs ALL arithmetic calculations:
#   • Earned Exposure / Earned Premium  (from payroll Excel)
#   • EST Exposure / EST YTD Premium    (from policy XML × completion ratio)
#   • Variance and Variance Percentage  per class code / state
#   • Overall totals

# No LLM is used in this node – keeping the system regulator-safe.

# FIX: calculate_variance and assess_risk now return PARTIAL dicts
#      (only the keys they change) instead of the full state object.
#      Returning the full state from nodes that participate in fan-in
#      convergence causes INVALID_CONCURRENT_GRAPH_UPDATE in LangGraph.
# """
# import logging
# from datetime import datetime

# from app.agent_langgraph.wc_state import WCAuditState

# logger = logging.getLogger(__name__)


# def calculate_variance(state: WCAuditState) -> dict:
#     """
#     Core deterministic variance calculation node.

#     Formula reference (from Formulas_rules.txt):
#     ─────────────────────────────────────────────
#     Earned Exposure  = SUM(Exposure) filtered by policy, class code, state
#     Earned Premium   = SUM(Earned_premium) filtered by policy, class code, state

#     EST Exposure     = (XML Exposure / expected_submissions) × submitted_count
#     EST YTD Premium  = (XML EstCCpremium / expected_submissions) × submitted_count

#     Variance         = Earned Premium − EST YTD Premium
#     Variance %       = (Variance / EST YTD Premium) × 100

#     Returns only: class_code_variance, overall_variance, errors, agent_logs
#     """
#     excel_records = state.get("excel_records", [])
#     xml_records   = state.get("xml_records",   [])
#     errors        = list(state.get("errors", []))

#     if not xml_records:
#         errors.append("No XML policy records available for variance calculation.")
#         return {
#             "errors":             errors,
#             "class_code_variance": [],
#             "overall_variance":   {},
#             "agent_logs": [{
#                 "agent":     "premium_agent",
#                 "status":    "error",
#                 "reason":    "No XML records",
#                 "timestamp": datetime.utcnow().isoformat(),
#             }],
#         }

#     # Retrieve submission stats
#     audit_meta      = state.get("audit_xl_records", [{}])[0]
#     submitted_count = float(audit_meta.get("submitted_count", state.get("submitted_count", 0)))

#     # Snapshot specialist findings for root-cause lookup (read-only)
#     officer_findings   = state.get("officer_findings",   [])
#     class_code_findings = state.get("class_code_findings", [])
#     frequency_findings  = state.get("frequency_findings",  [])

#     class_code_results     = []
#     total_earned_exposure  = 0.0
#     total_earned_premium   = 0.0
#     total_est_exposure     = 0.0
#     total_est_ytd_premium  = 0.0

#     for xml_rec in xml_records:
#         policy_num    = str(xml_rec.get("PolicyNumber", "")).strip()
#         class_code    = str(xml_rec.get("classCode", "")).strip()
#         state_code    = str(xml_rec.get("StateCode", "")).strip()
#         expected_subs = float(xml_rec.get("expected_payroll_submissions", 1) or 1)

#         # Aggregate payroll records matching (policy, class, state)
#         matching = [
#             r for r in excel_records
#             if str(r.get("policy_number", "")).strip() == policy_num
#             and str(r.get("class_code",   "")).strip() == class_code
#             and str(r.get("state_code",   "")).strip() == state_code
#         ]

#         earned_exposure = sum(float(r.get("exposure",        0) or 0) for r in matching)
#         earned_premium  = sum(float(r.get("earned_premium",  0) or 0) for r in matching)

#         xml_exposure    = float(xml_rec.get("Exposure",    0) or 0)
#         xml_est_cc_prem = float(xml_rec.get("EstCCpremium", 0) or 0)

#         est_exposure    = (xml_exposure    / expected_subs) * submitted_count
#         est_ytd_premium = (xml_est_cc_prem / expected_subs) * submitted_count

#         variance     = earned_premium - est_ytd_premium
#         variance_pct = (variance / est_ytd_premium * 100) if est_ytd_premium != 0 else 0.0

#         root_cause = _determine_root_cause(
#             variance_pct,
#             officer_findings,
#             class_code_findings,
#             frequency_findings,
#             class_code,
#             state_code,
#         )

#         is_flagged = abs(variance_pct) > 10

#         class_code_results.append({
#             "PolicyNumber":    policy_num,
#             "StateCode":       state_code,
#             "ClassCode":       class_code,
#             "earned_exposure": round(earned_exposure,  2),
#             "earned_premium":  round(earned_premium,   2),
#             "est_exposure":    round(est_exposure,     2),
#             "est_ytd_premium": round(est_ytd_premium,  2),
#             "variance":        round(variance,         2),
#             "variance_pct":    round(variance_pct,     4),
#             "root_cause":      root_cause,
#             "is_flagged":      is_flagged,
#             "match_count":     len(matching),
#         })

#         total_earned_exposure += earned_exposure
#         total_earned_premium  += earned_premium
#         total_est_exposure    += est_exposure
#         total_est_ytd_premium += est_ytd_premium

#     overall_variance     = total_earned_premium - total_est_ytd_premium
#     overall_variance_pct = (
#         (overall_variance / total_est_ytd_premium * 100)
#         if total_est_ytd_premium != 0 else 0.0
#     )

#     overall_results = {
#         "earned_exposure":  round(total_earned_exposure,  2),
#         "earned_premium":   round(total_earned_premium,   2),
#         "est_exposure":     round(total_est_exposure,     2),
#         "est_ytd_premium":  round(total_est_ytd_premium,  2),
#         "variance":         round(overall_variance,       2),
#         "variance_pct":     round(overall_variance_pct,   4),
#     }

#     log_entry = {
#         "agent":       "premium_agent",
#         "status":      "success",
#         "class_codes": len(class_code_results),
#         "overall":     overall_results,
#         "timestamp":   datetime.utcnow().isoformat(),
#     }

#     logger.info(
#         f"[PremiumAgent] Variance: {overall_variance:+.2f} "
#         f"({overall_variance_pct:+.2f}%) across {len(class_code_results)} class codes."
#     )

#     # ── Only return keys this node owns ───────────────────────────────
#     return {
#         "class_code_variance": class_code_results,
#         "overall_variance":    overall_results,
#         "agent_logs":          [log_entry],
#     }


# def _determine_root_cause(
#     variance_pct: float,
#     officer_findings: list,
#     class_code_findings: list,
#     frequency_findings: list,
#     class_code: str,
#     state_code: str,
# ) -> str:
#     """Rule-based root cause assignment."""
#     if not officer_findings and not class_code_findings and not frequency_findings:
#         return "payroll_variance" if abs(variance_pct) > 5 else "none"

#     for f in officer_findings:
#         if f.get("class_code") == class_code or f.get("state_code") == state_code:
#             return "officer_mismatch"

#     for f in class_code_findings:
#         if f.get("class_code") == class_code:
#             return "class_code_mismatch"

#     for f in frequency_findings:
#         if f.get("state_code") == state_code:
#             return "frequency_gap"

#     return "payroll_variance" if abs(variance_pct) > 5 else "none"


# def assess_risk(state: WCAuditState) -> dict:
#     """
#     Assign risk level and recommendation based on overall variance.
#     Deterministic rule engine — no AI.

#     Returns only: risk_level, recommendation, hitl_required, agent_logs
#     """
#     overall      = state.get("overall_variance", {})
#     variance_pct = float(overall.get("variance_pct", 0))
#     variance_amt = float(overall.get("variance",     0))

#     officer_issues = len(state.get("officer_findings",   []))
#     freq_issues    = len(state.get("frequency_findings", []))

#     # Risk level
#     if abs(variance_pct) > 20 or officer_issues > 0 or freq_issues > 2:
#         risk_level = "high"
#     elif abs(variance_pct) > 10 or freq_issues > 0:
#         risk_level = "medium"
#     else:
#         risk_level = "low"

#     # Recommendation
#     if variance_amt < -100:
#         recommendation = "refund"
#     elif variance_amt > 100:
#         recommendation = "additional_premium"
#     elif officer_issues > 0 or freq_issues > 0:
#         recommendation = "clarification"
#     else:
#         recommendation = "no_action"

#     # HITL required for high risk or significant amounts
#     hitl_required = (
#         risk_level == "high"
#         or abs(variance_amt) > 500
#         or officer_issues > 0
#     )

#     log_entry = {
#         "agent":          "risk_assessor",
#         "risk_level":     risk_level,
#         "recommendation": recommendation,
#         "hitl_required":  hitl_required,
#         "timestamp":      datetime.utcnow().isoformat(),
#     }

#     logger.info(
#         f"[RiskAssessor] Risk={risk_level}, Rec={recommendation}, "
#         f"HITL={hitl_required}"
#     )

#     # ── Only return keys this node owns ───────────────────────────────
#     return {
#         "risk_level":     risk_level,
#         "recommendation": recommendation,
#         "hitl_required":  hitl_required,
#         "agent_logs":     [log_entry],
#     }


"""
Premium Agent (Deterministic)
Performs ALL arithmetic calculations:
  • Earned Exposure / Earned Premium  (from payroll Excel)
  • EST Exposure / EST YTD Premium    (from policy XML × completion ratio)
  • Variance and Variance Percentage  per class code / state
  • Overall totals

No LLM is used in this node – keeping the system regulator-safe.

FIX: calculate_variance and assess_risk now return PARTIAL dicts
     (only the keys they change) instead of the full state object.
     Returning the full state from nodes that participate in fan-in
     convergence causes INVALID_CONCURRENT_GRAPH_UPDATE in LangGraph.
"""
import logging
from datetime import datetime

from app.agent_langgraph.wc_state import WCAuditState

logger = logging.getLogger(__name__)


def calculate_variance(state: WCAuditState) -> dict:
    """
    Core deterministic variance calculation node.

    Formula reference (from Formulas_rules.txt):
    ─────────────────────────────────────────────
    Earned Exposure  = SUM(Exposure) filtered by policy, class code, state
    Earned Premium   = SUM(Earned_premium) filtered by policy, class code, state

    EST Exposure     = (XML Exposure / expected_submissions) × submitted_count
    EST YTD Premium  = (XML EstCCpremium / expected_submissions) × submitted_count

    Variance         = Earned Premium − EST YTD Premium
    Variance %       = (Variance / EST YTD Premium) × 100

    Returns only: class_code_variance, overall_variance, errors, agent_logs
    """
    excel_records = state.get("excel_records", [])
    xml_records   = state.get("xml_records",   [])
    errors        = list(state.get("errors", []))

    if not xml_records:
        errors.append("No XML policy records available for variance calculation.")
        return {
            "errors":             errors,
            "class_code_variance": [],
            "overall_variance":   {},
            "agent_logs": [{
                "agent":     "premium_agent",
                "status":    "error",
                "reason":    "No XML records",
                "timestamp": datetime.utcnow().isoformat(),
            }],
        }

    # Retrieve submission stats
    audit_meta      = state.get("audit_xl_records", [{}])[0]
    submitted_count = float(audit_meta.get("submitted_count", state.get("submitted_count", 0)))

    # Snapshot specialist findings for root-cause lookup (read-only)
    officer_findings   = state.get("officer_findings",   [])
    class_code_findings = state.get("class_code_findings", [])
    frequency_findings  = state.get("frequency_findings",  [])

    class_code_results     = []
    total_earned_exposure  = 0.0
    total_earned_premium   = 0.0
    total_est_exposure     = 0.0
    total_est_ytd_premium  = 0.0

    for xml_rec in xml_records:
        policy_num    = str(xml_rec.get("PolicyNumber", "")).strip()
        class_code    = str(xml_rec.get("classCode", "")).strip()
        state_code    = str(xml_rec.get("StateCode", "")).strip()
        expected_subs = float(xml_rec.get("expected_payroll_submissions", 1) or 1)

        # Aggregate payroll records matching (policy, class, state)
        matching = [
            r for r in excel_records
            if str(r.get("policy_number", "")).strip() == policy_num
            and str(r.get("class_code",   "")).strip() == class_code
            and str(r.get("state_code",   "")).strip() == state_code
        ]

        earned_exposure = sum(float(r.get("exposure",        0) or 0) for r in matching)
        earned_premium  = sum(float(r.get("earned_premium",  0) or 0) for r in matching)

        xml_exposure    = float(xml_rec.get("Exposure",    0) or 0)
        xml_est_cc_prem = float(xml_rec.get("EstCCpremium", 0) or 0)

        est_exposure    = (xml_exposure    / expected_subs) * submitted_count
        est_ytd_premium = (xml_est_cc_prem / expected_subs) * submitted_count

        variance     = earned_premium - est_ytd_premium
        variance_pct = (variance / est_ytd_premium * 100) if est_ytd_premium != 0 else 0.0

        root_cause = _determine_root_cause(
            variance_pct,
            officer_findings,
            class_code_findings,
            frequency_findings,
            class_code,
            state_code,
        )

        is_flagged = abs(variance_pct) > 10

        class_code_results.append({
            "PolicyNumber":    policy_num,
            "StateCode":       state_code,
            "ClassCode":       class_code,
            "earned_exposure": round(earned_exposure,  2),
            "earned_premium":  round(earned_premium,   2),
            "est_exposure":    round(est_exposure,     2),
            "est_ytd_premium": round(est_ytd_premium,  2),
            "variance":        round(variance,         2),
            "variance_pct":    round(variance_pct,     4),
            "root_cause":      root_cause,
            "is_flagged":      is_flagged,
            "match_count":     len(matching),
        })

        total_earned_exposure += earned_exposure
        total_earned_premium  += earned_premium
        total_est_exposure    += est_exposure
        total_est_ytd_premium += est_ytd_premium

    overall_variance     = total_earned_premium - total_est_ytd_premium
    overall_variance_pct = (
        (overall_variance / total_est_ytd_premium * 100)
        if total_est_ytd_premium != 0 else 0.0
    )

    overall_results = {
        "earned_exposure":  round(total_earned_exposure,  2),
        "earned_premium":   round(total_earned_premium,   2),
        "est_exposure":     round(total_est_exposure,     2),
        "est_ytd_premium":  round(total_est_ytd_premium,  2),
        "variance":         round(overall_variance,       2),
        "variance_pct":     round(overall_variance_pct,   4),
    }

    log_entry = {
        "agent":       "premium_agent",
        "status":      "success",
        "class_codes": len(class_code_results),
        "overall":     overall_results,
        "timestamp":   datetime.utcnow().isoformat(),
    }

    logger.info(
        f"[PremiumAgent] Variance: {overall_variance:+.2f} "
        f"({overall_variance_pct:+.2f}%) across {len(class_code_results)} class codes."
    )

    # ── Only return keys this node owns ───────────────────────────────
    return {
        "class_code_variance": class_code_results,
        "overall_variance":    overall_results,
        "agent_logs":          [log_entry],
    }


def _determine_root_cause(
    variance_pct: float,
    officer_findings: list,
    class_code_findings: list,
    frequency_findings: list,
    class_code: str,
    state_code: str,
) -> str:
    """Rule-based root cause assignment."""
    if not officer_findings and not class_code_findings and not frequency_findings:
        return "payroll_variance" if abs(variance_pct) > 5 else "none"

    for f in officer_findings:
        if f.get("class_code") == class_code or f.get("state_code") == state_code:
            return "officer_mismatch"

    for f in class_code_findings:
        if f.get("class_code") == class_code:
            return "class_code_mismatch"

    for f in frequency_findings:
        if f.get("state_code") == state_code:
            return "frequency_gap"

    return "payroll_variance" if abs(variance_pct) > 5 else "none"


def assess_risk(state: WCAuditState) -> dict:
    """
    Assign risk level and recommendation based on overall variance.
    Deterministic rule engine — no AI.

    Respects the tenant-level ``hitl_globally_enabled`` flag injected
    into the state by the worker before graph execution:
      • True  (default) — HITL checkpoint fires for high-risk audits
      • False           — hitl_required is forced to False for every audit;
                          the graph routes directly to explanation_agent

    Returns only: risk_level, recommendation, hitl_required, agent_logs
    """
    overall      = state.get("overall_variance", {})
    variance_pct = float(overall.get("variance_pct", 0))
    variance_amt = float(overall.get("variance",     0))

    officer_issues = len(state.get("officer_findings",   []))
    freq_issues    = len(state.get("frequency_findings", []))

    # ── Risk level (always calculated; used for reporting even when HITL off) ──
    if abs(variance_pct) > 20 or officer_issues > 0 or freq_issues > 2:
        risk_level = "high"
    elif abs(variance_pct) > 10 or freq_issues > 0:
        risk_level = "medium"
    else:
        risk_level = "low"

    # ── Recommendation ────────────────────────────────────────────────────────
    if variance_amt < -100:
        recommendation = "refund"
    elif variance_amt > 100:
        recommendation = "additional_premium"
    elif officer_issues > 0 or freq_issues > 0:
        recommendation = "clarification"
    else:
        recommendation = "no_action"

    # ── HITL gate ─────────────────────────────────────────────────────────────
    # Read the global HITL switch injected by the worker.
    # Defaults to True so existing audits are unaffected if the key is absent.
    hitl_globally_enabled = state.get("hitl_globally_enabled", True)

    if not hitl_globally_enabled:
        # Administrator has disabled HITL globally — bypass regardless of risk
        hitl_required = False
        hitl_bypass_reason = "HITL globally disabled by administrator"
        logger.info(
            f"[RiskAssessor] HITL globally disabled — forcing hitl_required=False "
            f"(risk_level={risk_level})"
        )
    else:
        # Normal rule-based HITL trigger
        hitl_required = (
            risk_level == "high"
            or abs(variance_amt) > 500
            or officer_issues > 0
        )
        hitl_bypass_reason = None

    log_entry = {
        "agent":               "risk_assessor",
        "risk_level":          risk_level,
        "recommendation":      recommendation,
        "hitl_required":       hitl_required,
        "hitl_globally_enabled": hitl_globally_enabled,
        **({"hitl_bypass_reason": hitl_bypass_reason} if hitl_bypass_reason else {}),
        "timestamp":           datetime.utcnow().isoformat(),
    }

    logger.info(
        f"[RiskAssessor] Risk={risk_level}, Rec={recommendation}, "
        f"HITL={hitl_required} (global_enabled={hitl_globally_enabled})"
    )

    # ── Only return keys this node owns ───────────────────────────────────────
    return {
        "risk_level":     risk_level,
        "recommendation": recommendation,
        "hitl_required":  hitl_required,
        "agent_logs":     [log_entry],
    }