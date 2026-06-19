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
        if len(rows) <= 1:
            return pd.DataFrame(columns=colunas)
        padded = [(r + ['']*n)[:n] for r in rows[1:]]
        return pd.DataFrame(padded, columns=colunas)
    except Exception as e:
        st.error(f"Erro ao ler '{tab}': {e}")
        return pd.DataFrame(columns=colunas)

def append(tab, row):
    get_svc().values().append(
        spreadsheetId=SHEET_ID, range=f"{tab}!A:A",
        valueInputOption="USER_ENTERED", body={"values": [row]}
    ).execute()

def update(tab, linha, row):
    col_fim = chr(ord('A') + len(row) - 1)
    get_svc().values().update(
        spreadsheetId=SHEET_ID, range=f"{tab}!A{linha}:{col_fim}{linha}",
        valueInputOption="USER_ENTERED", body={"values": [row]}
    ).execute()

def delete_row(tab, linha):
    svc = get_svc()
    meta = svc.get(spreadsheetId=SHEET_ID).execute()
    gid  = next((s["properties"]["sheetId"] for s in meta["sheets"]
                 if s["properties"]["title"] == tab), 0)
    svc.batchUpdate(spreadsheetId=SHEET_ID, body={"requests": [{"deleteDimension": {"range": {
        "sheetId": gid, "dimension": "ROWS",
        "startIndex": linha - 1, "endIndex": linha
    }}}]}).execute()

# ── Helpers ───────────────────────────────────────────────────────────────────

def num(s):
    try:
        if s is None or str(s).strip() in ('', 'nan', 'None'): return 0.0
        s = str(s).strip().replace('R$','').replace(' ','')
        if ',' in s and '.' in s:
            s = s.replace('.','').replace(',','.') if s.rindex(',') > s.rindex('.') else s.replace(',','')
        elif ',' in s:
            s = s.replace(',','.')
        return float(s)
    except:
        return 0.0

def fmt(v):
    return str(round(float(v), 2)).replace('.', ',')

def brl(v):
    s = f"{float(v):,.2f}".replace(',','X').replace('.',',').replace('X','.')
    return f"R$ {s}"

def mes_label(m):
    meses = {"01":"Jan","02":"Fev","03":"
