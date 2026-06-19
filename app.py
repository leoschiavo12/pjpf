import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

st.set_page_config(page_title="Financeiro PJ/PF", page_icon="💼", layout="wide")

# ── Configuração de estilo ────────────────────────────────────────────────────
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

def load_config():
    df = ler("config", ["chave","valor"])
    return {r["chave"]: r["valor"] for _, r in df.iterrows()}

def num(s):
    try:
        if s is None or str(s).strip() in ('', 'nan', 'None'): return 0.0
        s = str(s).strip().replace('R$','').replace(' ','')
        s = s.replace(',','.')
        return float(s)
    except: return 0.0

# ── Estrutura da Página ──────────────────────────────────────────────────────
st.markdown("## 💼 Financeiro PJ/PF")
aba_pj, aba_pf, aba_config = st.tabs(["🏢 Gestão PJ", "👤 Finanças PF", "⚙️ Configurações"])

with aba_pj:
    st.write("Conteúdo da Gestão PJ...")

with aba_pf:
    st.write("Conteúdo das Finanças PF...")

with aba_config:
    cfg = load_config()
    st.subheader("⚙️ Configurações do Sistema")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🏢 PJ")
        # step=None remove os botões +/-
        pro_labore_c = st.number_input("Pro-labore bruto (R$)", value=num(cfg.get("pro_labore","0")), step=None, format="%.2f")
        prev_c       = st.number_input("Previdência (R$)", value=num(cfg.get("prev_privada","0")), step=None, format="%.2f")
        aliq_c       = st.number_input("Alíquota DAS (%)", value=num(cfg.get("aliquota_simples","0,06"))*100, step=None, format="%.2f")
        contador_c   = st.number_input("Contador (R$)", value=num(cfg.get("contador","0")), step=None, format="%.2f")

    with col2:
        st.markdown("### 👤 PF (Planos)")
        fies_c       = st.number_input("FIES (R$)", value=num(cfg.get("fies","635,29")), step=None, format="%.2f")
        meta_inv_c   = st.number_input("Meta de Investimento (%)", value=num(cfg.get("meta_investimento_pct","0,20"))*100, step=None, format="%.2f")
        meta_casa_c  = st.number_input("Meta Casa Própria (R$)", value=num(cfg.get("meta_casa_propria","4000")), step=None, format="%.2f")

    if st.button("💾 Salvar todas as configurações", type="primary"):
        st.success("Configurações salvas (lógica de salvar aqui)!")
