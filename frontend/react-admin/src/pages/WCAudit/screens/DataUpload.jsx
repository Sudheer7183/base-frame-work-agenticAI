import { useState } from "react";
import {
  uploadAuditFiles,
  startAudit,
  startBatchAuditFromAPI,
  previewAPIPolicies,
} from "../../../api/wcAuditAPI";
import C from "../constants/colors";
import { StatusBadge, SectionHeader } from "../ui";
import SkippedPoliciesBanner from "./SkippedPoliciesBanner";
import FileDropZone from "./FileDropZone";

// Local money formatter — uses minimumFractionDigits:0 intentionally
const money = (n) =>
  n == null ? "—" : `$${Number(n).toLocaleString(undefined, { minimumFractionDigits: 0 })}`;

const REQUIRED_FIELDS = ["policy_number", "insured_name", "state_code", "effective_date", "expiration_date"];
// Backend returns "—" (em dash) for missing values — treat it the same as null/""
const isMissing = (v) => !v || String(v).trim() === "" || String(v).trim() === "—";

function DataUpload({ onAuditStarted, onBatchStarted }) {
  // ── File-upload state ──────────────────────────────────────────────
  const [payrollFile,  setPayrollFile]  = useState(null);
  const [policyFile,   setPolicyFile]   = useState(null);
  const [metaFile,     setMetaFile]     = useState(null);
  const [policyNumber, setPolicyNumber] = useState("");
  const [dragging,     setDragging]     = useState(null);
  const [uploading,    setUploading]    = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [starting,     setStarting]     = useState(false);
  const [started,      setStarted]      = useState(null);
  const [error,        setError]        = useState(null);

  // ── API Batch state (two-step) ─────────────────────────────────────
  const [apiMode,         setApiMode]         = useState(true);
  const [previewing,      setPreviewing]      = useState(false);
  const [previewData,     setPreviewData]     = useState(null);
  const [previewError,    setPreviewError]    = useState(null);
  const [starting2,       setStarting2]       = useState(false);
  const [batchResult,     setBatchResult]     = useState(null);
  const [batchError,      setBatchError]      = useState(null);
  const [skippedPolicies, setSkippedPolicies] = useState([]);

  const allReady = payrollFile && policyFile && metaFile && policyNumber.trim();

  // ── File upload handlers ───────────────────────────────────────────
  const handleUpload = async () => {
    if (!allReady) return;
    setUploading(true); setError(null);
    try {
      const result = await uploadAuditFiles(payrollFile, policyFile, metaFile);
      setUploadResult(result);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleStart = async () => {
    if (!uploadResult) return;
    setStarting(true); setError(null);
    try {
      const result = await startAudit({
        policy_number:        policyNumber.trim(),
        payroll_file_path:    uploadResult.payroll_file_path,
        policy_xml_path:      uploadResult.policy_xml_path,
        audit_meta_file_path: uploadResult.audit_meta_file_path,
      });
      setStarted(result);
      onAuditStarted?.(result.audit_case_id);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setStarting(false);
    }
  };

  // ── Step 1: Preview policies ───────────────────────────────────────
  const handlePreview = async () => {
    setPreviewing(true); setPreviewError(null); setPreviewData(null); setBatchResult(null);
    try {
      const result = await previewAPIPolicies();
      setPreviewData(result);
    } catch (err) {
      setPreviewError(err.response?.data?.detail || err.message || "Preview failed");
    } finally {
      setPreviewing(false);
    }
  };

  // ── Step 2: Start the batch ────────────────────────────────────────
  const handleStartBatch = async () => {
    if (!previewData?.policies?.length) return;

    const valid   = [];
    const skipped = [];

    previewData.policies.forEach(p => {
      if (!p.available) {
        skipped.push({ ...p, _skipReason: "Not found / unavailable in Mock API" });
        return;
      }
      const missingFields = REQUIRED_FIELDS.filter(f => isMissing(p[f]));
      if (missingFields.length > 0) {
        skipped.push({ ...p, _skipReason: `Missing required fields: ${missingFields.join(", ")}` });
      } else {
        valid.push(p.policy_number);
      }
    });

    setSkippedPolicies(skipped);

    if (valid.length === 0) {
      setBatchError("No processable policies found. All records are either unavailable or missing required fields.");
      return;
    }

    setStarting2(true); setBatchError(null);
    try {
      const result = await startBatchAuditFromAPI(valid);
      setBatchResult(result);
      onBatchStarted?.(result.cases.map(c => c.audit_case_id));
    } catch (err) {
      setBatchError(err.response?.data?.detail || err.message || "Batch start failed");
    } finally {
      setStarting2(false);
    }
  };

  const handleReset = () => {
    setPreviewData(null); setPreviewError(null);
    setBatchResult(null); setBatchError(null);
    setSkippedPolicies([]);
  };

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:20 }}>

      {/* ── Source selector tabs ──────────────────────────────────── */}
      <div style={{ display:"flex", gap:0, background:C.bg, borderRadius:12,
        border:`1px solid ${C.border}`, overflow:"hidden", alignSelf:"flex-start" }}>
        {[
          { key:true, label:"🔌  Fetch from API", desc:"Pull all policies from Mock API" },
        ].map(tab => (
          <button key={String(tab.key)} onClick={() => { setApiMode(tab.key); handleReset(); }}
            style={{ padding:"12px 28px", border:"none", cursor:"pointer",
              background: apiMode === tab.key
                ? `linear-gradient(135deg, ${C.accent}, ${C.teal})`
                : "transparent",
              color: apiMode === tab.key ? "#fff" : C.muted,
              fontWeight:700, fontSize:13, transition:"all 0.2s",
              borderRight:`1px solid ${C.border}` }}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── API FETCH TAB ── */}
      {apiMode && (
        <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:28 }}>

          {/* IDLE: nothing loaded yet */}
          {!previewData && !batchResult && (
            <>
              <SectionHeader
                title="Fetch All Policies from API"
                sub="Preview available policies before starting the batch audit" />

              <div style={{ display:"flex", gap:14, marginBottom:24 }}>
                {[
                  { icon:"🔍", title:"Preview First",    desc:"Loads all policy details from the Mock API so you can review before committing" },
                  { icon:"⚡", title:"Cache & Queue",    desc:"Policy configs are cached in Redis — worker only fetches payroll data" },
                  { icon:"🤖", title:"Full Pipeline",    desc:"Each policy runs the complete LangGraph pipeline with HITL when required" },
                ].map((item, i) => (
                  <div key={i} style={{ flex:1, background:C.bg, borderRadius:12,
                    padding:"16px 18px", border:`1px solid ${C.border}` }}>
                    <div style={{ fontSize:22, marginBottom:8 }}>{item.icon}</div>
                    <div style={{ fontSize:13, fontWeight:700, color:C.text, marginBottom:4 }}>{item.title}</div>
                    <div style={{ fontSize:12, color:C.muted, lineHeight:1.5 }}>{item.desc}</div>
                  </div>
                ))}
              </div>

              {previewError && (
                <div style={{ padding:"10px 14px", background:"#FEE2E2", borderRadius:8,
                  border:`1px solid #FECACA`, fontSize:13, color:"#991B1B", marginBottom:16 }}>
                  ✗ {previewError}
                </div>
              )}

              <button disabled={previewing} onClick={handlePreview}
                style={{
                  background: previewing ? C.border : `linear-gradient(135deg, ${C.accent}, ${C.teal})`,
                  color:"#fff", border:"none", borderRadius:10, padding:"13px 32px",
                  fontSize:15, fontWeight:800, cursor:previewing ? "default" : "pointer",
                  display:"flex", alignItems:"center", gap:10, transition:"all 0.2s",
                  opacity:previewing ? 0.7 : 1,
                  boxShadow:previewing ? "none" : "0 4px 16px rgba(30,111,217,0.3)",
                }}>
                {previewing
                  ? <><span style={{ fontSize:18 }}>⚙️</span> Loading Policy Details…</>
                  : <><span style={{ fontSize:18 }}>🔍</span> Fetch Policies from API</>
                }
              </button>
            </>
          )}

          {/* STEP 1 DONE: Policy preview table */}
          {previewData && !batchResult && (
            <div style={{ display:"flex", flexDirection:"column", gap:16 }}>

              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center",
                flexWrap:"wrap", gap:12 }}>
                <div>
                  <h3 style={{ margin:0, fontSize:17, fontWeight:800, color:C.text }}>
                    Policy Preview — {previewData.total} Policies Found
                  </h3>
                  <div style={{ fontSize:12, color:C.muted, marginTop:3 }}>
                    Policy details loaded and cached. Review below, then start the batch.
                  </div>
                </div>
                <div style={{ display:"flex", gap:10 }}>
                  <button onClick={handleReset}
                    style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:8,
                      padding:"7px 14px", fontSize:12, cursor:"pointer", color:C.muted, fontWeight:600 }}>
                    ↺ Reload
                  </button>
                  <button onClick={handleStartBatch} disabled={starting2}
                    style={{
                      background: starting2 ? "#86EFAC" : C.green,
                      color:"#fff", border:"none", borderRadius:10,
                      padding:"10px 24px", fontSize:14, fontWeight:800,
                      cursor: starting2 ? "default" : "pointer",
                      display:"flex", alignItems:"center", gap:8,
                      boxShadow: starting2 ? "none" : "0 4px 14px rgba(16,185,129,0.35)",
                      transition:"all 0.2s",
                    }}>
                    {starting2
                      ? <><span>⚙️</span> Queuing…</>
                      : <><span>▶</span> Start Batch Audit ({previewData.policies.filter(p => p.available && REQUIRED_FIELDS.every(f => !isMissing(p[f]))).length} processable)</>
                    }
                  </button>
                </div>
              </div>

              {batchError && (
                <div style={{ padding:"10px 14px", background:"#FEE2E2", borderRadius:8,
                  border:`1px solid #FECACA`, fontSize:13, color:"#991B1B" }}>
                  ✗ {batchError}
                </div>
              )}

              {skippedPolicies.length > 0 && !batchResult && (
                <SkippedPoliciesBanner policies={skippedPolicies} />
              )}

              {/* KPI chips */}
              <div style={{ display:"flex", gap:12 }}>
                {[
                  { label:"Will Process",  value: previewData.policies.filter(p => p.available && REQUIRED_FIELDS.every(f => !isMissing(p[f]))).length, color:C.green  },
                  { label:"Unavailable",   value: previewData.policies.filter(p => !p.available).length, color:C.red    },
                  { label:"Missing Data",  value: previewData.policies.filter(p => p.available && REQUIRED_FIELDS.some(f => isMissing(p[f]))).length, color:C.amber  },
                  { label:"States",        value: new Set(previewData.policies.map(p => p.state_code).filter(Boolean)).size, color:C.accent },
                ].map(({ label, value, color }) => (
                  <div key={label} style={{ background:C.bg, borderRadius:10,
                    padding:"10px 18px", border:`1px solid ${C.border}`, textAlign:"center" }}>
                    <div style={{ fontSize:20, fontWeight:800, color }}>{value}</div>
                    <div style={{ fontSize:11, color:C.muted, fontWeight:600 }}>{label}</div>
                  </div>
                ))}
              </div>

              {/* Policy detail table */}
              <div style={{ border:`1px solid ${C.border}`, borderRadius:12, overflow:"hidden" }}>
                <div style={{ display:"grid",
                  gridTemplateColumns:"1.6fr 2fr 1fr 1fr 0.8fr 1.2fr 1fr 0.7fr",
                  background:"#F8FAFD", borderBottom:`1px solid ${C.border}`,
                  padding:"10px 16px", gap:8 }}>
                  {["Policy Number","Insured Name","Eff. Date","Exp. Date","State","Class Codes","Est Premium","Freq"].map(h => (
                    <div key={h} style={{ fontSize:10, fontWeight:700, color:C.muted,
                      textTransform:"uppercase", letterSpacing:0.7 }}>{h}</div>
                  ))}
                </div>

                <div style={{ maxHeight:380, overflowY:"auto" }}>
                  {previewData.policies.map((p, i) => (
                    <div key={p.policy_number}
                      style={{
                        display:"grid",
                        gridTemplateColumns:"1.6fr 2fr 1fr 1fr 0.8fr 1.2fr 1fr 0.7fr",
                        padding:"11px 16px", gap:8, alignItems:"center",
                        borderBottom:`1px solid ${C.border}`,
                        background: !p.available
                          ? "#FFF7F7"
                          : (p.available && REQUIRED_FIELDS.some(f => isMissing(p[f])))
                            ? "#FFFBEB"
                            : i % 2 === 0 ? "#fff" : C.bg,
                        transition:"background 0.12s",
                      }}
                      onMouseEnter={e => {
                        if (!p.available) return;
                        const hasMissing = REQUIRED_FIELDS.some(f => isMissing(p[f]));
                        e.currentTarget.style.background = hasMissing ? "#FEF3C7" : "#EEF2FF";
                      }}
                      onMouseLeave={e => {
                        const hasMissing = REQUIRED_FIELDS.some(f => isMissing(p[f]));
                        e.currentTarget.style.background = !p.available ? "#FFF7F7"
                          : hasMissing ? "#FFFBEB"
                          : i % 2 === 0 ? "#fff" : C.bg;
                      }}
                    >
                      <div style={{ fontSize:13, fontWeight:700,
                        color: p.available ? C.accent : C.muted,
                        display:"flex", alignItems:"center", gap:6 }}>
                        {!p.available && <span title="Not found in Mock API" style={{ color:C.red }}>⚠</span>}
                        {p.available && REQUIRED_FIELDS.some(f => isMissing(p[f])) && (
                          <span title={`Missing: ${REQUIRED_FIELDS.filter(f => isMissing(p[f])).join(", ")}`}
                            style={{ color:C.amber }}>⚠</span>
                        )}
                        {p.policy_number}
                      </div>
                      <div style={{ fontSize:12, color:C.text, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
                        {p.insured_name || "—"}
                      </div>
                      <div style={{ fontSize:12, color:C.muted }}>{p.effective_date || "—"}</div>
                      <div style={{ fontSize:12, color:C.muted }}>{p.expiration_date || "—"}</div>
                      <div style={{ fontSize:12, fontWeight:700, color:C.text }}>{p.state_code || "—"}</div>
                      <div style={{ fontSize:11, color:C.muted, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
                        {p.class_codes || "—"}
                      </div>
                      <div style={{ fontSize:12, fontWeight:600, color:C.text }}>
                        {p.est_premium ? money(p.est_premium) : "—"}
                      </div>
                      <div style={{ fontSize:11, color:C.muted }}>{p.payroll_frequency || "—"}</div>
                    </div>
                  ))}
                </div>
              </div>

              {previewData.errors?.length > 0 && (
                <div style={{ padding:"12px 16px", background:"#FEF3C7", borderRadius:10,
                  border:`1px solid ${C.amber}`, fontSize:12, color:"#92400E" }}>
                  ⚠️ <strong>{previewData.errors.length} policy(ies) unavailable:</strong>
                  <ul style={{ margin:"4px 0 0 16px", padding:0 }}>
                    {previewData.errors.map((e, i) => <li key={i}>{e}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* STEP 2 DONE: Batch queued */}
          {batchResult && (
            <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
              <div style={{ padding:"16px 20px", background:"#DCFCE7", borderRadius:12,
                border:`1px solid #86EFAC`, display:"flex", alignItems:"center", gap:14 }}>
                <span style={{ fontSize:28 }}>🚀</span>
                <div>
                  <div style={{ fontSize:15, fontWeight:800, color:"#15803D" }}>
                    {batchResult.total_queued} policies queued for audit!
                  </div>
                  <div style={{ fontSize:12, color:"#166534", marginTop:2 }}>
                    Batch ID: {batchResult.batch_id} — Monitor progress on the AI Audit screen.
                  </div>
                </div>
              </div>

              <div style={{ border:`1px solid ${C.border}`, borderRadius:12, overflow:"hidden" }}>
                <div style={{ display:"grid", gridTemplateColumns:"1.6fr 2fr 1fr 0.8fr 1fr",
                  background:"#F8FAFD", borderBottom:`1px solid ${C.border}`,
                  padding:"10px 16px", gap:8 }}>
                  {["Policy Number","Insured Name","Case ID","State","Status"].map(h => (
                    <div key={h} style={{ fontSize:10, fontWeight:700, color:C.muted,
                      textTransform:"uppercase", letterSpacing:0.7 }}>{h}</div>
                  ))}
                </div>
                <div style={{ maxHeight:300, overflowY:"auto" }}>
                  {batchResult.cases.map((c, i) => {
                    const detail = previewData?.policies.find(p => p.policy_number === c.policy_number);
                    return (
                      <div key={c.audit_case_id}
                        style={{ display:"grid", gridTemplateColumns:"1.6fr 2fr 1fr 0.8fr 1fr",
                          padding:"11px 16px", gap:8, alignItems:"center",
                          borderBottom:`1px solid ${C.border}`,
                          background: i % 2 === 0 ? "#fff" : C.bg }}>
                        <div style={{ fontSize:13, fontWeight:700, color:C.accent }}>{c.policy_number}</div>
                        <div style={{ fontSize:12, color:C.muted, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
                          {detail?.insured_name || "—"}
                        </div>
                        <div style={{ fontSize:13, color:C.text }}>#{c.audit_case_id}</div>
                        <div style={{ fontSize:12, fontWeight:700, color:C.text }}>{detail?.state_code || "—"}</div>
                        <span><StatusBadge status="pending" /></span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {batchResult.errors?.length > 0 && (
                <div style={{ padding:"12px 16px", background:"#FEF3C7", borderRadius:10,
                  border:`1px solid ${C.amber}`, fontSize:12, color:"#92400E" }}>
                  ⚠️ <strong>{batchResult.errors.length} failed to queue:</strong>
                  <ul style={{ margin:"4px 0 0 16px", padding:0 }}>
                    {batchResult.errors.map((e, i) => <li key={i}>{e}</li>)}
                  </ul>
                </div>
              )}

              <button onClick={handleReset}
                style={{ alignSelf:"flex-start", background:C.bg,
                  border:`1px solid ${C.border}`, borderRadius:8,
                  padding:"7px 16px", fontSize:12, cursor:"pointer", color:C.muted }}>
                ↺ Run another batch
              </button>
            </div>
          )}
        </div>
      )}

      {/* How it works */}
      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>
        <SectionHeader title="How it works"
          sub={apiMode ? "Two-step API batch audit pipeline" : "The 3-step file audit pipeline"} />
        <div style={{ display:"flex", gap:16 }}>
          {(apiMode ? [
            { n:"1", title:"Preview",    desc:"Backend fetches all policies + configs from Mock API. Details shown in a table for review.", icon:"🔍" },
            { n:"2", title:"Queue",      desc:"Confirmed policies are pushed to the Redis audit queue with configs pre-cached.", icon:"⚡" },
            { n:"3", title:"Process",    desc:"Worker processes each policy — fetches payroll data only (config already cached). HITL when high-risk.", icon:"🤖" },
          ] : [
            { n:"1", title:"Upload",  desc:"Drop payroll Excel, policy XML, and audit metadata. Files are securely processed.", icon:"📂" },
            { n:"2", title:"Analyze", desc:"LangGraph multi-agent pipeline: Ingestion → Specialist agents → Premium calculation → AI narrative.", icon:"🤖" },
            { n:"3", title:"Review",  desc:"Auditor reviews variance report, HITL decisions, and AI explanation. Download final report.", icon:"📊" },
          ]).map(s => (
            <div key={s.n} style={{ flex:1, background:C.bg, borderRadius:12, padding:"18px 20px" }}>
              <div style={{ width:32, height:32, borderRadius:"50%", background:C.accent,
                color:"#fff", display:"flex", alignItems:"center", justifyContent:"center",
                fontWeight:800, fontSize:14, marginBottom:12 }}>{s.n}</div>
              <div style={{ fontSize:16 }}>{s.icon}</div>
              <div style={{ fontSize:14, fontWeight:700, color:C.text, marginBottom:6 }}>{s.title}</div>
              <div style={{ fontSize:12, color:C.muted, lineHeight:1.6 }}>{s.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default DataUpload;