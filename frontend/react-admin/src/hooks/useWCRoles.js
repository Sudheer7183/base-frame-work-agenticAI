// // src/hooks/useWCRoles.js
// import { useAuth } from "../auth";   // adjust path to your auth.jsx location

// // ── Role constants (must match wc_rbac.py exactly) ────────────────────────────
// const WC_SUPER_ADMIN = "Wc_super_admin";
// const WC_ADMIN       = "wc_admin";
// const WC_PROVIDERS   = "wc_providers";
// const WC_AGENTS      = "wc_agents";

// /**
//  * Extract WC realm roles from the Keycloak JWT.
//  * Keycloak stores realm roles at:  token.realm_access.roles
//  * The platform's useAuth exposes the raw token as `auth.token` or
//  * the parsed payload as `auth.user` / `auth.tokenParsed`.
//  * We try both shapes so this works regardless of which the platform returns.
//  */
// function extractRoles(auth) {
//   // Shape 1: auth.tokenParsed is the decoded JWT payload dict
//   if (auth?.tokenParsed?.realm_access?.roles) {
//     return new Set(auth.tokenParsed.realm_access.roles);
//   }
//   // Shape 2: auth.user has a roles array directly
//   if (Array.isArray(auth?.user?.roles)) {
//     return new Set(auth.user.roles);
//   }
//   // Shape 3: auth.user.realm_access
//   if (auth?.user?.realm_access?.roles) {
//     return new Set(auth.user.realm_access.roles);
//   }
//   return new Set();
// }

// /**
//  * useWCRoles — returns boolean flags for each WC role.
//  * Higher roles inherit all lower permissions (mirrors _ROLE_HIERARCHY in Python).
//  *
//  * Usage:
//  *   const { canUpload, canApproveHITL, isSuperAdmin } = useWCRoles();
//  */
// export function useWCRoles() {
//   const auth  = useAuth();
//   const roles = extractRoles(auth);

//   // A role is satisfied if the user holds it OR any role above it
//   const has = (role) => roles.has(role);

//   const isSuperAdmin = has(WC_SUPER_ADMIN);
//   const isAdmin      = isSuperAdmin || has(WC_ADMIN);
//   const isProvider   = isAdmin      || has(WC_PROVIDERS);
//   const isAgent      = isProvider   || has(WC_AGENTS);

//   return {
//     // Raw flags
//     isSuperAdmin,
//     isAdmin,
//     isProvider,
//     isAgent,

//     // Named permission flags — use these in JSX instead of raw role names
//     // so you can change role names in one place without touching every component.
//     canViewDashboard:    isAgent,        // everyone
//     canViewPolicies:     isAgent,        // everyone
//     canViewVariance:     isProvider,        // everyone
//     canViewAIAudit:      isProvider,        // everyone
//     canViewReports:      isProvider,     // providers and above
//     canUpload:           isAdmin,        // admins and above
//     canStartAudit:       isAdmin,        // admins and above
//     canApproveHITL:      isProvider,        // admins and above — matches require_wc_admin on backend
//     canDownloadReport:   isProvider,     // providers and above
//     canViewAllTenants:   isSuperAdmin,   // super admin only
//     canViewAdministartion:isSuperAdmin,

//     // For the user display in the topbar
//     displayRole: isSuperAdmin ? "Super Admin"
//                : isAdmin      ? "Admin"
//                : isProvider   ? "Provider"
//                : isAgent      ? "Agent"
//                : "Unknown",

//     // Raw roles set in case you need a custom check
//     roles,
//   };
// }

// src/hooks/useWCRoles.js
//
// FIXED: roles are now derived from auth.user (React state) which is updated
// by the AuthProvider's proactive refresh loop.  Previously this hook was
// reading auth.tokenParsed / auth.user.roles from the initial login snapshot
// and never re-reading after a token refresh, so stale roles persisted until
// a hard page reload.

import { useAuth } from "../auth";   // adjust path to your auth.jsx location

// ── Role constants (must match Keycloak realm role names exactly) ─────────────
const WC_SUPER_ADMIN = "Wc_super_admin";
const WC_ADMIN       = "wc_admin";
const WC_PROVIDERS   = "wc_providers";
const WC_AGENTS      = "wc_agents";

/**
 * Extract WC realm roles from wherever the platform stores them.
 *
 * The auth context now keeps `user` as the decoded JWT payload and updates it
 * on every silent refresh, so reading `auth.user.roles` always reflects the
 * current Keycloak state — no page reload needed.
 */
function extractRoles(auth) {
  // Primary source: auth.user.roles (set by our fixed AuthProvider)
  if (Array.isArray(auth?.user?.roles)) {
    return new Set(auth.user.roles);
  }

  // Fallback shapes kept for backward-compatibility
  if (auth?.tokenParsed?.realm_access?.roles) {
    return new Set(auth.tokenParsed.realm_access.roles);
  }
  if (auth?.user?.realm_access?.roles) {
    return new Set(auth.user.realm_access.roles);
  }

  return new Set();
}

/**
 * useWCRoles — returns boolean flags for each WC role.
 *
 * Because it reads from the auth context (React state), it re-renders
 * automatically whenever AuthProvider calls setUser() after a token refresh.
 * No manual polling or page reload required.
 *
 * Usage:
 *   const { canUpload, canApproveHITL, isSuperAdmin } = useWCRoles();
 */
export function useWCRoles() {
  const auth  = useAuth();
  const roles = extractRoles(auth);

  const has = (role) => roles.has(role);

  const isSuperAdmin = has(WC_SUPER_ADMIN);
  const isAdmin      = isSuperAdmin || has(WC_ADMIN);
  const isProvider   = isAdmin      || has(WC_PROVIDERS);
  const isAgent      = isProvider   || has(WC_AGENTS);

  return {
    // Raw flags
    isSuperAdmin,
    isAdmin,
    isProvider,
    isAgent,

    // Named permission flags
    canViewDashboard:    isAgent,
    canViewPolicies:     isAgent,
    canViewVariance:     isProvider,
    canViewAIAudit:      isProvider,
    canViewReports:      isProvider,
    canUpload:           isAdmin,
    canStartAudit:       isAdmin,
    canApproveHITL:      isProvider,
    canDownloadReport:   isProvider,
    canViewAllTenants:   isSuperAdmin,

    displayRole: isSuperAdmin ? "Super Admin"
               : isAdmin      ? "Admin"
               : isProvider   ? "Provider"
               : isAgent      ? "Agent"
               : "Unknown",

    roles,
  };
}