import React, { useState } from 'react';
import { useAuth } from './auth';

export default function LoginPage() {
  const [email, setEmail]         = useState('');
  const [password, setPassword]   = useState('');
  const [error, setError]         = useState('');
  const [loading, setLoading]     = useState(false);

  // ── redirecting flag ────────────────────────────────────────────────────────
  // After login() resolves, applyTokenData() inside auth.jsx calls setUser()
  // which triggers a React re-render of AppContent. The /login route then sees
  // user !== null and renders <Navigate to="/admin/tenants"> — causing a brief
  // flash of that page BEFORE window.location.href fires to the subdomain.
  //
  // Setting redirecting=true immediately after success renders a full-screen
  // spinner instead, which completely blocks that re-render. The spinner
  // disappears when the browser navigates away.
  const [redirecting, setRedirecting] = useState(false);

  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await login(email, password);

      if (!result.success) {
        setError(result.error || 'Login failed');
        setLoading(false);
        return;
      }

      // ── Immediately block any further re-renders ─────────────────────────
      // This must happen BEFORE any async work or state that could trigger
      // AppContent to re-render with user set.
      setRedirecting(true);

      const { protocol, port } = window.location;
      const portStr    = port ? `:${port}` : '';
      const baseDomain = import.meta.env.VITE_BASE_DOMAIN || 'localhost';

      if (result.tenantSlug) {
        // ── Tenant user → redirect to their subdomain with tokens ───────────
        // localStorage is origin-scoped. Tokens on localhost:3000 are invisible
        // to newadmin15.localhost:3000. We pass them as URL params for one hop.
        // AuthCallback on the subdomain consumes them, writes to its own
        // localStorage, then wipes them from the URL.
        const accessToken   = localStorage.getItem('access_token');
        const refreshToken  = localStorage.getItem('refresh_token');
        const currentTenant = localStorage.getItem('current_tenant');

        const params = new URLSearchParams();
        if (accessToken)   params.set('at', accessToken);
        if (refreshToken)  params.set('rt', refreshToken);
        if (currentTenant) params.set('ct', currentTenant);

        window.location.href =
          `${protocol}//${result.tenantSlug}.${baseDomain}${portStr}/auth-callback?${params.toString()}`;
      } else {
        // ── Super admin → same origin, localStorage already set ─────────────
        window.location.href =
          `${protocol}//${baseDomain}${portStr}/admin/tenants`;
      }

    } catch (err) {
      setError('An unexpected error occurred');
      setLoading(false);
      setRedirecting(false);
    }
  };

  // ── Full-screen redirect spinner ────────────────────────────────────────────
  // Shown between login() success and browser navigation completing.
  // Prevents ANY flash of other pages during the handoff.
  if (redirecting) {
    return (
      <div style={{
        display: 'flex', justifyContent: 'center', alignItems: 'center',
        minHeight: '100vh', background: '#f5f7fb',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: 48, height: 48,
            border: '4px solid #e5e7eb',
            borderTopColor: '#3b82f6',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px',
          }} />
          <p style={{ color: '#6b7280', fontSize: '14px' }}>
            Redirecting to your workspace...
          </p>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex', justifyContent: 'center', alignItems: 'center',
      minHeight: '100vh', background: '#f5f7fb',
    }}>
      <form onSubmit={handleSubmit} style={{
        background: 'white', padding: '32px', borderRadius: '12px',
        width: '100%', maxWidth: '400px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      }}>
        <h1 style={{ marginBottom: '24px', fontSize: '24px', fontWeight: '600' }}>
          Tenant Admin Login
        </h1>

        {error && (
          <div style={{
            background: '#fee', color: '#c00', padding: '12px',
            borderRadius: '6px', marginBottom: '16px', fontSize: '14px',
          }}>
            {error}
          </div>
        )}

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500', color: '#374151' }}>
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ width: '100%', padding: '10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '14px', boxSizing: 'border-box' }}
          />
        </div>

        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500', color: '#374151' }}>
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ width: '100%', padding: '10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '14px', boxSizing: 'border-box' }}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            width: '100%', padding: '12px',
            background: loading ? '#ccc' : 'linear-gradient(135deg,#3b82f6,#9333ea)',
            color: 'white', border: 'none', borderRadius: '6px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '16px', fontWeight: '500',
          }}
        >
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
}