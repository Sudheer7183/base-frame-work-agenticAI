import { useState, useEffect, useCallback } from "react";
import { listAuditCases } from "../../api/wcAuditAPI";
import { useWCRoles } from "../../hooks/useWCRoles";

// Layout
import Sidebar    from "./layout/Sidebar";
import Topbar     from "./layout/Topbar";
import PageHeader from "./layout/PageHeader";

// Shared UI
import { AccessDenied } from "./ui";

// Screens
import Dashboard        from "./screens/Dashboard";
import PoliciesScreen   from "./screens/PoliciesScreen";
import VarianceAnalysis from "./screens/VarianceAnalysis";
import AIAuditScreen    from "./screens/AIAuditScreen";
import AuditDetail      from "./screens/AuditDetail";
import DataUpload       from "./screens/DataUpload";
import Administration   from "./screens/Administration";
import ReportsScreen    from "./screens/ReportsScreen";

// ── Page title / subtitle map ─────────────────────────────────────────────────
const PAGE_TITLES = {
  dashboard:      { title:"Dashboard",         sub:"Workers' Compensation Policy Audit Overview" },
  policies:       { title:"Policies",          sub:"Manage and review all active policy audits" },
  variance:       { title:"Variance Analysis", sub:"EST Exposure vs. Earned Exposure and EST YTD Premium vs. Earned Premium explorer" },
  "ai-audit":     { title:"AI Audit Engine",   sub:"Multi-agent LangGraph orchestration & analysis" },
  reports:        { title:"Reports",           sub:"Generate and export audit documentation" },
  upload:         { title:"Data Upload",       sub:"Ingest payroll submissions and policy files" },
  "audit-detail": { title:"Policy Review",     sub:"Detailed audit workflow and HITL decisions" },
  Administration: { title:"Adminstartion",     sub:"To create users and to do configurations" },
};

export default function WCAuditApp() {
  // ── Routing & UI state ────────────────────────────────────────────────────
  const [screen,       setScreen]       = useState("dashboard");
  const [selectedCase, setSelectedCase] = useState(null);
  const [collapsed,    setCollapsed]    = useState(false);
  const [notifOpen,    setNotifOpen]    = useState(false);

  // ── Data state ────────────────────────────────────────────────────────────
  const [cases,        setCases]        = useState([]);
  const [loadingCases, setLoadingCases] = useState(true);
  const [activeCaseId, setActiveCaseId] = useState(null);
  const [batchCaseIds, setBatchCaseIds] = useState([]);

  // ── Role-based access ─────────────────────────────────────────────────────
  const {
    canViewReports,
    canUpload,
    canApproveHITL,
    canViewAllTenants,
    displayRole,
    isSuperAdmin,
    canViewAIAudit,
    canViewVariance,
    canViewDashboard,
    canViewPolicies,
    canViewAdministartion,
  } = useWCRoles();

  // ── Nav items ─────────────────────────────────────────────────────────────
  const allNavItems = [
    { id:"dashboard",      label:"Dashboard",        icon:"⊞", visible:canViewDashboard     },
    { id:"policies",       label:"Policies",          icon:"📋", visible:canViewPolicies      },
    { id:"variance",       label:"Variance Analysis", icon:"📈", visible:canViewVariance      },
    { id:"ai-audit",       label:"AI Audit",          icon:"🤖", visible:canViewAIAudit       },
    { id:"reports",        label:"Reports",           icon:"📊", visible:canViewReports       },
    { id:"upload",         label:"Data Ingestion",    icon:"⬆",  visible:canUpload            },
    { id:"Administration", label:"Administration",    icon:"⚙",  visible:canViewAdministartion },
  ];

  const navItems = allNavItems.filter(item =>
    item.visible === undefined || item.visible === true
  );

  // Guard: if the current screen is not in the visible nav, fall back to dashboard
  useEffect(() => {
    const visibleIds = new Set(navItems.map(n => n.id));
    if (!visibleIds.has(screen) && screen !== "audit-detail") {
      setScreen("dashboard");
    }
  }, [navItems, screen]);

  // ── Data fetching ─────────────────────────────────────────────────────────
  const refreshCases = useCallback(async () => {
    setLoadingCases(true);
    try {
      const data = await listAuditCases();
      setCases(data);
    } catch (err) {
      console.error("[WCAuditApp] Failed to load cases", err);
    } finally {
      setLoadingCases(false);
    }
  }, []);

  useEffect(() => { refreshCases(); }, [refreshCases]);

  // ── Notifications derived from live cases ─────────────────────────────────
  const notifications = [
    ...cases.filter(c => c.status === "error").map(c => ({
      id:c.audit_case_id, type:"alert",
      msg:`Error in case ${c.policy_number}: ${c.errors || "unknown error"}`, time:"recent",
    })),
    ...cases.filter(c => c.hitl_required && c.status !== "completed").map(c => ({
      id:`h-${c.audit_case_id}`, type:"warning",
      msg:`HITL review required for ${c.policy_number}`, time:"pending",
    })),
    ...cases.filter(c => c.status === "completed").slice(0, 2).map(c => ({
      id:`d-${c.audit_case_id}`, type:"info",
      msg:`Audit completed for ${c.policy_number}`, time:"done",
    })),
  ].slice(0, 5);

  const cur = PAGE_TITLES[screen] || PAGE_TITLES.dashboard;

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div style={{ display:"flex", height:"100vh", fontFamily:"'DM Sans','Segoe UI',sans-serif",
      background:"#F0F4FA", overflow:"hidden" }}>

      {/* Sidebar */}
      <Sidebar
        screen={screen}
        setScreen={setScreen}
        collapsed={collapsed}
        setCollapsed={setCollapsed}
        navItems={navItems}
      />

      {/* Main area */}
      <div style={{ flex:1, display:"flex", flexDirection:"column", overflow:"hidden" }}>

        {/* Topbar */}
        <Topbar
          notifications={notifications}
          notifOpen={notifOpen}
          setNotifOpen={setNotifOpen}
        />

        {/* Page header */}
        <PageHeader title={cur.title} sub={cur.sub} />

        {/* Screen content */}
        <div style={{ flex:1, overflowY:"auto", padding:24 }}>

          {screen === "dashboard" && (
            <Dashboard
              setScreen={setScreen}
              setSelectedCase={setSelectedCase}
              cases={cases}
            />
          )}

          {screen === "policies" && (
            <PoliciesScreen
              setScreen={setScreen}
              setSelectedCase={setSelectedCase}
              cases={cases}
              onRefresh={refreshCases}
            />
          )}

          {screen === "variance" && (
            <VarianceAnalysis cases={cases} />
          )}

          {screen === "ai-audit" && (
            <AIAuditScreen
              cases={cases}
              onCaseCreated={refreshCases}
              activeCaseId={activeCaseId}
              batchCaseIds={batchCaseIds}
            />
          )}

          {screen === "reports" && (
            canViewReports
              ? <ReportsScreen cases={cases} />
              : <AccessDenied requiredRole="Provider or above" />
          )}

          {screen === "upload" && (
            <DataUpload
              onAuditStarted={(id) => {
                setActiveCaseId(id);
                refreshCases();
                setScreen("ai-audit");
              }}
              onBatchStarted={(ids) => {
                setBatchCaseIds(ids);
                refreshCases();
                setScreen("ai-audit");
              }}
            />
          )}

          {screen === "Administration" && (
            isSuperAdmin
              ? <Administration setScreen={setScreen} onDataCleared={refreshCases} />
              : <AccessDenied requiredRole="Super Admin" />
          )}

          {screen === "audit-detail" && (
            <AuditDetail
              auditCase={selectedCase}
              setScreen={setScreen}
              onHITLDecision={refreshCases}
            />
          )}
        </div>
      </div>

      {/* Notification click-away overlay */}
      {notifOpen && (
        <div onClick={() => setNotifOpen(false)}
          style={{ position:"fixed", inset:0, zIndex:99 }} />
      )}
    </div>
  );
}