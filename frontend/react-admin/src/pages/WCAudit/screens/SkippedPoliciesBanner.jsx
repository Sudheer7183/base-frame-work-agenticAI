import { useState } from "react";
import C from "../constants/colors";

function SkippedPoliciesBanner({ policies }) {
  const [expanded, setExpanded] = useState(false);
  if (!policies || policies.length === 0) return null;
  return (
    <div style={{ background:"#FFF7ED", border:"1px solid #FED7AA",
      borderRadius:12, padding:"14px 18px", display:"flex",
      alignItems:"flex-start", gap:12 }}>
      <span style={{ fontSize:20, flexShrink:0 }}>⚠️</span>
      <div style={{ flex:1 }}>
        <div style={{ fontWeight:700, fontSize:14, color:"#9A3412", marginBottom:4 }}>
          {policies.length} {policies.length === 1 ? "policy" : "policies"} skipped — will not be queued
        </div>
        <div style={{ fontSize:12, color:"#C2410C", marginBottom:8 }}>
          These records were excluded before submission because they are either unavailable
          in the Mock API or are missing required fields.
        </div>
        <button onClick={() => setExpanded(v => !v)}
          style={{ background:"#FED7AA", border:"none", borderRadius:6,
            padding:"4px 14px", fontSize:12, fontWeight:700,
            cursor:"pointer", color:"#9A3412" }}>
          {expanded ? "Hide Details ▲" : "View Details ▼"}
        </button>
        {expanded && (
          <div style={{ marginTop:12, display:"flex", flexDirection:"column", gap:6 }}>
            {policies.map((p, i) => (
              <div key={i} style={{ background:"#fff", border:"1px solid #FECACA",
                borderRadius:8, padding:"10px 14px",
                display:"flex", alignItems:"center", gap:14, flexWrap:"wrap" }}>
                <span style={{ fontSize:13, fontWeight:700, color:"#6B7E99", minWidth:130 }}>
                  {p.policy_number || <em style={{ color:"#EF4444" }}>No policy_number</em>}
                </span>
                <span style={{ fontSize:13, flex:1, color:"#1A2B42" }}>
                  {p.insured_name || <em style={{ color:"#9CA3AF" }}>Unknown insured</em>}
                </span>
                <span style={{ fontSize:11, background:"#FEE2E2", color:"#DC2626",
                  borderRadius:20, padding:"2px 10px", fontWeight:700, whiteSpace:"nowrap" }}>
                  {p._skipReason}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default SkippedPoliciesBanner;