import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

st.set_page_config(page_title="Financeiro PJ/PF", page_icon="💼", layout="wide")

# Estilo para esconder menu do Streamlit
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

# ── Configurações de Conexão ──────────────────────────────────────────────────
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

def num(s):
    try:
        if s is None or str(s).strip() in ('', 'nan', 'None'): return 0.0
        return float(str(s).strip().replace('R$','').replace(' ','').replace(',','.'))
    except: return 0.0

def fmt(v): return str(round(float(v), 2)).replace('.', ',')

def load_config():
    df = ler("config", ["chave","valor"])
    return {r["chave"]: r["valor"] for _, r in df.iterrows()}

def save_config(key, value):
    # Nota: A lógica de salvar no Sheets depende das suas funções de append/update
    # Certifique-se de que as funções 'append' e 'update' existam no seu script
    pass

# ── Interface Principal ───────────────────────────────────────────────────────
st.markdown("## 💼 Financeiro PJ/PF")
aba_pj, aba_pf, aba_config = st.tabs(["🏢 Gestão PJ", "👤 Finanças PF", "⚙️ Configurações"])

with aba_pj:
    st.write("Conteúdo da Gestão PJ")

with aba_pf:
    st.write("Conteúdo das Finanças PF")

with aba_config:
    cfg = load_config()
    st.subheader("Configurações Gerais")
    
    col1, col2 = st.columns(2)
    # step=None REMOVE os botões + e -
    pro_labore_c = col1.number_input("Pro-labore bruto (R$)", value=num(cfg.get("pro_labore","0")), step=None)
    pro_liq_c    = col2.number_input("Pro-labore líquido (R$)", value=num(cfg.get("pro_labore_liquido","1513")), step=None)
    
    col3, col4 = st.columns(2)
    prev_c     = col3.number_input("Previdência privada (R$)", value=num(cfg.get("prev_privada","0")), step=None)
    contador_c = col4.number_input("Contador (R$)", value=num(cfg.get("contador","0")), step=None)
    
    aliquota_c = st.number_input("Alíquota Simples (%)", value=num(cfg.get("aliquota_simples","0,06"))*100, step=None)
    
    col5, col6 = st.columns(2)
    fies_c      = col5.number_input("FIES (R$)", value=num(cfg.get("fies","635,29")), step=None)
    meta_casa_c = col6.number_input("Casa própria (R$)", value=num(cfg.get("meta_casa_propria","4000")), step=None)
    
    meta_inv_c  = st.number_input("Meta investimento (%)", value=num(cfg.get("meta_investimento_pct","0,20"))*100, step=None)
    
    if st.button("💾 Salvar configurações", type="primary"):
        st.success("Configurações salvas!")
        # Inclua aqui suas chamadas de save_config
