# Getting Started with Agentic AI i18n Package

Complete guide to implementing internationalization in your Agentic AI Platform application.

## 📋 Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Backend Setup (FastAPI)](#backend-setup)
4. [React Setup](#react-setup)
5. [Streamlit Setup](#streamlit-setup)
6. [Translation Workflow](#translation-workflow)
7. [Testing](#testing)

---

## Installation

### Backend Dependencies

```bash
# Install Babel for backend i18n
pip install babel python-babel

# Or install from requirements
cd backend
pip install -r requirements.txt
```

### React Dependencies

```bash
# Install i18next and related packages
cd react
npm install i18next react-i18next i18next-browser-languagedetector i18next-http-backend

# Or install from package.json
npm install
```

### Streamlit

No additional dependencies required - uses Python standard library + Streamlit.

---

## Quick Start

### 1. Copy Package to Your Project

```bash
# Copy the entire i18n package to your project
cp -r agentic-ai-i18n-package /path/to/your/project/i18n
```

### 2. Backend Integration (5 minutes)

```python
# backend/app/main.py
from fastapi import FastAPI
from i18n.backend.core.i18n import init_i18n
from i18n.backend.core.middleware import LocaleMiddleware

# Create FastAPI app
app = FastAPI()

# Initialize i18n
init_i18n()

# Add locale middleware
app.add_middleware(LocaleMiddleware)

# Use translations in endpoints
from i18n.backend.core.i18n import _

@app.get("/welcome")
async def welcome():
    return {"message": _("Welcome to Agentic AI Platform")}
```

### 3. React Integration (5 minutes)

```typescript
// frontend/react-admin/src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { I18nextProvider } from 'react-i18next';
import i18n from './i18n/config/i18n';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <I18nextProvider i18n={i18n}>
      <App />
    </I18nextProvider>
  </React.StrictMode>
);

// Use in components
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();
  
  return (
    <div>
      <h1>{t('common:welcome')}</h1>
      <button>{t('common:save')}</button>
    </div>
  );
}
```

### 4. Streamlit Integration (5 minutes)

```python
# frontend/streamlit-hitl/app.py
import streamlit as st
from i18n.streamlit.core.i18n import init_i18n, _
from i18n.streamlit.components.language_selector import render_language_selector

# Initialize i18n
init_i18n()

# Add language selector to sidebar
with st.sidebar:
    render_language_selector()

# Use translations
st.title(_("Human-in-the-Loop Console"))
st.write(_("Welcome to the HITL interface"))
```

---

## Backend Setup

### Directory Structure

```
backend/
├── i18n/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── i18n.py          # Core i18n module
│   │   └── middleware.py    # FastAPI middleware
│   ├── translations/
│   │   ├── en/LC_MESSAGES/
│   │   ├── es/LC_MESSAGES/
│   │   └── ...
│   └── babel.cfg            # Babel configuration
```

### 1. Initialize i18n in Your App

```python
# backend/app/main.py
from fastapi import FastAPI
from i18n.backend.core.i18n import init_i18n
from i18n.backend.core.middleware import LocaleMiddleware

app = FastAPI()

# Initialize i18n system
init_i18n()

# Add middleware
app.add_middleware(LocaleMiddleware)
```

### 2. Use Translations in Endpoints

```python
from i18n.backend.core.i18n import _, _n, format_date, format_currency

@app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    return {
        "message": _("Product details"),
        "price": format_currency(99.99, "USD"),
        "updated": format_date(datetime.now())
    }

@app.get("/api/cart")
async def get_cart():
    item_count = 5
    return {
        "message": _n(
            "You have {n} item in your cart",
            "You have {n} items in your cart",
            item_count
        )
    }
```

### 3. Extract Translatable Strings

```bash
# Extract strings from Python files
cd backend
pybabel extract -F babel.cfg -o translations/messages.pot .

# Initialize new language
pybabel init -i translations/messages.pot -d translations -l es

# Update existing translations
pybabel update -i translations/messages.pot -d translations

# Compile translations
pybabel compile -d translations
```

---

## React Setup

### Directory Structure

```
react/
├── src/
│   ├── i18n/
│   │   ├── config/
│   │   │   └── i18n.ts      # i18next config
│   │   ├── components/
│   │   │   └── LanguageSelector/
│   │   └── locales/
│   │       ├── en.json
│   │       ├── es.json
│   │       └── ...
```

### 1. Configure i18next

Already configured in `react/src/config/i18n.ts`. Just import it:

```typescript
// src/main.tsx
import './i18n/config/i18n';
```

### 2. Use Translations in Components

```typescript
import { useTranslation } from 'react-i18next';

function TenantCard() {
  const { t } = useTranslation(['common', 'admin']);
  
  return (
    <div>
      <h2>{t('admin:tenants.title')}</h2>
      <button>{t('common:create')}</button>
      <p>{t('admin:tenants.list')}</p>
    </div>
  );
}
```

### 3. Add Language Selector

```typescript
import { LanguageSelector } from './i18n/components/LanguageSelector';

function App() {
  return (
    <div>
      <header>
        <LanguageSelector />
      </header>
      {/* Rest of your app */}
    </div>
  );
}
```

### 4. Format Values

```typescript
import { useTranslation } from 'react-i18next';

function Dashboard() {
  const { t, i18n } = useTranslation();
  
  return (
    <div>
      {/* Format dates */}
      <p>{t('createdAt', { 
        date: new Date(), 
        formatParams: { date: { format: 'long' } } 
      })}</p>
      
      {/* Format currency */}
      <p>{t('price', { 
        val: 99.99, 
        formatParams: { val: { style: 'currency', currency: 'USD' } } 
      })}</p>
      
      {/* Pluralization */}
      <p>{t('itemCount', { count: 5 })}</p>
    </div>
  );
}
```

---

## Streamlit Setup

### Directory Structure

```
streamlit/
├── i18n/
│   ├── core/
│   │   ├── __init__.py
│   │   └── i18n.py          # Core i18n module
│   ├── components/
│   │   └── language_selector.py
│   └── translations/
```

### 1. Initialize in Your App

```python
# streamlit_app.py
import streamlit as st
from i18n.streamlit.core.i18n import init_i18n, _
from i18n.streamlit.components.language_selector import render_language_selector

# Must be first Streamlit command
st.set_page_config(page_title=_("HITL Console"), layout="wide")

# Initialize i18n
init_i18n()

# Add language selector
with st.sidebar:
    render_language_selector()
```

### 2. Use Translations

```python
from i18n.streamlit.core.i18n import _, _n, format_datetime_i18n

# Simple translation
st.title(_("Human-in-the-Loop Console"))

# Pluralization
count = 5
st.write(_n("You have {n} pending review", "You have {n} pending reviews", count))

# Format datetime
st.write(_("Last updated: ") + format_datetime_i18n(datetime.now(), "long"))

# Format currency
from i18n.streamlit.core.i18n import format_currency_i18n
st.write(_("Total: ") + format_currency_i18n(1234.56, "USD"))
```

### 3. Add Custom Translations

```python
from i18n.streamlit.core.i18n import update_translations

# Add Spanish translations
spanish_translations = {
    "Dashboard": "Panel de Control",
    "Settings": "Configuración",
    "Agents": "Agentes",
}

update_translations("es", spanish_translations)
```

---

## Translation Workflow

### 1. Development Phase

1. Write code with translation keys
2. Extract translatable strings
3. Test with default language

### 2. Translation Phase

1. Send PO files to translators
2. Review translations
3. Compile updated translations

### 3. Deployment Phase

1. Include compiled MO files
2. Test all languages
3. Deploy with confidence

---

## Testing

### Backend Tests

```python
# tests/test_i18n.py
from i18n.backend.core.i18n import set_locale, gettext as _

def test_spanish_translation():
    set_locale('es')
    assert _("Hello") == "Hola"

def test_pluralization():
    set_locale('en')
    message = _n("You have {n} message", "You have {n} messages", 5)
    assert "messages" in message
```

### React Tests

```typescript
// tests/i18n.test.tsx
import { render } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import i18n from '../i18n/config/i18n';

test('renders translated text', () => {
  const { getByText } = render(
    <I18nextProvider i18n={i18n}>
      <MyComponent />
    </I18nextProvider>
  );
  
  expect(getByText('Welcome')).toBeInTheDocument();
});
```

### Streamlit Tests

```python
# tests/test_streamlit_i18n.py
from i18n.streamlit.core.i18n import set_locale, gettext as _

def test_translation():
    set_locale('fr')
    assert _("Hello") == "Bonjour"
```

---

## Next Steps

1. **Read the detailed guides:**
   - [Backend Guide](backend-guide.md)
   - [React Guide](react-guide.md)
   - [Streamlit Guide](streamlit-guide.md)

2. **Learn about RTL support:**
   - [RTL Guide](rtl-guide.md)

3. **Set up translation workflow:**
   - [Translation Workflow](translation-workflow.md)

4. **Explore best practices:**
   - [Best Practices](best-practices.md)

---

## 🆘 Troubleshooting

### Translations not loading?

1. Check file paths
2. Verify locale code format
3. Check browser console for errors
4. Ensure files are properly compiled

### RTL not working?

1. Check language code is in RTL_LANGUAGES
2. Verify CSS is loaded
3. Check document direction attribute

### Performance issues?

1. Enable translation caching
2. Preload critical languages
3. Lazy load non-essential namespaces

---

## 📞 Support

- Documentation: [docs/](.)
- Issues: GitHub Issues
- Email: support@agenticai.com

---

**Happy Translating! 🌍**
