#!/bin/bash

# Create directory structure
mkdir -p config
mkdir -p backend/{core,translations/{en,es,fr,de,ar,ja,zh}/LC_MESSAGES,tests}
mkdir -p react/src/{config,hooks,components/{LanguageSelector,TranslationProvider},utils,locales,styles,types}
mkdir -p react/tests
mkdir -p streamlit/{core,components,pages,translations,tests}
mkdir -p tools/{scripts,cli,dashboard}
mkdir -p docs
mkdir -p examples/{backend-fastapi,react-app,streamlit-app}

echo "Directory structure created successfully!"
