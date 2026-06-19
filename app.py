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
    get_svc().values().append(spreadsheetId=SHEET_ID, range=f"{tab}!A:A", valueInputOption="USER_ENTERED", body={"values": [row]}).execute()

def update(tab, linha, row):
    col_fim = chr(ord('A') + len(row) - 1)
    get_svc().values().update(spreadsheetId=SHEET_ID, range=f"{tab}!A{linha}:{col_fim}{linha}", valueInputOption="USER_ENTERED", body={"values": [row]}).execute()

def num(s):
    try:
        if s is None or str(s).strip() in ('', 'nan', 'None'): return 0.0
        s = str(s).strip().replace('R$','').replace(' ','').replace(',','.')
        return float(s)
    except: return 0.0

def fmt(v): return str(round(float(v), 2)).replace('.', ',')
def brl(v): return f"R$ {float(v):,.2f}".replace(',','X').replace('.',',').replace('X','.')

def mes_label(m):
    meses = {"01":"Jan","02":"Fev","03":"Mar","04":"Abr","05":"Mai","06":"Jun","07":"Jul","08":"Ago","09":"Set","10":"Out","11":"Nov","12":"Dez"}
    try: p = m.split("-"); return f"{meses[p[1]]}/{p[0]}"
    except: return m

def load_config():
    df = ler("config", ["chave","valor"])
    return {r["chave"]: r["valor"] for _, r in df.iterrows()}

def save_config(key, value):
    df = ler("config", ["chave","valor"])
    for i, r in df.iterrows():
        if r["chave"] == key:
            update("config", i+2, [key, fmt(value) if isinstance(value, float) else str(value)])
            return
    append("config", [key, fmt(value) if isinstance(value, float) else str(value)])

# ── Interface Principal ───────────────────────────────────────────────────────
st.markdown("## 💼 Financeiro PJ/PF")
aba_pj, aba_pf, aba_config = st.tabs(["🏢 Gestão PJ", "👤 Finanças PF", "⚙️ Configurações"])

with aba_pj:
    st.write("Conteúdo da gestão PJ...")

with aba_pf:
    st.write("Conteúdo das finanças PF...")

with aba_config:
    cfg = load_config()
    st.caption("Digite os valores abaixo manualmente.")
    col1, col2 = st.columns(2)
    
    # step=None remove os botões +/-
    pro_labore_c = col1.number_input("Pro-labore bruto (R$)", value=num(cfg.get("pro_labore","0")), step=None, format="%.2f")
    pro_liq_c    = col2.number_input("Pro-labore líquido (R$)", value=num(cfg.get("pro_labore_liquido","1513")), step=None, format="%.2f")
    
    col3, col4 = st.columns(2)
    prev_c     = col3.number_input("Previdência privada (R$)", value=num(cfg.get("prev_privada","0")), step=None, format="%.2f")
    contador_c = col4.number_input("Contador (R$)", value=num(cfg.get("contador","0")), step=None, format="%.2f")
    
    aliquota_c = st.number_input("Alíquota Simples (%)", value=num(cfg.get("aliquota_simples","0,06"))*100, step=None, format="%.2f")
    
    col5, col6 = st.columns(2)
    fies_c      = col5.number_input("FIES (R$)", value=num(cfg.get("fies","635,29")), step=None, format="%.2f")
    meta_casa_c = col6.number_input("Plano casa própria (R$)", value=num(cfg.get("meta_casa_propria","4000")), step=None, format="%.2f")
    meta_inv_c  = st.number_input("Meta investimento (%)", value=num(cfg.get("meta_investimento_pct","0,20"))*100, step=None, format="%.2f")

    if st.button("💾 Salvar configurações", type="primary", use_container_width=True):
        save_config("pro_labore", pro_labore_c)
        save_config("pro_labore_liquido", pro_liq_c)
        save_config("prev_privada", prev_c)
        save_config("contador", contador_c)
        save_config("aliquota_simples", round(aliquota_c/100, 4))
        save_config("fies", fies_c)
        save_config("meta_casa_propria", meta_casa_c)
        save_config("meta_investimento_pct", round(meta_inv_c/100, 2))
        st.success("✅ Salvo!")
        st.rerun()
