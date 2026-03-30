/**
 * Workers' Compensation Audit – API Service
 * Wraps all /api/v1/wc-audit/* endpoints.
 * Reuses the existing tenant-aware axios interceptor pattern
 * (same pattern as agentBuilderAPI.js).
 *
 * File: frontend/react-admin/src/api/wcAuditAPI.js
 */

import axios from "axios";

const API_BASE_URL = "http://localhost:8002/api/v1";

// ── Tenant-aware axios client (mirrors agentBuilderAPI.js pattern) ────────────
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;

  const raw = localStorage.getItem("current_tenant") ||
               localStorage.getItem("tenant_id") ||
               sessionStorage.getItem("tenantId") ||
               sessionStorage.getItem("tenant_id");

  if (raw) {
    try {
      const parsed = JSON.parse(raw);
      config.headers["X-Tenant-ID"] = parsed.slug || parsed;
    } catch {
      config.headers["X-Tenant-ID"] = raw;
    }
  }
  return config;
});


// ── Upload Files ──────────────────────────────────────────────────────────────
/**
 * Upload the three source files for an audit session.
 * @param {File} payrollFile   - Payroll Excel (.xlsx)
 * @param {File} policyXml    - Policy XML (.xml)
 * @param {File} auditMeta    - Audit metadata Excel (.xlsx)
 * @returns {{ session_id, payroll_file_path, policy_xml_path, audit_meta_file_path }}
 */
export async function uploadAuditFiles(payrollFile, policyXml, auditMeta) {
  const form = new FormData();
  form.append("payroll_file", payrollFile);
  form.append("policy_xml",   policyXml);
  form.append("audit_meta",   auditMeta);

  const { data } = await apiClient.post("/wc-audit/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}


// ── Start Audit ───────────────────────────────────────────────────────────────
/**
 * Kick off the LangGraph audit workflow.
 * @param {object} params
 *   - policy_number        {string}
 *   - payroll_file_path    {string}  from uploadAuditFiles response
 *   - policy_xml_path      {string}
 *   - audit_meta_file_path {string}
 *   - tenant_id            {string}  optional; interceptor also sets header
 * @returns {{ audit_case_id, status, message }}
 */
export async function startAudit(params) {
  const { data } = await apiClient.post("/wc-audit/start", params);
  return data;
}


// ── Poll Audit Status ─────────────────────────────────────────────────────────
/**
 * Poll the status of a running or completed audit.
 * @param {number|string} auditCaseId
 * @returns {AuditStatusResponse}
 *   { audit_case_id, policy_number, status, risk_level, recommendation,
 *     hitl_required, variance, variance_pct, errors, created_at,
 *     overall_variance, class_code_variance, ai_narrative, agent_logs, ... }
 */
export async function getAuditStatus(auditCaseId) {
  const { data } = await apiClient.get(`/wc-audit/status/${auditCaseId}`);
  return data;
}


// ── List Audit Cases ──────────────────────────────────────────────────────────
/**
 * Retrieve all audit cases for the current tenant.
 * Requires the backend to expose GET /wc-audit/cases (add if missing).
 * Falls back to an empty array so the UI degrades gracefully.
 */
export async function listAuditCases() {
  try {
    const { data } = await apiClient.get("/wc-audit/cases");
    return Array.isArray(data) ? data : data.cases ?? [];
  } catch {
    return [];
  }
}


// ── HITL Decision ─────────────────────────────────────────────────────────────
/**
 * Submit a human-in-the-loop decision (approve / reject / override).
 * @param {number} auditCaseId
 * @param {{ decision: "approve"|"reject", notes?: string }} payload
 */
export async function submitHITLDecision(auditCaseId, payload) {
  const { data } = await apiClient.post(
    `/wc-audit/${auditCaseId}/hitl-decision`,
    payload
  );
  return data;
}


// ── Download Report ───────────────────────────────────────────────────────────
/**
 * Trigger report download. Opens the file in a new tab.
 * @param {number} auditCaseId
 */
export async function downloadReport(auditCaseId, filename) {
  try {
    const response = await apiClient.get(
      `/wc-audit/report/${auditCaseId}/download`,
      { responseType: "blob" }
    );
 
    // Extract filename from Content-Disposition if server provides it
    const disposition = response.headers?.["content-disposition"] || "";
    const serverName  = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)?.[1]
                          ?.replace(/['"]/g, "");
    const saveAs = filename || serverName || `wc_audit_report_${auditCaseId}.xlsx`;
 
    // Create a temporary blob URL and programmatically click it to save
    const url  = URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href     = url;
    link.download = saveAs;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error("[downloadReport] Failed:", err);
    alert(`Report download failed: ${err.response?.data?.detail || err.message}`);
  }
}


// ── Polling Helper ────────────────────────────────────────────────────────────
/**
 * Poll getAuditStatus every `intervalMs` until status is terminal
 * ("completed" | "error" | "hitl_pending").
 * @param {number} auditCaseId
 * @param {function} onUpdate  - called with each status response
 * @param {number}   intervalMs - default 3 000 ms
 * @returns {function} stop  - call to cancel polling
 */
export function pollAuditStatus(auditCaseId, onUpdate, intervalMs = 3000) {
  // Terminal states that stop fast polling — hitl_pending slows down but keeps going
  const TERMINAL_STOP = new Set(["completed", "error"]);
  const TERMINAL_SLOW = new Set(["hitl_pending"]);  // 10s interval while waiting for HITL
  let active = true;
  let currentInterval = intervalMs;

  const tick = async () => {
    if (!active) return;
    try {
      const status = await getAuditStatus(auditCaseId);
      onUpdate(status);

      if (!active) return;

      if (TERMINAL_STOP.has(status.status)) {
        // Fully done — stop polling
        return;
      } else if (TERMINAL_SLOW.has(status.status)) {
        // HITL waiting — slow down to 10s to avoid hammering the backend
        currentInterval = 10000;
        setTimeout(tick, currentInterval);
      } else {
        // Still running — use normal interval
        currentInterval = intervalMs;
        setTimeout(tick, currentInterval);
      }
    } catch (err) {
      console.error("[wcAuditAPI] polling error:", err);
      if (active) setTimeout(tick, currentInterval * 2);
    }
  };

  tick();
  return () => { active = false; };
}


// ── List policies available in Mock API ───────────────────────────────────────
/**
 * Fetch all available policies from the Mock Data Source API.
 * @returns {{ count, policies: [{policy_number, insured_name, status, files, ...}] }}
 */
export async function listMockAPIPolicies() {
  const MOCK_API = import.meta.env.VITE_MOCK_API_URL || "http://localhost:9000";
  const { data } = await axios.get(`${MOCK_API}/api/v1/policies?status=available`);
  return data;
}

// ── Start Audit from API source ───────────────────────────────────────────────
/**
 * Queue a single policy audit using the Mock API as data source.
 * No file upload needed — the backend fetches data from Mock API itself.
 * @param {string} policyNumber
 * @returns {{ audit_case_id, status, message }}
 */
export async function startAuditFromAPI(policyNumber) {
  const { data } = await apiClient.post("/wc-audit/start-from-api", {
    policy_number: policyNumber,
  });
  return data;
}


export async function startBatchAuditFromAPI(policyNumbers = []) {
  const { data } = await apiClient.post("/wc-audit/start-batch-from-api", {
    policy_numbers: policyNumbers.length ? policyNumbers : undefined,
  });
  return data;
}
 