"""
Explanation Agent (LLM-Assisted)
Generates plain-English audit narratives using Claude (Anthropic API).
Called AFTER all deterministic calculations are complete.

This is the ONLY agent that uses an LLM — keeping the system
regulator-safe by separating AI from arithmetic.
"""
import json
import logging
import os
from datetime import datetime

import httpx

from app.agent_langgraph.wc_state import WCAuditState

logger = logging.getLogger(__name__)

GROQ_API_KEY = "*****"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
MODEL        = "openai/gpt-oss-120b"  # or "mixtral-8x7b-32768"


async def explanation_agent(state: WCAuditState) -> WCAuditState:
    """
    Generate an auditor-ready narrative using Claude.
    Falls back to a deterministic template if the API is unavailable.
    """
    overall         = state.get("overall_variance", {})
    cc_variances    = state.get("class_code_variance", [])
    officer_issues  = state.get("officer_findings",    [])
    freq_issues     = state.get("frequency_findings",  [])
    cc_issues       = state.get("class_code_findings", [])
    risk_level      = state.get("risk_level",          "low")
    recommendation  = state.get("recommendation",      "no_action")
    policy_cfg      = state.get("policy_config",       {})

    # Build a structured prompt context
    context = {
        "policy_number":    state.get("policy_number"),
        "insured_name":     policy_cfg.get("insured_name", "Unknown"),
        "effective_date":   policy_cfg.get("effective_date"),
        "expiration_date":  policy_cfg.get("expiration_date"),
        "first_check_date": state.get("first_check_date"),
        "last_check_date":  state.get("last_check_date"),
        "submitted_count":  state.get("submitted_count"),
        "expected_submissions": round(float(state.get("expected_submissions", 0)), 1),
        "overall_variance": overall,
        "flagged_class_codes": [
            cv for cv in cc_variances if cv.get("is_flagged")
        ],
        "officer_issues":   officer_issues,
        "frequency_issues": freq_issues,
        "class_code_issues": [i for i in cc_issues if i.get("issue") == "invalid_class_code"],
        "risk_level":       risk_level,
        "recommendation":   recommendation,
    }

    prompt = f"""You are a licensed Workers' Compensation Audit specialist.
Based on the following audit findings, write a professional audit narrative (2-4 paragraphs)
that explains:
1. What was audited and the policy period
2. What variances or issues were found (use specific numbers)
3. The root cause(s) of the variance
4. The recommendation (refund / additional premium / clarification)

Audit data:
{json.dumps(context, indent=2, default=str)}

Write the narrative in plain English for an insurance auditor. Be specific about dollar amounts,
class codes, and dates where available. Do NOT use bullet points — write in paragraphs only."""

    narrative = ""

    if GROQ_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    GROQ_URL,
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": MODEL,
                        "messages": [
                            {"role": "system", "content": "You are a licensed Workers' Compensation Audit specialist."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 800,
                    },
                )

                data = response.json()
                narrative = data["choices"][0]["message"]["content"].strip()

        except Exception as exc:
            logger.error(f"[ExplanationAgent] LLM call failed: {exc}")
            narrative = _fallback_narrative(context)
    else:
        logger.warning("[ExplanationAgent] No GROQ_API_KEY — using fallback narrative.")
        narrative = _fallback_narrative(context)

    state["ai_narrative"] = narrative
    state["agent_logs"].append({
        "agent":    "explanation_agent",
        "status":   "success",
        "source":   "llm" if GROQ_API_KEY and narrative else "fallback",
        "timestamp": datetime.utcnow().isoformat(),
    })

    print("state value of the narrative",narrative)

    return state


def _fallback_narrative(ctx: dict) -> str:
    """Deterministic fallback narrative when LLM is unavailable."""
    overall  = ctx.get("overall_variance", {})
    variance = float(overall.get("variance", 0))
    var_pct  = float(overall.get("variance_pct", 0))
    rec      = ctx.get("recommendation", "no_action")
    policy   = ctx.get("policy_number", "N/A")
    insured  = ctx.get("insured_name", "The insured")

    rec_text = {
        "refund":             f"a refund of ${abs(variance):,.2f} is due to the insured",
        "additional_premium": f"an additional premium of ${abs(variance):,.2f} is owed",
        "clarification":      "further clarification is required before a final determination",
        "no_action":          "no further action is required at this time",
    }.get(rec, "further review is recommended")

    officer_note = ""
    if ctx.get("officer_issues"):
        officer_note = (
            f" {len(ctx['officer_issues'])} officer payroll classification "
            "discrepancy(ies) were identified that may have materially impacted the premium."
        )

    freq_note = ""
    if ctx.get("frequency_issues"):
        fi = ctx["frequency_issues"][0]
        freq_note = (
            f" The audit identified {fi.get('gap', 0):.0f} missing payroll submission(s) "
            f"against an expectation of {ctx.get('expected_submissions', 0):.0f} submissions "
            f"for the policy period."
        )

    return (
        f"This audit covers Workers' Compensation policy {policy} for {insured} "
        f"with an effective period from {ctx.get('effective_date', 'N/A')} to "
        f"{ctx.get('expiration_date', 'N/A')}. Payroll submissions were reviewed from "
        f"{ctx.get('first_check_date', 'N/A')} to {ctx.get('last_check_date', 'N/A')} "
        f"with {ctx.get('submitted_count', 0)} payroll reports submitted.\n\n"
        f"The audit calculation produced an overall premium variance of "
        f"${variance:+,.2f} ({var_pct:+.2f}%), indicating {rec_text}."
        f"{officer_note}{freq_note}\n\n"
        f"Risk level for this audit has been assessed as {ctx.get('risk_level', 'unknown').upper()}. "
        f"All findings have been documented in the variance breakdown report and are available "
        f"for auditor review and Manual approval."
    )
