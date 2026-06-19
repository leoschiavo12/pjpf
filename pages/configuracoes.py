import streamlit as st
from utils.sheets import load_config, save_config
from utils.formatters import brl


def render():
    st.title("⚙️ Configurações")
    st.caption("Valores que mudam anualmente ou raramente. Altere aqui e tudo é recalculado automaticamente.")

    cfg = load_config()

    with st.form("form_config"):
        st.subheader("🏢 PJ — Parâmetros")

        col1, col2 = st.columns(2)
        pro_labore = col1.number_input(
            "Pro-labore bruto (R$)",
            value=float(cfg.get("pro_labore", 0)),
            min_value=0.0, step=100.0, format="%.2f",
            help="Base de cálculo para DARF (11%) e custo da empresa"
        )
        pro_labore_liq = col2.number_input(
            "Pro-labore líquido (R$)",
            value=float(cfg.get("pro_labore_liquido", 1513.0)),
            min_value=0.0, step=50.0, format="%.2f",
            help="Valor que entra na sua conta Nubank PF"
        )

        col3, col4 = st.columns(2)
        prev_privada = col3.number_input(
            "Previdência privada (R$/mês)",
            value=float(cfg.get("prev_privada", 0)),
            min_value=0.0, step=50.0, format="%.2f"
        )
        contador = col4.number_input(
            "Honorários do contador (R$/mês)",
            value=float(cfg.get("contador", 0)),
            min_value=0.0, step=50.0, format="%.2f"
        )

        aliquota_simples = st.slider(
            "Alíquota Simples Nacional (%)",
            min_value=1.0, max_value=20.0,
            value=float(cfg.get("aliquota_simples", 0.06)) * 100,
            step=0.1,
            format="%.1f%%"
        )

        st.divider()
        st.subheader("🏦 PF — Parâmetros")

        col5, col6 = st.columns(2)
        fies = col5.number_input(
            "FIES — parcela mensal (R$)",
            value=float(cfg.get("fies", 635.29)),
            min_value=0.0, step=10.0, format="%.2f",
            help="Transferência mensal para Banco do Brasil (vence dia 10)"
        )
        meta_casa = col6.number_input(
            "Plano casa própria (R$/mês)",
            value=float(cfg.get("meta_casa_propria", 4000.0)),
            min_value=0.0, step=100.0, format="%.2f"
        )

        meta_invest = st.slider(
            "Meta de investimento (% da entrada Nubank)",
            min_value=5, max_value=60,
            value=int(float(cfg.get("meta_investimento_pct", 0.20)) * 100),
            step=5,
            format="%d%%"
        )

        submitted = st.form_submit_button("💾 Salvar configurações", type="primary",
                                           use_container_width=True)

    if submitted:
        save_config("pro_labore", pro_labore)
        save_config("pro_labore_liquido", pro_labore_liq)
        save_config("prev_privada", prev_privada)
        save_config("contador", contador)
        save_config("aliquota_simples", round(aliquota_simples / 100, 4))
        save_config("fies", fies)
        save_config("meta_casa_propria", meta_casa)
        save_config("meta_investimento_pct", round(meta_invest / 100, 2))
        st.success("✅ Configurações salvas com sucesso!")
        st.rerun()

    # Preview com os valores atuais
    st.divider()
    st.subheader("👀 Preview — impacto no mês típico")
    st.caption("Simulação com pro-labore como receita base (sem NFs)")

    pl = float(cfg.get("pro_labore", 0))
    alq = float(cfg.get("aliquota_simples", 0.06))
    pp = float(cfg.get("prev_privada", 0))
    cnt = float(cfg.get("contador", 0))
    fi = float(cfg.get("fies", 635.29))
    pll = float(cfg.get("pro_labore_liquido", 1513.0))
    mi = float(cfg.get("meta_investimento_pct", 0.20))
    mc = float(cfg.get("meta_casa_propria", 4000.0))

    darf = pl * 0.11
    st.info(
        f"DARF mensal: **{brl(darf)}** | "
        f"Custos fixos mín: **{brl(darf + pp + cnt)}** | "
        f"Investimento mín (só pro-labore): **{brl(pll * mi)}** | "
        f"Casa própria: **{brl(mc)}** | "
        f"FIES: **{brl(fi)}**"
    )
