// import { downloadReport } from "../../api/wcAuditAPI";
import { downloadReport } from "../../../api/wcAuditAPI";
import C from "../constants/colors";
import { SectionHeader, RiskBadge } from "../ui";

function ReportsScreen({ cases }) {
  const completed = cases.filter(c => c.status === "completed");

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
      <div style={{ display:"flex", gap:16 }}>
        {[
          { title:"Variance Summary Report",    desc:"Total EST Exposure & Earned Exposure delta vs. EST YTD Premium across all policies", icon:"📊", color:C.accent },
          { title:"Audit Evidence Package",     desc:"Full evidence trail with narratives and source data",                                 icon:"📋", color:C.purple },
          { title:"High Risk Policy Report",    desc:"All policies above 20% variance threshold",                                          icon:"⚠️", color:C.red    },
          { title:"Class Code Analysis",        desc:"Misclassification rates by class code and composite rate",                           icon:"🔍", color:C.teal   },
        ].map((r, i) => (
          <div key={i} style={{ flex:1, background:C.card, border:`1px solid ${C.border}`,
            borderRadius:14, padding:20, cursor:"pointer", transition:"all 0.15s" }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = r.color; e.currentTarget.style.transform = "translateY(-2px)"; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.transform = "none"; }}>
            <div style={{ fontSize:32, marginBottom:12 }}>{r.icon}</div>
            <div style={{ fontSize:14, fontWeight:700, color:C.text, marginBottom:6 }}>{r.title}</div>
            <div style={{ fontSize:12, color:C.muted, lineHeight:1.5, marginBottom:14 }}>{r.desc}</div>
            <button style={{ background:r.color, color:"#fff", border:"none", borderRadius:7,
              padding:"7px 16px", fontSize:12, fontWeight:700, cursor:"pointer", width:"100%" }}>
              Generate →
            </button>
          </div>
        ))}
      </div>

      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>
        <SectionHeader title="Completed Audits" sub="Download reports for finalised cases" />
        {completed.length === 0 ? (
          <div style={{ textAlign:"center", padding:40, color:C.muted, fontSize:14 }}>
            No completed audits yet.
          </div>
        ) : (
          <table style={{ width:"100%", borderCollapse:"collapse" }}>
            <thead>
              <tr style={{ borderBottom:`2px solid ${C.border}`, background:"#F8FAFD" }}>
                {["Policy Number","Risk","Variance %","Recommendation","Date","Actions"].map(h => (
                  <th key={h} style={{ padding:"10px 14px", textAlign:"left", fontSize:11,
                    color:C.muted, fontWeight:700, textTransform:"uppercase" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {completed.map(c => (
                <tr key={c.audit_case_id} style={{ borderBottom:`1px solid ${C.border}` }}>
                  <td style={{ padding:"13px 14px", fontSize:13, fontWeight:700, color:C.accent }}>
                    {c.policy_number}
                  </td>
                  <td style={{ padding:"13px 14px" }}><RiskBadge risk={c.risk_level} /></td>
                  <td style={{ padding:"13px 14px", fontSize:13, fontWeight:700,
                    color:(c.variance_pct || 0) > 10 ? C.red : C.green }}>
                    {Number(c.variance_pct || 0).toFixed(1)}%
                  </td>
                  <td style={{ padding:"13px 14px", fontSize:12, color:C.muted, textTransform:"capitalize" }}>
                    {c.recommendation?.replace("_"," ") || "—"}
                  </td>
                  <td style={{ padding:"13px 14px", fontSize:12, color:C.muted }}>
                    {new Date(c.created_at).toLocaleDateString()}
                  </td>
                  <td style={{ padding:"13px 14px" }}>
                    <button onClick={() => downloadReport(c.audit_case_id)}
                      style={{ background:C.accent, color:"#fff", border:"none", borderRadius:6,
                        padding:"5px 12px", fontSize:12, fontWeight:600, cursor:"pointer" }}>
                      ⬇ Report
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default ReportsScreen;