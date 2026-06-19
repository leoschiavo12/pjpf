import streamlit as st
import pandas as pd
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ── Conexão ────────────────────────────────────────────────────────────────────

SHEET_ID = st.secrets["google_sheets"]["spreadsheet_id"]

def get_sheets_service():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=creds).spreadsheets()

def _ler_aba(tab: str, colunas: list) -> pd.DataFrame:
    """lê uma aba e retorna DataFrame com as colunas definidas"""
    try:
        svc = get_sheets_service()
        n   = len(colunas)
        col_fim = chr(ord('A') + n - 1)
        res  = svc.values().get(
            spreadsheetId=SHEET_ID, range=f"{tab}!A:{col_fim}"
        ).execute()
        rows = res.get("values", [])
        if len(rows) <= 1:
            return pd.DataFrame(columns=colunas)
        padded = [(r + [''] * n)[:n] for r in rows[1:]]
        return pd.DataFrame(padded, columns=colunas)
    except Exception as e:
        st.error(f"Erro ao ler aba '{tab}': {e}")
        return pd.DataFrame(columns=colunas)

def _append_row(tab: str, row: list):
    """adiciona uma linha no final da aba"""
    svc = get_sheets_service()
    svc.values().append(
        spreadsheetId=SHEET_ID,
        range=f"{tab}!A:A",
        valueInputOption="USER_ENTERED",
        body={"values": [row]}
    ).execute()

def _update_row(tab: str, linha: int, row: list):
    """atualiza uma linha específica (1-based, incluindo header)"""
    col_fim = chr(ord('A') + len(row) - 1)
    svc = get_sheets_service()
    svc.values().update(
        spreadsheetId=SHEET_ID,
        range=f"{tab}!A{linha}:{col_fim}{linha}",
        valueInputOption="USER_ENTERED",
        body={"values": [row]}
    ).execute()

def _delete_row(tab: str, linha: int, sheet_gid: int = 0):
    """deleta uma linha específica (1-based)"""
    svc = get_sheets_service()
    start = linha - 1  # converte para 0-based
    body = {"requests": [{"deleteDimension": {"range": {
        "sheetId": sheet_gid,
        "dimension": "ROWS",
        "startIndex": start,
        "endIndex": start + 1
    }}}]}
    svc.batchUpdate(spreadsheetId=SHEET_ID, body=body).execute()

def _fmt(v):
    """formata número para salvar no Sheets (vírgula decimal, padrão BR)"""
    return str(round(float(v), 2)).replace('.', ',')

def _num(s):
    """converte string do Sheets para float — aceita vírgula ou ponto decimal"""
    try:
        if s is None or str(s).strip() in ('', 'nan', 'None'):
            return 0.0
        s = str(s).strip().replace('R$', '').replace(' ', '')
        # formato BR: 1.234,56
        if ',' in s and '.' in s:
            if s.rindex(',') > s.rindex('.'):
                s = s.replace('.', '').replace(',', '.')
            else:
                s = s.replace(',', '')
        # só vírgula: 0,06 → 0.06
        elif ',' in s:
            s = s.replace(',', '.')
        return float(s)
    except:
        return 0.0

# ── Config ─────────────────────────────────────────────────────────────────────

CONFIG_COLS = ["chave", "valor"]

def load_config() -> dict:
    df = _ler_aba("config", CONFIG_COLS)
    return {row["chave"]: row["valor"] for _, row in df.iterrows()}

def save_config(key: str, value):
    df = _ler_aba("config", CONFIG_COLS)
    for i, row in df.iterrows():
        if row["chave"] == key:
            _update_row("config", i + 2, [key, str(value).replace('.', ',')])
            return
    _append_row("config", [key, str(value).replace('.', ',')])

# ── NFs ────────────────────────────────────────────────────────────────────────

NF_COLS = ["id", "cliente", "descricao", "valor",
           "mes_competencia", "mes_faturamento", "status", "criado_em"]

def load_nfs() -> pd.DataFrame:
    df = _ler_aba("nfs", NF_COLS)
    if df.empty:
        return df
    df["valor"] = df["valor"].apply(_num)
    df["id"]    = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)
    return df

def add_nf(cliente: str, descricao: str, valor: float,
           mes_competencia: str, mes_faturamento: str, status: str):
    df     = load_nfs()
    next_id = int(df["id"].max()) + 1 if not df.empty else 1
    now    = datetime.now().strftime("%d/%m/%Y %H:%M")
    _append_row("nfs", [next_id, cliente, descricao, _fmt(valor),
                         mes_competencia, mes_faturamento, status, now])

def update_nf_status(nf_id: int, new_status: str):
    df = load_nfs()
    for i, row in df.iterrows():
        if int(row["id"]) == nf_id:
            linha = i + 2  # +1 header +1 por ser 1-based
            row_atual = [row["id"], row["cliente"], row["descricao"],
                         _fmt(row["valor"]), row["mes_competencia"],
                         row["mes_faturamento"], new_status, row["criado_em"]]
            _update_row("nfs", linha, row_atual)
            return

def delete_nf(nf_id: int):
    df = load_nfs()
    # busca o sheet_gid da aba nfs
    svc = get_sheets_service()
    meta = svc.get(spreadsheetId=SHEET_ID).execute()
    gid  = next((s["properties"]["sheetId"]
                 for s in meta["sheets"]
                 if s["properties"]["title"] == "nfs"), 0)
    for i, row in df.iterrows():
        if int(row["id"]) == nf_id:
            _delete_row("nfs", i + 2, gid)
            return

# ── Custos PJ ──────────────────────────────────────────────────────────────────

CUSTOS_COLS = ["mes_ref", "receita_faturada", "simples_nacional", "pro_labore_bruto",
               "darf", "prev_privada", "contador", "total_custos",
               "saldo_pj", "distribuicao_lucros", "fechado"]

def load_custos_pj() -> pd.DataFrame:
    df = _ler_aba("custos_pj", CUSTOS_COLS)
    if df.empty:
        return df
    for col in CUSTOS_COLS[1:-1]:  # tudo menos mes_ref e fechado
        df[col] = df[col].apply(_num)
    return df

def save_fechamento_pj(mes_ref: str, receita: float, cfg: dict):
    pro_labore    = float(cfg.get("pro_labore", 0))
    aliquota      = _num(cfg.get("aliquota_simples", "0,06"))
    prev_privada  = _num(cfg.get("prev_privada", "0"))
    contador      = _num(cfg.get("contador", "0"))
    fies          = _num(cfg.get("fies", "635,29"))
    pro_labore_liq = _num(cfg.get("pro_labore_liquido", "1513"))

    simples       = receita * aliquota
    darf          = pro_labore * 0.11
    total_custos  = simples + darf + prev_privada + contador + pro_labore
    saldo_pj      = receita - total_custos
    dist_lucros   = max(0.0, saldo_pj - fies)

    row = [mes_ref, _fmt(receita), _fmt(simples), _fmt(pro_labore),
           _fmt(darf), _fmt(prev_privada), _fmt(contador),
           _fmt(total_custos), _fmt(saldo_pj), _fmt(dist_lucros), "Sim"]

    df = load_custos_pj()
    for i, r in df.iterrows():
        if r["mes_ref"] == mes_ref:
            _update_row("custos_pj", i + 2, row)
            return round(dist_lucros, 2), round(pro_labore_liq, 2)

    _append_row("custos_pj", row)
    return round(dist_lucros, 2), round(pro_labore_liq, 2)

# ── Fluxo PJ ───────────────────────────────────────────────────────────────────

FLUXO_PJ_COLS = ["mes_ref", "receita", "total_custos", "saldo_pj",
                  "pro_labore_liq", "fies", "distribuicao_lucros",
                  "total_nubank", "investimento", "casa_propria", "saldo_livre"]

def load_fluxo_pj() -> pd.DataFrame:
    df = _ler_aba("fluxo_pj", FLUXO_PJ_COLS)
    if df.empty:
        return df
    for col in FLUXO_PJ_COLS[1:]:
        df[col] = df[col].apply(_num)
    return df

def save_fluxo_pj_resumo(mes_ref: str, receita: float, total_custos: float,
                          saldo_pj: float, pro_labore_liq: float, fies: float,
                          dist_lucros: float, total_nubank: float,
                          investimento: float, casa_propria: float,
                          saldo_livre: float):
    row = [mes_ref, _fmt(receita), _fmt(total_custos), _fmt(saldo_pj),
           _fmt(pro_labore_liq), _fmt(fies), _fmt(dist_lucros),
           _fmt(total_nubank), _fmt(investimento), _fmt(casa_propria), _fmt(saldo_livre)]

    df = load_fluxo_pj()
    for i, r in df.iterrows():
        if r["mes_ref"] == mes_ref:
            _update_row("fluxo_pj", i + 2, row)
            return
    _append_row("fluxo_pj", row)

# ── Fluxo PF ───────────────────────────────────────────────────────────────────

FLUXO_PF_COLS = ["mes_ref", "pro_labore_liquido", "distribuicao_lucros",
                  "total_nubank", "investimento", "casa_propria",
                  "saldo_livre", "pct_investimento"]

def load_fluxo_pf() -> pd.DataFrame:
    df = _ler_aba("fluxo_pf", FLUXO_PF_COLS)
    if df.empty:
        return df
    for col in FLUXO_PF_COLS[1:]:
        df[col] = df[col].apply(_num)
    return df

def save_fluxo_pf(mes_ref: str, pro_labore_liq: float,
                   dist_lucros: float, cfg: dict):
    meta_invest  = _num(cfg.get("meta_investimento_pct", "0,20"))
    casa_propria = _num(cfg.get("meta_casa_propria", "4000"))

    total_nubank = pro_labore_liq + dist_lucros
    investimento = total_nubank * meta_invest
    saldo_livre  = total_nubank - investimento - casa_propria
    pct          = round(meta_invest * 100, 1)

    row = [mes_ref, _fmt(pro_labore_liq), _fmt(dist_lucros),
           _fmt(total_nubank), _fmt(investimento), _fmt(casa_propria),
           _fmt(saldo_livre), _fmt(pct)]

    df = load_fluxo_pf()
    for i, r in df.iterrows():
        if r["mes_ref"] == mes_ref:
            _update_row("fluxo_pf", i + 2, row)
            return
    _append_row("fluxo_pf", row)
