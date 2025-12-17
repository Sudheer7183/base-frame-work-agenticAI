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
} from "lucide-react";
import "./tenant-admin.css";

const API_BASE = "/platform/tenants";

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

  useEffect(() => {
    loadTenants();
  }, []);

  const loadTenants = () => {
    setLoading(true);
    setTimeout(() => {
      setTenants([
        {
          slug: "acme",
          name: "Acme Corporation",
          schema_name: "tenant_acme",
          status: "active",
          admin_email: "admin@acme.com",
          max_users: 100,
          created_at: "2024-01-15T10:30:00Z",
          updated_at: "2024-01-20T14:22:00Z",
          config: { features: { ai_enabled: true } },
        },
        {
          slug: "demo",
          name: "Demo Account",
          schema_name: "tenant_demo",
          status: "suspended",
          admin_email: "demo@example.com",
          max_users: 10,
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-02-15T16:45:00Z",
          config: { suspension_reason: "Payment overdue" },
        },
      ]);
      setLoading(false);
    }, 500);
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
        <button className="btn primary" onClick={() => setShowCreateModal(true)}>
          <Plus /> New Tenant
        </button>
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
  const [formData, setFormData] = useState({
    slug: "",
    name: "",
    admin_email: "",
    max_users: "",
    description: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.slug || !formData.name) {
      alert("Slug and Name are required");
      return;
    }

    try {
      const res = await fetch(API_BASE, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          slug: formData.slug,
          name: formData.name,
          admin_email: formData.admin_email,
          max_users: formData.max_users
            ? Number(formData.max_users)
            : null,
          description: formData.description,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Tenant creation failed");
      }

      onSuccess();   // refresh list
      onClose();     // close modal
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="modal-backdrop">
      <form className="modal" onSubmit={handleSubmit}>
        <h2>Create Tenant</h2>

        <input
          placeholder="Tenant Slug"
          value={formData.slug}
          onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
        />

        <input
          placeholder="Display Name"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
        />

        <input
          placeholder="Admin Email"
          value={formData.admin_email}
          onChange={(e) =>
            setFormData({ ...formData, admin_email: e.target.value })
          }
        />

        <input
          type="number"
          placeholder="Max Users"
          value={formData.max_users}
          onChange={(e) =>
            setFormData({ ...formData, max_users: e.target.value })
          }
        />

        <textarea
          placeholder="Description"
          value={formData.description}
          onChange={(e) =>
            setFormData({ ...formData, description: e.target.value })
          }
        />

        <div className="modal-actions">
          <button type="button" className="btn outline" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary">
            Create Tenant
          </button>
        </div>
      </form>
    </div>
  );
}


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
