import streamlit as st

st.set_page_config(
    page_title="Financeiro PJ/PF",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Imports das páginas ───────────────────────────────────────────────────────
from pages import visao_geral, notas_fiscais, gestao_pj, financas_pf, fluxo_caixa, configuracoes

# ── Sidebar de navegação ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💼 Financeiro PJ/PF")
    st.divider()

    pagina = st.radio(
        "Navegação",
        options=[
            "🏠 Visão Geral",
            "📄 Notas Fiscais",
            "🏢 Gestão PJ",
            "👤 Finanças PF",
            "📊 Fluxo de Caixa",
            "⚙️ Configurações",
        ],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("v1.0 · Leo Schiavo")

# ── Roteamento ────────────────────────────────────────────────────────────────
if pagina == "🏠 Visão Geral":
    visao_geral.render()
elif pagina == "📄 Notas Fiscais":
    notas_fiscais.render()
elif pagina == "🏢 Gestão PJ":
    gestao_pj.render()
elif pagina == "👤 Finanças PF":
    financas_pf.render()
elif pagina == "📊 Fluxo de Caixa":
    fluxo_caixa.render()
elif pagina == "⚙️ Configurações":
    configuracoes.render()
