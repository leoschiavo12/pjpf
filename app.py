import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

st.set_page_config(page_title="Financeiro PJ/PF", page_icon="💼", layout="wide")

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
        res  = get_svc().values().get(spreadsheetId=SHEET_ID, range=f"{tab}!A:{col_fim}").execute()
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
    st.subheader("🏢 Gestão PJ")
    st.write("Funcionalidades da PJ aqui...")

with aba_pf:
    st.subheader("👤 Finanças PF")
    st.write("Funcionalidades da PF aqui...")

with aba_config:
    st.subheader("⚙️ Configurações do Sistema")
    cfg = load_config()
    st.caption("Digite os valores abaixo manualmente.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🏢 PJ")
        pro_labore_c = st.number_input("Pro-labore (R$)", value=num(cfg.get("pro_labore","0")), step=None, format="%.2f")
        prev_c       = st.number_input("Previdência (R$)", value=num(cfg.get("prev_privada","0")), step=None, format="%.2f")
        aliq_c       = st.number_input("Alíquota DAS (%)", value=num(cfg.get("aliquota_simples","0,06"))*100, step=None, format="%.2f")
        contador_c   = st.number_input("Contador (R$)", value=num(cfg.get("contador","0")), step=None, format="%.2f")

    with col2:
        st.markdown("### 👤 PF (Planos)")
        fies_c       = st.number_input("FIES (R$)", value=num(cfg.get("fies","635,29")), step=None, format="%.2f")
        meta_inv_c   = st.number_input("Meta de Investimento (%)", value=num(cfg.get("meta_investimento_pct","0,20"))*100, step=None, format="%.2f")
        meta_casa_c  = st.number_input("Casa Própria (R$)", value=num(cfg.get("meta_casa_propria","4000")), step=None, format="%.2f")

    if st.button("💾 Salvar todas as configurações", type="primary", use_container_width=True):
        save_config("pro_labore", pro_labore_c)
        save_config("prev_privada", prev_c)
        save_config("aliquota_simples", round(aliq_c/100, 4))
        save_config("contador", contador_c)
        save_config("fies", fies_c)
        save_config("meta_investimento_pct", round(meta_inv_c/100, 2))
        save_config("meta_casa_propria", meta_casa_c)
        st.success("Configurações salvas!")
        st.rerun()
