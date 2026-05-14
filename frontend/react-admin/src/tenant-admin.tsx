


import React, { useState, useEffect } from "react";
import {
  Search,
  Plus,
  Settings,
  AlertCircle,
  CheckCircle,
  XCircle,
  Clock,
  Trash2,
  PlayCircle,
  PauseCircle,
  RefreshCw,
  Users,
  Database,
  Calendar,
  Mail,
  LogOut,
} from "lucide-react";
import "./tenant-admin.css";
import { useAuth } from './auth';

const API_BASE = "http://127.0.0.1:8002/platform/tenants";

const statusConfig: any = {
  active: { className: "status active", icon: CheckCircle, label: "Active" },
  inactive: { className: "status inactive", icon: XCircle, label: "Inactive" },
  provisioning: { className: "status provisioning", icon: Clock, label: "Provisioning" },
  suspended: { className: "status suspended", icon: PauseCircle, label: "Suspended" },
  deprovisioning: { className: "status deprovisioning", icon: AlertCircle, label: "Deprovisioning" },
};

export default function TenantAdminInterface() {
  const [tenants, setTenants] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedTenant, setSelectedTenant] = useState<any>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [notification, setNotification] = useState<any>(null);

  const { user, logout } = useAuth();

  useEffect(() => {
    loadTenants();
  }, []);

  const safeJson = async (res: Response): Promise<any> => {
    const text = await res.text();
    if (!text) return {};
    try {
      return JSON.parse(text);
    } catch {
      return { detail: text };
    }
  };
  const loadTenants = async () => {
    setLoading(true);

    try {
      const accessToken = localStorage.getItem("access_token");

      const res = await fetch(`${API_BASE}/get-tenants`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
      });

      const data = await safeJson(res);

      if (!res.ok) {
        throw new Error(data.detail || "Failed to fetch tenants");
      }

      console.log("Tenants:", data);

      setTenants(data.tenants || []);
    } catch (err) {
      console.error("Error loading tenants:", err);
    } finally {
      setLoading(false);
    }
  };
  const filteredTenants = tenants.filter((t) => {
    const s = searchTerm.toLowerCase();
    return (
      (t.name.toLowerCase().includes(s) || t.slug.toLowerCase().includes(s)) &&
      (statusFilter === "all" || t.status === statusFilter)
    );
  });

  const showNotificationMsg = (message: string, type = "success") => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  return (
    <div className="page">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <Database />
          </div>
          <div>
            <h1>Tenant Administration</h1>
            <p>Multi-tenant management console</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ fontSize: '14px', color: '#6b7280' }}>
            {user?.email || 'Admin'}
          </span>
          <button className="btn primary" onClick={() => setShowCreateModal(true)}>
            <Plus /> New Tenant
          </button>
          <button
            className="btn outline"
            onClick={logout}
            title="Logout"
          >
            <LogOut />
          </button>
        </div>
      </header>

      {/* Notification */}
      {notification && (
        <div className={`toast ${notification.type}`}>
          {notification.message}
        </div>
      )}

      {/* Stats */}
      <div className="stats">
        <StatCard label="Total Tenants" value={tenants.length} icon={Database} />
        <StatCard label="Active" value={tenants.filter(t => t.status === "active").length} icon={CheckCircle} />
        <StatCard label="Suspended" value={tenants.filter(t => t.status === "suspended").length} icon={PauseCircle} />
        <StatCard label="Total Users" value={tenants.reduce((s, t) => s + (t.max_users || 0), 0)} icon={Users} />
      </div>

      {/* Filters */}
      <div className="filters">
        <div className="search">
          <Search />
          <input
            placeholder="Search tenants..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
        </select>

        <button className="btn outline" onClick={loadTenants}>
          <RefreshCw /> Refresh
        </button>
      </div>

      {/* Table */}
      <div className="table-card">
        {loading ? (
          <div className="loading">
            <RefreshCw className="spin" /> Loading tenants...
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Tenant</th>
                <th>Status</th>
                <th>Schema</th>
                <th>Users</th>
                <th>Created</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filteredTenants.map((t) => {
                const status = statusConfig[t.status];
                const Icon = status.icon;
                return (
                  <tr key={t.slug}>
                    <td>
                      <strong>{t.name}</strong>
                      <div className="muted">{t.slug}</div>
                    </td>
                    <td>
                      <span className={status.className}>
                        <Icon /> {status.label}
                      </span>
                    </td>
                    <td><code>{t.schema_name}</code></td>
                    <td><Users /> {t.max_users}</td>
                    <td>{new Date(t.created_at).toLocaleDateString()}</td>
                    <td className="actions">
                      <button
                        className="icon-btn"
                        onClick={() => {
                          setSelectedTenant(t);
                          setShowDetailsModal(true);
                        }}
                      >
                        <Settings />
                      </button>
                      <button className="icon-btn danger"><Trash2 /></button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {showCreateModal && <CreateTenantModal onClose={() => setShowCreateModal(false)} onSuccess={loadTenants} />}
      {showDetailsModal && selectedTenant && (
        <TenantDetailsModal tenant={selectedTenant} onClose={() => setShowDetailsModal(false)} />
      )}
    </div>
  );
}

/* ---------- Components ---------- */

function StatCard({ label, value, icon: Icon }: any) {
  return (
    <div className="stat-card">
      <div>
        <p>{label}</p>
        <h2>{value}</h2>
      </div>
      <Icon />
    </div>
  );
}

function CreateTenantModal({ onClose, onSuccess }: any) {
  // const [formData, setFormData] = useState({
  //   slug: "",
  //   name: "",
  //   admin_email: "",
  //   max_users: "",
  //   description: "",
  // });

  const [formData, setFormData] = useState({
    slug: "",
    name: "",
    admin_email: "",
    username: "",
    full_name: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const accessToken = localStorage.getItem('access_token');

  console.log("Access token create tenant", accessToken);
  

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => {
      const next = { ...prev, [name]: value };
      // auto-fill username from slug while username hasn't been touched
      if (name === "slug" && !prev.username) next.username = value;
      return next;
    });
  };

  // Safely parse a Response — never throws on empty or non-JSON bodies
  const safeJson = async (res: Response): Promise<any> => {
    const text = await res.text();
    if (!text) return {};
    try {
      return JSON.parse(text);
    } catch {
      return { detail: text };
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // // All six fields are required
    // const missing = (
    //   Object.keys(formData) as (keyof FormData)[]
    // ).filter((k) => !formData[k].trim());

    // if (missing.length) {
    //   setError(`Required: ${missing.join(", ")}`);
    //   return;
    // }

    setLoading(true);
    try {
      const res = await fetch(API_BASE, {
        method: "POST",
        headers: { 'Authorization': `Bearer ${accessToken}`,
        "Content-Type": "application/json" },
        body: JSON.stringify({
          slug: formData.slug.trim(),
          name: formData.name.trim(),
          admin_email: formData.admin_email.trim(),
          username: formData.username.trim(),
          full_name: formData.full_name.trim(),
          password: formData.password,
        }),
      });

      const data = await safeJson(res);   // always safe, never throws

      if (!res.ok) {
        throw new Error(data.detail || `Request failed (${res.status})`);
      }


      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // const handleSubmit = async (e: React.FormEvent) => {
  //   e.preventDefault();

  //   if (!formData.slug || !formData.name) {
  //     alert("Slug and Name are required");
  //     return;
  //   }

  //   try {
  //     const res = await fetch(API_BASE, {
  //       method: "POST",
  //       headers: {
  //         "Content-Type": "application/json",
  //       },
  //       body: JSON.stringify({
  //         slug: formData.slug,
  //         name: formData.name,
  //         admin_email: formData.admin_email,
  //         max_users: formData.max_users
  //           ? Number(formData.max_users)
  //           : null,
  //         description: formData.description,
  //       }),
  //     });

  //     if (!res.ok) {
  //       const err = await res.json();
  //       throw new Error(err.detail || "Tenant creation failed");
  //     }

  //     onSuccess();   // refresh list
  //     onClose();     // close modal
  //   } catch (err: any) {
  //     alert(err.message);
  //   }
  // };

  return (
    <div
      style={{
        position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)",
        display: "flex", alignItems: "center", justifyContent: "center",
        zIndex: 50,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "#fff", borderRadius: 12, padding: "2rem",
          width: "100%", maxWidth: 520, boxShadow: "0 20px 60px rgba(0,0,0,0.15)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{ margin: "0 0 1.5rem", fontSize: "1.25rem", fontWeight: 700 }}>
          Create Tenant
        </h2>

        <form onSubmit={handleSubmit} noValidate>

          {/* ── Tenant ───────────────────────────────────── */}
          <Label>Slug *</Label>
          <Input name="slug" value={formData.slug}
            onChange={handleChange} placeholder="e.g. acme" />

          <Label>Name *</Label>
          <Input name="name" value={formData.name}
            onChange={handleChange} placeholder="e.g. Acme Corporation" />

          <Label>Admin Email *</Label>
          <Input type="email" name="admin_email" value={formData.admin_email}
            onChange={handleChange} placeholder="admin@acme.com" />

          {/* ── Admin User ───────────────────────────────── */}
          <Divider label="Admin User" />

          <Label>Username *</Label>
          <Input name="username" value={formData.username}
            onChange={handleChange} placeholder="admin"
            autoComplete="off" />

          <Label>Full Name *</Label>
          <Input name="full_name" value={formData.full_name}
            onChange={handleChange} placeholder="Admin User" />

          <Label>Password *</Label>
          <Input type="password" name="password" value={formData.password}
            onChange={handleChange} placeholder="••••••••"
            autoComplete="new-password" />

          {/* ── Error ────────────────────────────────────── */}
          {error && (
            <p style={{ color: "#dc2626", fontSize: "0.85rem", marginTop: "0.75rem" }}>
              {error}
            </p>
          )}

          {/* ── Actions ──────────────────────────────────── */}
          <div style={{
            display: "flex", justifyContent: "flex-end",
            gap: "0.75rem", marginTop: "1.5rem"
          }}>
            <button type="button" onClick={onClose} disabled={loading}
              style={cancelStyle}>
              Cancel
            </button>
            <button type="submit" disabled={loading}
              style={{ ...submitStyle, opacity: loading ? 0.6 : 1 }}>
              {loading ? "Creating…" : "Create Tenant"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Tiny helpers ─────────────────────────────────────────────────────────────

function Label({ children }: { children: React.ReactNode }) {
  return (
    <label style={{
      display: "block", fontSize: "0.8125rem", fontWeight: 600,
      color: "#374151", marginBottom: "0.25rem"
    }}>
      {children}
    </label>
  );
}

function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      style={{
        display: "block", width: "100%", boxSizing: "border-box",
        padding: "0.5rem 0.75rem", fontSize: "0.9375rem",
        border: "1px solid #d1d5db", borderRadius: 6,
        marginBottom: "0.875rem", outline: "none",
      }}
    />
  );
}

function Divider({ label }: { label: string }) {
  return (
    <div style={{
      display: "flex", alignItems: "center",
      gap: "0.75rem", margin: "1.25rem 0 1rem"
    }}>
      <div style={{ flex: 1, height: 1, background: "#e5e7eb" }} />
      <span style={{
        fontSize: "0.75rem", fontWeight: 700,
        textTransform: "uppercase", letterSpacing: "0.07em",
        color: "#6b7280"
      }}>
        {label}
      </span>
      <div style={{ flex: 1, height: 1, background: "#e5e7eb" }} />
    </div>
  );
}

const cancelStyle: React.CSSProperties = {
  padding: "0.5rem 1.25rem", background: "transparent",
  border: "1px solid #d1d5db", borderRadius: 6, cursor: "pointer",
  fontSize: "0.9375rem",
};

const submitStyle: React.CSSProperties = {
  padding: "0.5rem 1.25rem", background: "#3b49df",
  color: "#fff", border: "none", borderRadius: 6,
  cursor: "pointer", fontWeight: 600, fontSize: "0.9375rem",
};


function TenantDetailsModal({ tenant, onClose }: any) {
  return (
    <div className="modal-backdrop">
      <div className="modal large">
        <div className="modal-header">
          <h2>{tenant.name}</h2>
          <button onClick={onClose}><XCircle /></button>
        </div>
        <pre>{JSON.stringify(tenant.config, null, 2)}</pre>
      </div>
    </div>
  );
}