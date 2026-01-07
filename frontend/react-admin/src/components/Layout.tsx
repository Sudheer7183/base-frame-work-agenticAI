/**
 * Layout Component with Corrected i18n Usage
 * 
 * FIXED: Changed from t('common:nav.dashboard') to t('common.nav.dashboard')
 */

import React, { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { LanguageSelector } from '../i18n/components/LanguageSelector';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { t, i18n } = useTranslation();
  
  // Update HTML attributes when language changes
  useEffect(() => {
    document.documentElement.lang = i18n.language;
    document.documentElement.dir = i18n.dir();
  }, [i18n.language]);
  
  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="header-left">
          {/* FIXED: Changed from 'common:app.title' to 'common.app.title' */}
          <h1>{t('common.app.title', 'Agentic AI Platform')}</h1>
        </div>
        
        <div className="header-right">
          <LanguageSelector variant="dropdown" showNativeNames={true} />
        </div>
      </header>
      
      <aside className="app-sidebar">
        <nav>
          <ul>
            {/* FIXED: Changed all navigation keys from colon (:) to dot (.) notation */}
            <li>
              <a href="/admin/dashboard">{t('common.nav.dashboard', 'Dashboard')}</a>
            </li>
            <li>
              <a href="/admin/tenants">{t('common.nav.tenants', 'Tenants')}</a>
            </li>
            <li>
              <a href="/admin/agents">{t('common.nav.agents', 'Agents')}</a>
            </li>
            <li>
              <a href="/admin/workflows">{t('common.nav.workflows', 'Workflows')}</a>
            </li>
          </ul>
        </nav>
      </aside>
      
      <main className="app-content">
        {children}
      </main>
      
      <footer className="app-footer">
        {/* FIXED: Changed from 'common:footer.copyright' to 'common.footer.copyright' */}
        <p>{t('common.footer.copyright', '© 2024 Agentic AI Platform')}</p>
      </footer>
    </div>
  );
};