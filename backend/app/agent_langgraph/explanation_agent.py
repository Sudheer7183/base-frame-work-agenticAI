
"""
Explanation Agent (LLM-Assisted)
Generates plain-English audit narratives.

Uses the platform's existing LLMProvider factory (backend/app/workflows/nodes.py)
so provider selection, API keys, and model config all come from settings — 
no hardcoding anywhere in this file.
"""
import json
import logging
from datetime import datetime
from typing import Any

from app.agent_langgraph.wc_state import WCAuditState
from app.workflows.nodes import LLMProvider  # ← platform's existing factory
from app.services.token_parser import TokenParser
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "You are a licensed Workers' Compensation Audit specialist."


async def explanation_agent(state: WCAuditState) -> dict:
    """
    Generate an auditor-ready narrative using the platform LLM provider.
    Returns a partial dict — LangGraph merges it into the master state.
    """
    overall        = state.get("overall_variance", {})
    cc_variances   = state.get("class_code_variance", [])
    officer_issues = state.get("officer_findings", [])
    freq_issues    = state.get("frequency_findings", [])
    cc_issues      = state.get("class_code_findings", [])
    risk_level     = state.get("risk_level", "low")
    recommendation = state.get("recommendation", "no_action")
    policy_cfg     = state.get("policy_config", {})

    context = {
        "policy_number":        state.get("policy_number"),
        "insured_name":         policy_cfg.get("insured_name", "Unknown"),
        "effective_date":       policy_cfg.get("effective_date"),
        "expiration_date":      policy_cfg.get("expiration_date"),
        "first_check_date":     state.get("first_check_date"),
        "last_check_date":      state.get("last_check_date"),
        "submitted_count":      state.get("submitted_count"),
        "expected_submissions": round(float(state.get("expected_submissions", 0)), 1),
        "overall_variance":     overall,
        "flagged_class_codes":  [cv for cv in cc_variances if cv.get("is_flagged")],
        "officer_issues":       officer_issues,
        "frequency_issues":     freq_issues,
        "class_code_issues":    [i for i in cc_issues if i.get("issue") == "invalid_class_code"],
        "risk_level":           risk_level,
        "recommendation":       recommendation,
    }

    prompt = f"""Based on the following audit findings, write a professional audit narrative
(2-4 paragraphs) that explains:
1. What was audited and the policy period
2. What variances or issues were found (use specific numbers)
3. The root cause(s) of the variance
4.The recommendation (refund / additional premium / clarification) 
Note for Variance calculation:
    1.Variance Formula Used = Actual Earned premium - Estimated earned premium
    2.Refund to be issued = Postive variance (which means Extra money has been paid by the insured than the estimated). 
    3.Additional premium to be collected = Negative Variance (which means the insured paid less amount than expected/estimated)

Audit data:
{json.dumps(context, indent=2, default=str)}

Write in plain English for an insurance auditor. Be specific about dollar amounts,
class codes, and dates where available. Write in paragraphs only — no bullet points."""

    narrative = ""
    source    = "fallback"

    try:

        provider = LLMProvider.get_provider({
            "provider":    state.get("llm_provider"),   # optional per-audit override
            "temperature": 0.3,
            "max_tokens":  800,
        })
        print("I am using LLM provider values",provider)
        result    = await provider.generate(prompt, system_prompt=SYSTEM_PROMPT)
        narrative = result["content"]
        source    = result.get("provider", "llm")
        logger.info("[ExplanationAgent] Narrative generated via %s", source)

    except Exception as exc:
        logger.error("[ExplanationAgent] LLM call failed: %s — using fallback", exc)
        narrative = _fallback_narrative(context)
        source    = "fallback"

    # ── Return partial dict — LangGraph merges into master state ─────────
    return {
        "ai_narrative": narrative,
        "agent_logs": state.get("agent_logs", []) + [{
            "agent":     "explanation_agent",
            "status":    "success",
            "source":    source,
            "timestamp": datetime.utcnow().isoformat(),
        }],
    }


def _fallback_narrative(ctx: dict) -> str:
    """Deterministic fallback when LLM is unavailable."""
    print("I have fall backed to the backup function")
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
        f"Risk level for this audit has been assessed as "
        f"{ctx.get('risk_level', 'unknown').upper()}. All findings have been documented "
        f"in the variance breakdown report and are available for auditor review."
    )