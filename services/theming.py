import streamlit as st

THEMES = {
    "catppuccin-latte": {
        "name": "Catppuccin Latte",
        "bg": "#f5f1f3",
        "surface": "#ffffff",
        "text": "#2c2a2e",
        "muted": "#6c6a70",
        "primary": "#8839ef",
        "secondary": "#04a5e5",
        "border": "#e6e0e4",
        "card": "#ffffff",
    },
    "nord": {
        "name": "Nord",
        "bg": "#2e3440",
        "surface": "#3b4252",
        "text": "#eceff4",
        "muted": "#d8dee9",
        "primary": "#88c0d0",
        "secondary": "#a3be8c",
        "border": "#4c566a",
        "card": "#434c5e",
    },
}


def apply_theme(theme_key: str) -> None:
    theme = THEMES.get(theme_key, THEMES["catppuccin-latte"])
    st.markdown(
        f"""
        <style>
        :root {{
            --mw-bg: {theme['bg']};
            --mw-surface: {theme['surface']};
            --mw-text: {theme['text']};
            --mw-muted: {theme['muted']};
            --mw-primary: {theme['primary']};
            --mw-secondary: {theme['secondary']};
            --mw-border: {theme['border']};
            --mw-card: {theme['card']};
        }}
        html, body, [class*="css"] {{
            font-family: "Segoe UI", "Inter", sans-serif;
            color: var(--mw-text);
            background-color: var(--mw-bg);
        }}
        .stApp {{
            background-color: var(--mw-bg);
        }}
        .stSidebar {{
            background-color: var(--mw-surface);
        }}
        .stButton>button {{
            background-color: var(--mw-primary);
            color: #fff;
            border-radius: 10px;
            border: 0;
            padding: 0.5rem 1rem;
        }}
        .stButton>button:hover {{
            background-color: var(--mw-secondary);
            color: #fff;
        }}
        .stSelectbox>div>div,
        .stTextInput>div>div,
        .stTextArea>div>textarea,
        .stNumberInput>div>div {{
            background-color: var(--mw-surface);
            color: var(--mw-text);
            border-color: var(--mw-border);
        }}
        .stMarkdown, .stCaption, .stMetric {{
            color: var(--mw-text);
        }}
        .mw-card {{
            background-color: var(--mw-card);
            border: 1px solid var(--mw-border);
            border-radius: 16px;
            padding: 16px;
            margin-bottom: 16px;
        }}
        .mw-muted {{
            color: var(--mw-muted);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def theme_options():
    return {key: value["name"] for key, value in THEMES.items()}
