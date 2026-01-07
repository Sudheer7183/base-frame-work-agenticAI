"""
Auto-Translation CLI Tool
Automatically translate missing translation keys

Version: 1.0
License: MIT
"""

import click
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """
    Translation Service CLI
    
    Automatically translate missing translation keys across all languages.
    """
    pass


@cli.command()
@click.option(
    '--provider',
    type=click.Choice(['google', 'deepl', 'libre'], case_sensitive=False),
    required=True,
    help='Translation provider to use'
)
@click.option(
    '--api-key',
    help='API key for the translation service'
)
@click.option(
    '--source-lang',
    default='en',
    help='Source language code (default: en)'
)
@click.option(
    '--target-langs',
    help='Comma-separated target language codes (e.g., es,fr,de)'
)
@click.option(
    '--source-file',
    type=click.Path(exists=True),
    help='Source translation file (JSON)'
)
@click.option(
    '--locales-dir',
    type=click.Path(exists=True),
    help='Directory containing locale JSON files'
)
@click.option(
    '--skip-existing',
    is_flag=True,
    default=True,
    help='Skip keys that already have translations'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show what would be translated without actually translating'
)
@click.option(
    '--api-url',
    help='API URL for LibreTranslate (if using libre provider)'
)
def translate(
    provider: str,
    api_key: Optional[str],
    source_lang: str,
    target_langs: Optional[str],
    source_file: Optional[str],
    locales_dir: Optional[str],
    skip_existing: bool,
    dry_run: bool,
    api_url: Optional[str]
):
    """
    Auto-translate missing translation keys
    
    Examples:
    
    \b
    # Translate React locales using DeepL
    python -m translation-service.tools.cli translate \\
        --provider deepl \\
        --api-key YOUR_KEY \\
        --locales-dir ./react/src/locales \\
        --target-langs es,fr,de
    
    \b
    # Translate single file using Google
    python -m translation-service.tools.cli translate \\
        --provider google \\
        --api-key YOUR_KEY \\
        --source-file ./locales/en.json \\
        --target-langs es,fr
    
    \b
    # Use self-hosted LibreTranslate (free)
    python -m translation-service.tools.cli translate \\
        --provider libre \\
        --api-url http://localhost:5000 \\
        --locales-dir ./react/src/locales \\
        --target-langs es,fr,de
    """
    # Validate inputs
    if not source_file and not locales_dir:
        click.echo("Error: Either --source-file or --locales-dir must be provided", err=True)
        sys.exit(1)
    
    if not target_langs:
        click.echo("Error: --target-langs must be provided", err=True)
        sys.exit(1)
    
    target_lang_list = [lang.strip() for lang in target_langs.split(',')]
    
    # Import translation service
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from translation_service.core.translator import create_translation_manager
    
    # Create translation manager
    click.echo(f"\n{'='*60}")
    click.echo(f"Initializing {provider.upper()} translation service...")
    click.echo(f"{'='*60}\n")
    
    try:
        config = {}
        if api_url:
            config['api_url'] = api_url
        
        manager = create_translation_manager(
            provider_name=provider,
            api_key=api_key,
            **config
        )
    except Exception as e:
        click.echo(f"Error initializing provider: {e}", err=True)
        sys.exit(1)
    
    # Process files
    if source_file:
        # Single file mode
        source_path = Path(source_file)
        source_data = load_json(source_path)
        
        for target_lang in target_lang_list:
            process_translation(
                manager,
                source_data,
                source_lang,
                target_lang,
                source_path.parent,
                source_path.stem,
                skip_existing,
                dry_run
            )
    
    elif locales_dir:
        # Directory mode
        locales_path = Path(locales_dir)
        source_file_path = locales_path / f"{source_lang}.json"
        
        if not source_file_path.exists():
            click.echo(f"Error: Source file not found: {source_file_path}", err=True)
            sys.exit(1)
        
        source_data = load_json(source_file_path)
        
        for target_lang in target_lang_list:
            process_translation(
                manager,
                source_data,
                source_lang,
                target_lang,
                locales_path,
                target_lang,
                skip_existing,
                dry_run
            )
    
    # Show statistics
    click.echo(f"\n{'='*60}")
    click.echo("Translation Statistics")
    click.echo(f"{'='*60}\n")
    
    stats = manager.get_stats()
    click.echo(f"Translations requested: {stats['translations_requested']}")
    click.echo(f"Cache hits: {stats['cache_hits']}")
    click.echo(f"Cache misses: {stats['cache_misses']}")
    click.echo(f"Cache hit rate: {stats['cache_hit_rate']:.1f}%")
    click.echo(f"API calls: {stats['api_calls']}")
    click.echo(f"Characters translated: {stats['characters_translated']:,}")
    click.echo(f"Estimated cost: ${stats['estimated_cost_usd']:.2f} USD")
    
    click.echo(f"\n{'='*60}")
    if dry_run:
        click.echo("✅ Dry run complete! No files were modified.")
    else:
        click.echo("✅ Translation complete!")
    click.echo(f"{'='*60}\n")


def load_json(file_path: Path) -> Dict:
    """Load JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return {}


def save_json(file_path: Path, data: Dict):
    """Save JSON file with pretty formatting"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved: {file_path}")
    except Exception as e:
        logger.error(f"Failed to save {file_path}: {e}")


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(d: Dict, sep: str = '.') -> Dict:
    """Unflatten dictionary back to nested structure"""
    result = {}
    for key, value in d.items():
        parts = key.split(sep)
        d = result
        for part in parts[:-1]:
            if part not in d:
                d[part] = {}
            d = d[part]
        d[parts[-1]] = value
    return result


def process_translation(
    manager,
    source_data: Dict,
    source_lang: str,
    target_lang: str,
    output_dir: Path,
    output_filename: str,
    skip_existing: bool,
    dry_run: bool
):
    """Process translation for a single target language"""
    click.echo(f"\nTranslating {source_lang} → {target_lang}...")
    click.echo("-" * 40)
    
    # Load existing target file if it exists
    target_file = output_dir / f"{output_filename}.json"
    if target_file.exists():
        target_data = load_json(target_file)
        click.echo(f"Loaded existing: {target_file}")
    else:
        target_data = {}
        click.echo(f"Creating new: {target_file}")
    
    # Flatten dictionaries for easier processing
    source_flat = flatten_dict(source_data)
    target_flat = flatten_dict(target_data)
    
    # Find keys that need translation
    keys_to_translate = []
    texts_to_translate = []
    
    for key, source_text in source_flat.items():
        # Skip if target already has this key and skip_existing is True
        if skip_existing and key in target_flat and target_flat[key]:
            continue
        
        # Skip empty source texts
        if not source_text or not str(source_text).strip():
            continue
        
        keys_to_translate.append(key)
        texts_to_translate.append(str(source_text))
    
    if not keys_to_translate:
        click.echo("✓ No keys to translate (all up to date)")
        return
    
    click.echo(f"Keys to translate: {len(keys_to_translate)}")
    
    if dry_run:
        click.echo("\nDry run - would translate:")
        for i, (key, text) in enumerate(zip(keys_to_translate[:5], texts_to_translate[:5])):
            click.echo(f"  {key}: {text[:50]}...")
        if len(keys_to_translate) > 5:
            click.echo(f"  ... and {len(keys_to_translate) - 5} more")
        return
    
    # Translate in batch
    try:
        click.echo("Translating...")
        with click.progressbar(
            length=len(texts_to_translate),
            label=f"Progress"
        ) as bar:
            translated_texts = manager.translate_batch(
                texts_to_translate,
                source_lang,
                target_lang
            )
            bar.update(len(texts_to_translate))
        
        # Update target data
        for key, translated in zip(keys_to_translate, translated_texts):
            target_flat[key] = translated
        
        # Unflatten and save
        target_data_updated = unflatten_dict(target_flat)
        save_json(target_file, target_data_updated)
        
        click.echo(f"✓ Translated {len(keys_to_translate)} keys")
        
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


@cli.command()
@click.option(
    '--locales-dir',
    type=click.Path(exists=True),
    required=True,
    help='Directory containing locale JSON files'
)
@click.option(
    '--source-lang',
    default='en',
    help='Source language to compare against'
)
def validate(locales_dir: str, source_lang: str):
    """
    Validate translation files
    
    Check for:
    - Missing keys
    - Empty translations
    - Inconsistent structure
    """
    click.echo(f"\n{'='*60}")
    click.echo("Validating Translation Files")
    click.echo(f"{'='*60}\n")
    
    locales_path = Path(locales_dir)
    source_file = locales_path / f"{source_lang}.json"
    
    if not source_file.exists():
        click.echo(f"Error: Source file not found: {source_file}", err=True)
        sys.exit(1)
    
    source_data = load_json(source_file)
    source_keys = set(flatten_dict(source_data).keys())
    
    click.echo(f"Source language: {source_lang}")
    click.echo(f"Total keys in source: {len(source_keys)}\n")
    
    # Check all other locale files
    for locale_file in sorted(locales_path.glob("*.json")):
        if locale_file.stem == source_lang:
            continue
        
        lang = locale_file.stem
        data = load_json(locale_file)
        keys = set(flatten_dict(data).keys())
        
        missing = source_keys - keys
        extra = keys - source_keys
        
        # Count empty values
        flat = flatten_dict(data)
        empty = [k for k, v in flat.items() if not v or not str(v).strip()]
        
        # Calculate completion
        completion = ((len(keys) - len(empty)) / len(source_keys)) * 100 if source_keys else 0
        
        click.echo(f"{lang.upper()}: {completion:.1f}% complete")
        if missing:
            click.echo(f"  ✗ Missing {len(missing)} keys")
        if empty:
            click.echo(f"  ⚠ {len(empty)} empty translations")
        if extra:
            click.echo(f"  ⚠ {len(extra)} extra keys")
        if not missing and not empty and not extra:
            click.echo(f"  ✓ Perfect match with source")
        click.echo()
    
    click.echo(f"{'='*60}\n")


@cli.command()
def providers():
    """List available translation providers and their status"""
    click.echo(f"\n{'='*60}")
    click.echo("Available Translation Providers")
    click.echo(f"{'='*60}\n")
    
    providers_info = [
        {
            "name": "Google Cloud Translation",
            "code": "google",
            "languages": "100+",
            "cost": "$20/1M chars",
            "quality": "High",
            "setup": "API key or service account"
        },
        {
            "name": "DeepL",
            "code": "deepl",
            "languages": "30+",
            "cost": "$22/1M chars",
            "quality": "Highest",
            "setup": "API key from deepl.com"
        },
        {
            "name": "LibreTranslate",
            "code": "libre",
            "languages": "30+",
            "cost": "Free (self-hosted)",
            "quality": "Medium",
            "setup": "Self-host or use public API"
        },
    ]
    
    for provider in providers_info:
        click.echo(f"{provider['name']} ({provider['code']})")
        click.echo(f"  Languages: {provider['languages']}")
        click.echo(f"  Cost: {provider['cost']}")
        click.echo(f"  Quality: {provider['quality']}")
        click.echo(f"  Setup: {provider['setup']}")
        click.echo()
    
    click.echo(f"{'='*60}\n")


if __name__ == '__main__':
    cli()
