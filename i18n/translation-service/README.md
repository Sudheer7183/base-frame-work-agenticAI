# 🌐 Auto-Translation Service (Optional Add-on)

**Automatically translate your i18n keys using AI translation services**

## 📋 Overview

This is an **optional module** for the Agentic AI i18n package that adds automatic translation capabilities. It allows you to:

✅ Auto-translate missing translation keys  
✅ Support multiple translation providers  
✅ Cache translations to save API costs  
✅ Batch process for efficiency  
✅ Keep manual translations intact  

---

## 🎯 Key Features

### 1. Multiple Providers
- **Google Cloud Translation** - 100+ languages, high quality
- **DeepL** - 30+ languages, highest quality
- **LibreTranslate** - 30+ languages, free (self-hosted)

### 2. Intelligent Processing
- ✅ **Batch translation** - Process multiple texts at once
- ✅ **Translation caching** - Never translate the same text twice
- ✅ **Skip existing** - Only translate missing keys
- ✅ **Preserve manual** - Manual translations are never overwritten

### 3. Cost Management
- ✅ **Usage tracking** - Monitor characters translated
- ✅ **Cost estimation** - Know costs before translating
- ✅ **Cache efficiency** - Reduce API calls by 80%+

### 4. Easy to Use
- ✅ **CLI tool** - Simple command-line interface
- ✅ **Python API** - Programmatic access
- ✅ **Validation** - Check translation completeness

---

## 📦 Installation

### Base Dependencies

```bash
pip install click requests
```

### Provider-Specific Dependencies

**Google Cloud Translation:**
```bash
pip install google-cloud-translate
```

**DeepL:**
```bash
pip install deepl
```

**LibreTranslate** (self-hosted):
```bash
# No additional dependencies - uses HTTP API
# Or run with Docker:
docker run -ti --rm -p 5000:5000 libretranslate/libretranslate
```

---

## 🚀 Quick Start

### Option 1: CLI Tool (Easiest)

```bash
# Translate React locales using DeepL
python -m translation-service.tools.cli translate \
  --provider deepl \
  --api-key YOUR_DEEPL_KEY \
  --locales-dir ./react/src/locales \
  --target-langs es,fr,de

# Translate using free LibreTranslate (self-hosted)
python -m translation-service.tools.cli translate \
  --provider libre \
  --api-url http://localhost:5000 \
  --locales-dir ./react/src/locales \
  --target-langs es,fr,de

# Dry run (preview without translating)
python -m translation-service.tools.cli translate \
  --provider deepl \
  --api-key YOUR_KEY \
  --locales-dir ./react/src/locales \
  --target-langs es \
  --dry-run
```

### Option 2: Python API

```python
from translation_service.core.translator import create_translation_manager

# Create translation manager
manager = create_translation_manager(
    provider_name='deepl',
    api_key='your-api-key'
)

# Translate single text
translated = manager.translate(
    "Welcome to our platform",
    source_lang='en',
    target_lang='es'
)
print(translated)  # "Bienvenido a nuestra plataforma"

# Translate batch
texts = ["Hello", "Welcome", "Thank you"]
translated = manager.translate_batch(
    texts,
    source_lang='en',
    target_lang='fr'
)
print(translated)  # ["Bonjour", "Bienvenue", "Merci"]

# Get statistics
stats = manager.get_stats()
print(f"Characters translated: {stats['characters_translated']}")
print(f"Estimated cost: ${stats['estimated_cost_usd']:.2f}")
```

---

## 🛠️ Translation Workflow

### Step 1: Write Your Code (English)

```typescript
// React component with English text
function Welcome() {
  const { t } = useTranslation();
  return <h1>{t('welcome.title')}</h1>;
}
```

### Step 2: Create English Translations

```json
// locales/en.json
{
  "welcome": {
    "title": "Welcome to Agentic AI Platform"
  }
}
```

### Step 3: Auto-Translate Missing Languages

```bash
# Auto-translate to Spanish, French, German
python -m translation-service.tools.cli translate \
  --provider deepl \
  --api-key YOUR_KEY \
  --locales-dir ./react/src/locales \
  --target-langs es,fr,de
```

### Step 4: Review and Adjust

```json
// locales/es.json (auto-generated)
{
  "welcome": {
    "title": "Bienvenido a la Plataforma Agentic AI"
  }
}

// You can manually adjust if needed
{
  "welcome": {
    "title": "Bienvenido a Agentic AI"  // ✓ Manual edit preserved!
  }
}
```

### Step 5: Re-run Safely

```bash
# Run again - only translates NEW keys
# Your manual edits are preserved!
python -m translation-service.tools.cli translate \
  --provider deepl \
  --api-key YOUR_KEY \
  --locales-dir ./react/src/locales \
  --target-langs es,fr,de \
  --skip-existing  # Default: preserves existing translations
```

---

## 📊 Provider Comparison

| Provider | Languages | Quality | Cost | Setup |
|----------|-----------|---------|------|-------|
| **Google Cloud** | 100+ | High | $20/1M chars | API key or service account |
| **DeepL** | 30+ | Highest | $22/1M chars | API key from deepl.com |
| **LibreTranslate** | 30+ | Medium | Free (self-hosted) | Docker or public API |

### Recommendations

**Best Quality:** DeepL  
**Most Languages:** Google Cloud Translation  
**Free/Privacy:** LibreTranslate (self-hosted)  
**Best Value:** Google Cloud Translation  

---

## 💰 Cost Examples

### Example 1: Small App
- **Keys**: 100 keys
- **Languages**: 3 additional languages (es, fr, de)
- **Avg length**: 20 characters per key
- **Total**: 100 × 20 × 3 = 6,000 characters

**Cost**: < $0.20 USD with any provider

### Example 2: Large App
- **Keys**: 500 keys
- **Languages**: 6 additional languages
- **Avg length**: 30 characters per key
- **Total**: 500 × 30 × 6 = 90,000 characters

**Cost**: ~$2.00 USD with any provider

### Example 3: Enterprise App
- **Keys**: 2,000 keys
- **Languages**: 6 additional languages
- **Avg length**: 40 characters per key
- **Total**: 2,000 × 40 × 6 = 480,000 characters

**Cost**: ~$10.00 USD with any provider

**With 80% cache hit rate on updates**: < $2.00 USD

---

## 🔧 Advanced Usage

### Programmatic Translation

```python
from translation_service.core.translator import create_translation_manager
import json

# Initialize
manager = create_translation_manager('deepl', api_key='YOUR_KEY')

# Load source translations
with open('locales/en.json', 'r') as f:
    en_translations = json.load(f)

# Translate to Spanish
es_translations = {}
for key, value in en_translations.items():
    if isinstance(value, str):
        es_translations[key] = manager.translate(value, 'en', 'es')
    elif isinstance(value, dict):
        # Handle nested translations
        es_translations[key] = translate_nested(manager, value, 'en', 'es')

# Save
with open('locales/es.json', 'w') as f:
    json.dump(es_translations, f, indent=2, ensure_ascii=False)
```

### Custom Provider

```python
from translation_service.core.translator import TranslationProvider

class MyCustomProvider(TranslationProvider):
    def _initialize(self):
        # Setup your provider
        pass
    
    def translate_text(self, text, source_lang, target_lang):
        # Your translation logic
        return translated_text
    
    def translate_batch(self, texts, source_lang, target_lang):
        # Batch translation
        return translated_texts
    
    def get_supported_languages(self):
        return ['en', 'es', 'fr']
    
    def get_usage_stats(self):
        return {"provider": "Custom"}

# Use it
from translation_service.core.translator import TranslationManager

provider = MyCustomProvider()
manager = TranslationManager(provider)
```

---

## 🎯 Best Practices

### 1. Use Caching
✅ Enable cache (default)  
✅ Cache saves 80%+ on subsequent runs  
✅ Especially important for development  

### 2. Batch Processing
✅ Translate multiple files at once  
✅ More efficient than one-by-one  
✅ Better API rate limits  

### 3. Manual Review
✅ Always review auto-translations  
✅ Adjust for context and brand voice  
✅ Manual edits are preserved on re-run  

### 4. Start Small
✅ Test with 1-2 languages first  
✅ Validate quality before scaling  
✅ Use dry-run to preview  

### 5. Version Control
✅ Commit auto-translated files  
✅ Review diffs before merging  
✅ Track translation history  

---

## 📚 CLI Commands

### Translate
```bash
# Basic usage
cli translate --provider deepl --api-key KEY --locales-dir ./locales --target-langs es,fr

# All options
cli translate \
  --provider deepl \              # Provider: google, deepl, libre
  --api-key YOUR_KEY \            # API key
  --source-lang en \              # Source language (default: en)
  --target-langs es,fr,de \       # Target languages (comma-separated)
  --locales-dir ./locales \       # Directory with locale files
  --skip-existing \               # Skip existing translations (default)
  --dry-run                       # Preview without translating
```

### Validate
```bash
# Check translation completeness
cli validate --locales-dir ./react/src/locales
```

### List Providers
```bash
# Show available providers
cli providers
```

---

## 🔒 Security & Privacy

### API Keys
- Never commit API keys to git
- Use environment variables:
  ```bash
  export DEEPL_API_KEY="your-key"
  cli translate --provider deepl --api-key $DEEPL_API_KEY ...
  ```

### Self-Hosted Option
- Use LibreTranslate for complete privacy
- All data stays on your servers
- No external API calls
- Free and open source

---

## ❓ FAQ

**Q: Will auto-translation overwrite my manual translations?**  
A: No! With `--skip-existing` (default), only missing keys are translated.

**Q: What if I don't like an auto-translation?**  
A: Just edit it manually. Your changes are preserved on subsequent runs.

**Q: How accurate are the translations?**  
A: DeepL offers the highest quality (~95% accuracy for common languages). Google is also excellent (~90%). LibreTranslate is good (~80%) for a free option.

**Q: Can I translate backend PO files?**  
A: Yes! The service can be extended to translate PO files. Current version focuses on JSON (React/frontend).

**Q: Does it support placeholders like {{variable}}?**  
A: Yes! Translation providers preserve special syntax like `{{name}}`, `{count}`, etc.

**Q: What about pluralization?**  
A: You'll need to translate each plural form separately. The service preserves the structure.

---

## 🆘 Troubleshooting

### Error: API key invalid
```bash
# Check your API key
# Google: Ensure Cloud Translation API is enabled
# DeepL: Verify key from account settings
# LibreTranslate: Check server is running
```

### Error: Rate limit exceeded
```bash
# Use caching to reduce calls
# Translate in smaller batches
# Wait and retry
```

### Error: Language not supported
```bash
# Check supported languages:
cli providers

# Or programmatically:
manager.provider.get_supported_languages()
```

---

## 📄 License

MIT License - Same as main i18n package

---

## 🔗 Resources

- [Google Cloud Translation](https://cloud.google.com/translate)
- [DeepL API](https://www.deepl.com/pro-api)
- [LibreTranslate](https://libretranslate.com/)

---

**Made with ❤️ for the Agentic AI Platform**
