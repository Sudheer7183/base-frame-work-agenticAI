import { useState } from "react";
import { downloadReport } from "../../../api/wcAuditAPI";
import C from "../constants/colors";
import { money } from "../constants/formatters";

function ResultsAndHITLPanel({ status, onApprove }) {
  const [note,       setNote]       = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [decision,   setDecision]   = useState(null);

  const isHITL      = status.status === "hitl_pending";
  const isCompleted = status.status === "completed";
  const ov          = status.overall_variance || {};

  const riskColor = status.risk_level === "high"   ? C.red
                  : status.risk_level === "medium"  ? C.amber : C.green;
  const recColor  = status.recommendation === "additional_premium" ? C.amber
                  : status.recommendation === "refund"             ? C.green
                  : status.recommendation === "clarification"      ? C.purple : C.muted;

  const handleDecision = async (d) => {
    setDecision(d);
    setSubmitting(true);
    try {
      await onApprove(d, note);
    } finally {
      setSubmitting(false);
      setDecision(null);
    }
  };

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:12 }}>

      {/* HITL banner */}
      {isHITL && (
        <div style={{ padding:"14px 18px", borderRadius:12,
          background:"linear-gradient(135deg, #FEF3C7, #FDE68A)",
          border:`1px solid ${C.amber}`, display:"flex", alignItems:"center", gap:14 }}>
          <span style={{ fontSize:26 }}>⚠️</span>
          <div>
            <div style={{ fontSize:14, fontWeight:800, color:"#78350F" }}>
              Human Review Required — High-Risk Audit
            </div>
            <div style={{ fontSize:12, color:"#92400E", marginTop:2 }}>
              The AI pipeline has paused and is awaiting your approval before finalizing.
              Review the findings below then approve or reject.
            </div>
          </div>
        </div>
      )}

      {/* Metrics grid */}
      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:20 }}>
        <div style={{ fontSize:14, fontWeight:700, color:C.text, marginBottom:12 }}>
          Audit Results — Case #{status.audit_case_id}
        </div>

        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10, marginBottom:14 }}>
          {[
            { label:"Overall Variance",
              value:money(Math.round(ov.variance || status.variance || 0)),
              color:(ov.variance || status.variance || 0) > 0 ? C.red : C.green },
            { label:"Variance %",
              value:`${Number(ov.variance_pct || status.variance_pct || 0).toFixed(2)}%`,
              color:Math.abs(ov.variance_pct || status.variance_pct || 0) > 10 ? C.red : C.green },
            { label:"Risk Level",        value:status.risk_level?.toUpperCase() || "—", color:riskColor },
            { label:"Recommendation",    value:status.recommendation?.replace(/_/g," ") || "—", color:recColor },
            { label:"Earned Premium",    value:money(Math.round(ov.earned_premium    || 0)), color:C.text },
            { label:"EST YTD Premium",   value:money(Math.round(ov.est_ytd_premium   || 0)), color:C.text },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ background:C.bg, borderRadius:10, padding:"11px 14px" }}>
              <div style={{ fontSize:10, color:C.muted, fontWeight:700, textTransform:"uppercase",
                letterSpacing:0.8, marginBottom:3 }}>{label}</div>
              <div style={{ fontSize:15, fontWeight:800, color }}>{value}</div>
            </div>
          ))}
        </div>

        {/* Flagged class codes */}
        {(status.class_code_variance || []).filter(r => r.is_flagged).length > 0 && (
          <div style={{ marginBottom:14 }}>
            <div style={{ fontSize:12, fontWeight:700, color:C.text, marginBottom:8 }}>
              Flagged Class Codes
            </div>
            {(status.class_code_variance || []).filter(r => r.is_flagged).map((row, i) => (
              <div key={i} style={{ display:"flex", justifyContent:"space-between",
                alignItems:"center", padding:"8px 12px", background:"#FEF2F2",
                borderRadius:8, marginBottom:6, border:`1px solid #FECACA` }}>
                <div style={{ fontSize:12, color:C.text }}>
                  <strong>Class {row.ClassCode}</strong> ({row.StateCode}) —{" "}
                  Variance: <strong style={{ color:C.red }}>{money(Math.round(row.variance))}</strong>
                  {" "}({Number(row.variance_pct).toFixed(1)}%)
                </div>
                <span style={{ fontSize:10, fontWeight:700, color:C.red,
                  background:"#FEE2E2", padding:"2px 8px", borderRadius:20 }}>⚠ Flag</span>
              </div>
            ))}
          </div>
        )}

        {/* HITL Approval Form */}
        {isHITL && (
          <div style={{ borderTop:`1px solid ${C.border}`, paddingTop:14 }}>
            <div style={{ fontSize:13, fontWeight:700, color:C.text, marginBottom:8 }}>
              Auditor Decision
            </div>
            <textarea value={note} onChange={e => setNote(e.target.value)}
              placeholder="Add notes, overrides, or justification for your decision (optional)…"
              style={{ width:"100%", border:`1px solid ${C.border}`, borderRadius:8, padding:"10px 12px",
                fontSize:13, color:C.text, resize:"vertical", minHeight:72, outline:"none",
                boxSizing:"border-box", marginBottom:12, fontFamily:"inherit" }} />
            <div style={{ display:"flex", gap:10 }}>
              <button disabled={submitting} onClick={() => handleDecision("approve")}
                style={{ flex:1, background:submitting && decision === "approve" ? "#86EFAC" : C.green,
                  color:"#fff", border:"none", borderRadius:10, padding:"12px 0",
                  fontSize:14, fontWeight:800, cursor:submitting ? "default" : "pointer",
                  display:"flex", alignItems:"center", justifyContent:"center", gap:8 }}>
                {submitting && decision === "approve" ? "⏳ Submitting…" : "✓ Approve & Finalize"}
              </button>
              <button disabled={submitting} onClick={() => handleDecision("reject")}
                style={{ flex:1, background:submitting && decision === "reject" ? "#FCA5A5" : C.red,
                  color:"#fff", border:"none", borderRadius:10, padding:"12px 0",
                  fontSize:14, fontWeight:800, cursor:submitting ? "default" : "pointer",
                  display:"flex", alignItems:"center", justifyContent:"center", gap:8 }}>
                {submitting && decision === "reject" ? "⏳ Submitting…" : "✗ Reject"}
              </button>
            </div>
          </div>
        )}

        {/* Download for completed */}
        {isCompleted && (
          <button onClick={() => downloadReport(status.audit_case_id)}
            style={{ width:"100%", background:C.accent, color:"#fff", border:"none", borderRadius:10,
              padding:"11px 0", fontSize:13, fontWeight:700, cursor:"pointer", marginTop:4 }}>
            ⬇ Download Audit Report
          </button>
        )}
      </div>
    </div>
  );
}

export default ResultsAndHITLPanel;