import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io
import base64
import gspread
from google.oauth2.service_account import Credentials

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y CONEXIÓN GSHEET
# ==========================================
st.set_page_config(
    page_title="Atlético Centurión - Finanzas & Club",
    page_icon="⚽",
    layout="wide"
)

if "es_admin" not in st.session_state:
    st.session_state["es_admin"] = False

@st.cache_resource
def conectar_google_sheets():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # Se corrige el formato de salto de línea de la clave privada
    creds_dict = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

    credentials = Credentials.from_service_account_info(
        creds_dict,
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    sheet = client.open("Finanzas Atletico Centurion")
    return sheet

def get_dataframe(sheet_name, columns):
    try:
        sh = conectar_google_sheets()
        ws = sh.worksheet(sheet_name)
        records = ws.get_all_records()
        df = pd.DataFrame(records)
        if df.empty:
            return pd.DataFrame(columns=columns)
        return df
    except Exception:
        return pd.DataFrame(columns=columns)

# Estilos CSS Personalizados
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    .header-centurion {
        background: linear-gradient(135deg, #002B49 0%, #0A4B7C 100%);
        color: white; padding: 24px; border-radius: 16px;
        text-align: center; margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0, 43, 73, 0.25);
        border-bottom: 4px solid #00A3E0;
    }
    .header-centurion h1 { color: #FFFFFF !important; font-weight: 800; font-size: 2.2rem; margin: 0; }
    .header-centurion p { color: #E2E8F0; margin-top: 6px; font-size: 1.05rem; margin-bottom: 0; }
    .stButton>button {
        background-color: #002B49 !important; color: #FFFFFF !important;
        border-radius: 8px !important; font-weight: 600 !important;
    }
    div[data-testid="stMetricValue"] { color: #002B49 !important; font-weight: 700; }
    .stTabs [data-baseweb="tab"] { background-color: #E2E8F0; border-radius: 8px 8px 0 0; padding: 8px 16px; color: #002B49; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #002B49 !important; color: #FFFFFF !important; }
    .footer-sponsors { background-color: #002B49; color: white; padding: 30px; border-radius: 16px; margin-top: 50px; text-align: center; border-top: 4px solid #00A3E0; }
    .sponsor-badge { background-color: #FFFFFF; color: #002B49; padding: 12px 20px; border-radius: 10px; font-weight: 700; display: inline-block; margin: 8px; border: 2px solid #E2E8F0; }
    .sponsor-badge span { display: block; font-size: 0.8rem; color: #64748B; font-weight: 400; }
    .comment-box { background-color: #F1F5F9; border-radius: 8px; padding: 10px 15px; margin-top: 8px; border-left: 3px solid #002B49; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNCIONES DE BASE DE DATOS (GOOGLE SHEETS)
# ==========================================
def obtener_auspiciadores():
    df = get_dataframe("auspiciadores", ["id", "nombre", "rubro", "contacto"])
    return df.sort_values(by="nombre", ascending=True) if not df.empty and "nombre" in df.columns else df

def agregar_auspiciador(nombre, rubro, contacto):
    sh = conectar_google_sheets()
    ws = sh.worksheet("auspiciadores")
    df = get_dataframe("auspiciadores", ["id", "nombre", "rubro", "contacto"])
    nuevo_id = 1
    if not df.empty and "id" in df.columns:
        ids = pd.to