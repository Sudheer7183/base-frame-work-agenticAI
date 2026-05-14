

// import { useState, useEffect, useRef, createContext, useContext, useCallback } from 'react';

// const AuthContext = createContext(null);

// const KEYCLOAK_CONFIG = {
//   url: import.meta.env.VITE_KEYCLOAK_URL,
//   realm: import.meta.env.VITE_KEYCLOAK_REALM,
//   clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID
// };

// const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// // ─── How many seconds before expiry we proactively refresh ───────────────────
// const REFRESH_BUFFER_SECONDS = 60;
// // ─── How often we check whether the token needs refreshing (ms) ──────────────
// const REFRESH_CHECK_INTERVAL_MS = 30_000;

// // ─── Pure helpers (no React state) ───────────────────────────────────────────

// function decodeTokenPayload(token) {
//   try {
//     const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
//     const json = decodeURIComponent(
//       atob(base64).split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join('')
//     );
//     const payload = JSON.parse(json);
//     console.log("payload data from front",payload);
    
//     return {
//       id:         payload.sub,
//       email:      payload.email || payload.preferred_username,
//       name:       payload.name  || payload.preferred_username,
//       username:   payload.preferred_username,
//       roles:      payload.realm_access?.roles || [],
//       tenant:     payload.tenant || null,
//       exp:        payload.exp   || null,   // ← keep the raw expiry
//     };
//   } catch {
//     return null;
//   }
// }

// function tokenExpiresInSeconds(decodedUser) {
//   if (!decodedUser?.exp) return 0;
//   return decodedUser.exp - Math.floor(Date.now() / 1000);
// }

// function buildTenantInfo(decodedUser) {
//   if (!decodedUser?.tenant) return null;
//   return { slug: decodedUser.tenant, name: decodedUser.tenant };
// }

// // async function keycloakTokenRequest(params) {
// //   const body = new URLSearchParams({ client_id: KEYCLOAK_CONFIG.clientId, ...params });
// //   const res = await fetch(
// //     `${KEYCLOAK_CONFIG.url}/realms/${KEYCLOAK_CONFIG.realm}/protocol/openid-connect/token`,
// //     { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: body.toString() }
// //   );
// //   if (!res.ok) {
// //     const err = await res.json().catch(() => ({}));
// //     throw new Error(err.error_description || 'Keycloak token request failed');
// //   }
  
  
// //   return res.json();
// // }

// async function keycloakTokenRequest(params) {
//   const res = await fetch(
//     `${import.meta.env.VITE_API_BASE_URL}/auth/token`,   // your backend
//     {
//       method:  'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body:    JSON.stringify({
//         email:    params.username,
//         password: params.password,
//       }),
//     }
//   );
//   if (!res.ok) {
//     const err = await res.json().catch(() => ({}));
//     throw new Error(err.detail || 'Login failed');
//   }
//   return res.json();  // same shape — access_token, refresh_token, etc.
// }

// // ─── AuthProvider ─────────────────────────────────────────────────────────────

// export const AuthProvider = ({ children }) => {
//   const [user, setUser]               = useState(null);
//   const [loading, setLoading]         = useState(true);
//   const [currentTenant, setCurrentTenant] = useState(null);

//   // Keep a ref so the interval callback always sees the latest user
//   const userRef = useRef(null);
//   userRef.current = user;

//   // ── Internal: apply token data to state + localStorage ─────────────────────
//   const applyTokenData = useCallback((data) => {
//     const decoded = decodeTokenPayload(data.access_token);
//     if (!decoded) return null;

//     localStorage.setItem('access_token',  data.access_token);
//     localStorage.setItem('refresh_token', data.refresh_token);

//     const tenantInfo = buildTenantInfo(decoded);
//     if (tenantInfo) {
//       localStorage.setItem('current_tenant', JSON.stringify(tenantInfo));
//       setCurrentTenant(tenantInfo);
//     }

//     setUser(decoded);    // ← roles live here; every refresh updates this
//     return decoded;
//   }, []);

//   // ── Internal: perform a refresh token exchange ──────────────────────────────
//   const doRefresh = useCallback(async () => {
//     const storedRefresh = localStorage.getItem('refresh_token');
//     if (!storedRefresh) return false;

//     try {
//       const data = await keycloakTokenRequest({
//         grant_type:    'refresh_token',
//         refresh_token: storedRefresh,
//       });
//       console.log("data from the callback",data);
//       applyTokenData(data);
//       console.log('[Auth] Token refreshed — roles updated');
//       return true;
//     } catch (err) {
//       console.warn('[Auth] Silent refresh failed:', err.message);
//       return false;
//     }
//   }, [applyTokenData]);

//   // ── Proactive refresh loop ──────────────────────────────────────────────────
//   // Runs every REFRESH_CHECK_INTERVAL_MS and refreshes if the token
//   // will expire within REFRESH_BUFFER_SECONDS. This is what prevents the
//   // "works after reload" symptom — we never let the token go stale.
//   useEffect(() => {
//     const id = setInterval(async () => {
//       const current = userRef.current;
//       if (!current) return;

//       const secsLeft = tokenExpiresInSeconds(current);
//       console.debug(`[Auth] Token expires in ${secsLeft}s`);

//       if (secsLeft < REFRESH_BUFFER_SECONDS) {
//         await doRefresh();
//       }
//     }, REFRESH_CHECK_INTERVAL_MS);

//     return () => clearInterval(id);
//   }, [doRefresh]);

//   // ── Bootstrap: restore session from localStorage ────────────────────────────
//   useEffect(() => {
//     const storedToken   = localStorage.getItem('access_token');
//     const storedRefresh = localStorage.getItem('refresh_token');

//     if (!storedToken || !storedRefresh) {
//       setLoading(false);
//       return;
//     }

//     const decoded = decodeTokenPayload(storedToken);
//     if (!decoded) { setLoading(false); return; }

//     const secsLeft = tokenExpiresInSeconds(decoded);

//     if (secsLeft > 10) {
//       // Token is still valid — use it immediately, then schedule a fetch of
//       // the full profile in the background so the UI is not blocked.
//       const tenantInfo = buildTenantInfo(decoded);
//       if (tenantInfo) {
//         setCurrentTenant(tenantInfo);
//         localStorage.setItem('current_tenant', JSON.stringify(tenantInfo));
//       }
//       setUser(decoded);
//       setLoading(false);

//       // Optionally hydrate from /users/me in the background
//       fetchUserProfile(storedToken).catch(() => {/* non-fatal */});
//     } else {
//       // Token expired (or very close) — try silent refresh before rendering
//       doRefresh().finally(() => setLoading(false));
//     }
//   }, [doRefresh]); // eslint-disable-line react-hooks/exhaustive-deps

//   // ── Fetch full profile from backend ────────────────────────────────────────
//   async function fetchUserProfile(accessToken) {
//     const res = await fetch(`${API_BASE_URL}/api/v1/users/me`, {
//       headers: { Authorization: `Bearer ${accessToken}` },
//     });
//     if (!res.ok) return;
//     // We intentionally do NOT overwrite roles from the profile endpoint —
//     // roles always come from the Keycloak JWT so they stay in sync with
//     // whatever Keycloak assigned at token-issue / refresh time.
//   }

//   // ── Public: login ───────────────────────────────────────────────────────────
//   const login = async (email, password) => {
//     try {
//       const data = await keycloakTokenRequest({
//         grant_type: 'password',
//         username:   email,
//         password,
//       });
//       console.log("data from the callback",data);
//       const decoded = applyTokenData(data);
//       if (!decoded) throw new Error('Could not decode token');
//       // return { success: true };
//       return { success: true, tenantSlug: decoded.tenant ?? null };
//     } catch (err) {
//       console.error('[Auth] Login error:', err);
//       return { success: false, error: err.message };
//     }
//   };

//   // ── Public: logout ──────────────────────────────────────────────────────────
//   const logout = async () => {
//     try {
//       const storedRefresh = localStorage.getItem('refresh_token');
//       if (storedRefresh) {
//         await keycloakTokenRequest({
//           grant_type:    'refresh_token',   // Keycloak logout via token endpoint
//           refresh_token: storedRefresh,
//           // Some realms need a separate logout endpoint — adjust if needed
//         }).catch(() => {/* best-effort */});
//       }
//     } finally {
//       localStorage.removeItem('access_token');
//       localStorage.removeItem('refresh_token');
//       localStorage.removeItem('current_tenant');
//       setUser(null);
//       setCurrentTenant(null);
//     }
//   };

//   const hasRole  = (role)  => (user?.roles || []).includes(role);
//   const isAdmin  = ()      => ['ADMIN','SUPER_ADMIN','admin','super_admin','realm-admin'].some(hasRole);

//   return (
//     <AuthContext.Provider value={{
//       user, loading, currentTenant,
//       login, logout, hasRole, isAdmin,
//       // Expose manual refresh so components can call it if needed
//       refreshToken: doRefresh,
//     }}>
//       {children}
//     </AuthContext.Provider>
//   );
// };

// export const useAuth = () => {
//   const ctx = useContext(AuthContext);
//   if (!ctx) throw new Error('useAuth must be used within AuthProvider');
//   return ctx;
// };

// // ─── ProtectedRoute ───────────────────────────────────────────────────────────

// export const ProtectedRoute = ({ children, requireAdmin = false }) => {
//   const { user, loading, isAdmin } = useAuth();

//   if (loading) {
//     return (
//       <div style={{ display:'flex', justifyContent:'center', alignItems:'center', minHeight:'100vh', background:'#f5f7fb' }}>
//         <div style={{ textAlign:'center' }}>
//           <div style={{ width:48, height:48, border:'4px solid #e5e7eb', borderTopColor:'#3b82f6', borderRadius:'50%', animation:'spin 1s linear infinite', margin:'0 auto 16px' }} />
//           <p style={{ color:'#6b7280' }}>Loading…</p>
//         </div>
//       </div>
//     );
//   }

//   if (!user) return null;

//   if (requireAdmin && !isAdmin()) {
//     return (
//       <div style={{ display:'flex', justifyContent:'center', alignItems:'center', minHeight:'100vh', background:'#f5f7fb' }}>
//         <div style={{ background:'white', padding:32, borderRadius:12, textAlign:'center', boxShadow:'0 2px 8px rgba(0,0,0,.1)', maxWidth:400 }}>
//           <div style={{ fontSize:48, marginBottom:16 }}>🔒</div>
//           <h2 style={{ color:'#ef4444', marginBottom:8 }}>Access Denied</h2>
//           <p style={{ color:'#6b7280', marginBottom:16 }}>Admin privileges required</p>
//           <p style={{ fontSize:12, color:'#9ca3af' }}>Your roles: {user?.roles?.join(', ') || 'None'}</p>
//           <button onClick={() => window.location.href='/'} style={{ padding:'10px 20px', background:'#3b82f6', color:'white', border:'none', borderRadius:6, cursor:'pointer' }}>
//             Go to Home
//           </button>
//         </div>
//       </div>
//     );
//   }

//   return children;
// };

// // ─── apiClient — always reads a fresh token from localStorage ────────────────
// // This is the key fix: instead of closing over a stale token variable, it reads
// // from localStorage on EVERY request, so it always gets whatever the refresh
// // loop just stored there.

// export const apiClient = {
//   async request(url, options = {}) {
//     // Always read the latest token — the refresh loop keeps this up-to-date
//     const accessToken = localStorage.getItem('access_token');
//     if (!accessToken) {
//       window.location.href = '/login';
//       throw new Error('No access token');
//     }

//     const tenantRaw = localStorage.getItem('current_tenant');
//     let tenantSlug  = null;
//     try {
//       tenantSlug = tenantRaw ? JSON.parse(tenantRaw)?.slug : null;
//     } catch { /* ignore */ }

//     const headers = {
//       'Content-Type':  'application/json',
//       'Authorization': `Bearer ${accessToken}`,
//       ...(tenantSlug ? { 'X-Tenant-ID': tenantSlug } : {}),
//       ...options.headers,
//     };

//     let response = await fetch(url, { ...options, headers });

//     // ── On 401: attempt a single silent refresh then retry once ────────────
//     if (response.status === 401) {
//       console.warn('[apiClient] 401 received — attempting silent refresh');
//       const refreshToken = localStorage.getItem('refresh_token');
//       if (!refreshToken) { window.location.href = '/login'; throw new Error('Unauthorised'); }

//       try {
//         const body = new URLSearchParams({
//           client_id:     KEYCLOAK_CONFIG.clientId,
//           grant_type:    'refresh_token',
//           refresh_token: refreshToken,
//         });
//         const tokenRes = await fetch(
//           `${KEYCLOAK_CONFIG.url}/realms/${KEYCLOAK_CONFIG.realm}/protocol/openid-connect/token`,
//           { method:'POST', headers:{ 'Content-Type':'application/x-www-form-urlencoded' }, body: body.toString() }
//         );

//         if (!tokenRes.ok) throw new Error('Refresh failed');

//         const data = await tokenRes.json();
//         localStorage.setItem('access_token',  data.access_token);
//         localStorage.setItem('refresh_token', data.refresh_token);

//         // Update tenant from new token
//         const decoded = decodeTokenPayload(data.access_token);
//         if (decoded?.tenant) {
//           localStorage.setItem('current_tenant', JSON.stringify({ slug: decoded.tenant, name: decoded.tenant }));
//         }

//         // Retry original request with the new token
//         headers['Authorization'] = `Bearer ${data.access_token}`;
//         response = await fetch(url, { ...options, headers });

//       } catch {
//         window.location.href = '/login';
//         throw new Error('Session expired');
//       }
//     }

//     if (!response.ok) {
//       const err = await response.json().catch(() => ({ detail: 'Request failed' }));
//       throw new Error(err.detail || 'Request failed');
//     }

//     return response.json();
//   },

//   get:    (url)        => apiClient.request(url),
//   post:   (url, data)  => apiClient.request(url, { method:'POST',   body: JSON.stringify(data) }),
//   patch:  (url, data)  => apiClient.request(url, { method:'PATCH',  body: JSON.stringify(data) }),
//   put:    (url, data)  => apiClient.request(url, { method:'PUT',    body: JSON.stringify(data) }),
//   delete: (url)        => apiClient.request(url, { method:'DELETE' }),
// };

// // Inject spin keyframe once
// if (typeof document !== 'undefined') {
//   const s = document.createElement('style');
//   s.textContent = '@keyframes spin { to { transform: rotate(360deg); } }';
//   document.head.appendChild(s);
// }

import { useState, useEffect, useRef, createContext, useContext, useCallback } from 'react';

const AuthContext = createContext(null);

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const REFRESH_BUFFER_SECONDS    = 60;
const REFRESH_CHECK_INTERVAL_MS = 30_000;

// ─── Pure helpers ─────────────────────────────────────────────────────────────

function decodeTokenPayload(token) {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const json   = decodeURIComponent(
      atob(base64).split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join('')
    );
    const payload = JSON.parse(json);
    return {
      id:       payload.sub,
      email:    payload.email || payload.preferred_username,
      name:     payload.name  || payload.preferred_username,
      username: payload.preferred_username,
      roles:    payload.realm_access?.roles || [],
      tenant:   payload.tenant || null,
      exp:      payload.exp    || null,
    };
  } catch {
    return null;
  }
}

function tokenExpiresInSeconds(decodedUser) {
  if (!decodedUser?.exp) return 0;
  return decodedUser.exp - Math.floor(Date.now() / 1000);
}

function buildTenantInfo(decodedUser) {
  if (!decodedUser?.tenant) return null;
  return { slug: decodedUser.tenant, name: decodedUser.tenant };
}

// ─── Backend proxy — all token operations ────────────────────────────────────
// Never calls Keycloak directly from the browser.
// Works from any origin (localhost, subdomain) — no CORS ever.
async function backendTokenRequest(params) {
  const res = await fetch(`${API_BASE_URL}/auth/token`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Token request failed');
  }
  return res.json();
}

// ─── AuthProvider ─────────────────────────────────────────────────────────────

export const AuthProvider = ({ children }) => {
  const [user, setUser]                   = useState(null);
  const [loading, setLoading]             = useState(true);
  const [currentTenant, setCurrentTenant] = useState(null);

  const userRef = useRef(null);
  userRef.current = user;

  // ── applyTokenData ──────────────────────────────────────────────────────────
  //
  // KEY CHANGE: this is now exposed in AuthContext so AuthCallback can call it
  // directly — setting auth state in memory without any page reload.
  //
  // Previously AuthCallback used window.location.replace() which caused:
  //   full page reload → AuthProvider re-initializes → loading=true → useEffect
  //   reads localStorage → brief window where loading=false & user=null → FLASH
  //
  // Now AuthCallback calls applyTokenData() → user state is set immediately in
  // the existing AuthProvider instance → navigate() does client-side routing →
  // zero reload, zero bootstrap phase, zero flash.
  //
  const applyTokenData = useCallback((data) => {
    const decoded = decodeTokenPayload(data.access_token);
    if (!decoded) return null;

    localStorage.setItem('access_token',  data.access_token);
    if (data.refresh_token) {
      localStorage.setItem('refresh_token', data.refresh_token);
    }

    const tenantInfo = buildTenantInfo(decoded);
    if (tenantInfo) {
      localStorage.setItem('current_tenant', JSON.stringify(tenantInfo));
      setCurrentTenant(tenantInfo);
    }

    setUser(decoded);
    return decoded;
  }, []);

  // ── Silent refresh ──────────────────────────────────────────────────────────
  const doRefresh = useCallback(async () => {
    const storedRefresh = localStorage.getItem('refresh_token');
    if (!storedRefresh) return false;
    try {
      const data = await backendTokenRequest({
        grant_type:    'refresh_token',
        refresh_token: storedRefresh,
      });
      applyTokenData(data);
      console.log('[Auth] Token refreshed successfully');
      return true;
    } catch (err) {
      console.warn('[Auth] Silent refresh failed:', err.message);
      return false;
    }
  }, [applyTokenData]);

  // ── Proactive refresh loop ──────────────────────────────────────────────────
  useEffect(() => {
    const id = setInterval(async () => {
      const current  = userRef.current;
      if (!current) return;
      const secsLeft = tokenExpiresInSeconds(current);
      console.debug(`[Auth] Token expires in ${secsLeft}s`);
      if (secsLeft < REFRESH_BUFFER_SECONDS) {
        await doRefresh();
      }
    }, REFRESH_CHECK_INTERVAL_MS);
    return () => clearInterval(id);
  }, [doRefresh]);

  // ── Bootstrap: restore session from localStorage ────────────────────────────
  useEffect(() => {
    const storedToken   = localStorage.getItem('access_token');
    const storedRefresh = localStorage.getItem('refresh_token');

    if (!storedToken || !storedRefresh) {
      setLoading(false);
      return;
    }

    const decoded  = decodeTokenPayload(storedToken);
    if (!decoded) { setLoading(false); return; }

    const secsLeft = tokenExpiresInSeconds(decoded);

    if (secsLeft > 10) {
      const tenantInfo = buildTenantInfo(decoded);
      if (tenantInfo) {
        setCurrentTenant(tenantInfo);
        localStorage.setItem('current_tenant', JSON.stringify(tenantInfo));
      }
      setUser(decoded);
      setLoading(false);
    } else {
      doRefresh().finally(() => setLoading(false));
    }
  }, [doRefresh]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Public: login ───────────────────────────────────────────────────────────
  const login = async (email, password) => {
    try {
      const data    = await backendTokenRequest({ grant_type: 'password', username: email, password });
      const decoded = applyTokenData(data);
      if (!decoded) throw new Error('Could not decode token');
      return { success: true, tenantSlug: decoded.tenant ?? null };
    } catch (err) {
      console.error('[Auth] Login error:', err);
      return { success: false, error: err.message };
    }
  };

  // ── Public: logout ──────────────────────────────────────────────────────────
  const logout = async () => {
    try {
      const storedRefresh = localStorage.getItem('refresh_token');
      if (storedRefresh) {
        await backendTokenRequest({ grant_type: 'refresh_token', refresh_token: storedRefresh }).catch(() => {});
      }
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('current_tenant');
      setUser(null);
      setCurrentTenant(null);
    }
  };

  const hasRole = (role) => (user?.roles || []).includes(role);
  const isAdmin = ()     => ['ADMIN','SUPER_ADMIN','admin','super_admin','realm-admin'].some(hasRole);

  return (
    <AuthContext.Provider value={{
    user, loading, currentTenant,
    login, logout, hasRole, isAdmin,
    refreshToken:   doRefresh,
    applyTokenData,              // ← ADD THIS ONE LINE
  }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

// ─── ProtectedRoute ───────────────────────────────────────────────────────────

export const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const { user, loading, isAdmin } = useAuth();

  if (loading) {
    return (
      <div style={{ display:'flex', justifyContent:'center', alignItems:'center', minHeight:'100vh', background:'#f5f7fb' }}>
        <div style={{ textAlign:'center' }}>
          <div style={{ width:48, height:48, border:'4px solid #e5e7eb', borderTopColor:'#3b82f6', borderRadius:'50%', animation:'spin 1s linear infinite', margin:'0 auto 16px' }} />
          <p style={{ color:'#6b7280' }}>Loading…</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  if (requireAdmin && !isAdmin()) {
    return (
      <div style={{ display:'flex', justifyContent:'center', alignItems:'center', minHeight:'100vh', background:'#f5f7fb' }}>
        <div style={{ background:'white', padding:32, borderRadius:12, textAlign:'center', boxShadow:'0 2px 8px rgba(0,0,0,.1)', maxWidth:400 }}>
          <div style={{ fontSize:48, marginBottom:16 }}>🔒</div>
          <h2 style={{ color:'#ef4444', marginBottom:8 }}>Access Denied</h2>
          <p style={{ color:'#6b7280', marginBottom:16 }}>Admin privileges required</p>
          <p style={{ fontSize:12, color:'#9ca3af' }}>Your roles: {user?.roles?.join(', ') || 'None'}</p>
          <button onClick={() => window.location.href='/'} style={{ padding:'10px 20px', background:'#3b82f6', color:'white', border:'none', borderRadius:6, cursor:'pointer' }}>
            Go to Home
          </button>
        </div>
      </div>
    );
  }

  return children;
};

// ─── apiClient ────────────────────────────────────────────────────────────────

export const apiClient = {
  async request(url, options = {}) {
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) { window.location.href = '/login'; throw new Error('No access token'); }

    const tenantRaw = localStorage.getItem('current_tenant');
    let tenantSlug  = null;
    try { tenantSlug = tenantRaw ? JSON.parse(tenantRaw)?.slug : null; } catch { /* ignore */ }

    const headers = {
      'Content-Type':  'application/json',
      'Authorization': `Bearer ${accessToken}`,
      ...(tenantSlug ? { 'X-Tenant-ID': tenantSlug } : {}),
      ...options.headers,
    };

    let response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
      console.warn('[apiClient] 401 — attempting silent refresh');
      const storedRefresh = localStorage.getItem('refresh_token');
      if (!storedRefresh) { window.location.href = '/login'; throw new Error('Unauthorised'); }

      try {
        const data = await backendTokenRequest({ grant_type: 'refresh_token', refresh_token: storedRefresh });
        localStorage.setItem('access_token',  data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        const decoded = decodeTokenPayload(data.access_token);
        if (decoded?.tenant) {
          localStorage.setItem('current_tenant', JSON.stringify({ slug: decoded.tenant, name: decoded.tenant }));
        }
        headers['Authorization'] = `Bearer ${data.access_token}`;
        response = await fetch(url, { ...options, headers });
      } catch {
        window.location.href = '/login';
        throw new Error('Session expired');
      }
    }

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(err.detail || 'Request failed');
    }
    return response.json();
  },

  get:    (url)       => apiClient.request(url),
  post:   (url, data) => apiClient.request(url, { method: 'POST',   body: JSON.stringify(data) }),
  patch:  (url, data) => apiClient.request(url, { method: 'PATCH',  body: JSON.stringify(data) }),
  put:    (url, data) => apiClient.request(url, { method: 'PUT',    body: JSON.stringify(data) }),
  delete: (url)       => apiClient.request(url, { method: 'DELETE' }),
};

if (typeof document !== 'undefined') {
  const s = document.createElement('style');
  s.textContent = '@keyframes spin { to { transform: rotate(360deg); } }';
  document.head.appendChild(s);
}