/**
 * src/pages/Tenants.tsx
 * Tenants management page with i18n
 */

import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Layout } from '../components/Layout'
import './Tenants.css'

interface Tenant {
  id: string
  name: string
  created_at: string
  agent_count: number
  agent_count_text?: string
}

export const TenantsPage: React.FC = () => {
  const { t, i18n } = useTranslation(['common', 'admin'])
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    fetchTenants()
  }, [i18n.language])  // Refetch when language changes
  
  const fetchTenants = async () => {
    try {
      setLoading(true)
      
      // Send locale to backend
      const response = await fetch('http://localhost:8000/api/tenants', {
        headers: {
          'Accept-Language': i18n.language,
        }
      })
      
      const data = await response.json()
      setTenants(data.tenants || [])
    } catch (error) {
      console.error('Failed to fetch tenants:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleCreateTenant = async () => {
    const name = prompt(t('admin:tenant.enterName'))
    if (!name) return
    
    try {
      const response = await fetch('http://localhost:8000/api/tenants', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept-Language': i18n.language,
        },
        body: JSON.stringify({ name })
      })
      
      const data = await response.json()
      alert(data.message)
      fetchTenants()  // Refresh list
    } catch (error) {
      alert(t('admin:tenant.createFailed'))
    }
  }
  
  if (loading) {
    return (
      <Layout>
        <div className="loading">{t('common:loading')}</div>
      </Layout>
    )
  }
  
  return (
    <Layout>
      <div className="tenants-page">
        <div className="page-header">
          <h1>{t('admin:tenant.title')}</h1>
          <p>{t('admin:tenant.subtitle')}</p>
        </div>
        
        <div className="page-actions">
          <button onClick={handleCreateTenant} className="btn-primary">
            {t('common:actions.create')}
          </button>
          <button onClick={fetchTenants} className="btn-secondary">
            {t('common:actions.refresh')}
          </button>
        </div>
        
        <div className="tenants-list">
          {tenants.length === 0 ? (
            <div className="empty-state">
              <p>{t('admin:tenant.noTenants')}</p>
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>{t('admin:tenant.fields.name')}</th>
                  <th>{t('admin:tenant.fields.created')}</th>
                  <th>{t('admin:tenant.fields.agents')}</th>
                  <th>{t('common:actions.title')}</th>
                </tr>
              </thead>
              <tbody>
                {tenants.map(tenant => (
                  <tr key={tenant.id}>
                    <td>{tenant.name}</td>
                    <td>{tenant.created_at}</td>
                    <td>{tenant.agent_count_text || tenant.agent_count}</td>
                    <td>
                      <button className="btn-small">
                        {t('common:actions.edit')}
                      </button>
                      <button className="btn-small btn-danger">
                        {t('common:actions.delete')}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </Layout>
  )
}