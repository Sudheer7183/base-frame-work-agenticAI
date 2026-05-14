// import React from 'react';
// import {
//   BrowserRouter, Routes, Route, Navigate,
//   useNavigate, useLocation
// } from 'react-router-dom';
// import { AuthProvider, ProtectedRoute, useAuth } from './auth';
// import LoginPage from './LoginPage';
// import TenantAdminInterface from './tenant-admin';
// import AgentList from './AgentList';
// import { Database, Bot, Users } from 'lucide-react';

// import InviteUserPage from './pages/InviteUserPage';
// import AcceptInvitationPage from './pages/AcceptInvitationPage';
// import UserManagementTable from './components/UserManagementTable';
// import AgentBuilder from './components/AgentBuilder/AgentBuilder';
// import { Layout } from './components/Layout';
// import WCAuditApp from './pages/WCAudit';
// import CarrierPortalApp from './pages/WCAudit/carrier-portal-v2/CarrierPortalApp';


// // ─── useTenantFromSubdomain ───────────────────────────────────────────────────
// //
// // Reads the tenant slug purely from the subdomain of the current hostname.
// //
// // Local dev examples:
// //   acme.localhost:3000  →  "acme"
// //   localhost:3000       →  null   (super admin)
// //
// // Production examples:
// //   acme.yourdomain.com  →  "acme"
// //   yourdomain.com       →  null   (super admin)
// //
// function useTenantFromSubdomain(): string | null {
//   const hostname = window.location.hostname; // e.g. "acme.localhost"
//   const parts    = hostname.split('.');

//   // "acme.localhost" → ["acme","localhost"]  → length 2, first part ≠ "localhost"
//   // "localhost"      → ["localhost"]         → length 1                → null
//   // "acme.yourdomain.com" → ["acme","yourdomain","com"] → length > 2   → "acme"
//   if (parts.length === 1) return null;                     // plain localhost
//   if (parts.length === 2 && parts[0] === 'localhost') return null; // safety guard
//   return parts[0] || null;
// }


// // ─── isSuperAdminUser ─────────────────────────────────────────────────────────

// function isSuperAdminUser(user: any): boolean {
//   const roles: string[] = user?.roles ?? user?.realm_access?.roles ?? [];
//   return roles.some((r: string) => r.toUpperCase() === 'SUPER_ADMIN');
// }


// // ─── MainLayout ───────────────────────────────────────────────────────────────

// function MainLayout({ children }: { children: React.ReactNode }) {
//   const navigate   = useNavigate();
//   const location   = useLocation();
//   const { user }   = useAuth();
//   const superAdmin = isSuperAdminUser(user);

//   // Tenant is identified by subdomain — no URL param needed here at all.
//   // Navigation is just plain /admin/... paths; the subdomain provides context.
//   const getActiveTab = () => {
//     const path = location.pathname;
//     if (path.includes('/wc-audit/carrier-portal')) return 'carrier-portal';
//     if (path.includes('/wc-audit'))                return 'Workmencomp';
//     if (path.includes('/users'))                   return 'users';
//     if (path.includes('/agents'))                  return 'agents';
//     return 'tenants';
//   };

//   const activeTab = getActiveTab();

//   // Clean and simple — subdomain carries the tenant, paths are generic.
//   const handleTabChange = (_tab: string, path: string) => {
//     navigate(path);
//   };

//   const tabStyle = (tab: string): React.CSSProperties => ({
//     padding: '16px 0',
//     background: 'none',
//     border: 'none',
//     borderBottom: activeTab === tab ? '2px solid #3b82f6' : '2px solid transparent',
//     color: activeTab === tab ? '#3b82f6' : '#6b7280',
//     fontWeight: 500,
//     cursor: 'pointer',
//     display: 'flex',
//     alignItems: 'center',
//     gap: '8px',
//     fontSize: '14px',
//     transition: 'all 0.2s ease',
//   });

//   const hoverProps = {
//     onMouseEnter: (e: React.MouseEvent<HTMLButtonElement>) => { e.currentTarget.style.opacity = '0.7'; },
//     onMouseLeave: (e: React.MouseEvent<HTMLButtonElement>) => { e.currentTarget.style.opacity = '1'; },
//   };

//   return (
//     <div style={{ minHeight: '100vh', background: '#f5f7fb' }}>
//       <div style={{ background: 'white', borderBottom: '1px solid #e5e7eb', padding: '0 24px' }}>
//         <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', gap: '32px' }}>

//           {/* Tenants tab — SUPER ADMIN only (localhost, no subdomain) */}
//           {superAdmin && (
//             <button
//               onClick={() => handleTabChange('tenants', '/admin/tenants')}
//               style={tabStyle('tenants')}
//               {...hoverProps}
//             >
//               <Database size={18} /> Tenants
//             </button>
//           )}

//           <button onClick={() => handleTabChange('users', '/admin/users')} style={tabStyle('users')} {...hoverProps}>
//             <Users size={18} /> Users
//           </button>

//           <button onClick={() => handleTabChange('agents', '/admin/agents')} style={tabStyle('agents')} {...hoverProps}>
//             <Bot size={18} /> Agents
//           </button>

//           <button onClick={() => handleTabChange('Workmencomp', '/admin/wc-audit')} style={tabStyle('Workmencomp')} {...hoverProps}>
//             <Bot size={18} /> Workmencomp
//           </button>

//           <button onClick={() => handleTabChange('carrier-portal', '/admin/wc-audit/carrier-portal')} style={tabStyle('carrier-portal')} {...hoverProps}>
//             <Bot size={18} /> Carrier portal
//           </button>

//         </div>
//       </div>
//       {children}
//     </div>
//   );
// }


// // ─── AdminRoutes ──────────────────────────────────────────────────────────────
// // Single route table — works the same for both localhost and acme.localhost
// // because the subdomain is transparent to React Router.

// function AdminRoutes({ superAdmin }: { superAdmin: boolean }) {
//   return (
//     <Routes>
//       <Route
//         path="tenants"
//         element={superAdmin ? <TenantAdminInterface /> : <Navigate to="users" replace />}
//       />
//       <Route path="users"                     element={<UserManagementTable />} />
//       <Route path="users/invite"              element={<InviteUserPage />} />
//       <Route path="agents"                    element={<AgentList />} />
//       <Route path="agents/create"             element={<AgentBuilder />} />
//       <Route path="agents/:id/edit"           element={<AgentBuilder />} />
//       <Route path="wc-audit/carrier-portal/*" element={<CarrierPortalApp />} />
//       <Route path="wc-audit/*"                element={<WCAuditApp />} />
//       <Route index element={<Navigate to={superAdmin ? 'tenants' : 'users'} replace />} />
//     </Routes>
//   );
// }


// // ─── AppContent ───────────────────────────────────────────────────────────────

// function AppContent() {
//   const { user, loading } = useAuth();
//   const superAdmin  = isSuperAdminUser(user);
//   const tenantSlug  = useTenantFromSubdomain(); // reads hostname — not URL path

//   // Super admin on localhost        → /admin/tenants
//   // Tenant user on acme.localhost   → /admin/users  (subdomain already scopes them)
//   const defaultPath = superAdmin ? '/admin/tenants' : '/admin/users';

//   if (loading) {
//     return (
//       <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f5f7fb' }}>
//         <div style={{ textAlign: 'center' }}>
//           <div style={{ width: 48, height: 48, border: '4px solid #e5e7eb', borderTopColor: '#3b82f6', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
//           <p style={{ color: '#6b7280' }}>Loading...</p>
//         </div>
//       </div>
//     );
//   }

//   // Guard: if a tenant user somehow lands on plain localhost (no subdomain),
//   // redirect them to their own subdomain. Prevents cross-tenant access via URL.
//   if (user && !superAdmin && !tenantSlug) {
//     const stored = localStorage.getItem('current_tenant');
//     const slug   = stored ? JSON.parse(stored)?.slug : null;
//     if (slug) {
//       const { protocol, port } = window.location;
//       const portStr = port ? `:${port}` : '';
//       window.location.href = `${protocol}//${slug}.localhost${portStr}/admin/users`;
//       return null; // halt render while redirecting
//     }
//   }

//   const protectedLayout = (
//     <ProtectedRoute requireAdmin={true}>
//       <MainLayout>
//         <AdminRoutes superAdmin={superAdmin} />
//       </MainLayout>
//     </ProtectedRoute>
//   );

//   return (
//     <Routes>
//       {/* ── Public ─────────────────────────────────────────────────────────── */}
//       <Route
//         path="/login"
//         element={!user ? <LoginPage /> : <Navigate to={defaultPath} replace />}
//       />
//       <Route path="/accept-invitation" element={<AcceptInvitationPage />} />

//       {/* ── Protected: /admin/* ────────────────────────────────────────────
//           Works for BOTH:
//             localhost:3000/admin/tenants       → super admin
//             acme.localhost:3000/admin/users    → tenant user
//           React Router sees only the path — subdomain is handled by the hook. */}
//       <Route
//         path="/admin/*"
//         element={!user ? <Navigate to="/login" replace /> : protectedLayout}
//       />

//       {/* ── Default redirects ──────────────────────────────────────────────── */}
//       <Route path="/"  element={<Navigate to={user ? defaultPath : '/login'} replace />} />
//       <Route path="*"  element={<Navigate to={user ? defaultPath : '/login'} replace />} />
//     </Routes>
//   );
// }


// // ─── Root ─────────────────────────────────────────────────────────────────────

// export default function App() {
//   return (
//     <AuthProvider>
//       <BrowserRouter>
//         <AppContent />
//         <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
//       </BrowserRouter>
//     </AuthProvider>
//   );
// }

import React, { useEffect } from 'react';
import {
  BrowserRouter, Routes, Route, Navigate,
  useNavigate, useLocation
} from 'react-router-dom';
import { AuthProvider, ProtectedRoute, useAuth } from './auth';
import LoginPage from './LoginPage';
import TenantAdminInterface from './tenant-admin';
import AgentList from './AgentList';
import { Database, Bot, Users } from 'lucide-react';

import InviteUserPage from './pages/InviteUserPage';
import AcceptInvitationPage from './pages/AcceptInvitationPage';
import UserManagementTable from './components/UserManagementTable';
import AgentBuilder from './components/AgentBuilder/AgentBuilder';
import { Layout } from './components/Layout';
import WCAuditApp from './pages/WCAudit';
import CarrierPortalApp from './pages/WCAudit/carrier-portal-v2/CarrierPortalApp';


// ─── useTenantFromSubdomain ───────────────────────────────────────────────────
function useTenantFromSubdomain(): string | null {
  const hostname = window.location.hostname;
  const parts    = hostname.split('.');
  if (parts.length === 1) return null;
  if (parts.length === 2 && parts[0] === 'localhost') return null;
  return parts[0] || null;
}

// ─── buildSubdomainRedirect ───────────────────────────────────────────────────
function buildSubdomainRedirect(slug: string, destination = '/admin/users'): string {
  const { protocol, port } = window.location;
  const portStr    = port ? `:${port}` : '';
  const baseDomain = (import.meta as any).env?.VITE_BASE_DOMAIN || 'localhost';

  const accessToken   = localStorage.getItem('access_token');
  const refreshToken  = localStorage.getItem('refresh_token');
  const currentTenant = localStorage.getItem('current_tenant');

  const params = new URLSearchParams();
  if (accessToken)   params.set('at',   accessToken);
  if (refreshToken)  params.set('rt',   refreshToken);
  if (currentTenant) params.set('ct',   currentTenant);
  params.set('dest', destination);

  return `${protocol}//${slug}.${baseDomain}${portStr}/auth-callback?${params.toString()}`;
}

// ─── isSuperAdminUser ─────────────────────────────────────────────────────────
function isSuperAdminUser(user: any): boolean {
  const roles: string[] = user?.roles ?? user?.realm_access?.roles ?? [];
  return roles.some((r: string) => r.toUpperCase() === 'SUPER_ADMIN');
}

// ─── FullPageSpinner ──────────────────────────────────────────────────────────
function FullPageSpinner({ message = 'Loading...' }: { message?: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f5f7fb' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ width: 48, height: 48, border: '4px solid #e5e7eb', borderTopColor: '#3b82f6', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
        <p style={{ color: '#6b7280' }}>{message}</p>
      </div>
    </div>
  );
}

// ─── AuthCallback ─────────────────────────────────────────────────────────────
//
// Route: /auth-callback
//
// Uses applyTokenData() + navigate() instead of window.location.replace()
// so there is NO page reload — the AuthProvider instance stays alive,
// user state is set before navigate() fires, zero flash possible.
//
function AuthCallback() {
  const navigate                    = useNavigate();
  const { applyTokenData }          = useAuth();

  useEffect(() => {
    const params        = new URLSearchParams(window.location.search);
    const accessToken   = params.get('at');
    const refreshToken  = params.get('rt');
    const currentTenant = params.get('ct');
    const dest          = params.get('dest') || '/admin/users';

    if (!accessToken) {
      navigate('/login', { replace: true });
      return;
    }

    // 1. Write tokens into THIS origin's localStorage
    localStorage.setItem('access_token', accessToken);
    if (refreshToken)  localStorage.setItem('refresh_token',  refreshToken);
    if (currentTenant) {
      // Always overwrite with the freshly passed tenant — never keep stale value
      localStorage.setItem('current_tenant', currentTenant);
    }

    // 2. Hydrate AuthProvider state directly — NO page reload
    //    Sets user + currentTenant in the existing provider instance.
    applyTokenData({ access_token: accessToken, refresh_token: refreshToken || '' });

    // 3. Strip tokens from URL
    window.history.replaceState({}, document.title, dest);

    // 4. Client-side navigation — user already set, renders admin page directly
    navigate(dest, { replace: true });

  }, [applyTokenData]); // eslint-disable-line react-hooks/exhaustive-deps

  return <FullPageSpinner message="Authenticating..." />;
}


// ─── MainLayout ───────────────────────────────────────────────────────────────
function MainLayout({ children }: { children: React.ReactNode }) {
  const navigate   = useNavigate();
  const location   = useLocation();
  const { user }   = useAuth();
  const superAdmin = isSuperAdminUser(user);

  const getActiveTab = () => {
    const path = location.pathname;
    if (path.includes('/wc-audit/carrier-portal')) return 'carrier-portal';
    if (path.includes('/wc-audit'))                return 'Workmencomp';
    if (path.includes('/users'))                   return 'users';
    if (path.includes('/agents'))                  return 'agents';
    return 'tenants';
  };

  const activeTab = getActiveTab();
  const handleTabChange = (_tab: string, path: string) => navigate(path);

  const tabStyle = (tab: string): React.CSSProperties => ({
    padding: '16px 0', background: 'none', border: 'none',
    borderBottom: activeTab === tab ? '2px solid #3b82f6' : '2px solid transparent',
    color: activeTab === tab ? '#3b82f6' : '#6b7280',
    fontWeight: 500, cursor: 'pointer', display: 'flex',
    alignItems: 'center', gap: '8px', fontSize: '14px',
    transition: 'all 0.2s ease',
  });

  const hoverProps = {
    onMouseEnter: (e: React.MouseEvent<HTMLButtonElement>) => { e.currentTarget.style.opacity = '0.7'; },
    onMouseLeave: (e: React.MouseEvent<HTMLButtonElement>) => { e.currentTarget.style.opacity = '1'; },
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f5f7fb' }}>
      <div style={{ background: 'white', borderBottom: '1px solid #e5e7eb', padding: '0 24px' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', gap: '32px' }}>
          {superAdmin && (
            <button onClick={() => handleTabChange('tenants', '/admin/tenants')} style={tabStyle('tenants')} {...hoverProps}>
              <Database size={18} /> Tenants
            </button>
          )}
          <button onClick={() => handleTabChange('users', '/admin/users')} style={tabStyle('users')} {...hoverProps}>
            <Users size={18} /> Users
          </button>
          <button onClick={() => handleTabChange('agents', '/admin/agents')} style={tabStyle('agents')} {...hoverProps}>
            <Bot size={18} /> Agents
          </button>
          <button onClick={() => handleTabChange('Workmencomp', '/admin/wc-audit')} style={tabStyle('Workmencomp')} {...hoverProps}>
            <Bot size={18} /> Workmencomp
          </button>
          <button onClick={() => handleTabChange('carrier-portal', '/admin/wc-audit/carrier-portal')} style={tabStyle('carrier-portal')} {...hoverProps}>
            <Bot size={18} /> Carrier portal
          </button>
        </div>
      </div>
      {children}
    </div>
  );
}

// ─── AdminRoutes ──────────────────────────────────────────────────────────────
function AdminRoutes({ superAdmin }: { superAdmin: boolean }) {
  return (
    <Routes>
      <Route path="tenants" element={superAdmin ? <TenantAdminInterface /> : <Navigate to="users" replace />} />
      <Route path="users"                     element={<UserManagementTable />} />
      <Route path="users/invite"              element={<InviteUserPage />} />
      <Route path="agents"                    element={<AgentList />} />
      <Route path="agents/create"             element={<AgentBuilder />} />
      <Route path="agents/:id/edit"           element={<AgentBuilder />} />
      <Route path="wc-audit/carrier-portal/*" element={<CarrierPortalApp />} />
      <Route path="wc-audit/*"                element={<WCAuditApp />} />
      <Route index element={<Navigate to={superAdmin ? 'tenants' : 'users'} replace />} />
    </Routes>
  );
}

// ─── AppContent ───────────────────────────────────────────────────────────────
function AppContent() {
  const { user, loading } = useAuth();
  const superAdmin = isSuperAdminUser(user);
  const tenantSlug = useTenantFromSubdomain();

  const defaultPath = superAdmin ? '/admin/tenants' : '/admin/users';

  if (loading) return <FullPageSpinner />;

  // ── Cross-origin safety guard ──────────────────────────────────────────────
  //
  // Triggered when a tenant user lands on plain localhost (no subdomain).
  // Example: user clears the subdomain from the URL bar and hits enter.
  //
  // THE FIX:
  // BEFORE — read slug from localStorage.current_tenant
  //   → stale: written by a PREVIOUS login session on localhost:3000
  //   → caused redirect to the wrong (old) tenant's subdomain
  //
  // AFTER — read slug from user.tenant (decoded from the JWT in memory)
  //   → always reflects the CURRENT authenticated user's tenant
  //   → JWT is the single source of truth, never stale
  //   → localStorage.current_tenant is only used to carry the value
  //     across origins in the auth-callback handoff, not for routing decisions
  //
  if (user && !superAdmin && !tenantSlug) {
    const slug = (user as any).tenant ?? null;  // ← JWT tenant, never stale
    console.log("whether user is there ");
    
    if (slug) {
      // Pass tokens along so the subdomain can bootstrap its localStorage
      window.location.href = buildSubdomainRedirect(slug, '/admin/users');
      return null;
    }

    // user.tenant is empty (shouldn't happen for a valid tenant user)
    // Fall through to /login as a safe fallback
  }

  const protectedLayout = (
    <ProtectedRoute requireAdmin={true}>
      <MainLayout>
        <AdminRoutes superAdmin={superAdmin} />
      </MainLayout>
    </ProtectedRoute>
  );

  return (
    <Routes>
      <Route path="/login"             element={!user ? <LoginPage /> : <Navigate to={defaultPath} replace />} />
      <Route path="/accept-invitation" element={<AcceptInvitationPage />} />
      <Route path="/auth-callback"     element={<AuthCallback />} />
      <Route path="/admin/*"           element={!user ? <Navigate to="/login" replace /> : protectedLayout} />
      <Route path="/"  element={<Navigate to={user ? defaultPath : '/login'} replace />} />
      <Route path="*"  element={<Navigate to={user ? defaultPath : '/login'} replace />} />
    </Routes>
  );
}

// ─── Root ─────────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppContent />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </BrowserRouter>
    </AuthProvider>
  );
}