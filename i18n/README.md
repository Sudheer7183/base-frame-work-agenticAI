# 🌍 Agentic AI Platform - Production i18n Package v3.0

Complete internationalization framework for the Agentic AI Platform with unified support across Backend (FastAPI), React Admin, and Streamlit HITL interfaces.

## 🎯 Features

- ✅ **Unified Architecture** - Consistent i18n across all platform components
- ✅ **7 Languages** - English, Spanish, French, German, Arabic, Japanese, Chinese
- ✅ **RTL Support** - Full right-to-left layout support for Arabic
- ✅ **Type Safety** - Full TypeScript support with auto-completion
- ✅ **Production Ready** - Battle-tested patterns and best practices
- ✅ **Developer Tools** - CLI for translation management and validation
- ✅ **Hot Reload** - Development mode with instant translation updates

## 📦 Package Structure

```
i18n-package/
├── config/                   # Shared configuration
│   ├── languages.yaml       # Language definitions
│   └── namespaces.yaml      # Translation namespaces
│
├── backend/                 # FastAPI i18n (Babel)
│   ├── core/               # Core i18n modules
│   ├── translations/       # PO/MO files
│   └── tests/             # Unit tests
│
├── react/                  # React i18n (i18next)
│   ├── src/
│   │   ├── config/        # i18next configuration
│   │   ├── hooks/         # React hooks
│   │   ├── components/    # UI components
│   │   └── locales/       # Translation JSON files
│   └── tests/
│
├── streamlit/             # Streamlit i18n (Babel)
│   ├── core/             # Core i18n modules
│   ├── components/       # Streamlit components
│   └── translations/     # Translation files
│
├── tools/                # Development tools
│   ├── scripts/         # Automation scripts
│   ├── cli/            # Command-line tool
│   └── dashboard/      # Translation management UI
│
└── docs/               # Documentation
    ├── getting-started.md
    ├── backend-guide.md
    ├── react-guide.md
    └── streamlit-guide.md
```

## 🚀 Quick Start

### Backend (FastAPI)

```python
from backend.core.i18n import init_i18n, _, format_date
from backend.core.middleware import LocaleMiddleware

# Initialize i18n
init_i18n()

# Add middleware to FastAPI app
app.add_middleware(LocaleMiddleware)

# Use in endpoints
@app.get("/welcome")
async def welcome():
    return {"message": _("Welcome to Agentic AI Platform")}
```

### React

```typescript
import { I18nextProvider } from 'react-i18next';
import i18n from './config/i18n';
import { LanguageSelector } from './components/LanguageSelector';

function App() {
  return (
    <I18nextProvider i18n={i18n}>
      <LanguageSelector />
      {/* Your app content */}
    </I18nextProvider>
  );
}
```

### Streamlit

```python
from streamlit.core.i18n import init_i18n, _, format_datetime_i18n
from streamlit.components.language_selector import render_language_selector

# Initialize
init_i18n()

# Add language selector to sidebar
with st.sidebar:
    render_language_selector()

# Use translations
st.title(_("Agent Management"))
```

## 🌐 Supported Languages

| Code | Language | Native Name | Direction | Status |
|------|----------|-------------|-----------|---------|
| `en` | English | English | LTR | ✅ Complete |
| `es` | Spanish | Español | LTR | ✅ Complete |
| `fr` | French | Français | LTR | ✅ Complete |
| `de` | German | Deutsch | LTR | ✅ Complete |
| `ar` | Arabic | العربية | RTL | ✅ Complete |
| `ja` | Japanese | 日本語 | LTR | ✅ Complete |
| `zh` | Chinese | 中文 | LTR | ✅ Complete |

## 🛠️ Development Tools

### CLI Tool

```bash
# Extract translatable strings
python -m tools.cli extract --all

# Sync translations across platforms
python -m tools.cli sync

# Validate translation files
python -m tools.cli validate

# Compile translations
python -m tools.cli compile

# Export to various formats
python -m tools.cli export --format json
```

### Translation Dashboard

```bash
# Start the translation management UI
python -m tools.dashboard.app
```

## 📚 Documentation

- [Getting Started Guide](docs/getting-started.md)
- [Backend Integration](docs/backend-guide.md)
- [React Integration](docs/react-guide.md)
- [Streamlit Integration](docs/streamlit-guide.md)
- [RTL Support](docs/rtl-guide.md)
- [Translation Workflow](docs/translation-workflow.md)
- [API Reference](docs/api-reference.md)
- [Best Practices](docs/best-practices.md)

## 🔧 Installation

### Backend Dependencies

```bash
pip install babel python-babel gettext
```

### React Dependencies

```bash
npm install i18next react-i18next i18next-browser-languagedetector i18next-http-backend
```

### Development Tools

```bash
pip install pyyaml click rich tabulate
npm install -D @types/i18next @types/react-i18next
```

## 🎨 Key Features

### Context-Aware Translations

```python
# Backend
from backend.core.i18n import pgettext

button_save = pgettext("button", "Save")  # Context: button
menu_save = pgettext("menu", "Save")      # Context: menu
```

```typescript
// React
const { t } = useTranslation();
const buttonSave = t('Save', { context: 'button' });
const menuSave = t('Save', { context: 'menu' });
```

### Pluralization

```python
# Backend
from backend.core.i18n import ngettext

message = ngettext(
    "You have {n} pending task",
    "You have {n} pending tasks",
    count
)
```

```typescript
// React
const message = t('pendingTasks', { count: 5 });
// Translation: "pendingTasks_one": "You have {{count}} pending task"
//              "pendingTasks_other": "You have {{count}} pending tasks"
```

### Formatted Values

```python
# Backend - Dates, Numbers, Currency
from backend.core.i18n import format_date, format_currency

formatted_date = format_date(datetime.now(), format="long")
formatted_price = format_currency(99.99, "USD")
```

```typescript
// React
const formattedDate = t('createdAt', { 
  date: new Date(), 
  formatParams: { date: { format: 'long' } } 
});

const formattedPrice = t('price', { 
  val: 99.99, 
  formatParams: { val: { style: 'currency', currency: 'USD' } } 
});
```

### RTL Support

```typescript
// React - Automatic RTL detection
import { useRTL } from './hooks/useRTL';

function MyComponent() {
  const { isRTL, direction } = useRTL();
  
  return (
    <div dir={direction} className={isRTL ? 'rtl' : 'ltr'}>
      {/* Content automatically adjusts */}
    </div>
  );
}
```

```python
# Streamlit - RTL styling
from streamlit.core.i18n import is_rtl, get_current_locale

if is_rtl(get_current_locale()):
    st.markdown('<div dir="rtl">', unsafe_allow_html=True)
```

## 🔄 Translation Workflow

1. **Extract** - Extract translatable strings from source code
2. **Translate** - Professional translators work on PO/JSON files
3. **Review** - Quality assurance and validation
4. **Compile** - Compile to optimized MO/JSON files
5. **Deploy** - Deploy with application

## 📊 Translation Progress

Track translation progress with the included dashboard:

```bash
python -m tools.dashboard.app
```

Features:
- Real-time progress tracking per language
- Missing translation detection
- Consistency validation
- Export/import capabilities

## 🧪 Testing

```bash
# Backend tests
pytest backend/tests/

# React tests
npm test --prefix react/

# Streamlit tests
pytest streamlit/tests/
```

## 🤝 Contributing

1. Add new translations to appropriate locale files
2. Run validation: `python -m tools.cli validate`
3. Test in all supported languages
4. Submit PR with translation updates

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Support

- Documentation: [docs/](docs/)
- Issues: GitHub Issues
- Email: support@agenticai.com

## 🔗 Resources

- [i18next Documentation](https://www.i18next.com/)
- [Babel Documentation](http://babel.pocoo.org/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Unicode CLDR](http://cldr.unicode.org/)

---

**Version:** 3.0.0  
**Last Updated:** 2026-01-01  
**Maintainer:** Agentic AI Platform Team

---

## 🤖 Optional: Auto-Translation Service

**NEW!** Automatically translate missing keys using AI translation services.

### Quick Example

```bash
# Auto-translate all missing keys to Spanish, French, German
python -m translation-service.tools.cli translate \
  --provider deepl \
  --api-key YOUR_KEY \
  --locales-dir ./react/src/locales \
  --target-langs es,fr,de
```

### Features

✅ **Multiple Providers**: Google, DeepL, LibreTranslate (free)  
✅ **Smart Caching**: Never translate the same text twice  
✅ **Preserves Manual Edits**: Your manual translations are never overwritten  
✅ **Cost Effective**: Typical cost < $10 for entire app  
✅ **Free Option**: Self-host LibreTranslate  

### Documentation

See [translation-service/README.md](translation-service/README.md) for complete documentation.

**Note**: This is an optional add-on. You can use manual translations only if preferred.

