# Installation & Integration Guide

Complete guide for integrating the i18n package into your Agentic AI Platform v1.3.

## 📋 Prerequisites

- Python 3.8+ (for backend)
- Node.js 18+ (for React)
- Streamlit 1.32+ (for HITL interface)
- Git

---

## 🚀 Installation Steps

### Step 1: Copy i18n Package to Your Project

```bash
# Navigate to your Agentic AI Platform root directory
cd /path/to/agentic-ai-platform-v1.3-complete

# Copy the i18n package
cp -r /path/to/agentic-ai-i18n-package ./i18n

# Verify structure
ls -la i18n/
```

### Step 2: Install Backend Dependencies

```bash
cd backend

# Install Babel and related packages
pip install babel==2.13.0 python-babel==2.13.0

# Or add to requirements.txt
echo "babel>=2.13.0" >> requirements.txt
echo "python-babel>=2.13.0" >> requirements.txt
pip install -r requirements.txt
```

### Step 3: Install React Dependencies

```bash
cd ../frontend/react-admin

# Install i18next packages
npm install i18next react-i18next i18next-browser-languagedetector i18next-http-backend

# Or add to package.json and install
npm install
```

### Step 4: Setup Streamlit (No additional dependencies needed)

Streamlit i18n uses Python standard library only.

---

## 🔧 Backend Integration

### 1. Update `backend/app/main.py`

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import i18n
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "i18n"))

from backend.core.i18n import init_i18n
from backend.core.middleware import LocaleMiddleware

# Create app
app = FastAPI(
    title="Agentic AI Platform",
    version="1.3.0"
)

# Initialize i18n BEFORE adding middleware
init_i18n()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Locale middleware AFTER CORS
app.add_middleware(LocaleMiddleware)

# Your existing routes...
```

### 2. Update API Endpoints

```python
# backend/app/api/tenants.py
from fastapi import APIRouter, HTTPException
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "i18n"))
from backend.core.i18n import _, format_datetime

router = APIRouter()

@router.get("/tenants")
async def list_tenants():
    return {
        "message": _("Tenant list"),
        "tenants": [
            {
                "name": "Acme Corp",
                "created": format_datetime(tenant.created_at)
            }
        ]
    }

@router.post("/tenants")
async def create_tenant(tenant_data: dict):
    # ... create tenant logic ...
    return {
        "message": _("Tenant created successfully"),
        "tenant": tenant
    }
```

### 3. Create Translation Files

```bash
cd backend

# Create translations directory
mkdir -p ../i18n/backend/translations/{en,es,fr,de,ar,ja,zh}/LC_MESSAGES

# Extract translatable strings
pybabel extract -F ../i18n/backend/babel.cfg -o ../i18n/backend/translations/messages.pot .

# Initialize languages
for lang in es fr de ar ja zh; do
    pybabel init -i ../i18n/backend/translations/messages.pot \
                  -d ../i18n/backend/translations -l $lang
done

# Compile translations
pybabel compile -d ../i18n/backend/translations
```

---

## ⚛️ React Integration

### 1. Copy i18n Configuration

```bash
# Copy i18n config to React src
cp -r ../i18n/react/src/* frontend/react-admin/src/i18n/

# Create public locales directory
mkdir -p frontend/react-admin/public/locales
```

### 2. Update `main.tsx`

```typescript
// frontend/react-admin/src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Import i18n configuration (must be before App)
import './i18n/config/i18n'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

### 3. Add Language Selector to Layout

```typescript
// frontend/react-admin/src/components/Layout.tsx
import { LanguageSelector } from '../i18n/components/LanguageSelector'

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-layout">
      <header className="app-header">
        <h1>Agentic AI Platform</h1>
        <LanguageSelector variant="dropdown" />
      </header>
      
      <main className="app-content">
        {children}
      </main>
    </div>
  )
}
```

### 4. Use Translations in Components

```typescript
// frontend/react-admin/src/pages/Tenants.tsx
import { useTranslation } from 'react-i18next'

export function TenantsPage() {
  const { t } = useTranslation(['common', 'admin'])
  
  return (
    <div>
      <h1>{t('admin:title')}</h1>
      <p>{t('admin:subtitle')}</p>
      
      <button>{t('common:create')}</button>
      <button>{t('common:refresh')}</button>
    </div>
  )
}
```

### 5. Copy Translation Files

```bash
# Copy translations to public directory
cp ../i18n/react/src/locales/*.json \
   frontend/react-admin/public/locales/
```

---

## 🎯 Streamlit Integration

### 1. Update `streamlit-hitl/app.py`

```python
# frontend/streamlit-hitl/app.py
import streamlit as st
import sys
from pathlib import Path

# Add i18n to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "i18n"))

from streamlit.core.i18n import init_i18n, _, format_datetime_i18n
from streamlit.components.language_selector import render_language_selector

# Page config (must be first)
st.set_page_config(
    page_title="HITL Console",
    page_icon="👁️",
    layout="wide"
)

# Initialize i18n
init_i18n()

# Sidebar with language selector
with st.sidebar:
    render_language_selector()
    st.markdown("---")

# Main content
st.title(_("Human-in-the-Loop Console"))
st.write(_("Review and approve agent outputs"))
```

### 2. Update Streamlit Pages

```python
# frontend/streamlit-hitl/pages/1_🤖_Agents.py
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "i18n"))

from streamlit.core.i18n import init_i18n, _, _n
from streamlit.components.language_selector import render_language_selector

init_i18n()

st.set_page_config(page_title=_("Agents"), page_icon="🤖")

with st.sidebar:
    render_language_selector()

st.title(_("Agent Management"))

# Use pluralization
agent_count = 42
st.write(_n("You have {n} agent", "You have {n} agents", agent_count))
```

---

## 📝 Directory Structure After Integration

```
agentic-ai-platform-v1.3-complete/
├── i18n/                           # i18n package
│   ├── config/
│   ├── backend/
│   ├── react/
│   ├── streamlit/
│   └── docs/
│
├── backend/
│   └── app/
│       └── main.py                 # Updated with i18n
│
├── frontend/
│   ├── react-admin/
│   │   ├── src/
│   │   │   ├── i18n/              # i18n configuration
│   │   │   └── main.tsx           # Updated with i18n
│   │   └── public/
│   │       └── locales/           # Translation files
│   │
│   └── streamlit-hitl/
│       ├── app.py                 # Updated with i18n
│       └── pages/                 # Updated pages
│
└── README.md
```

---

## ✅ Verification

### Test Backend

```bash
cd backend
uvicorn app.main:app --reload

# Test API with different locales
curl http://localhost:8000/api/tenants \
  -H "Accept-Language: es"

curl http://localhost:8000/api/tenants?locale=fr
```

### Test React

```bash
cd frontend/react-admin
npm run dev

# Open http://localhost:3000
# Change language using selector
# Verify translations update
```

### Test Streamlit

```bash
cd frontend/streamlit-hitl
streamlit run app.py

# Open http://localhost:8501
# Use sidebar language selector
# Verify translations update
```

---

## 🔄 Adding New Translations

### Backend

```bash
cd backend

# Update source code with _("New message")

# Extract new strings
pybabel extract -F ../i18n/backend/babel.cfg \
  -o ../i18n/backend/translations/messages.pot .

# Update all language files
pybabel update -i ../i18n/backend/translations/messages.pot \
  -d ../i18n/backend/translations

# Edit PO files and add translations
nano ../i18n/backend/translations/es/LC_MESSAGES/messages.po

# Compile
pybabel compile -d ../i18n/backend/translations
```

### React

```bash
# Edit translation files
nano frontend/react-admin/public/locales/en.json
nano frontend/react-admin/public/locales/es.json

# Restart dev server
npm run dev
```

### Streamlit

```python
# Add translations programmatically
from streamlit.core.i18n import update_translations

spanish_translations = {
    "New Feature": "Nueva Característica",
    "Another Message": "Otro Mensaje"
}

update_translations("es", spanish_translations)
```

---

## 🐛 Troubleshooting

### Issue: Translations not loading

**Solution:**
1. Check file paths are correct
2. Verify locale codes match
3. Check browser console for errors
4. Restart development servers

### Issue: RTL not working for Arabic

**Solution:**
1. Verify language code is 'ar'
2. Check CSS is loaded
3. Inspect document `dir` attribute
4. Clear browser cache

### Issue: Backend locale not detected

**Solution:**
1. Verify middleware is added
2. Check middleware order (CORS before LocaleMiddleware)
3. Send Accept-Language header
4. Use ?locale=es query parameter

---

## 📚 Next Steps

1. **Customize translations** for your application
2. **Add more languages** as needed
3. **Set up CI/CD** for automated translation updates
4. **Review documentation** for advanced features

---

## 🆘 Support

- Documentation: `i18n/docs/`
- Issues: Report on GitHub
- Email: support@agenticai.com

---

**Integration Complete! 🎉**
