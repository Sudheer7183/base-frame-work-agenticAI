"""
Language Selector Component for Streamlit

Version: 3.0
License: MIT
"""

import streamlit as st
from typing import Optional
from ..core.i18n import (
    get_current_locale,
    set_locale,
    get_available_locales,
    get_locale_info,
    SUPPORTED_LOCALES,
)


def render_language_selector(
    key: str = "language_selector",
    show_flags: bool = True,
    show_native_names: bool = True,
    horizontal: bool = False,
) -> None:
    """
    Render a language selector in Streamlit
    
    Args:
        key: Unique key for the selector widget
        show_flags: Show country flags
        show_native_names: Show native language names
        horizontal: Use horizontal radio buttons instead of selectbox
    
    Example:
        ```python
        import streamlit as st
        from streamlit.components.language_selector import render_language_selector
        
        # In sidebar
        with st.sidebar:
            render_language_selector()
        ```
    """
    current_locale = get_current_locale()
    available_locales = get_available_locales()
    
    # Build language options
    options = []
    for locale in available_locales:
        info = get_locale_info(locale)
        
        label = ""
        if show_flags:
            label += f"{info.get('flag', '')} "
        
        if show_native_names:
            label += info.get('native_name', locale)
        else:
            label += info.get('name', locale)
        
        options.append((locale, label.strip()))
    
    # Create lookup dicts
    locale_to_label = {locale: label for locale, label in options}
    label_to_locale = {label: locale for locale, label in options}
    
    # Get current selection label
    current_label = locale_to_label.get(current_locale, options[0][1])
    
    # Render selector
    if horizontal:
        # Horizontal radio buttons
        st.markdown("#### 🌐 Language")
        selected_label = st.radio(
            "Select Language",
            options=[label for _, label in options],
            index=[label for _, label in options].index(current_label),
            key=key,
            label_visibility="collapsed",
            horizontal=True,
        )
    else:
        # Dropdown selectbox
        selected_label = st.selectbox(
            "🌐 Language",
            options=[label for _, label in options],
            index=[label for _, label in options].index(current_label),
            key=key,
        )
    
    # Update locale if changed
    selected_locale = label_to_locale[selected_label]
    if selected_locale != current_locale:
        set_locale(selected_locale)
        st.rerun()


def render_compact_language_selector(key: str = "compact_lang_selector") -> None:
    """
    Render a compact language selector (flags only)
    
    Args:
        key: Unique key for the selector widget
    
    Example:
        ```python
        # At the top of the page
        col1, col2, col3 = st.columns([6, 1, 1])
        with col3:
            render_compact_language_selector()
        ```
    """
    current_locale = get_current_locale()
    available_locales = get_available_locales()
    
    # Build options (flags only)
    options = []
    for locale in available_locales:
        info = get_locale_info(locale)
        flag = info.get('flag', locale.upper())
        options.append((locale, flag))
    
    locale_to_flag = {locale: flag for locale, flag in options}
    flag_to_locale = {flag: locale for locale, flag in options}
    
    current_flag = locale_to_flag.get(current_locale, options[0][1])
    
    # Render compact selector
    selected_flag = st.selectbox(
        "Lang",
        options=[flag for _, flag in options],
        index=[flag for _, flag in options].index(current_flag),
        key=key,
        label_visibility="collapsed",
    )
    
    selected_locale = flag_to_locale[selected_flag]
    if selected_locale != current_locale:
        set_locale(selected_locale)
        st.rerun()


def render_language_info_card() -> None:
    """
    Render a card showing current language information
    
    Example:
        ```python
        with st.sidebar:
            render_language_info_card()
        ```
    """
    current_locale = get_current_locale()
    info = get_locale_info(current_locale)
    
    st.markdown("---")
    st.markdown(f"""
    ### 🌐 Current Language
    
    **{info.get('flag', '')} {info.get('native_name', current_locale)}**
    
    - Code: `{current_locale}`
    - Direction: {info.get('direction', 'ltr').upper()}
    - Name: {info.get('name', '')}
    """)
    st.markdown("---")


__all__ = [
    "render_language_selector",
    "render_compact_language_selector",
    "render_language_info_card",
]
