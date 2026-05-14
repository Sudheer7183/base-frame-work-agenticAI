
"""
api_ingestion_node.py — CACHE-AWARE (replaces existing file)
=============================================================
Only change from the previous version:
  • _get_cached_config() helper — reads policy-config from Redis before HTTP
  • api_ingestion_node() — calls cache first, falls back to HTTP on miss

All normalizers and error helpers are unchanged.
"""
import json
import os
import logging
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

MOCK_API_BASE           = os.getenv("MOCK_API_BASE_URL", "http://localhost:9000/api/v1")
POLICY_CONFIG_CACHE_TTL = int(os.getenv("POLICY_CONFIG_CACHE_TTL_SECS", 86400))


# ─────────────────────────────────────────────────────────────────────────────
# Redis cache helper  (sync — node runs in thread pool)
# ─────────────────────────────────────────────────────────────────────────────

def _get_cached_config(policy_number: str) -> dict | None:
    """
    Read a pre-fetched policy config from Redis (set by /preview-api-policies).
    Uses the synchronous redis client because api_ingestion_node runs in
    asyncio.to_thread() — not on the async event loop.
    Returns the parsed dict on hit, None on miss or any error.
    """
    try:
        import redis as _sync_redis
        r   = _sync_redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
        )
        raw = r.get(f"policy_config:{policy_number}")
        if raw:
            logger.debug(f"[APIIngestion] Cache HIT  — config for {policy_number}")
            return json.loads(raw)
        logger.debug(f"[APIIngestion] Cache MISS — config for {policy_number}")
        return None
    except Exception as exc:
        logger.debug(f"[APIIngestion] Redis unavailable ({exc}) — will fetch from API")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Main ingestion node
# ─────────────────────────────────────────────────────────────────────────────

def api_ingestion_node(state: dict) -> dict:
    """
    Replaces parse_payroll_excel + parse_policy_xml + parse_audit_metadata
    when data_source == "api".

    Optimised flow:
      1. Fetch payroll from Mock API  (always fresh — changes every audit period)
      2. Try Redis cache for policy config  (pre-loaded by /preview-api-policies)
      3. Cache miss → fetch config from Mock API  (fallback for single-policy runs)
    """
    policy_number = state.get("policy_number", "").strip()
    if not policy_number:
        return _err("policy_number missing from state")

    try:
        # ── 1. Payroll (always from API) ─────────────────────────────────────
        r1 = requests.get(
            f"{MOCK_API_BASE}/policies/{policy_number}/payroll",
            timeout=20,
        )
        if r1.status_code == 404:
            return _err(
                f"Policy {policy_number} not found in Mock API (404). "
                "Ensure the mock server has payroll data for this policy."
            )
        r1.raise_for_status()
        raw_payroll   = r1.json().get("records", [])
        excel_records = [_normalize_payroll_row(row) for row in raw_payroll]

        # ── 2. Policy config — cache-first ───────────────────────────────────
        config       = _get_cached_config(policy_number)
        config_source = "redis_cache"

        if config is None:
            # Cache miss — fetch from API (single-policy /start-from-api path)
            logger.info(f"[APIIngestion] Fetching config from API for {policy_number}")
            r2 = requests.get(
                f"{MOCK_API_BASE}/policies/{policy_number}/policy-config",
                timeout=20,
            )
            if r2.status_code == 404:
                return _err(f"Policy config for {policy_number} not found in Mock API (404).")
            r2.raise_for_status()
            config       = r2.json()
            config_source = "api"

        raw_xml      = config.get("xml_records", [])
        raw_meta     = config.get("audit_meta", {})
        raw_officers = config.get("officers", [])

        xml_records      = [_normalize_xml_record(row) for row in raw_xml]
        audit_xl_records = [_normalize_audit_meta(raw_meta)]
        officers         = [_normalize_officer(o) for o in (raw_officers or [])]

        first_xml     = xml_records[0] if xml_records else {}
        policy_config = {
            "policy_number":        first_xml.get("PolicyNumber", policy_number),
            "effective_date":       first_xml.get("EffectiveDate", ""),
            "expiration_date":      first_xml.get("ExpirationDate", ""),
            "insured_name":         first_xml.get("InsuredName", ""),
            "est_premium":          first_xml.get("premium", 0.0),
            "payroll_frequency":    raw_meta.get("a_payroll_frequency", "1W"),
            "expected_submissions": raw_meta.get("a_expected_payroll_sub",
                                        first_xml.get("expected_payroll_submissions", 0)),
            "state_code":           first_xml.get("StateCode", ""),
            "officers":             officers,
        }

        logger.info(
            f"[APIIngestion] {policy_number}: {len(excel_records)} payroll rows, "
            f"{len(xml_records)} class codes, {len(officers)} officers | "
            f"config_source={config_source}"
        )

        return {
            "excel_records":        excel_records,
            "xml_records":          xml_records,
            "policy_config":        policy_config,
            "payroll_frequency":    policy_config["payroll_frequency"],
            "expected_submissions": policy_config["expected_submissions"],
            "audit_xl_records":     audit_xl_records,
            "submitted_count":raw_meta.get("a_actual_payroll_sub", 0),
            # "submitted_count2":      raw_meta.get("a_actual_payroll_sub2", 0),
            "first_check_date":     raw_meta.get("a_first_check_date", ""),
            "last_check_date":      raw_meta.get("a_last_check_date", ""),
            "actual_submissions":   float(raw_meta.get("a_actual_payroll_sub2", 0)),
            "agent_logs": [{
                "agent":         "ingestion_excel",
                "status":        "complete",
                "payroll_rows":  len(excel_records),
                "class_codes":   len(xml_records),
                "config_source": config_source,
                "source":        MOCK_API_BASE,
                "timestamp":     datetime.utcnow().isoformat(),
            }, {
                "agent":     "ingestion_xml",
                "status":    "complete",
                "timestamp": datetime.utcnow().isoformat(),
            }, {
                "agent":     "ingestion_audit_meta",
                "status":    "complete",
                "timestamp": datetime.utcnow().isoformat(),
            }],
        }

    except requests.HTTPError as http_exc:
        status = http_exc.response.status_code if http_exc.response else "?"
        return _err(f"HTTP {status} from Mock API for {policy_number}: {http_exc}")

    except Exception as exc:
        logger.exception(f"[APIIngestion] Unhandled error for {policy_number}")
        return _err(str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# Officer normalizer — fixes state_code/date field swap from Mock API
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_officer(officer: dict) -> dict:
    raw   = str(officer.get("state_code") or "").strip()
    title = str(officer.get("title") or "").strip()
    is_date_like = "/" in raw or "-" in raw or len(raw) > 5
    state_code   = (title[:5] if title else None) if (is_date_like or not raw) else raw[:5]
    return {
        "officer_name":  str(officer.get("officer_name") or officer.get("name") or ""),
        "title":         title,
        "is_on_payroll": bool(officer.get("is_on_payroll", False)),
        "ownership_pct": float(officer.get("ownership_pct", 0) or 0),
        "state_code":    state_code,
        **{k: v for k, v in officer.items()
           if k not in ("officer_name", "name", "title", "is_on_payroll", "ownership_pct", "state_code")},
    }


# ─────────────────────────────────────────────────────────────────────────────
# Normalizers (unchanged from previous version)
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_payroll_row(row: dict) -> dict:
    return {
        "ClassCode":     str(row.get("class_code", "") or "").strip(),
        "StateCode":     str(row.get("state_code",  "") or "").strip(),
        "EmployeeName":  row.get("employee_name", ""),
        "EENo":          str(row.get("ee_no", "") or ""),
        "CheckDate":     row.get("check_date", ""),
        "Wages":         float(row.get("wages", 0) or 0),
        "OvertimePay":   float(row.get("overtime_pay", 0) or 0),
        "DoubleTime":    float(row.get("double_time", 0) or 0),
        "Tips":          float(row.get("tips", 0) or 0),
        "NetPay":        float(row.get("net_pay", 0) or 0),
        "Exposure":      float(row.get("exposure", 0) or 0),
        "NetRate":       float(row.get("net_rate", 0) or 0),
        "EarnedPremium": float(row.get("earned_premium", 0) or 0),
        "PolicyNumber":  row.get("policy_number", ""),
        "ClientName":    row.get("client_name", ""),
        "PolEffDate":    row.get("pol_eff_date", ""),
        "ProcessDate":   row.get("process_date", ""),
        **row,
    }


def _normalize_xml_record(row: dict) -> dict:
    raw_cc     = str(row.get("classCode") or row.get("ClassCode") or "").strip()
    class_code = raw_cc.split()[0] if raw_cc else ""
    state_code = str(row.get("StateCode") or row.get("state_code") or "").strip()
    return {
        "ClassCode":     class_code,
        "StateCode":     state_code,
        "PolicyNumber":  row.get("PolicyNumber", ""),
        "EffectiveDate": row.get("EffectiveDate", ""),
        "ExpirationDate":row.get("ExpirationDate", ""),
        "InsuredName":   row.get("InsuredName", ""),
        "premium":               float(row.get("premium", 0) or 0),
        "CompositeRate":         float(row.get("CompositeRate", 0) or 0),
        "net_rate":              float(row.get("CompositeRate", 0) or 0),
        "est_exposure":          float(row.get("Exposure", 0) or 0),
        "Exposure":              float(row.get("Exposure", 0) or 0),
        "est_ytd_premium":       float(row.get("EstPremium", 0) or 0),
        "EstPremium":            float(row.get("EstPremium", 0) or 0),
        "EstCCpremium":          float(row.get("EstCCpremium", 0) or 0),
        "expected_payroll_submissions": int(row.get("expected_payroll_submissions", 0) or 0),
        "actual_payroll_submissions":   int(row.get("actual_payroll_submissions", 0) or 0),
        "Number_of_Payroll_Reports_Submitted": int(
            row.get("Number_of_Payroll_Reports_Submitted", 0) or 0),
        **row,
        "classCode": class_code,
    }


def _normalize_audit_meta(meta: dict) -> dict:
    return {
        "a_payroll_frequency":       meta.get("a_payroll_frequency", "1W"),
        "a_first_check_date":        meta.get("a_first_check_date", ""),
        "a_last_check_date":         meta.get("a_last_check_date", ""),
        "a_actual_payroll_sub":      int(meta.get("a_actual_payroll_sub", 0) or 0),
        "a_expected_payroll_sub":    int(meta.get("a_expected_payroll_sub", 0) or 0),
        "a_officer_on_payroll":      meta.get("a_officer_on_payroll", "No"),
        "a_reporting_by_class_code": meta.get("a_reporting_by_class_code", "Yes"),
        **meta,
    }


def _err(msg: str) -> dict:
    logger.error(f"[APIIngestion] {msg}")
    return {
        "excel_records":    [],
        "xml_records":      [],
        "policy_config":    {},
        "audit_xl_records": [{}],
        "errors": [f"api_ingestion_node failed: {msg}"],
        "agent_logs": [{
            "agent":     "ingestion_excel",
            "status":    "error",
            "error":     msg,
            "timestamp": datetime.utcnow().isoformat(),
        }],
    }