import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ══════════════════════════════════════════════════════════════════════════════
# 1. FUNÇÕES DE SUPORTE E CONEXÃO (Devem vir antes do uso)
# ══════════════════════════════════════════════════════════════════════════════

# [Cole aqui as suas funções get_svc, ler, append, update, delete_row]
# [Cole aqui as suas funções helpers: num, fmt, brl, mes_label]

def load_config():
    # Exemplo simples, ajuste conforme sua implementação original
    df = ler("config", ["chave","valor"])
    return {r["chave"]: r["valor"] for _, r in df.iterrows()}

def save_config(key, value):
    df = ler("config", ["chave","valor"])
    # [Lógica de save_config original]

# [Cole aqui as funções load_nfs, load_custos_pj, load_fluxo_pj, load_fluxo_pf, etc.]

# ══════════════════════════════════════════════════════════════════════════════
# 2. CONFIGURAÇÃO E ABAS
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="Financeiro PJ/PF", page_icon="💼", layout="wide")
st.markdown("## 💼 Financeiro PJ/PF")

aba_pj, aba_pf, aba_config = st.tabs(["🏢 Gestão PJ", "👤 Finanças PF", "⚙️ Configurações"])

# ══════════════════════════════════════════════════════════════════════════════
# 3. CONTEÚDO DAS ABAS
# ══════════════════════════════════════════════════════════════════════════════

with aba_pj:
    resumo, nfs_tab = st.tabs(["📈 Resumo", "📄 Notas Fiscais"])
    with resumo:
        st.write("Conteúdo do Resumo...")
    with nfs_tab:
        st.write("Conteúdo das NFs...")

with aba_pf:
    orcamento, planos, reserva = st.tabs(["💰 Orçamento Mensal", "🎯 Planos", "🛡️ Reserva"])
    with orcamento:
        st.write("Orçamento...")
    with planos:
        st.write("Planos...")
    with reserva:
        st.write("Reserva...")

with aba_config:
    st.subheader("⚙️ Configurações do Sistema")
    cfg = load_config() # Agora a função já foi lida pelo Python!

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🏢 PJ")
        pro_labore = st.number_input("Pro-labore bruto (R$)", value=float(num(cfg.get("pro_labore","0"))), step=100.0)
        # ... (adicione seus outros inputs aqui)
    with col2:
        st.markdown("### 👤 PF")
        fies = st.number_input("FIES (R$)", value=float(num(cfg.get("fies","635,29"))), step=10.0)
        # ... (adicione seus outros inputs aqui)

    if st.button("💾 Salvar configurações", type="primary"):
        save_config("pro_
