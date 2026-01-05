import streamlit as st


def apply_theme():
    st.markdown(
        """
        <style>
        html, body, [class*="css"]  {
            background-color: #0b0b12;
            color: #f8f8ff;
            font-family: 'Segoe UI', sans-serif;
        }
        .stApp {
            background: radial-gradient(circle at top, #191933 0%, #0b0b12 55%);
        }
        .miniwins-card {
            background: #141428;
            border: 2px solid #6b5bff;
            border-radius: 16px;
            padding: 16px;
            box-shadow: 0 0 12px rgba(107, 91, 255, 0.35);
        }
        .miniwins-accent {
            color: #3cffd0;
        }
        .stButton>button {
            background-color: #6b5bff;
            color: #ffffff;
            border-radius: 12px;
            border: 0;
        }
        .stButton>button:hover {
            background-color: #887bff;
            color: #ffffff;
        }
        .stSelectbox>div>div, .stTextInput>div>div, .stTextArea>div>textarea {
            background-color: #111122;
            color: #ffffff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
