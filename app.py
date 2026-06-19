import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

st.set_page_config(page_title="Financeiro PJ/PF", page_icon="💼", layout="wide")

# Estilo para esconder menu lateral
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

# ── Conexão Google Sheets ─────────────────────────────────────────────────────
SHEET_ID = st.secrets["google_sheets"]["spreadsheet_id"]

def get_svc():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=creds).spreadsheets()

def ler(tab, colunas):
    try:
        n = len(colunas)
        col_fim = chr(ord('A') + n - 1)
        res = get_svc().values().get(spreadsheetId=SHEET_ID, range=f"{tab}!A:{col_fim}").execute()
        rows = res.get("values", [])
        if len(rows) <= 1: return pd.DataFrame(columns=colunas)
        padded = [(r + ['']*n)[:n] for r in rows[1:]]
        return pd.DataFrame(padded, columns=colunas)
    except: return pd.DataFrame(columns=colunas)

def append(tab, row):
    get_svc().values().append(spreadsheetId=SHEET_ID, range=f"{tab}!A:A",
        valueInputOption="USER_ENTERED", body={"values": [row]}).execute()

def update(tab, linha, row):
    col_fim = chr(ord('A') + len(row) - 1)
    get_svc().values().update(spreadsheetId=SHEET_ID, range=f"{tab}!A{linha}:{col_fim}{linha}",
        valueInputOption="USER_ENTERED", body={"values": [row]}).execute()

# ── Helpers ───────────────────────────────────────────────────────────────────
def num(s):
    try:
        s = str(s).strip().replace('R$','').replace(' ','')
        s = s.replace('.','').replace(',','.') if ',' in s and '.' in s else s.replace(',','.')
        return float(s)
    except: return 0.0

def fmt(v): return str(round(float(v), 2)).replace('.', ',')

# ── Funções de Carga ──────────────────────────────────────────────────────────
def load_config():
    df = ler("config", ["chave","valor"])
    return {r["chave"]: r["valor"] for _, r in df.iterrows()}

def save_config(key, value):
    df = ler("config", ["chave","valor"])
    for i, r in df.iterrows():
        if r["chave"] == key:
            update("config", i+2, [key, fmt(value)])
            return
    append("config", [key, fmt(value)])

# ── Interface Principal ───────────────────────────────────────────────────────
st.markdown("## 💼 Financeiro PJ/PF")
aba_pj, aba_pf, aba_config = st.tabs(["🏢 Gestão PJ", "👤 Finanças PF", "⚙️ Configurações"])

with aba_pj:
