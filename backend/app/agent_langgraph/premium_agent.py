

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

from collections import defaultdict
from datetime import datetime

import os
from dotenv import load_dotenv

from collections import defaultdict
from datetime import datetime
import logging
import calendar
from dateutil.relativedelta import relativedelta
logger = logging.getLogger(__name__)

load_dotenv(dotenv_path="D:/sudheer/new-base-platform-agentiai/agentic-ai-platform-v1.3-complete/backend/.env" )

# def calculate_variance(state: WCAuditState) -> dict:
#     """
#     Core deterministic variance calculation node.
#     """

#     excel_records = state.get("excel_records", [])
#     xml_records   = state.get("xml_records",   [])
#     errors        = list(state.get("errors", []))

#     if not xml_records:
#         errors.append("No XML policy records available for variance calculation.")
#         return {
#             "errors":              errors,
#             "class_code_variance": [],
#             "overall_variance":    {},
#             "agent_logs": [{
#                 "agent":     "premium_agent",
#                 "status":    "error",
#                 "reason":    "No XML records",
#                 "timestamp": datetime.utcnow().isoformat(),
#             }],
#         }

#     # ─────────────────────────────────────────────
#     # Submission stats
#     # ─────────────────────────────────────────────

#     audit_meta      = state.get("audit_xl_records", [{}])[0]

#     submitted_count = float(
#         audit_meta.get(
#             "submitted_count",
#             state.get("submitted_count", 0)
#         )
#     )

#     submitted_count2 = float(
#         audit_meta.get(
#             "submitted_count2",
#             state.get("submitted_count2", 0)
#         )
#     )

#     officer_findings    = state.get("officer_findings",    [])
#     class_code_findings = state.get("class_code_findings", [])
#     frequency_findings  = state.get("frequency_findings",  [])

#     class_code_results    = []

#     total_earned_exposure = 0.0
#     total_earned_premium  = 0.0
#     total_est_exposure    = 0.0
#     total_est_ytd_premium = 0.0
#     total_cc_premium      = 0.0

#     # Global monthly aggregation for UI chart
#     global_monthly: dict = defaultdict(
#         lambda: {
#             "earned_premium": 0.0,
#             "est_premium": 0.0,
#         }
#     )

#     # ─────────────────────────────────────────────
#     # Process each class code
#     # ─────────────────────────────────────────────

#     for xml_rec in xml_records:

#         policy_num = str(
#             xml_rec.get("PolicyNumber", "")
#         ).strip()

#         class_code = str(
#             xml_rec.get("classCode", "")
#         ).strip()

#         state_code = str(
#             xml_rec.get("StateCode", "")
#         ).strip()

#         expected_subs = float(
#             xml_rec.get("expected_payroll_submissions", 1) or 1
#         )

#         # ─────────────────────────────────────────
#         # Match payroll rows
#         # ─────────────────────────────────────────

#         matching = [
#             r for r in excel_records
#             if str(r.get("policy_number", "")).strip() == policy_num
#             and str(r.get("class_code", "")).strip() == class_code
#             and str(r.get("state_code", "")).strip() == state_code
#         ]

#         earned_exposure = sum(
#             float(r.get("exposure", 0) or 0)
#             for r in matching
#         )

#         earned_premium = sum(
#             float(r.get("earned_premium", 0) or 0)
#             for r in matching
#         )

#         xml_exposure = float(
#             xml_rec.get("Exposure", 0) or 0
#         )

#         xml_est_cc_prem = float(
#             xml_rec.get("EstCCpremium", 0) or 0
#         )

#         est_exposure = (
#             (xml_exposure / expected_subs) * submitted_count
#         )

#         est_ytd_premium = (
#             (xml_est_cc_prem / expected_subs) * submitted_count
#         )

#         variance = earned_premium - est_ytd_premium

#         variance_pct = (
#             (variance / est_ytd_premium * 100)
#             if est_ytd_premium != 0 else 0.0
#         )

#         # ─────────────────────────────────────────
#         # MONTHLY TREND INCLUDING MISSING MONTHS
#         # ─────────────────────────────────────────

#         monthly_map: dict = defaultdict(lambda: {
#             "earned_premium": 0.0,
#             "exposure":       0.0,
#             "net_rate_sum":   0.0,
#             "row_count":      0,
#             "run_dates":      set(),
#         })

#         effective_date = xml_rec.get("EffectiveDate", "")
#         expiration_date  = xml_rec.get("ExpirationDate",  "")

#         try:
#             eff_dt = datetime.strptime(effective_date, "%m/%d/%Y")

#             # ── System date override (for testing) ───────────────────────────────
#             # NOTE: also accept BACKEND_SYSTEM_DATE (correct spelling) alongside
#             # the old BACKEND_SYSTEMD_DATE so both work during the transition period
#             system_date = os.getenv("BACKEND_SYSTEM_DATE") or os.getenv("BACKEND_SYSTEMD_DATE")
#             if system_date:
#                 today = datetime.strptime(system_date, "%m/%d/%Y")
#             else:
#                 today = datetime.now()

#             # ── Expiration date ──────────────────────────────────────────────────
#             # Parse it once. If it fails or is missing, exp_dt stays None.
#             exp_dt = None
#             if expiration_date:
#                 try:
#                     exp_dt = datetime.strptime(expiration_date, "%m/%d/%Y")
#                 except ValueError:
#                     pass   # malformed date — safe fallback to today below

#             # ── End bound: stop at whichever comes first ─────────────────────────
#             # • Expired policy  → exp_dt < today  → loop stops at expiration month
#             # • Active policy   → exp_dt > today  → loop stops at today (no future buckets)
#             # • Missing exp_dt  → falls back to today (same behaviour as before)
#             end_bound = min(today, exp_dt) if exp_dt else today

#             # Start from the effective month
#             current = datetime(eff_dt.year, eff_dt.month, 1)

#             # Create all months up to (and including) the end_bound month
#             while current <= end_bound:                 # ← was: while current <= today

#                 month_key = current.strftime("%Y-%m")
#                 monthly_map[month_key]                  # pre-create empty bucket

#                 # Next month — same manual rollover as before (no logic change here)
#                 if current.month == 12:
#                     current = datetime(current.year + 1, 1, 1)
#                 else:
#                     current = datetime(current.year, current.month + 1, 1)

#         except Exception:
#             pass

#         # ─────────────────────────────────────────
#         # Fill actual payroll data
#         # ─────────────────────────────────────────

#         for r in matching:

#             check_date = r.get("check_date")

#             if not check_date:
#                 continue

#             try:
#                 dt = datetime.strptime(
#                     check_date,
#                     "%m/%d/%Y"
#                 )

#                 month = dt.strftime("%Y-%m")

#             except Exception:
#                 continue

#             monthly_map[month]["earned_premium"] += float(
#                 r.get("earned_premium", 0) or 0
#             )

#             monthly_map[month]["exposure"] += float(
#                 r.get("exposure", 0) or 0
#             )

#             monthly_map[month]["net_rate_sum"] += float(
#                 r.get("net_rate", 0) or 0
#             )

#             monthly_map[month]["row_count"] += 1

#             monthly_map[month]["run_dates"].add(check_date)

#         # ─────────────────────────────────────────
#         # Monthly estimated premium
#         # ─────────────────────────────────────────

#         monthly_results = []

#         # monthly_est_premium = (
#         #     (xml_est_cc_prem / expected_subs)
#         #     if expected_subs else 0.0
#         # )
#         # active_months = len(monthly_map) or 1
#         # monthly_est_premium = est_ytd_premium / active_months
#         month_weights: dict[str, float] = {}
#         for month_key in monthly_map:
#             year, mon = int(month_key[:4]), int(month_key[5:7])
#             days_in_month = calendar.monthrange(year, mon)[1]

#             month_start = datetime(year, mon, 1)
#             month_end   = datetime(year, mon, days_in_month)

#             # Clamp to [eff_dt, end_bound]
#             active_start = max(month_start, eff_dt)
#             active_end   = min(month_end,   end_bound)

#             active_days = max((active_end - active_start).days + 1, 0)

#             month_weights[month_key] = active_days / days_in_month

#         total_weight = sum(month_weights.values()) or 1.0

#         # ── Monthly loop ─────────────────────────────────────────────────────
#         monthly_results = []


#         for month, data in sorted(monthly_map.items()):

#             earned_premium_month = data["earned_premium"]

#             # est_premium_month = monthly_est_premium
#             est_premium_month = est_ytd_premium * (
#                 month_weights.get(month, 1.0) / total_weight
#             )

#             variance_m = (
#                 earned_premium_month - est_premium_month
#             )

#             variance_pct_m = (
#                 (variance_m / est_premium_month * 100)
#                 if est_premium_month else 0.0
#             )

#             monthly_results.append({
#                 "month": month,

#                 "earned_premium": round(
#                     earned_premium_month,
#                     2
#                 ),

#                 "est_premium": round(
#                     est_premium_month,
#                     2
#                 ),

#                 # Indicates missing payroll month
#                 "missing_payroll": (
#                     earned_premium_month == 0
#                 ),

#                 "exposure": round(
#                     data["exposure"],
#                     2
#                 ),

#                 "distinct_runs": len(
#                     data["run_dates"]
#                 ),

#                 "variance": round(
#                     variance_m,
#                     2
#                 ),

#                 "variance_pct": round(
#                     variance_pct_m,
#                     2
#                 ),
#             })

#             # Feed global chart
#             global_monthly[month]["earned_premium"] += (
#                 earned_premium_month
#             )

#             global_monthly[month]["est_premium"] += (
#                 est_premium_month
#             )

#         # ─────────────────────────────────────────
#         # Root cause analysis
#         # ─────────────────────────────────────────

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

#             "earned_exposure": round(
#                 earned_exposure,
#                 2
#             ),

#             "earned_premium": round(
#                 earned_premium,
#                 2
#             ),

#             "est_exposure": round(
#                 est_exposure,
#                 2
#             ),

#             "est_ytd_premium": round(
#                 est_ytd_premium,
#                 2
#             ),

#             "variance": round(
#                 variance,
#                 2
#             ),

#             "variance_pct": round(
#                 variance_pct,
#                 4
#             ),

#             "monthly_breakdown": monthly_results,

#             "root_cause": root_cause,

#             "is_flagged": is_flagged,

#             "match_count": len(matching),
#         })

#         total_earned_exposure += earned_exposure
#         total_earned_premium  += earned_premium
#         total_est_exposure    += est_exposure
#         total_est_ytd_premium += est_ytd_premium
#         total_cc_premium      += xml_est_cc_prem

#     # ─────────────────────────────────────────────
#     # Global monthly trend
#     # ─────────────────────────────────────────────

#     monthly_trend = [
#         {
#             "month": m,

#             "earned": round(
#                 v["earned_premium"],
#                 2
#             ),

#             "est": round(
#                 v["est_premium"],
#                 2
#             ),

#             "variance": round(
#                 v["earned_premium"] - v["est_premium"],
#                 2
#             ),
#         }
#         for m, v in sorted(global_monthly.items())
#     ]

#     # ─────────────────────────────────────────────
#     # Overall totals
#     # ─────────────────────────────────────────────

#     overall_variance = (
#         total_earned_premium - total_est_ytd_premium
#     )

#     overall_variance_pct = (
#         (overall_variance / total_est_ytd_premium * 100)
#         if total_est_ytd_premium != 0 else 0.0
#     )

#     expected_subs_gl = float(
#         audit_meta.get(
#             "a_expected_payroll_sub",
#             state.get("expected_submissions", 0)
#         ) or 0
#     )

#     missing_payrolls = max(
#         0,
#         int(expected_subs_gl - submitted_count2)
#     )

#     overall_results = {
#         "earned_exposure": round(
#             total_earned_exposure,
#             2
#         ),

#         "earned_premium": round(
#             total_earned_premium,
#             2
#         ),

#         "total_cc_premium": round(
#             total_cc_premium,
#             2
#         ),

#         "est_exposure": round(
#             total_est_exposure,
#             2
#         ),

#         "est_ytd_premium": round(
#             total_est_ytd_premium,
#             2
#         ),

#         "variance": round(
#             overall_variance,
#             2
#         ),

#         "variance_pct": round(
#             overall_variance_pct,
#             2
#         ),

#         "missing_payrolls": missing_payrolls,

#         "monthly_trend": monthly_trend,
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
#         f"({overall_variance_pct:+.2f}%) across "
#         f"{len(class_code_results)} class codes."
#     )

#     return {
#         "class_code_variance": class_code_results,
#         "overall_variance":    overall_results,
#         "agent_logs":          [log_entry],
#     }

FREQUENCY_CYCLE_DAYS = {
    52: 7,    # weekly        → expect run every 7  days
    26: 14,   # bi-weekly     → expect run every 14 days
    24: 15,   # semi-monthly  → expect run every 15 days
    12: 30,   # monthly       → expect run every 30 days
}

def parse_date(value: str | None, fmt: str = "%m/%d/%Y") -> datetime | None:
    """
    Safe date parser — returns None instead of raising on bad input.
    Single source of truth for all date parsing in this module.
    """
    if not value:
        return None
    try:
        return datetime.strptime(value, fmt)
    except (ValueError, TypeError):
        return None
 
def calculate_variance(state: WCAuditState) -> dict:
    """
    Core deterministic variance calculation node.
 
    Monthly est_premium is distributed only across "fair" months:
      Rule 1 — actual payroll arrived in that month  → always fair
      Rule 2 — policy's submission cycle has completed within that month
                 Start month : days_remaining_in_month >= cycle_days
                 End   month : today >= cycle_anchor_day in that month
 
    All months between start and end are unconditionally fair.
 
    Guarantee : Σ monthly_est_premium == est_ytd_premium (overall)
    """
 
    excel_records = state.get("excel_records", [])
    xml_records   = state.get("xml_records",   [])
    errors        = list(state.get("errors", []))
 
    if not xml_records:
        errors.append("No XML policy records available for variance calculation.")
        return {
            "errors":              errors,
            "class_code_variance": [],
            "overall_variance":    {},
            "agent_logs": [{
                "agent":     "premium_agent",
                "status":    "error",
                "reason":    "No XML records",
                "timestamp": datetime.utcnow().isoformat(),
            }],
        }
 
    # ─────────────────────────────────────────────
    # Submission stats
    # ─────────────────────────────────────────────
 
    audit_meta = state.get("audit_xl_records", [{}])[0]
 
    submitted_count = float(
        audit_meta.get(
            "submitted_count",
            state.get("submitted_count", 0)
        )
    )
 
    submitted_count2 = float(
        audit_meta.get(
            "submitted_count2",
            state.get("submitted_count2", 0)
        )
    )
 
    officer_findings    = state.get("officer_findings",    [])
    class_code_findings = state.get("class_code_findings", [])
    frequency_findings  = state.get("frequency_findings",  [])
 
    class_code_results    = []
 
    total_earned_exposure = 0.0
    total_earned_premium  = 0.0
    total_est_exposure    = 0.0
    total_est_ytd_premium = 0.0
    total_cc_premium      = 0.0
 
    # Global monthly aggregation for UI chart
    global_monthly: dict = defaultdict(
        lambda: {
            "earned_premium": 0.0,
            "est_premium":    0.0,
        }
    )
 
    # ─────────────────────────────────────────────
    # System date (supports test overrides)
    # ─────────────────────────────────────────────
 
    system_date_str = (
        os.getenv("BACKEND_SYSTEM_DATE")
        or os.getenv("BACKEND_SYSTEMD_DATE")
    )
    today = parse_date(system_date_str) if system_date_str else datetime.now()
 
    # ─────────────────────────────────────────────
    # Process each class code
    # ─────────────────────────────────────────────
 
    for xml_rec in xml_records:
 
        policy_num = str(xml_rec.get("PolicyNumber", "")).strip()
        class_code = str(xml_rec.get("classCode",    "")).strip()
        state_code = str(xml_rec.get("StateCode",    "")).strip()
 
        expected_subs = float(
            xml_rec.get("expected_payroll_submissions", 1) or 1
        )
 
        # Submission cycle in days for this policy's frequency
        cycle_days = FREQUENCY_CYCLE_DAYS.get(int(expected_subs), 30)
 
        # ─────────────────────────────────────────
        # Match payroll rows
        # ─────────────────────────────────────────
 
        matching = [
            r for r in excel_records
            if str(r.get("policy_number", "")).strip() == policy_num
            and str(r.get("class_code",   "")).strip() == class_code
            and str(r.get("state_code",   "")).strip() == state_code
        ]
 
        earned_exposure = sum(
            float(r.get("exposure",       0) or 0) for r in matching
        )
 
        earned_premium = sum(
            float(r.get("earned_premium", 0) or 0) for r in matching
        )
 
        xml_exposure    = float(xml_rec.get("Exposure",     0) or 0)
        xml_est_cc_prem = float(xml_rec.get("EstCCpremium", 0) or 0)
 
        est_exposure    = (xml_exposure    / expected_subs) * submitted_count
        est_ytd_premium = (xml_est_cc_prem / expected_subs) * submitted_count
 
        variance     = earned_premium - est_ytd_premium
        variance_pct = (
            (variance / est_ytd_premium * 100)
            if est_ytd_premium != 0 else 0.0
        )
 
        # ─────────────────────────────────────────
        # Pre-compute payroll months set — O(1) lookup later
        # ─────────────────────────────────────────
 
        payroll_months: set[str] = {
            dt.strftime("%Y-%m")
            for r in matching
            if (dt := parse_date(r.get("check_date")))
        }
 
        # ─────────────────────────────────────────
        # Build monthly buckets
        # ─────────────────────────────────────────
 
        monthly_map: dict = defaultdict(lambda: {
            "earned_premium": 0.0,
            "exposure":       0.0,
            "net_rate_sum":   0.0,
            "row_count":      0,
            "run_dates":      set(),
        })
 
        eff_dt    = None
        end_bound = None
 
        try:
            eff_dt = parse_date(xml_rec.get("EffectiveDate",  ""))
            exp_dt = parse_date(xml_rec.get("ExpirationDate", ""))
 
            if not eff_dt:
                raise ValueError("Missing or invalid EffectiveDate")
 
            end_bound = min(today, exp_dt) if exp_dt else today
 
            # ── Pre-create one bucket per calendar month ─────────────────
            # relativedelta(months=1) handles Dec→Jan rollover natively
            current = eff_dt.replace(day=1)
 
            while current <= end_bound:
                monthly_map[current.strftime("%Y-%m")]  # pre-create bucket
                current += relativedelta(months=1)
 
        except Exception:
            pass
 
        # ─────────────────────────────────────────
        # Fill actual payroll data
        # ─────────────────────────────────────────
 
        for r in matching:
 
            dt = parse_date(r.get("check_date"))
            if not dt:
                continue
 
            month = dt.strftime("%Y-%m")
 
            monthly_map[month]["earned_premium"] += float(
                r.get("earned_premium", 0) or 0
            )
            monthly_map[month]["exposure"]       += float(
                r.get("exposure",       0) or 0
            )
            monthly_map[month]["net_rate_sum"]   += float(
                r.get("net_rate",       0) or 0
            )
            monthly_map[month]["row_count"]      += 1
            monthly_map[month]["run_dates"].add(r["check_date"])
 
        # ─────────────────────────────────────────
        # Fair month logic — start and end months only
        #
        # Rule 1 : payroll arrived in that month   → always fair
        # Rule 2 : submission cycle completed
        #   Start month : days remaining in month >= cycle_days
        #   End   month : today >= cycle anchor day in that month
        #                 (anchor = effective date's day-of-month,
        #                  clamped to valid days of the end month)
        # ─────────────────────────────────────────
 
        if eff_dt and end_bound:
 
            # ── Start month ──────────────────────────────────────────────
            start_month_key    = eff_dt.strftime("%Y-%m")
 
            # relativedelta(day=31) snaps to last valid day of any month
            end_of_start_month  = eff_dt + relativedelta(day=31)
            days_remaining_in_start = (end_of_start_month - eff_dt).days + 1
 
            start_month_is_fair = (
                start_month_key in payroll_months        # Rule 1
                or days_remaining_in_start >= cycle_days # Rule 2
            )
 
            if not start_month_is_fair and start_month_key in monthly_map:
                del monthly_map[start_month_key]
 
            # ── End month ────────────────────────────────────────────────
            end_month_key = end_bound.strftime("%Y-%m")

            if end_month_key != start_month_key:

                # Monthly frequency → cycle is anchored to effective date's day
                # e.g. eff_dt=Jan 15, monthly → cycle due on 15th of every month
                if int(expected_subs) == 12:
                    anchor_in_end_month = (
                        end_bound.replace(day=1)
                        + relativedelta(day=eff_dt.day)  # clamps to valid day
                    )
                    cycle_completed_in_end_month = end_bound >= anchor_in_end_month

                # Weekly / bi-weekly / semi-monthly → just need enough days elapsed
                # e.g. bi-weekly (14d): May 20 has 20 days → 20 >= 14 → fair
                else:
                    days_active_in_end       = end_bound.day
                    cycle_completed_in_end_month = days_active_in_end >= cycle_days

                end_month_is_fair = (
                    end_month_key in payroll_months      # Rule 1
                    or cycle_completed_in_end_month      # Rule 2
                )

                if not end_month_is_fair and end_month_key in monthly_map:
                    del monthly_map[end_month_key]
 
        # ─────────────────────────────────────────
        # Monthly estimated premium
        #
        # Evenly distribute est_ytd_premium across fair months only.
        # Guarantee: Σ monthly_est_premium == est_ytd_premium
        # ─────────────────────────────────────────
 
        active_months       = len(monthly_map) or 1
        monthly_est_premium = est_ytd_premium / active_months
 
        # ─────────────────────────────────────────
        # Build monthly results
        # Assign remainder to last month to eliminate
        # floating-point rounding drift across rows.
        # ─────────────────────────────────────────
 
        monthly_results  = []
        running_est_total = 0.0
        sorted_months     = sorted(monthly_map.items())
 
        for i, (month, data) in enumerate(sorted_months):
 
            is_last = (i == len(sorted_months) - 1)
 
            earned_premium_month = data["earned_premium"]
 
            # Last month absorbs any cent-level rounding remainder
            if is_last:
                est_premium_month = round(
                    est_ytd_premium - running_est_total, 2
                )
            else:
                est_premium_month  = round(monthly_est_premium, 2)
                running_est_total += est_premium_month
 
            variance_m = earned_premium_month - est_premium_month
 
            variance_pct_m = (
                (variance_m / est_premium_month * 100)
                if est_premium_month else 0.0
            )
 
            monthly_results.append({
                "month": month,
 
                "earned_premium": round(earned_premium_month, 2),
                "est_premium":    round(est_premium_month,    2),
 
                # True missing payroll: fair month with zero runs submitted
                "missing_payroll": len(data["run_dates"]) == 0,
 
                "exposure":      round(data["exposure"], 2),
                "distinct_runs": len(data["run_dates"]),
 
                "variance":     round(variance_m,     2),
                "variance_pct": round(variance_pct_m, 2),
            })
 
            # Feed global chart with raw floats (rounded at output stage)
            global_monthly[month]["earned_premium"] += earned_premium_month
            global_monthly[month]["est_premium"]    += est_premium_month
 
        # ─────────────────────────────────────────
        # Root cause analysis
        # ─────────────────────────────────────────
 
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
            "PolicyNumber": policy_num,
            "StateCode":    state_code,
            "ClassCode":    class_code,
 
            "earned_exposure": round(earned_exposure,   2),
            "earned_premium":  round(earned_premium,    2),
            "est_exposure":    round(est_exposure,      2),
            "est_ytd_premium": round(est_ytd_premium,   2),
 
            "variance":     round(variance,     2),
            "variance_pct": round(variance_pct, 4),
 
            "monthly_breakdown": monthly_results,
 
            "root_cause":  root_cause,
            "is_flagged":  is_flagged,
            "match_count": len(matching),
        })
 
        total_earned_exposure += earned_exposure
        total_earned_premium  += earned_premium
        total_est_exposure    += est_exposure
        total_est_ytd_premium += est_ytd_premium
        total_cc_premium      += xml_est_cc_prem
 
    # ─────────────────────────────────────────────
    # Global monthly trend
    # Variance computed from raw floats — single round at output,
    # so monthly_trend variances always sum to overall_variance exactly.
    # ─────────────────────────────────────────────
 
    monthly_trend = [
        {
            "month":    m,
            "earned":   round(v["earned_premium"], 2),
            "est":      round(v["est_premium"],    2),
            "variance": round(
                v["earned_premium"] - v["est_premium"], 2
            ),
        }
        for m, v in sorted(global_monthly.items())
    ]
 
    # ─────────────────────────────────────────────
    # Overall totals
    # ─────────────────────────────────────────────
 
    overall_variance = total_earned_premium - total_est_ytd_premium
 
    overall_variance_pct = (
        (overall_variance / total_est_ytd_premium * 100)
        if total_est_ytd_premium != 0 else 0.0
    )
 
    expected_subs_gl = float(
        audit_meta.get(
            "a_expected_payroll_sub",
            state.get("expected_submissions", 0)
        ) or 0
    )
 
    missing_payrolls = max(
        0,
        int(expected_subs_gl - submitted_count2)
    )
 
    overall_results = {
        "earned_exposure":  round(total_earned_exposure, 2),
        "earned_premium":   round(total_earned_premium,  2),
        "total_cc_premium": round(total_cc_premium,      2),
        "est_exposure":     round(total_est_exposure,    2),
        "est_ytd_premium":  round(total_est_ytd_premium, 2),
 
        "variance":     round(overall_variance,     2),
        "variance_pct": round(overall_variance_pct, 2),
 
        "missing_payrolls": missing_payrolls,
        "monthly_trend":    monthly_trend,
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
        f"({overall_variance_pct:+.2f}%) across "
        f"{len(class_code_results)} class codes."
    )
 
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
    if abs(variance_pct) > 30 :
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