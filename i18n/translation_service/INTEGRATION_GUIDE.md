# 🤖 Translation Service Integration Guide

Complete guide for using the auto-translation service with your Agentic AI Platform i18n package.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Provider Setup](#provider-setup)
4. [Usage Examples](#usage-examples)
5. [Integration Workflow](#integration-workflow)
6. [Best Practices](#best-practices)

---

## Overview

The translation service is an **optional add-on** that:
- ✅ Automatically translates missing translation keys
- ✅ Preserves manual translations
- ✅ Supports multiple AI translation providers
- ✅ Caches results to save costs
- ✅ Works with React, Backend, and Streamlit

**Key Principle**: Manual translations are NEVER overwritten. The service only fills in missing keys.

---

## Installation

### Step 1: Base Requirements

```bash
cd /path/to/agentic-ai-platform/i18n/translation-service
pip install -r requirements.txt
```

This installs:
- `click` - CLI framework
- `requests` - HTTP client for LibreTranslate

### Step 2: Provider-Specific Installation

Choose ONE or more providers:

#### Option A: DeepL (Recommended for Quality)

```bash
pip install deepl
```

Get API key:
1. Sign up at https://www.deepl.com/pro-api
2. Choose Free (500k chars/month) or Pro plan
3. Copy API key from account settings

#### Option B: Google Cloud Translation

```bash
pip install google-cloud-translate
```

Setup:
1. Enable Cloud Translation API in Google Cloud Console
2. Create service account and download JSON key
3. Set environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
   ```

Or use API key directly

#### Option C: LibreTranslate (Free/Self-Hosted)

```bash
# No additional installation needed!

# Option 1: Use public API (limited)
# Just use --api-url https://libretranslate.com

# Option 2: Self-host with Docker (unlimited, recommended)
docker run -ti --rm -p 5000:5000 libretranslate/libretranslate

# Then use --api-url http://localhost:5000
```

---

## Provider Setup

### DeepL Setup

```bash
# Set environment variable
export DEEPL_API_KEY="your-api-key-here"

# Test connection
python -m translation_service.tools.cli translate \
  --provider deepl \
  --api-key $DEEPL_API_KEY \
  --locales-dir ./react/src/locales \
  --target-langs es \
  --dry-run
```

### Google Cloud Setup

```bash
# Method 1: Service Account (recommended)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# Method 2: API Key
export GOOGLE_API_KEY="your-api-key"

# Test
python -m translation_service.tools.cli translate \
  --provider google \
  --locales-dir ./react/src/locales \
  --target-langs es \
  --dry-run
```

### LibreTranslate Setup

```bash
# Start self-hosted server
docker run -d -p 5000:5000 libretranslate/libretranslate

# Test
python -m translation_service.tools.cli translate \
  --provider libre \
  --api-url http://localhost:5000 \
  --locales-dir ./react/src/locales \
  --target-langs es \
  --dry-run
```

---

## Usage Examples

### Example 1: Translate React Locales

```bash
# Scenario: You have English translations, need Spanish, French, German

cd /path/to/agentic-ai-platform

# Translate using DeepL
python -m i18n.translation-service.tools.cli translate \
  --provider deepl \
  --api-key $DEEPL_API_KEY \
  --locales-dir ./frontend/react-admin/src/i18n/locales \
  --target-langs es,fr,de

# Result:
# ✓ locales/es.json created/updated
# ✓ locales/fr.json created/updated
# ✓ locales/de.json created/updated
```

### Example 2: Add One New Language

```bash
# Scenario: You already have es, fr, de. Now adding Japanese.

python -m i18n.translation-service.tools.cli translate \
  --provider google \
  --api-key $GOOGLE_API_KEY \
  --locales-dir ./frontend/react-admin/src/i18n/locales \
  --target-langs ja

# Result:
# ✓ locales/ja.json created with all translations
```

### Example 3: Update After Adding New Keys

```bash
# Scenario: You added 10 new English keys. Need to translate them.

# Step 1: Add new keys to en.json
{
  "newFeature": {
    "title": "New Feature",
    "description": "This is our new feature"
  }
}

# Step 2: Auto-translate (only new keys)
python -m i18n.translation-service.tools.cli translate \
  --provider deepl \
  --api-key $DEEPL_API_KEY \
  --locales-dir ./frontend/react-admin/src/i18n/locales \
  --target-langs es,fr,de,ja,zh \
  --skip-existing  # Default: preserves existing translations

# Result:
# ✓ Only "newFeature" section translated in each language
# ✓ All existing translations preserved
```

### Example 4: Use Free LibreTranslate

```bash
# Start LibreTranslate server
docker run -d -p 5000:5000 libretranslate/libretranslate

# Translate
python -m i18n.translation-service.tools.cli translate \
  --provider libre \
  --api-url http://localhost:5000 \
  --locales-dir ./frontend/react-admin/src/i18n/locales \
  --target-langs es,fr,de

# No API key needed!
# No usage limits!
# Completely free!
```

### Example 5: Programmatic Usage

```python
# In your Python script
import sys
from pathlib import Path

# Add i18n to path
sys.path.insert(0, str(Path(__file__).parent / "i18n"))

from translation_service.core.translator import create_translation_manager
import json

# Create manager
manager = create_translation_manager(
    provider_name='deepl',
    api_key='your-api-key'
)

# Load English translations
with open('locales/en.json', 'r') as f:
    en_data = json.load(f)

# Translate to Spanish
es_data = {}
for key, value in en_data.items():
    if isinstance(value, str):
        es_data[key] = manager.translate(value, 'en', 'es')

# Save
with open('locales/es.json', 'w') as f:
    json.dump(es_data, f, indent=2, ensure_ascii=False)

# Check stats
stats = manager.get_stats()
print(f"Translated {stats['characters_translated']} characters")
print(f"Estimated cost: ${stats['estimated_cost_usd']:.2f}")
```

---

## Integration Workflow

### Workflow 1: New Project Setup

```bash
# 1. Create English translations manually
# Edit: frontend/react-admin/src/i18n/locales/en.json

# 2. Auto-translate to all target languages
python -m i18n.translation-service.tools.cli translate \
  --provider deepl \
  --api-key $DEEPL_API_KEY \
  --locales-dir ./frontend/react-admin/src/i18n/locales \
  --target-langs es,fr,de,ar,ja,zh

# 3. Review and adjust
# Manually edit any translations that need improvement

# 4. Commit to git
git add frontend/react-admin/src/i18n/locales/*.json
git commit -m "Add auto-translated locales"
```

### Workflow 2: Continuous Development

```bash
# Developer adds new features with English text

# 1. Add new English keys
# en.json: "newFeature.title": "New Feature"

# 2. Run auto-translation (only translates new keys)
python -m i18n.translation-service.tools.cli translate \
  --provider deepl \
  --api-key $DEEPL_API_KEY \
  --locales-dir ./frontend/react-admin/src/i18n/locales \
  --target-langs es,fr,de,ar,ja,zh

# 3. Commit
git add frontend/react-admin/src/i18n/locales/*.json
git commit -m "Auto-translate new feature strings"
```

### Workflow 3: Manual Override

```bash
# Sometimes auto-translation isn't perfect

# 1. Manually edit translation
# es.json: "newFeature.title": "Nueva Característica" → "Nueva Función"

# 2. Run auto-translation again (adds new keys only)
python -m i18n.translation-service.tools.cli translate \
  --provider deepl \
  --api-key $DEEPL_API_KEY \
  --locales-dir ./frontend/react-admin/src/i18n/locales \
  --target-langs es,fr,de

# Result: Your manual edit "Nueva Función" is preserved! ✓
```

---

## Best Practices

### 1. Version Control Strategy

```bash
# DO: Commit auto-translated files
git add locales/*.json
git commit -m "Auto-translate new keys"

# DO: Review diffs before committing
git diff locales/es.json

# DO: Use meaningful commit messages
git commit -m "Auto-translate dashboard module to Spanish, French, German"
```

### 2. Cost Management

```bash
# DO: Use dry-run first to estimate
python -m i18n.translation-service.tools.cli translate \
  --dry-run \
  --provider deepl \
  --api-key $DEEPL_API_KEY \
  --locales-dir ./locales \
  --target-langs es,fr,de

# Output shows: "Keys to translate: 150"
# Estimate: 150 keys × 30 chars avg × 3 langs = 13,500 chars
# Cost: < $0.30

# DO: Cache is enabled by default (saves 80%+ on reruns)

# DO: Translate in batches during development
# Don't translate after every single new key
```

### 3. Quality Assurance

```bash
# DO: Always review auto-translations
# Especially for:
# - Brand-specific terms
# - Technical jargon  
# - Cultural nuances
# - Marketing copy

# DO: Use validation
python -m i18n.translation-service.tools.cli validate \
  --locales-dir ./locales

# Shows: Completion % for each language
# Shows: Missing keys
# Shows: Empty translations
```

### 4. Provider Selection

**Use DeepL when:**
- Quality is critical
- Budget allows ($22/1M chars)
- Translating EU languages (excellent quality)

**Use Google when:**
- Need 100+ languages
- Cost-effective at scale ($20/1M chars)
- Good enough quality for most use cases

**Use LibreTranslate when:**
- Budget is very limited (free)
- Privacy is critical (self-hosted)
- Acceptable to review/edit more

### 5. Security

```bash
# DON'T: Commit API keys
# .gitignore should include:
.env
*.key
credentials.json

# DO: Use environment variables
export DEEPL_API_KEY="your-key"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"

# DO: Use .env files (not committed)
# .env
DEEPL_API_KEY=your-key-here
GOOGLE_API_KEY=your-key-here
```

---

## Troubleshooting

### Issue: "API key invalid"

```bash
# DeepL
# 1. Verify key at https://www.deepl.com/account/summary
# 2. Ensure you're using the correct API (Free vs Pro)

# Google
# 1. Check Cloud Translation API is enabled
# 2. Verify service account has Translate permissions
# 3. Check GOOGLE_APPLICATION_CREDENTIALS path
```

### Issue: "Rate limit exceeded"

```bash
# Solution 1: Wait and retry
# Solution 2: Use smaller batches
# Solution 3: Cache is your friend (automatically reduces calls)
```

### Issue: "Translation quality poor"

```bash
# Try different provider
# DeepL often has best quality

# Or manually review and edit
# Auto-translation is starting point, not final result
```

---

## 🎯 Summary

**The translation service:**
- ✅ Is completely optional
- ✅ Never overwrites manual translations
- ✅ Dramatically speeds up translation workflow
- ✅ Saves 80%+ time compared to manual translation
- ✅ Costs typically < $10 for entire app
- ✅ Has free option (LibreTranslate)

**Perfect for:**
- Quick prototyping
- Adding new languages fast
- Keeping translations in sync
- Reducing manual work

**Remember:**
- Always review auto-translations
- Manual edits are preserved
- Use validation to check completeness
- Start with small batch to test quality

---

**Happy Translating! 🌍**
