import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
# ... (mantenha aqui todas as suas funções de conexão, helpers e load_...)

st.set_page_config(page_title="Financeiro PJ/PF", page_icon="💼", layout="wide")

st.markdown("## 💼 Financeiro PJ/PF")

# DEFINIÇÃO DAS ABAS (deve vir antes dos blocos "with")
aba_pj, aba_pf, aba_config = st.tabs(["🏢 Gestão PJ", "👤 Finanças PF", "⚙️ Configurações"])

# ══════════════════════════════════════════════════════════════════════════════
# ABA PJ
# ══════════════════════════════════════════════════════════════════════════════
with aba_pj:
    resumo, nfs_tab = st.tabs(["📈 Resumo", "📄 Notas Fiscais"])
    with resumo:
        st.write("Conteúdo do Resumo PJ...")
    with nfs_tab:
        st.write("Conteúdo das NFs...")

# ══════════════════════════════════════════════════════════════════════════════
# ABA PF
# ══════════════════════════════════════════════════════════════════════════════
with aba_pf:
    orcamento, planos, reserva = st.tabs(["💰 Orçamento Mensal", "🎯 Planos", "🛡️ Reserva"])
    with orcamento:
        st.write("Distribuição do Fluxo...")
    with planos:
        st.write("Metas (FIES, Casa)...")
    with reserva:
        st.write("Reserva de emergência...")

# ══════════════════════════════════════════════════════════════════════════════
# ABA CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
with aba_config:
    st.subheader("⚙️ Configurações")
    cfg = load_config()
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏢 PJ")
        pro_labore = st.number_input("Pro-labore bruto (R$)", value=num(cfg.get("pro_labore","0")), step=100.0)
        # ... (adicione os outros campos aqui)
        
    with col2:
        st.markdown("### 👤 PF")
        fies = st.number_input("FIES (R$)", value=num(cfg.get("fies","635,29")), step=10.0)
        # ... (adicione os outros campos aqui)
        
    if st.button("💾 Salvar todas as configurações", type="primary"):
        save_config("pro_labore", pro_labore)
        save_config("fies", fies)
        st.success("Salvo!")
        st.rerun()
        
