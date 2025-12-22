import React, { useState, useEffect } from "react";
import {
  Search,
  Plus,
  Settings,
  CheckCircle,
  XCircle,
  RefreshCw,
  Bot,
  Trash2,
  PlayCircle,
  Edit,
  LogOut,
} from "lucide-react";
import { useAuth, apiClient } from './auth';
import "./tenant-admin.css";

const API_BASE = "http://localhost:8000/api/v1/agents";

interface Agent {
  id: number;
  name: string;
  description: string;
  workflow: string;
  config: any;
  active: boolean;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export default function AgentList() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [notification, setNotification] = useState<any>(null);
  const { user, logout, currentTenant } = useAuth();

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    setLoading(true);
    try {
      const activeOnly = activeFilter === "active";
      const data = await apiClient.get(`${API_BASE}?active_only=${activeOnly}`);
      setAgents(data);
    } catch (error: any) {
      console.error('Failed to load agents:', error);
      showNotificationMsg(error.message || 'Failed to load agents', 'error');
    } finally {
      setLoading(false);
    }
  };

  const filteredAgents = agents.filter((agent) => {
    const searchLower = searchTerm.toLowerCase();
    const matchesSearch = 
      agent.name.toLowerCase().includes(searchLower) ||
      agent.description?.toLowerCase().includes(searchLower);
    
    const matchesFilter = 
      activeFilter === "all" || 
      (activeFilter === "active" && agent.active) ||
      (activeFilter === "inactive" && !agent.active);
    
    return matchesSearch && matchesFilter;
  });

  const showNotificationMsg = (message: string, type = "success") => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const handleDeleteAgent = async (agentId: number) => {
    if (!window.confirm('Are you sure you want to delete this agent?')) {
      return;
    }

    try {
      await apiClient.delete(`${API_BASE}/${agentId}`);
      showNotificationMsg('Agent deleted successfully');
      loadAgents();
    } catch (error: any) {
      showNotificationMsg(error.message || 'Failed to delete agent', 'error');
    }
  };

  const handleToggleActive = async (agent: Agent) => {
    try {
      await apiClient.patch(`${API_BASE}/${agent.id}`, {
        active: !agent.active
      });
      showNotificationMsg(`Agent ${!agent.active ? 'activated' : 'deactivated'} successfully`);
      loadAgents();
    } catch (error: any) {
      showNotificationMsg(error.message || 'Failed to update agent', 'error');
    }
  };

  return (
    <div className="page">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <Bot />
          </div>
          <div>
            <h1>Agent Management</h1>
            <p>Manage your AI agents</p>
            {currentTenant && (
              <p style={{ fontSize: '12px', color: '#9ca3af' }}>
                Tenant: {currentTenant.name}
              </p>
            )}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ fontSize: '14px', color: '#6b7280' }}>
            {user?.email}
          </span>
          <button className="btn primary" onClick={() => setShowCreateModal(true)}>
            <Plus /> New Agent
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
        <StatCard 
          label="Total Agents" 
          value={agents.length} 
          icon={Bot} 
        />
        <StatCard 
          label="Active" 
          value={agents.filter(a => a.active).length} 
          icon={CheckCircle} 
        />
        <StatCard 
          label="Inactive" 
          value={agents.filter(a => !a.active).length} 
          icon={XCircle} 
        />
      </div>

      {/* Filters */}
      <div className="filters">
        <div className="search">
          <Search />
          <input
            placeholder="Search agents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <select value={activeFilter} onChange={(e) => setActiveFilter(e.target.value)}>
          <option value="all">All Agents</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>

        <button className="btn outline" onClick={loadAgents}>
          <RefreshCw /> Refresh
        </button>
      </div>

      {/* Table */}
      <div className="table-card">
        {loading ? (
          <div className="loading">
            <RefreshCw className="spin" /> Loading agents...
          </div>
        ) : filteredAgents.length === 0 ? (
          <div style={{ padding: '48px', textAlign: 'center', color: '#6b7280' }}>
            <Bot size={48} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
            <p>No agents found</p>
            <button 
              className="btn primary" 
              onClick={() => setShowCreateModal(true)}
              style={{ marginTop: '16px' }}
            >
              <Plus /> Create Your First Agent
            </button>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Agent</th>
                <th>Workflow</th>
                <th>Status</th>
                <th>Created</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filteredAgents.map((agent) => (
                <tr key={agent.id}>
                  <td>
                    <strong>{agent.name}</strong>
                    <div className="muted">{agent.description || 'No description'}</div>
                  </td>
                  <td><code>{agent.workflow}</code></td>
                  <td>
                    <span className={`status ${agent.active ? 'active' : 'inactive'}`}>
                      {agent.active ? <CheckCircle /> : <XCircle />}
                      {agent.active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>{new Date(agent.created_at).toLocaleDateString()}</td>
                  <td className="actions">
                    <button
                      className="icon-btn"
                      onClick={() => handleToggleActive(agent)}
                      title={agent.active ? 'Deactivate' : 'Activate'}
                    >
                      {agent.active ? <XCircle /> : <CheckCircle />}
                    </button>
                    <button
                      className="icon-btn"
                      title="Edit"
                    >
                      <Edit />
                    </button>
                    <button 
                      className="icon-btn danger"
                      onClick={() => handleDeleteAgent(agent.id)}
                      title="Delete"
                    >
                      <Trash2 />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showCreateModal && (
        <CreateAgentModal 
          onClose={() => setShowCreateModal(false)} 
          onSuccess={() => {
            setShowCreateModal(false);
            loadAgents();
          }} 
        />
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

function CreateAgentModal({ onClose, onSuccess }: any) {
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    workflow: "",
    active: true,
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name || !formData.workflow) {
      alert("Name and Workflow are required");
      return;
    }

    setLoading(true);
    try {
      await apiClient.post(API_BASE, formData);
      onSuccess();
    } catch (err: any) {
      alert(err.message || 'Failed to create agent');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <form className="modal" onSubmit={handleSubmit}>
        <h2>Create Agent</h2>

        <input
          placeholder="Agent Name"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          required
        />

        <input
          placeholder="Workflow (e.g., research_agent, chat_agent)"
          value={formData.workflow}
          onChange={(e) => setFormData({ ...formData, workflow: e.target.value })}
          required
        />

        <textarea
          placeholder="Description"
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
        />

        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px' }}>
          <input
            type="checkbox"
            checked={formData.active}
            onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
          />
          Active
        </label>

        <div className="modal-actions">
          <button type="button" className="btn outline" onClick={onClose} disabled={loading}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={loading}>
            {loading ? 'Creating...' : 'Create Agent'}
          </button>
        </div>
      </form>
    </div>
  );
}