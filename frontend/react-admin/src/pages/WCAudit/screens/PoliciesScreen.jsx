import { useState } from "react";
import { downloadReport } from "../../../api/wcAuditAPI";
import C from "../constants/colors";
import { fmt } from "../constants/formatters";
import { KpiCard, RiskBadge, StatusBadge } from "../ui";

function PoliciesScreen({ setScreen, setSelectedCase, cases, onRefresh }) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");

  const filtered = cases.filter(c =>
    (filter === "All" || c.risk_level?.toLowerCase() === filter.toLowerCase()) &&
    (c.policy_number?.toLowerCase().includes(search.toLowerCase()) ||
     String(c.audit_case_id).includes(search))
  );

  console.log("filtered data -->", cases);

  const high    = cases.filter(c => c.risk_level === "high").length;
  const pending = cases.filter(c => ["pending","running"].includes(c.status)).length;
  const done    = cases.filter(c => c.status === "completed").length;

  return (
    <div>
      <div style={{ display:"flex", gap:16, marginBottom:24, flexWrap:"wrap" }}>
        <KpiCard label="Total Policies"  value={cases.length} sub="Active policy terms"         accent={C.accent} />
        <KpiCard label="Pending Review"  value={pending}      sub="Awaiting auditor action"      accent={C.amber}  />
        <KpiCard label="High Risk"       value={high}         sub="Require immediate attention"  accent={C.red}    />
        <KpiCard label="Completed"       value={done}         sub="Fully audited"                accent={C.green}  />
      </div>

      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center",
          marginBottom:20, flexWrap:"wrap", gap:12 }}>
          <h2 style={{ margin:0, fontSize:18, fontWeight:700, color:C.text }}>Policy Management</h2>
          <div style={{ display:"flex", gap:10, alignItems:"center", flexWrap:"wrap" }}>
            <input value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Search policy # or case ID..."
              style={{ border:`1px solid ${C.border}`, borderRadius:8, padding:"8px 14px",
                fontSize:13, width:240, outline:"none", color:C.text }} />
            {["All","High","Medium","Low"].map(f => (
              <button key={f} onClick={() => setFilter(f)}
                style={{ background:filter === f ? C.accent : C.bg,
                  color:filter === f ? "#fff" : C.muted,
                  border:`1px solid ${filter === f ? C.accent : C.border}`,
                  borderRadius:20, padding:"5px 16px", fontSize:12, fontWeight:600, cursor:"pointer" }}>
                {f}
              </button>
            ))}
            <button onClick={onRefresh}
              style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:8,
                padding:"7px 14px", fontSize:12, cursor:"pointer", color:C.muted }}>
              ↻ Refresh
            </button>
          </div>
        </div>

        {cases.length === 0 ? (
          <div style={{ textAlign:"center", padding:60, color:C.muted, fontSize:14 }}>
            No audit cases found. Go to <strong>Data Upload</strong> to run your first audit.
          </div>
        ) : (
          <>
            <table style={{ width:"100%", borderCollapse:"collapse" }}>
              <thead>
                <tr style={{ borderBottom:`2px solid ${C.border}`, background:"#F8FAFD" }}>
                  {["Policy Number","Insured Name","St.","Variance","Earned Premium",
                    "Risk","Status","Agent Name","Actions"].map(h => (
                    <th key={h} style={{ textAlign:"left", padding:"10px 14px", fontSize:11,
                      fontWeight:700, color:C.muted, textTransform:"uppercase", letterSpacing:0.8 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map(c => (
                  <tr key={c.audit_case_id}
                    style={{ borderBottom:`1px solid ${C.border}`, transition:"background 0.1s" }}
                    onMouseEnter={e => e.currentTarget.style.background = "#F5F8FF"}
                    onMouseLeave={e => e.currentTarget.style.background = "transparent"}>

                    <td style={{ padding:"13px 14px", fontSize:13, fontWeight:700, color:C.accent,
                      cursor:"pointer" }}
                      onClick={() => { setSelectedCase(c); setScreen("audit-detail"); }}>
                      {c.policy_number}
                    </td>

                    <td style={{ padding:"13px 14px", fontSize:13, color:C.muted }}>{c.insured_name}</td>

                    <td style={{ padding:"13px 14px", fontSize:13, fontWeight:700, color:C.muted }}>{c.class_code_variance[0]?.StateCode}</td>

                    <td style={{ padding:"13px 14px" }}>
                      <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                        <div style={{ width:50, height:6, borderRadius:3, background:C.border, overflow:"hidden" }}>
                          <div style={{ width:`${Math.min((c.variance_pct || 0) * 3, 100)}%`,
                            height:"100%",
                            background:(c.variance_pct || 0) >= 25 ? C.red :
                                       (c.variance_pct || 0) >= 10 ? C.amber : C.green }} />
                        </div>
                        <span style={{ fontSize:13, fontWeight:700,
                          color:(c.variance_pct || 0) >= 25 ? C.red :
                               (c.variance_pct || 0) >= 10 ? C.amber : C.green }}>
                          {c.variance_pct != null ? `${Number(c.variance_pct).toFixed(1)}%` : "—"}
                        </span>
                      </div>
                    </td>

                    <td style={{ padding:"13px 14px", fontSize:13, fontWeight:600, color:C.text }}>
                      {fmt(c.overall_variance?.earned_premium)}
                    </td>

                    <td style={{ padding:"13px 14px" }}><RiskBadge risk={c.risk_level} /></td>
                    <td style={{ padding:"13px 14px" }}><StatusBadge status={c.status} /></td>
                    <td style={{ padding:"13px 14px", fontSize:12, color:C.muted }}>—</td>

                    <td style={{ padding:"13px 14px" }}>
                      <div style={{ display:"flex", gap:6 }}>
                        <button onClick={() => { setSelectedCase(c); setScreen("audit-detail"); }}
                          style={{ background:C.accent, color:"#fff", border:"none", borderRadius:6,
                            padding:"5px 12px", fontSize:12, fontWeight:600, cursor:"pointer" }}>
                          Review
                        </button>
                        <button onClick={() => downloadReport(c.audit_case_id)}
                          style={{ background:C.bg, color:C.muted, border:`1px solid ${C.border}`,
                            borderRadius:6, padding:"5px 10px", fontSize:12, cursor:"pointer" }}>
                          ⬇
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <div style={{ textAlign:"center", padding:40, color:C.muted, fontSize:14 }}>
                No cases match your filter.
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default PoliciesScreen;