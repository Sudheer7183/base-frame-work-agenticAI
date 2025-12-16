import React, { useState, useEffect } from 'react';
import { Search, Plus, Settings, AlertCircle, CheckCircle, XCircle, Clock, Trash2, PlayCircle, PauseCircle, RefreshCw, Users, Database, Calendar, Mail } from 'lucide-react';

const API_BASE = '/platform/tenants';

// Tenant status colors and icons
const statusConfig = {
  active: { color: 'text-green-600 bg-green-50 border-green-200', icon: CheckCircle, label: 'Active' },
  inactive: { color: 'text-gray-600 bg-gray-50 border-gray-200', icon: XCircle, label: 'Inactive' },
  provisioning: { color: 'text-blue-600 bg-blue-50 border-blue-200', icon: Clock, label: 'Provisioning' },
  suspended: { color: 'text-orange-600 bg-orange-50 border-orange-200', icon: PauseCircle, label: 'Suspended' },
  deprovisioning: { color: 'text-red-600 bg-red-50 border-red-200', icon: AlertCircle, label: 'Deprovisioning' }
};

export default function TenantAdminInterface() {
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedTenant, setSelectedTenant] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [notification, setNotification] = useState(null);

  // Mock data for demo (replace with actual API calls)
  useEffect(() => {
    loadTenants();
  }, []);

  const loadTenants = async () => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setTenants([
        {
          slug: 'acme',
          name: 'Acme Corporation',
          schema_name: 'tenant_acme',
          status: 'active',
          admin_email: 'admin@acme.com',
          max_users: 100,
          created_at: '2024-01-15T10:30:00Z',
          updated_at: '2024-01-20T14:22:00Z',
          config: { features: { ai_enabled: true, api_access: true } }
        },
        {
          slug: 'techstart',
          name: 'TechStart Inc',
          schema_name: 'tenant_techstart',
          status: 'active',
          admin_email: 'ops@techstart.io',
          max_users: 50,
          created_at: '2024-02-01T09:15:00Z',
          updated_at: '2024-02-10T11:30:00Z',
          config: { features: { ai_enabled: true } }
        },
        {
          slug: 'demo',
          name: 'Demo Account',
          schema_name: 'tenant_demo',
          status: 'suspended',
          admin_email: 'demo@example.com',
          max_users: 10,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-02-15T16:45:00Z',
          config: { suspension_reason: 'Payment overdue' }
        }
      ]);
      setLoading(false);
    }, 500);
  };

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const filteredTenants = tenants.filter(tenant => {
    const matchesSearch = tenant.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         tenant.slug.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || tenant.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleSuspend = async (slug) => {
    const reason = prompt('Enter suspension reason:');
    if (reason) {
      showNotification(`Tenant ${slug} suspended`, 'warning');
      loadTenants();
    }
  };

  const handleActivate = async (slug) => {
    showNotification(`Tenant ${slug} activated`, 'success');
    loadTenants();
  };

  const handleDelete = async (slug) => {
    if (confirm(`Are you sure you want to deprovision tenant ${slug}? This action cannot be undone.`)) {
      showNotification(`Tenant ${slug} scheduled for deprovisioning`, 'info');
      loadTenants();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Database className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Tenant Administration</h1>
                <p className="text-sm text-slate-500">Multi-tenant management console</p>
              </div>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all shadow-md hover:shadow-lg"
            >
              <Plus className="w-5 h-5" />
              <span>New Tenant</span>
            </button>
          </div>
        </div>
      </header>

      {/* Notification */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg ${
          notification.type === 'success' ? 'bg-green-500' :
          notification.type === 'warning' ? 'bg-orange-500' :
          notification.type === 'error' ? 'bg-red-500' : 'bg-blue-500'
        } text-white animate-slide-in`}>
          {notification.message}
        </div>
      )}

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatCard
            label="Total Tenants"
            value={tenants.length}
            icon={Database}
            color="blue"
          />
          <StatCard
            label="Active"
            value={tenants.filter(t => t.status === 'active').length}
            icon={CheckCircle}
            color="green"
          />
          <StatCard
            label="Suspended"
            value={tenants.filter(t => t.status === 'suspended').length}
            icon={PauseCircle}
            color="orange"
          />
          <StatCard
            label="Total Users"
            value={tenants.reduce((sum, t) => sum + (t.max_users || 0), 0)}
            icon={Users}
            color="purple"
          />
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                placeholder="Search tenants..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="suspended">Suspended</option>
              <option value="provisioning">Provisioning</option>
              <option value="inactive">Inactive</option>
            </select>
            <button
              onClick={loadTenants}
              className="flex items-center space-x-2 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Tenants Table */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          {loading ? (
            <div className="p-12 text-center">
              <RefreshCw className="w-8 h-8 text-slate-400 animate-spin mx-auto mb-4" />
              <p className="text-slate-600">Loading tenants...</p>
            </div>
          ) : filteredTenants.length === 0 ? (
            <div className="p-12 text-center">
              <Database className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">No tenants found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Tenant</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Schema</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Max Users</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Created</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold text-slate-600 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {filteredTenants.map((tenant) => (
                    <TenantRow
                      key={tenant.slug}
                      tenant={tenant}
                      onView={() => {
                        setSelectedTenant(tenant);
                        setShowDetailsModal(true);
                      }}
                      onSuspend={handleSuspend}
                      onActivate={handleActivate}
                      onDelete={handleDelete}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <CreateTenantModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            showNotification('Tenant created successfully');
            loadTenants();
          }}
        />
      )}

      {/* Details Modal */}
      {showDetailsModal && selectedTenant && (
        <TenantDetailsModal
          tenant={selectedTenant}
          onClose={() => {
            setShowDetailsModal(false);
            setSelectedTenant(null);
          }}
          onUpdate={() => {
            showNotification('Tenant updated successfully');
            loadTenants();
          }}
        />
      )}
    </div>
  );
}

function StatCard({ label, value, icon: Icon, color }) {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    orange: 'from-orange-500 to-orange-600',
    purple: 'from-purple-500 to-purple-600'
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-600 mb-1">{label}</p>
          <p className="text-3xl font-bold text-slate-900">{value}</p>
        </div>
        <div className={`w-12 h-12 bg-gradient-to-br ${colorClasses[color]} rounded-lg flex items-center justify-center`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );
}

function TenantRow({ tenant, onView, onSuspend, onActivate, onDelete }) {
  const status = statusConfig[tenant.status];
  const StatusIcon = status.icon;

  return (
    <tr className="hover:bg-slate-50 transition-colors">
      <td className="px-6 py-4">
        <div>
          <div className="font-semibold text-slate-900">{tenant.name}</div>
          <div className="text-sm text-slate-500">{tenant.slug}</div>
        </div>
      </td>
      <td className="px-6 py-4">
        <span className={`inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-medium border ${status.color}`}>
          <StatusIcon className="w-3 h-3" />
          <span>{status.label}</span>
        </span>
      </td>
      <td className="px-6 py-4">
        <code className="text-sm text-slate-700 bg-slate-100 px-2 py-1 rounded">{tenant.schema_name}</code>
      </td>
      <td className="px-6 py-4">
        <div className="flex items-center space-x-2">
          <Users className="w-4 h-4 text-slate-400" />
          <span className="text-slate-700">{tenant.max_users || 'Unlimited'}</span>
        </div>
      </td>
      <td className="px-6 py-4 text-sm text-slate-600">
        {new Date(tenant.created_at).toLocaleDateString()}
      </td>
      <td className="px-6 py-4 text-right">
        <div className="flex items-center justify-end space-x-2">
          <button
            onClick={onView}
            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            title="View details"
          >
            <Settings className="w-4 h-4" />
          </button>
          {tenant.status === 'active' && (
            <button
              onClick={() => onSuspend(tenant.slug)}
              className="p-2 text-orange-600 hover:bg-orange-50 rounded-lg transition-colors"
              title="Suspend"
            >
              <PauseCircle className="w-4 h-4" />
            </button>
          )}
          {tenant.status === 'suspended' && (
            <button
              onClick={() => onActivate(tenant.slug)}
              className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
              title="Activate"
            >
              <PlayCircle className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => onDelete(tenant.slug)}
            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </td>
    </tr>
  );
}

function CreateTenantModal({ onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    slug: '',
    name: '',
    admin_email: '',
    max_users: '',
    description: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSuccess();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-200">
          <h2 className="text-2xl font-bold text-slate-900">Create New Tenant</h2>
        </div>
        
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Tenant Slug *</label>
            <input
              type="text"
              value={formData.slug}
              onChange={(e) => setFormData({...formData, slug: e.target.value})}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="acme"
            />
            <p className="mt-1 text-xs text-slate-500">Lowercase letters, numbers, and hyphens only</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Display Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Acme Corporation"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Admin Email</label>
            <input
              type="email"
              value={formData.admin_email}
              onChange={(e) => setFormData({...formData, admin_email: e.target.value})}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="admin@acme.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Max Users</label>
            <input
              type="number"
              value={formData.max_users}
              onChange={(e) => setFormData({...formData, max_users: e.target.value})}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="100"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="3"
              placeholder="Optional description..."
            />
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all"
            >
              Create Tenant
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function TenantDetailsModal({ tenant, onClose, onUpdate }) {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">{tenant.name}</h2>
              <p className="text-sm text-slate-500">{tenant.slug}</p>
            </div>
            <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
              <XCircle className="w-6 h-6" />
            </button>
          </div>

          <div className="flex space-x-4 mt-4">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-4 py-2 rounded-lg transition-colors ${activeTab === 'overview' ? 'bg-blue-100 text-blue-700' : 'text-slate-600 hover:bg-slate-100'}`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('config')}
              className={`px-4 py-2 rounded-lg transition-colors ${activeTab === 'config' ? 'bg-blue-100 text-blue-700' : 'text-slate-600 hover:bg-slate-100'}`}
            >
              Configuration
            </button>
            <button
              onClick={() => setActiveTab('activity')}
              className={`px-4 py-2 rounded-lg transition-colors ${activeTab === 'activity' ? 'bg-blue-100 text-blue-700' : 'text-slate-600 hover:bg-slate-100'}`}
            >
              Activity
            </button>
          </div>
        </div>

        <div className="p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <InfoField label="Schema Name" value={tenant.schema_name} icon={Database} />
                <InfoField label="Status" value={tenant.status} icon={CheckCircle} />
                <InfoField label="Admin Email" value={tenant.admin_email || 'Not set'} icon={Mail} />
                <InfoField label="Max Users" value={tenant.max_users || 'Unlimited'} icon={Users} />
                <InfoField label="Created" value={new Date(tenant.created_at).toLocaleString()} icon={Calendar} />
                <InfoField label="Updated" value={new Date(tenant.updated_at).toLocaleString()} icon={Calendar} />
              </div>
            </div>
          )}

          {activeTab === 'config' && (
            <div>
              <h3 className="font-semibold text-slate-900 mb-4">Configuration</h3>
              <pre className="bg-slate-50 p-4 rounded-lg text-sm overflow-x-auto">
                {JSON.stringify(tenant.config, null, 2)}
              </pre>
            </div>
          )}

          {activeTab === 'activity' && (
            <div>
              <h3 className="font-semibold text-slate-900 mb-4">Recent Activity</h3>
              <div className="space-y-3">
                <ActivityItem date="2024-02-15" action="Tenant created" />
                <ActivityItem date="2024-02-16" action="Admin email updated" />
                <ActivityItem date="2024-02-20" action="Configuration changed" />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function InfoField({ label, value, icon: Icon }) {
  return (
    <div>
      <div className="flex items-center space-x-2 text-sm text-slate-600 mb-1">
        <Icon className="w-4 h-4" />
        <span>{label}</span>
      </div>
      <div className="text-slate-900 font-medium">{value}</div>
    </div>
  );
}

function ActivityItem({ date, action }) {
  return (
    <div className="flex items-center space-x-3 p-3 bg-slate-50 rounded-lg">
      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
      <div className="flex-1">
        <p className="text-sm text-slate-900">{action}</p>
        <p className="text-xs text-slate-500">{date}</p>
      </div>
    </div>
  );
}