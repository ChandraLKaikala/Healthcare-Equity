"""
Performance utilities for Healthcare Equity Analytics Dashboard
Caches CSS, styling, and frequently-used functions
"""
import streamlit as st

# Healthcare color scheme (shared across all pages)
COLORS = {
    'primary_blue': '#0052A3',
    'accent_teal': '#00A896',
    'success_green': '#2D6A4F',
    'warning_orange': '#D97706',
    'critical_red': '#DC2626',
    'dark_bg': '#0B1929',
    'card_bg': '#112240',
    'light_bg': '#E8F1F5',
    'text_light': '#E8E8E8',
    'text_muted': '#A8B5C1',
    'text_dark': '#0B1929'
}

@st.cache_data(ttl=3600)  # Cache CSS for 1 hour
def load_base_css():
    """Load and cache base CSS styling for all pages."""
    return f"""
    <style>
        * {{
            margin: 0;
            padding: 0;
        }}

        body, html {{
            background: linear-gradient(135deg, {COLORS['dark_bg']} 0%, #1a2332 100%) !important;
            color: {COLORS['text_light']} !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        }}

        [data-testid="stAppViewContainer"] {{
            background: linear-gradient(135deg, {COLORS['dark_bg']} 0%, #1a2332 100%) !important;
        }}

        [data-testid="stMain"] {{
            background: linear-gradient(135deg, {COLORS['dark_bg']} 0%, #1a2332 100%) !important;
            color: {COLORS['text_light']} !important;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {COLORS['card_bg']} 0%, {COLORS['dark_bg']} 100%) !important;
            border-right: 3px solid {COLORS['accent_teal']};
        }}

        h1, h2, h3, p, span, label, div {{
            color: {COLORS['text_light']} !important;
        }}

        h1, h2, h3 {{
            color: {COLORS['accent_teal']} !important;
            font-weight: 800;
            letter-spacing: -0.5px;
        }}

        h1 {{
            border-bottom: 3px solid {COLORS['accent_teal']};
            padding-bottom: 15px;
            margin-bottom: 30px;
        }}

        [data-testid="metric-container"] {{
            background: linear-gradient(135deg, {COLORS['primary_blue']}25 0%, {COLORS['accent_teal']}15 100%) !important;
            border-left: 5px solid {COLORS['primary_blue']};
            border-radius: 12px;
            padding: 20px !important;
            box-shadow: 0 8px 24px rgba(0, 102, 204, 0.15) !important;
            color: {COLORS['text_light']} !important;
        }}

        button {{
            background: linear-gradient(135deg, {COLORS['primary_blue']} 0%, {COLORS['accent_teal']} 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }}

        button:hover {{
            transform: translateY(-2px) !important;
        }}

        [data-testid="stTable"] {{
            background-color: {COLORS['card_bg']} !important;
        }}

        table {{
            background-color: {COLORS['card_bg']} !important;
            color: {COLORS['text_light']} !important;
        }}

        thead {{
            background-color: {COLORS['primary_blue']}30 !important;
        }}

        tbody tr {{
            background-color: {COLORS['card_bg']} !important;
            color: {COLORS['text_light']} !important;
        }}

        tbody tr:hover {{
            background-color: {COLORS['primary_blue']}20 !important;
        }}

        .stAlert {{
            background-color: {COLORS['card_bg']} !important;
            color: {COLORS['text_light']} !important;
            border-color: {COLORS['accent_teal']}40 !important;
        }}

        input, select, textarea {{
            background-color: {COLORS['card_bg']} !important;
            color: {COLORS['text_light']} !important;
            border-color: {COLORS['accent_teal']}40 !important;
        }}
    </style>
    """

@st.cache_resource
def get_databricks_connection():
    """Cache database connection across all page navigations."""
    try:
        from databricks_client import get_databricks_connection as get_client
        return get_client()
    except Exception as e:
        print(f"Warning: Could not establish Databricks connection: {str(e)[:100]}")
        return None

def apply_base_styling():
    """Apply cached base styling to current page."""
    st.markdown(load_base_css(), unsafe_allow_html=True)

def apply_page_header(title: str, subtitle: str, header_color: str):
    """Apply consistent page header styling."""
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {header_color}15 0%, {header_color}10 100%);
                border: 2px solid {header_color}; padding: 30px; border-radius: 15px; margin-bottom: 30px;
                box-shadow: 0 8px 32px rgba(220, 38, 38, 0.2);'>
        <h1 style='color: {header_color}; margin: 0 0 10px 0; font-size: 2.2em; border: none;'>{title}</h1>
        <p style='color: {COLORS["text_muted"]}; margin: 0; font-size: 1em;'>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)
