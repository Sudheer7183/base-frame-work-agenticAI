import { useState, useEffect } from "react";
import { getAuditConfig, updateAuditConfig, clearAllAuditData } from "../../../api/wcAuditAPI";
import C from "../constants/colors";

const CONFIRM_PHRASE = "DELETE ALL DATA";

function Administration({ setScreen, onDataCleared }) {
  // ── Tab state ──────────────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState("configuration");

  // ── Data wipe state ────────────────────────────────────────────────────────
  const [phase,      setPhase]      = useState("idle");
  const [confirmTxt, setConfirmTxt] = useState("");
  const [wipeResult, setWipeResult] = useState(null);
  const [wipeErr,    setWipeErr]    = useState("");

  // ── HITL config state ──────────────────────────────────────────────────────
  const [hitlEnabled,      setHitlEnabled]      = useState(true);
  const [configLoading,    setConfigLoading]    = useState(true);
  const [configSaving,     setConfigSaving]     = useState(false);
  const [configSaveStatus, setConfigSaveStatus] = useState(null);
  const [configErr,        setConfigErr]        = useState("");

  useEffect(() => {
    (async () => {
      setConfigLoading(true);
      try {
        const cfg = await getAuditConfig();
        setHitlEnabled(cfg.hitl_enabled ?? true);
      } catch (e) {
        setConfigErr(e.message || "Failed to load config");
      } finally {
        setConfigLoading(false);
      }
    })();
  }, []);

  const handleHitlToggle = async (newValue) => {
    setHitlEnabled(newValue);
    setConfigSaving(true);
    setConfigSaveStatus(null);
    try {
      await updateAuditConfig({ hitl_enabled: newValue });
      setConfigSaveStatus("saved");
      setTimeout(() => setConfigSaveStatus(null), 3000);
    } catch (e) {
      setConfigErr(e.message || "Failed to save config");
      setConfigSaveStatus("error");
      setHitlEnabled(!newValue);
    } finally {
      setConfigSaving(false);
    }
  };

  const handleWipe = async () => {
    setPhase("wiping");
    setWipeErr("");
    try {
      const data = await clearAllAuditData();
      setWipeResult(data);
      setPhase("done");
      onDataCleared?.();
    } catch (err) {
      setWipeErr(err.response?.data?.detail || err.message || "Unknown error");
      setPhase("error");
    }
  };

  const reset = () => {
    setPhase("idle");
    setConfirmTxt("");
    setWipeResult(null);
    setWipeErr("");
  };

  const TabBtn = ({ id, icon, label }) => (
    <button onClick={() => setActiveTab(id)}
      style={{
        display:"flex", alignItems:"center", gap:8,
        padding:"10px 20px", border:"none", cursor:"pointer",
        fontWeight:700, fontSize:13, borderRadius:"10px 10px 0 0",
        background: activeTab === id ? C.card : "transparent",
        color: activeTab === id ? C.accent : C.muted,
        borderBottom: activeTab === id ? `2px solid ${C.accent}` : "2px solid transparent",
        transition:"all 0.15s",
      }}>
      <span style={{ fontSize:15 }}>{icon}</span> {label}
    </button>
  );

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:0, maxWidth:900 }}>

      {/* Page header */}
      <div style={{ background:C.card, border:`1px solid ${C.border}`,
        borderRadius:14, padding:24, marginBottom:20 }}>
        <div style={{ display:"flex", alignItems:"center", gap:14 }}>
          <div style={{ width:44, height:44, borderRadius:12,
            background:"linear-gradient(135deg,#7C3AED,#EF4444)",
            display:"flex", alignItems:"center", justifyContent:"center", fontSize:22 }}>⚙</div>
          <div>
            <h2 style={{ margin:0, fontSize:20, fontWeight:800, color:C.text }}>Administration</h2>
            <p style={{ margin:"3px 0 0", fontSize:13, color:C.muted }}>
              Platform-level configuration and data management — Super Admin only.
            </p>
          </div>
        </div>
      </div>

      {/* Tab bar */}
      <div style={{ display:"flex", gap:4, borderBottom:`2px solid ${C.border}`,
        marginBottom:24, paddingLeft:4 }}>
        <TabBtn id="configuration" icon="⚙" label="Configuration" />
        <TabBtn id="data"          icon="🗑" label="Data Management" />
      </div>

      {/* ── CONFIGURATION TAB ── */}
      {activeTab === "configuration" && (
        <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
          <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:28 }}>

            <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:20 }}>
              <div style={{ width:40, height:40, borderRadius:10,
                background: hitlEnabled ? "linear-gradient(135deg,#1E6FD9,#0ABFBC)" : "#F3F4F6",
                display:"flex", alignItems:"center", justifyContent:"center", fontSize:20,
                transition:"background 0.3s" }}>👤</div>
              <div>
                <div style={{ fontSize:16, fontWeight:800, color:C.text }}>
                  Human-in-the-Loop (HITL) Review
                </div>
                <div style={{ fontSize:12, color:C.muted, marginTop:2 }}>
                  Controls whether high-risk audits pause for human approval before finalising.
                </div>
              </div>
            </div>

            {configLoading ? (
              <div style={{ display:"flex", alignItems:"center", gap:10,
                padding:"14px 18px", background:C.bg, borderRadius:10 }}>
                <div style={{ width:18, height:18, border:`2px solid ${C.accent}`,
                  borderTop:"2px solid transparent", borderRadius:"50%",
                  animation:"spin 0.8s linear infinite" }} />
                <span style={{ fontSize:13, color:C.muted }}>Loading configuration…</span>
              </div>
            ) : (
              <>
                {/* Toggle row */}
                <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between",
                  padding:"18px 22px",
                  background: hitlEnabled ? "#EFF6FF" : C.bg,
                  border:`1.5px solid ${hitlEnabled ? C.accent : C.border}`,
                  borderRadius:12, marginBottom:16, transition:"all 0.2s" }}>
                  <div>
                    <div style={{ fontSize:14, fontWeight:700, color:C.text }}>
                      HITL Reviews Globally{" "}
                      <span style={{
                        fontSize:11, fontWeight:700, padding:"2px 10px", borderRadius:20,
                        background: hitlEnabled ? "#DBEAFE" : "#F3F4F6",
                        color:      hitlEnabled ? C.accent  : C.muted,
                      }}>
                        {hitlEnabled ? "ENABLED" : "DISABLED"}
                      </span>
                    </div>
                    <div style={{ fontSize:12, color:C.muted, marginTop:4 }}>
                      {hitlEnabled
                        ? "High-risk audits will pause at the HITL checkpoint and await an auditor decision."
                        : "All audits will bypass the HITL checkpoint and complete automatically."}
                    </div>
                  </div>

                  {/* Toggle switch */}
                  <div
                    onClick={() => !configSaving && handleHitlToggle(!hitlEnabled)}
                    style={{
                      width:52, height:28, borderRadius:14, cursor: configSaving ? "default" : "pointer",
                      background: hitlEnabled ? C.accent : "#D1D5DB",
                      position:"relative", flexShrink:0, marginLeft:20,
                      transition:"background 0.25s",
                      opacity: configSaving ? 0.6 : 1,
                    }}>
                    <div style={{
                      position:"absolute", top:3,
                      left: hitlEnabled ? 26 : 3,
                      width:22, height:22, borderRadius:"50%", background:"#fff",
                      boxShadow:"0 1px 4px rgba(0,0,0,0.2)",
                      transition:"left 0.25s",
                    }} />
                  </div>
                </div>

                {configSaving && (
                  <div style={{ display:"flex", alignItems:"center", gap:8, fontSize:12,
                    color:C.muted, marginBottom:10 }}>
                    <div style={{ width:14, height:14, border:`2px solid ${C.accent}`,
                      borderTop:"2px solid transparent", borderRadius:"50%",
                      animation:"spin 0.8s linear infinite" }} />
                    Saving…
                  </div>
                )}
                {configSaveStatus === "saved" && (
                  <div style={{ fontSize:12, color:C.green, fontWeight:700, marginBottom:10 }}>
                    ✓ Configuration saved successfully
                  </div>
                )}
                {configSaveStatus === "error" && (
                  <div style={{ fontSize:12, color:C.red, fontWeight:700, marginBottom:10 }}>
                    ✗ Save failed: {configErr}
                  </div>
                )}
              </>
            )}

            {/* Behaviour explanation */}
            <div style={{ background:"#F8FAFD", border:`1px solid ${C.border}`, borderRadius:10, padding:"14px 18px" }}>
              <div style={{ fontSize:12, fontWeight:700, color:C.text, marginBottom:10 }}>
                How this setting affects the audit pipeline:
              </div>
              <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                {[
                  {
                    icon:"✅", label:"HITL Enabled (default)",
                    desc:"assess_risk sets hitl_required based on variance %, officer issues, and amount thresholds. High-risk audits pause at hitl_checkpoint.",
                    active: hitlEnabled,
                  },
                  {
                    icon:"⚡", label:"HITL Disabled",
                    desc:"assess_risk forces hitl_required = False for every audit regardless of risk level. All audits flow directly to explanation_agent → generate_report → END.",
                    active: !hitlEnabled,
                  },
                ].map(({ icon, label, desc, active }) => (
                  <div key={label} style={{
                    display:"flex", gap:10, padding:"10px 12px",
                    borderRadius:8, border:`1px solid ${active ? C.accent : C.border}`,
                    background: active ? "#EFF6FF" : "transparent",
                  }}>
                    <span style={{ fontSize:16, flexShrink:0 }}>{icon}</span>
                    <div>
                      <div style={{ fontSize:12, fontWeight:700, color: active ? C.accent : C.muted }}>{label}</div>
                      <div style={{ fontSize:11, color:C.muted, marginTop:2, lineHeight:1.5 }}>{desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── DATA MANAGEMENT TAB ── */}
      {activeTab === "data" && (
        <div style={{ background:C.card, border:`2px solid #FECACA`, borderRadius:14, padding:28 }}>

          <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:18 }}>
            <div style={{ width:38, height:38, borderRadius:10, background:"#FEE2E2",
              display:"flex", alignItems:"center", justifyContent:"center", fontSize:20 }}>🗑</div>
            <div>
              <div style={{ fontSize:16, fontWeight:800, color:"#991B1B" }}>Clear All Audit Data</div>
              <div style={{ fontSize:12, color:C.muted, marginTop:1 }}>
                Permanently deletes all audit cases and related policy data for this tenant.
              </div>
            </div>
          </div>

          <div style={{ background:"#FFF7ED", border:`1px solid #FED7AA`,
            borderRadius:10, padding:"14px 18px", marginBottom:20 }}>
            <div style={{ fontSize:12, fontWeight:700, color:"#92400E", marginBottom:8 }}>
              ⚠ The following data will be permanently erased:
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"6px 24px" }}>
              {["All Audit Cases","All Policy Records","Payroll Records","Variance Lines",
                "Agent Findings","HITL Reviews","Audit Reports","Policy Class Codes & Officers",
              ].map(item => (
                <div key={item} style={{ display:"flex", alignItems:"center", gap:6, fontSize:12, color:"#78350F" }}>
                  <span style={{ color:C.red, fontWeight:700 }}>✗</span> {item}
                </div>
              ))}
            </div>
          </div>

          {phase === "idle" && (
            <button onClick={() => setPhase("confirm")}
              style={{ background:C.red, color:"#fff", border:"none", borderRadius:10,
                padding:"11px 28px", fontSize:14, fontWeight:700, cursor:"pointer",
                display:"flex", alignItems:"center", gap:8 }}>
              🗑 Clear All Data
            </button>
          )}

          {phase === "confirm" && (
            <div style={{ background:"#FFF1F2", border:`1px solid #FECACA`, borderRadius:12, padding:20 }}>
              <div style={{ fontSize:14, fontWeight:700, color:"#991B1B", marginBottom:8 }}>
                Confirm Destructive Action
              </div>
              <div style={{ fontSize:13, color:C.text, marginBottom:14, lineHeight:1.6 }}>
                This action <strong>cannot be undone</strong>. Type{" "}
                <strong style={{ color:C.red }}>{CONFIRM_PHRASE}</strong> to continue:
              </div>
              <input value={confirmTxt} onChange={e => setConfirmTxt(e.target.value)}
                placeholder={CONFIRM_PHRASE}
                style={{ border:`2px solid ${confirmTxt === CONFIRM_PHRASE ? C.red : C.border}`,
                  borderRadius:8, padding:"10px 14px", fontSize:13, width:"100%",
                  outline:"none", boxSizing:"border-box", marginBottom:14,
                  fontFamily:"monospace", color:C.text,
                  background: confirmTxt === CONFIRM_PHRASE ? "#FFF1F2" : C.bg }} />
              <div style={{ display:"flex", gap:10 }}>
                <button disabled={confirmTxt !== CONFIRM_PHRASE} onClick={handleWipe}
                  style={{ background: confirmTxt === CONFIRM_PHRASE ? C.red : "#FCA5A5",
                    color:"#fff", border:"none", borderRadius:8, padding:"10px 22px",
                    fontSize:13, fontWeight:700,
                    cursor: confirmTxt === CONFIRM_PHRASE ? "pointer" : "default" }}>
                  ✗ Permanently Delete All Data
                </button>
                <button onClick={reset}
                  style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:8,
                    padding:"10px 22px", fontSize:13, fontWeight:600, cursor:"pointer", color:C.muted }}>
                  Cancel
                </button>
              </div>
            </div>
          )}

          {phase === "wiping" && (
            <div style={{ display:"flex", alignItems:"center", gap:14, padding:"16px 20px",
              background:"#FFF7ED", border:`1px solid #FED7AA`, borderRadius:10 }}>
              <div style={{ width:24, height:24, border:`3px solid ${C.amber}`,
                borderTop:"3px solid transparent", borderRadius:"50%",
                animation:"spin 0.8s linear infinite" }} />
              <div>
                <div style={{ fontSize:14, fontWeight:700, color:"#92400E" }}>Wiping data…</div>
                <div style={{ fontSize:12, color:C.muted, marginTop:2 }}>
                  Deleting all audit cases, policies, and related records from the database.
                </div>
              </div>
            </div>
          )}

          {phase === "done" && wipeResult && (
            <div style={{ background:"#F0FDF4", border:`1px solid #86EFAC`, borderRadius:12, padding:20 }}>
              <div style={{ fontSize:15, fontWeight:800, color:"#15803D", marginBottom:10 }}>
                ✓ Data cleared successfully
              </div>
              <div style={{ display:"flex", gap:12, flexWrap:"wrap", marginBottom:14 }}>
                {[
                  { label:"Audit Cases", value: wipeResult.deleted_cases    ?? 0 },
                  { label:"Policies",    value: wipeResult.deleted_policies  ?? 0 },
                  { label:"Total Rows",  value: wipeResult.total_deleted     ?? 0 },
                ].map(({ label, value }) => (
                  <div key={label} style={{ background:C.card, border:`1px solid ${C.border}`,
                    borderRadius:8, padding:"10px 18px", textAlign:"center" }}>
                    <div style={{ fontSize:22, fontWeight:800, color:C.text }}>{value}</div>
                    <div style={{ fontSize:11, color:C.muted, fontWeight:600, textTransform:"uppercase" }}>{label}</div>
                  </div>
                ))}
              </div>
              <div style={{ fontSize:12, color:C.muted, marginBottom:14 }}>
                Completed at {new Date().toLocaleTimeString()}. The UI has been refreshed.
              </div>
              <button onClick={reset}
                style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:8,
                  padding:"8px 18px", fontSize:13, fontWeight:600, cursor:"pointer", color:C.muted }}>
                Close
              </button>
            </div>
          )}

          {phase === "error" && (
            <div style={{ background:"#FFF1F2", border:`1px solid #FECACA`, borderRadius:12, padding:20 }}>
              <div style={{ fontSize:14, fontWeight:800, color:"#991B1B", marginBottom:6 }}>
                ✗ Operation failed
              </div>
              <div style={{ fontSize:13, color:C.text, marginBottom:14,
                background:"#FEE2E2", padding:"10px 14px", borderRadius:8, fontFamily:"monospace" }}>
                {wipeErr}
              </div>
              <button onClick={reset}
                style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:8,
                  padding:"8px 18px", fontSize:13, fontWeight:600, cursor:"pointer", color:C.muted }}>
                Dismiss
              </button>
            </div>
          )}
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

export default Administration;