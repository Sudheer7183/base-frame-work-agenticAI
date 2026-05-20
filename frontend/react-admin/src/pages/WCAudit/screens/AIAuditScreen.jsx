import { useState, useEffect, useRef, useCallback } from "react";
import {
  pollAuditStatus,
  submitHITLDecision,
  getAuditStatus,
} from "../../../api/wcAuditAPI";
import C from "../constants/colors";
import { KpiCard, SectionHeader, StatusBadge, RiskBadge } from "../ui";
import ResultsAndHITLPanel from "./ResultsAndHITLPanel";

function AIAuditScreen({ cases, onCaseCreated, activeCaseId: propCaseId, batchCaseIds }) {
  // ── Single-case watch ───────────────────────────────────────────
  const [auditCaseId, setAuditCaseId] = useState(null);
  const [status,      setStatus]      = useState(null);
  const [logs,        setLogs]        = useState([]);
  const [agentStatus, setAgentStatus] = useState({});
  const stopPollRef = useRef(null);

  // ── Batch mode state ────────────────────────────────────────────
  const [batchQueue,      setBatchQueue]      = useState([]);
  const [batchStatuses,   setBatchStatuses]   = useState({});
  const [hitlQueuedIds,   setHitlQueuedIds]   = useState([]);
  const [activeHITLCase,  setActiveHITLCase]  = useState(null);
  const batchPollsRef = useRef({});
  const [batchView,        setBatchView]        = useState("table");

  const isBatchMode = batchCaseIds && batchCaseIds.length > 0;

  const AGENT_LOG_LABELS = {
    ingestion_excel:      "Ingestion Agent     → payroll Excel parsed",
    ingestion_xml:        "Policy Parser       → XML class codes loaded",
    ingestion_audit_meta: "Metadata Agent      → audit dates & submission count loaded",
    api_ingestion_node:   "API Ingestion       → payroll & policy config fetched from API",
    officer_agent:        "Officer Agent       → officer payroll classification checked",
    class_code_agent:     "Class Code Agent    → class code usage validated",
    frequency_agent:      "Frequency Agent     → submission frequency analysed",
    premium_agent:        "Premium Agent       → variance calculation complete",
    risk_assessor:        "Risk Assessor       → risk level & recommendation assigned",
    explanation_agent:    "Explanation Agent   → AI narrative generated",
    hitl_checkpoint:      "HITL Checkpoint     → paused for human review",
  };

  // ── Single-case watcher ─────────────────────────────────────────
  const watchCase = useCallback((caseId) => {
    setAuditCaseId(caseId);
    setLogs([`[${new Date().toLocaleTimeString()}] 🚀 Workflow started — Case #${caseId}`]);
    if (stopPollRef.current) stopPollRef.current();
    const loggedAgents = new Set();

    stopPollRef.current = pollAuditStatus(caseId, (s) => {
      setStatus(s);
      const ts = new Date().toLocaleTimeString();
      const newAgentSt = {};
      (s.agent_logs || []).forEach(log => {
        if (!log.agent) return;
        newAgentSt[log.agent] = log.status === "error" ? "error" : "complete";
        if (!loggedAgents.has(log.agent)) {
          loggedAgents.add(log.agent);
          const label  = AGENT_LOG_LABELS[log.agent] ?? log.agent;
          const prefix = log.status === "error" ? "✗" : log.status === "skipped" ? "⏭" : "✓";
          setLogs(l => [...l, `[${ts}] ${prefix} ${label}`]);
        }
      });
      setAgentStatus(prev => ({...prev, ...newAgentSt}));
      if (s.status === "hitl_pending") {
        setLogs(l => [...l,
          `[${ts}] ⚠️  HITL required — case paused for human review`,
          `[${ts}]    Risk: ${s.risk_level?.toUpperCase()}, Variance: ${Number(s.variance_pct || 0).toFixed(2)}%`,
        ]);
        onCaseCreated?.();
      }
      if (s.status === "completed") {
        setLogs(l => [...l,
          `[${ts}] 🎉 Audit complete`,
          `[${ts}]    Variance: ${Number(s.variance_pct || 0).toFixed(2)}%  |  Risk: ${s.risk_level}  |  Rec: ${s.recommendation}`,
        ]);
        onCaseCreated?.();
        stopPollRef.current?.();
      }
      if (s.status === "rejected") { setLogs(l => [...l, `[${ts}] ✗ Audit rejected`]); stopPollRef.current?.(); }
      if (s.status === "error")    { setLogs(l => [...l, `[${ts}] ✗ Error: ${s.errors}`]); stopPollRef.current?.(); }
    });
  }, [onCaseCreated]);

  // ── Batch: start polling each case ID ───────────────────────────
  useEffect(() => {
    if (!isBatchMode || batchCaseIds.length === 0) return;
    setBatchQueue(batchCaseIds);
    setBatchStatuses({});
    setHitlQueuedIds([]);
    setActiveHITLCase(null);

    Object.values(batchPollsRef.current).forEach(stop => stop?.());
    batchPollsRef.current = {};

    batchCaseIds.forEach(caseId => {
      const stop = pollAuditStatus(caseId, (s) => {
        setBatchStatuses(prev => ({ ...prev, [caseId]: s }));
        onCaseCreated?.();

        if (s.status === "hitl_pending") {
          setHitlQueuedIds(prev =>
            prev.includes(caseId) ? prev : [...prev, caseId]
          );
          setActiveHITLCase(cur => cur ?? caseId);
        }

        if (["completed", "rejected", "error"].includes(s.status)) {
          batchPollsRef.current[caseId]?.();
          delete batchPollsRef.current[caseId];

          setHitlQueuedIds(prev => {
            const next = prev.filter(id => id !== caseId);
            return next;
          });

          setActiveHITLCase(cur => {
            if (cur === caseId) {
              const remaining = hitlQueuedIds.filter(id => id !== caseId);
              return remaining[0] ?? null;
            }
            return cur;
          });
        }
      });
      batchPollsRef.current[caseId] = stop;
    });

    return () => {
      Object.values(batchPollsRef.current).forEach(stop => stop?.());
      batchPollsRef.current = {};
    };
  }, [JSON.stringify(batchCaseIds)]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!activeHITLCase && hitlQueuedIds.length > 0) {
      setActiveHITLCase(hitlQueuedIds[0]);
    }
  }, [hitlQueuedIds, activeHITLCase]);

  useEffect(() => {
    return () => {
      stopPollRef.current?.();
      Object.values(batchPollsRef.current).forEach(stop => stop?.());
    };
  }, []);

  useEffect(() => {
    if (propCaseId && propCaseId !== auditCaseId) watchCase(propCaseId);
  }, [propCaseId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (propCaseId || isBatchMode) return;
    const active = cases.find(c => ["running","pending","hitl_pending"].includes(c.status));
    if (active && active.audit_case_id !== auditCaseId) watchCase(active.audit_case_id);
  }, [cases]); // eslint-disable-line react-hooks/exhaustive-deps

  const agentLabels = [
    { keys:["ingestion_excel","ingestion_audit_meta","api_ingestion_node"], label:"Ingestion Agent",   sub:"Payroll + audit metadata" },
    { keys:["ingestion_xml"],                          label:"Policy Parser",     sub:"XML class codes & rates" },
    { keys:["officer_agent"],                          label:"Officer Agent",     sub:"Officer classification" },
    { keys:["class_code_agent"],                       label:"Class Code Agent",  sub:"Class code validation" },
    { keys:["frequency_agent"],                        label:"Frequency Agent",   sub:"Submission frequency" },
    { keys:["premium_agent","risk_assessor"],          label:"Premium Agent",     sub:"Variance & risk scoring" },
    { keys:["explanation_agent"],                      label:"Explanation Agent", sub:"AI narrative" },
  ];

  const resolveStepStatus = (keys) => {
    let anyError = false, doneCount = 0;
    for (const k of keys) {
      if (agentStatus[k] === "error")    anyError = true;
      if (agentStatus[k] === "complete") doneCount++;
    }
    if (anyError)                  return "error";
    if (doneCount === keys.length) return "complete";
    if (doneCount > 0)             return "partial";
    return "pending";
  };

  const batchDone      = Object.values(batchStatuses).filter(s => s.status === "completed").length;
  const batchRejected  = Object.values(batchStatuses).filter(s => s.status === "rejected").length;
  const batchError_cnt = Object.values(batchStatuses).filter(s => s.status === "error").length;
  const batchRunning   = Object.values(batchStatuses).filter(s => ["pending","processing","running"].includes(s.status)).length;
  const batchHITL      = hitlQueuedIds.length;

  const activeHITLStatus = activeHITLCase ? batchStatuses[activeHITLCase] : null;

  const handleBatchHITL = async (decision, note) => {
    if (!activeHITLCase) return;
    try {
      await submitHITLDecision(activeHITLCase, { decision, notes: note });
      const fresh = await getAuditStatus(activeHITLCase);
      setBatchStatuses(prev => ({ ...prev, [activeHITLCase]: fresh }));
      onCaseCreated?.();

      setHitlQueuedIds(prev => {
        const next = prev.filter(id => id !== activeHITLCase);
        setActiveHITLCase(next[0] ?? null);
        return next;
      });
    } catch (err) {
      alert("HITL submission failed: " + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:20 }}>

      {/* Header card */}
      <div style={{ background:`linear-gradient(135deg, ${C.navy} 0%, ${C.navyLt} 100%)`,
        borderRadius:14, padding:28, color:"#fff" }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
          <div>
            <h2 style={{ margin:"0 0 6px", fontSize:22, fontWeight:800 }}>🤖 AI Audit Engine</h2>
            <p style={{ margin:0, opacity:0.7, fontSize:14 }}>
              LangGraph-powered multi-agent orchestration for automated earned exposure &amp; premium variance detection
            </p>
          </div>
          {!isBatchMode && auditCaseId && (
            <div style={{ textAlign:"right" }}>
              <div style={{ fontSize:12, opacity:0.6, marginBottom:4 }}>Monitoring Case</div>
              <div style={{ fontSize:22, fontWeight:800 }}>#{auditCaseId}</div>
              {status && <StatusBadge status={status.status} />}
            </div>
          )}
          {isBatchMode && (
            <div style={{ textAlign:"right", minWidth:160 }}>
              <div style={{ fontSize:12, opacity:0.6, marginBottom:4 }}>Batch Mode</div>
              <div style={{ fontSize:22, fontWeight:800 }}>{batchCaseIds.length} policies</div>
              <div style={{ fontSize:12, opacity:0.6, marginTop:4 }}>
                ✅ {batchDone} done · ⚠️ {batchHITL} HITL · ⚙️ {batchRunning} running
              </div>
            </div>
          )}
        </div>
        {!auditCaseId && !isBatchMode && (
          <div style={{ marginTop:16, padding:"12px 16px", background:"rgba(255,255,255,0.07)",
            borderRadius:10, fontSize:13, opacity:0.8 }}>
            Upload files in <strong>Data Upload</strong> to run an audit. The AI pipeline will
            automatically appear here once started.
          </div>
        )}
      </div>

      {/* ── BATCH MODE ── */}
      {isBatchMode && (
        <>
          <div style={{ display:"flex", gap:14 }}>
            <KpiCard label="Total Queued"   value={batchCaseIds.length}  sub="From API batch"          accent={C.accent} />
            <KpiCard label="Completed"      value={batchDone}            sub="Fully audited"           accent={C.green}  />
            <KpiCard label="HITL Pending"   value={batchHITL}            sub="Awaiting your review"    accent={C.amber}  />
            <KpiCard label="Running"        value={batchRunning}         sub="In pipeline"             accent={C.purple} />
            {(batchRejected + batchError_cnt) > 0 && (
              <KpiCard label="Issues"       value={batchRejected + batchError_cnt} sub="Rejected / Error" accent={C.red} />
            )}
          </div>

          {hitlQueuedIds.length > 0 && (
            <div style={{ background:"linear-gradient(135deg, #FEF3C7, #FDE68A)",
              border:`1px solid ${C.amber}`, borderRadius:12, padding:"14px 20px",
              display:"flex", alignItems:"center", gap:14 }}>
              <span style={{ fontSize:28 }}>⚠️</span>
              <div style={{ flex:1 }}>
                <div style={{ fontSize:14, fontWeight:800, color:"#78350F" }}>
                  {hitlQueuedIds.length} policy(ies) require human review
                </div>
                <div style={{ fontSize:12, color:"#92400E", marginTop:2 }}>
                  Reviewing case #{activeHITLCase} now
                  {hitlQueuedIds.length > 1
                    ? ` · ${hitlQueuedIds.length - 1} more in queue after this`
                    : ""}
                </div>
              </div>
              <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
                {hitlQueuedIds.map((id, i) => (
                  <button key={id} onClick={() => setActiveHITLCase(id)}
                    style={{ background: id === activeHITLCase ? C.amber : "rgba(0,0,0,0.1)",
                      color: id === activeHITLCase ? "#fff" : "#78350F",
                      border:"none", borderRadius:20, padding:"4px 12px",
                      fontSize:12, fontWeight:700, cursor:"pointer" }}>
                    #{id}{i === 0 && id === activeHITLCase ? " ← now" : ""}
                  </button>
                ))}
              </div>
            </div>
          )}

          {activeHITLCase && activeHITLStatus && (
            <div style={{ background:C.card, border:`2px solid ${C.amber}`, borderRadius:14, padding:24 }}>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
                <div>
                  <div style={{ fontSize:16, fontWeight:800, color:C.text }}>
                    Reviewing: {activeHITLStatus.policy_number} — Case #{activeHITLCase}
                  </div>
                  <div style={{ fontSize:12, color:C.muted, marginTop:2 }}>
                    Risk: <strong style={{ color:C.red }}>{activeHITLStatus.risk_level?.toUpperCase()}</strong>
                    &nbsp;·&nbsp;Variance: <strong>{Number(activeHITLStatus.variance_pct || 0).toFixed(2)}%</strong>
                    &nbsp;·&nbsp;Rec: <strong>{activeHITLStatus.recommendation?.replace(/_/g," ")}</strong>
                  </div>
                </div>
                <div style={{ display:"flex", gap:8 }}>
                  <RiskBadge risk={activeHITLStatus.risk_level} />
                  <StatusBadge status={activeHITLStatus.status} />
                </div>
              </div>
              <ResultsAndHITLPanel status={activeHITLStatus} onApprove={handleBatchHITL} />
            </div>
          )}

          {/* Batch policy status grid */}
          <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:18 }}>
              <div>
                <h2 style={{ margin:0, fontSize:18, fontWeight:700, color:C.text }}>
                  Batch Policy Progress
                </h2>
                <p style={{ margin:"4px 0 0", fontSize:13, color:C.muted }}>
                  All policies queued in this API batch — click a HITL case to review it
                </p>
              </div>
              <div style={{ display:"flex", background:C.bg, border:`1px solid ${C.border}`,
                borderRadius:10, overflow:"hidden", flexShrink:0 }}>
                {[
                  { key:"card",  icon:"⊞", label:"Cards"  },
                  { key:"table", icon:"☰", label:"Table"  },
                ].map(({ key, icon, label }) => (
                  <button key={key} onClick={() => setBatchView(key)}
                    style={{
                      display:"flex", alignItems:"center", gap:6,
                      padding:"7px 16px", border:"none", cursor:"pointer",
                      fontWeight:700, fontSize:12,
                      background: batchView === key
                        ? `linear-gradient(135deg, ${C.accent}, ${C.teal})`
                        : "transparent",
                      color: batchView === key ? "#fff" : C.muted,
                      transition:"all 0.15s",
                    }}>
                    <span style={{ fontSize:14 }}>{icon}</span>
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* CARD VIEW */}
            {batchView === "card" && (
              <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(260px, 1fr))", gap:10 }}>
                {batchCaseIds.map(caseId => {
                  const s        = batchStatuses[caseId];
                  const isHITL   = hitlQueuedIds.includes(caseId);
                  const isActive = caseId === activeHITLCase;
                  const varPct   = s?.variance_pct != null ? Number(s.variance_pct) : null;
                  const varColor = varPct == null ? C.muted
                                 : Math.abs(varPct) > 20 ? C.red
                                 : Math.abs(varPct) > 10 ? C.amber : C.green;
                  return (
                    <div key={caseId}
                      onClick={() => isHITL && setActiveHITLCase(caseId)}
                      style={{
                        background: isActive ? "#FFFBEB" : isHITL ? "#FFFDE7" : C.bg,
                        border: isActive ? `2px solid ${C.amber}`
                               : isHITL  ? `1px solid ${C.amber}`
                               : `1px solid ${C.border}`,
                        borderRadius:10, padding:"14px 16px",
                        cursor:isHITL ? "pointer" : "default",
                        transition:"all 0.15s", position:"relative",
                      }}
                      onMouseEnter={e => { if (!isHITL) e.currentTarget.style.background = "#F5F8FF"; }}
                      onMouseLeave={e => {
                        e.currentTarget.style.background =
                          isActive ? "#FFFBEB" : isHITL ? "#FFFDE7" : C.bg;
                      }}>
                      <div style={{ display:"flex", justifyContent:"space-between",
                        alignItems:"center", marginBottom:6 }}>
                        <div style={{ fontSize:13, fontWeight:800, color:C.accent }}>
                          {s?.policy_number || `Case #${caseId}`}
                        </div>
                        <StatusBadge status={s?.status || "pending"} />
                      </div>
                      <div style={{ display:"flex", justifyContent:"space-between",
                        alignItems:"center", marginBottom:4 }}>
                        <div style={{ fontSize:11, color:C.muted }}>Case #{caseId}</div>
                        {s?.risk_level && <RiskBadge risk={s.risk_level} />}
                      </div>
                      {varPct != null && (
                        <div style={{ marginTop:8 }}>
                          <div style={{ display:"flex", justifyContent:"space-between",
                            fontSize:11, color:C.muted, marginBottom:3 }}>
                            <span>Variance</span>
                            <span style={{ fontWeight:700, color:varColor }}>
                              {varPct > 0 ? "+" : ""}{varPct.toFixed(1)}%
                            </span>
                          </div>
                          <div style={{ background:C.border, borderRadius:4, height:4, overflow:"hidden" }}>
                            <div style={{
                              width:`${Math.min(Math.abs(varPct) * 2.5, 100)}%`,
                              height:"100%", background:varColor,
                              borderRadius:4, transition:"width 0.4s",
                            }} />
                          </div>
                        </div>
                      )}
                      {isHITL && (
                        <div style={{ marginTop:8, fontSize:11, fontWeight:700, color:C.amber,
                          display:"flex", alignItems:"center", gap:4 }}>
                          ⚠️ {isActive ? "Reviewing now" : "Click to review"}
                        </div>
                      )}
                      {(() => {
                        const ov       = s?.overall_variance || {};
                        const isPend   = ["pending","processing","running"].includes(s?.status);
                        const premium  = ov.earned_premium || ov.est_ytd_premium || 0;
                        const label    = (isPend && !ov.earned_premium && ov.est_ytd_premium)
                          ? "Est. Premium" : "Premium";
                        if (!premium) return null;
                        return (
                          <div style={{ marginTop:6, fontSize:11, color:C.muted }}>
                            {label}: <strong style={{ color:C.text }}>
                              ${Math.round(premium).toLocaleString()}
                            </strong>
                          </div>
                        );
                      })()}
                    </div>
                  );
                })}
              </div>
            )}

            {/* TABLE VIEW */}
            {batchView === "table" && (
              <div style={{ overflowX:"auto" }}>
                <table style={{ width:"100%", borderCollapse:"collapse" }}>
                  <thead>
                    <tr style={{ borderBottom:`2px solid ${C.border}`, background:"#F8FAFD" }}>
                      {["#","Policy Number","Case ID","Status","Risk","Variance %",
                        "Earned Premium","Recommendation","Action"].map(h => (
                        <th key={h} style={{ textAlign:"left", padding:"10px 14px", fontSize:11,
                          fontWeight:700, color:C.muted, textTransform:"uppercase",
                          letterSpacing:0.7, whiteSpace:"nowrap" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {batchCaseIds.map((caseId, idx) => {
                      const s        = batchStatuses[caseId];
                      const isHITL   = hitlQueuedIds.includes(caseId);
                      const isActive = caseId === activeHITLCase;
                      const varPct   = s?.variance_pct != null ? Number(s.variance_pct) : null;
                      const varColor = varPct == null ? C.muted
                                     : Math.abs(varPct) > 20 ? C.red
                                     : Math.abs(varPct) > 10 ? C.amber : C.green;
                      const rowBg    = isActive ? "#FFFBEB" : isHITL ? "#FFFDE7" : "transparent";
                      return (
                        <tr key={caseId}
                          onClick={() => isHITL && setActiveHITLCase(caseId)}
                          style={{
                            borderBottom:`1px solid ${C.border}`,
                            background:rowBg,
                            cursor:isHITL ? "pointer" : "default",
                            transition:"background 0.15s",
                          }}
                          onMouseEnter={e => {
                            if (!isHITL && !isActive) e.currentTarget.style.background = "#F5F8FF";
                          }}
                          onMouseLeave={e => {
                            e.currentTarget.style.background = rowBg;
                          }}>
                          <td style={{ padding:"12px 14px", fontSize:12, color:C.muted, fontWeight:600 }}>{idx + 1}</td>
                          <td style={{ padding:"12px 14px", fontSize:13, fontWeight:800, color:C.accent }}>
                            {s?.policy_number || "—"}
                            {isHITL && (
                              <span style={{ marginLeft:6, fontSize:10, fontWeight:700, color:C.amber }}>
                                ⚠️ {isActive ? "reviewing" : "HITL"}
                              </span>
                            )}
                          </td>
                          <td style={{ padding:"12px 14px", fontSize:12, color:C.muted }}>#{caseId}</td>
                          <td style={{ padding:"12px 14px" }}>
                            <StatusBadge status={s?.status || "pending"} />
                          </td>
                          <td style={{ padding:"12px 14px" }}>
                            {s?.risk_level ? <RiskBadge risk={s.risk_level} /> : <span style={{ color:C.muted }}>—</span>}
                          </td>
                          <td style={{ padding:"12px 14px", minWidth:110 }}>
                            {varPct != null ? (
                              <div>
                                <div style={{ fontWeight:700, fontSize:13, color:varColor, marginBottom:3 }}>
                                  {varPct > 0 ? "+" : ""}{varPct.toFixed(1)}%
                                </div>
                                <div style={{ background:C.border, borderRadius:4, height:4, width:80 }}>
                                  <div style={{
                                    width:`${Math.min(Math.abs(varPct) * 2.5, 100)}%`,
                                    height:"100%", background:varColor, borderRadius:4,
                                  }} />
                                </div>
                              </div>
                            ) : <span style={{ color:C.muted }}>—</span>}
                          </td>
                          <td style={{ padding:"12px 14px", fontSize:13, fontWeight:600, color:C.text }}>
                            {(() => {
                              const ov      = s?.overall_variance || {};
                              const premium = ov.earned_premium || ov.est_ytd_premium || 0;
                              return premium ? `$${Math.round(premium).toLocaleString()}` : "—";
                            })()}
                          </td>
                          <td style={{ padding:"12px 14px", fontSize:12, color:C.muted }}>
                            {s?.recommendation ? s.recommendation.replace(/_/g, " ") : "—"}
                          </td>
                          <td style={{ padding:"12px 14px" }}>
                            {isHITL ? (
                              <button
                                onClick={e => { e.stopPropagation(); setActiveHITLCase(caseId); }}
                                style={{ background:C.amber, color:"#fff", border:"none",
                                  borderRadius:6, padding:"5px 12px", fontSize:11,
                                  fontWeight:700, cursor:"pointer", whiteSpace:"nowrap" }}>
                                Review ▲
                              </button>
                            ) : (
                              <span style={{ fontSize:12, color:C.muted }}>—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {batchCaseIds.length === 0 && (
                  <div style={{ textAlign:"center", padding:40, color:C.muted, fontSize:14 }}>
                    No policies in this batch yet.
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}

      {/* ── SINGLE-CASE MODE ── */}
      {!isBatchMode && (
        <div style={{ display:"flex", gap:16 }}>
          {/* Agent Pipeline */}
          <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24, flex:1 }}>
            <SectionHeader title="Agent Pipeline Status" sub="Real-time LangGraph orchestration" />
            <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
              {agentLabels.map((a, i) => {
                const st        = resolveStepStatus(a.keys);
                const bgColor   = st === "complete" ? "#F0FDF4" : st === "error" ? "#FEF2F2" : st === "partial" ? "#EEF2FF" : C.bg;
                const bdColor   = st === "complete" ? C.green   : st === "error" ? C.red     : st === "partial" ? C.accent  : C.border;
                const circleClr = st === "complete" ? C.green   : st === "error" ? C.red     : st === "partial" ? C.accent  : C.border;
                const badge     = st === "complete" ? { bg:"#DCFCE7", color:C.green,  text:"Done" }
                                : st === "error"    ? { bg:"#FEE2E2", color:C.red,    text:"Error" }
                                : st === "partial"  ? { bg:"#DBEAFE", color:C.accent, text:"Running" }
                                :                    { bg:"#F3F4F6", color:C.muted,   text:"Pending" };
                const subText   = st === "complete" ? a.sub
                                : st === "error"    ? "Error encountered"
                                : st === "partial"  ? "Processing…" : "Waiting…";
                return (
                  <div key={a.keys.join()} style={{ display:"flex", alignItems:"center", gap:14,
                    padding:"12px 16px", borderRadius:10, transition:"all 0.3s",
                    background:bgColor, border:`1px solid ${bdColor}` }}>
                    <div style={{ width:32, height:32, borderRadius:"50%", flexShrink:0,
                      display:"flex", alignItems:"center", justifyContent:"center", fontSize:14,
                      background:circleClr, color: st === "pending" ? C.muted : "#fff" }}>
                      {st === "complete" ? "✓" : st === "error" ? "✗" : st === "partial" ? "⚙" : i + 1}
                    </div>
                    <div style={{ flex:1 }}>
                      <div style={{ fontSize:13, fontWeight:700, color:C.text }}>{a.label}</div>
                      <div style={{ fontSize:11, color:C.muted }}>{subText}</div>
                    </div>
                    <span style={{ fontSize:11, fontWeight:600, padding:"3px 10px", borderRadius:20,
                      background:badge.bg, color:badge.color }}>{badge.text}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Live log + results */}
          <div style={{ flex:1, display:"flex", flexDirection:"column", gap:16 }}>
            <div style={{ background:C.navy, borderRadius:14, padding:20, flex:1, minHeight:300 }}>
              <div style={{ fontSize:13, fontWeight:700, color:"#64B5F6", marginBottom:12,
                fontFamily:"monospace" }}>▶ AUDIT LOG</div>
              <div style={{ fontFamily:"'Courier New', monospace", fontSize:11.5, color:"#A8D8A8",
                lineHeight:1.8, overflowY:"auto", maxHeight:280 }}>
                {logs.length === 0
                  ? <span style={{ color:"#546E7A" }}>// Upload files then start an audit to see live output</span>
                  : logs.map((l, i) => <div key={i}>{l}</div>)}
              </div>
            </div>

            {status && ["completed","hitl_pending"].includes(status.status) && (
              <ResultsAndHITLPanel status={status} onApprove={async (decision, note) => {
                try {
                  await submitHITLDecision(status.audit_case_id, { decision, notes: note });
                  const fresh = await getAuditStatus(status.audit_case_id);
                  setStatus(fresh);
                  onCaseCreated?.();
                  const ts = new Date().toLocaleTimeString();
                  setLogs(l => [...l, `[${ts}] ✓ HITL decision submitted: ${decision}`]);
                } catch (err) {
                  alert("HITL submission failed: " + (err.response?.data?.detail || err.message));
                }
              }} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default AIAuditScreen;