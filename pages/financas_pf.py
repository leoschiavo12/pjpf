import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.sheets import load_config, load_fluxo_pf
from utils.formatters import brl, mes_label


def render():
    st.title("👤 Finanças PF")

    cfg = load_config()
    pf = load_fluxo_pf()

    meta_invest = float(cfg.get("meta_investimento_pct", 0.20))
    meta_casa = float(cfg.get("meta_casa_propria", 4000.0))
    fies = float(cfg.get("fies", 635.29))

    if pf.empty:
        st.info("Nenhum dado de PF ainda. Faça o fechamento de pelo menos um mês na aba Gestão PJ.")
        return

    tab_ultimo, tab_historico, tab_graficos = st.tabs([
        "📌 Último mês", "📋 Histórico", "📊 Gráficos"
    ])

    df = pf.sort_values("mes_ref", ascending=False)
    ultimo = df.iloc[0]

    # ── Último mês ──────────────────────────────────────────────────────────────
    with tab_ultimo:
        st.subheader(f"Distribuição PF — {mes_label(ultimo['mes_ref'])}")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total no Nubank", brl(float(ultimo["total_nubank"])))
        col2.metric("Pro-labore líquido", brl(float(ultimo["pro_labore_liquido"])))
        col3.metric("Distribuição de lucros", brl(float(ultimo["distribuicao_lucros"])))

        st.divider()

        col1, col2, col3 = st.columns(3)
        col1.metric(
            f"🏦 Investimento ({meta_invest*100:.0f}%)",
            brl(float(ultimo["investimento"])),
            help="Carteira de aposentadoria"
        )
        col2.metric("🏠 Casa própria", brl(float(ultimo["casa_propria"])))
        col3.metric(
            "💳 Saldo livre",
            brl(float(ultimo["saldo_livre"])),
            delta="para cartão de crédito"
        )

        st.divider()

        # Transferências
        st.markdown("#### 📤 Resumo de transferências do mês")

        trans = [
            {"Destino": "Nubank PF — Pro-labore", "Valor": brl(float(ultimo["pro_labore_liquido"])),
             "Conta": "Nubank"},
            {"Destino": "Banco do Brasil — FIES", "Valor": brl(fies), "Conta": "BB"},
            {"Destino": "Investimento (carteira)", "Valor": brl(float(ultimo["investimento"])),
             "Conta": "Corretora"},
            {"Destino": "Plano casa própria", "Valor": brl(float(ultimo["casa_propria"])),
             "Conta": "Reserva"},
            {"Destino": "Saldo livre (cartão)", "Valor": brl(float(ultimo["saldo_livre"])),
             "Conta": "Nubank"},
        ]
        st.dataframe(trans, hide_index=True, use_container_width=True)

        # Gauge investimento
        pct_atual = (float(ultimo["investimento"]) / float(ultimo["total_nubank"]) * 100
                     if float(ultimo["total_nubank"]) > 0 else 0)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=pct_atual,
            title={"text": "% investido da entrada Nubank"},
            delta={"reference": meta_invest * 100},
            gauge={
                "axis": {"range": [0, 50]},
                "bar": {"color": "#22C55E"},
                "steps": [
                    {"range": [0, meta_invest * 100 * 0.8], "color": "#FEE2E2"},
                    {"range": [meta_invest * 100 * 0.8, meta_invest * 100], "color": "#FEF9C3"},
                    {"range": [meta_invest * 100, 50], "color": "#DCFCE7"},
                ],
                "threshold": {
                    "line": {"color": "#3B82F6", "width": 4},
                    "thickness": 0.75,
                    "value": meta_invest * 100
                }
            },
            number={"suffix": "%", "valueformat": ".1f"}
        ))
        fig_gauge.update_layout(
            height=300,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    # ── Histórico ──────────────────────────────────────────────────────────────
    with tab_historico:
        df_show = df.copy()
        df_show["Mês"] = df_show["mes_ref"].apply(mes_label)
        rename = {
            "pro_labore_liquido": "Pro-labore",
            "distribuicao_lucros": "Dist. Lucros",
            "total_nubank": "Total Nubank",
            "investimento": "Investimento",
            "casa_propria": "Casa Própria",
            "saldo_livre": "Saldo Livre",
            "pct_investimento": "% Invest."
        }
        df_show = df_show[["Mês"] + list(rename.keys())].rename(columns=rename)
        for col in list(rename.values())[:-1]:
            df_show[col] = df_show[col].apply(brl)
        df_show["% Invest."] = df_show["% Invest."].apply(lambda x: f"{x:.1f}%")
        st.dataframe(df_show, hide_index=True, use_container_width=True)

    # ── Gráficos ───────────────────────────────────────────────────────────────
    with tab_graficos:
        if len(df) < 2:
            st.info("Registre pelo menos 2 meses para ver os gráficos.")
            return

        dfc = df.sort_values("mes_ref").copy()
        dfc["mes"] = dfc["mes_ref"].apply(mes_label)

        # Stacked bar: destinos do Nubank
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(name="Investimento", x=dfc["mes"],
                               y=dfc["investimento"], marker_color="#22C55E"))
        fig1.add_trace(go.Bar(name="Casa Própria", x=dfc["mes"],
                               y=dfc["casa_propria"], marker_color="#3B82F6"))
        fig1.add_trace(go.Bar(name="Saldo Livre", x=dfc["mes"],
                               y=dfc["saldo_livre"], marker_color="#F59E0B"))
        fig1.update_layout(
            title="Destinos do Nubank PF por mês",
            barmode="stack", height=400,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig1, use_container_width=True)

        # % investimento ao longo do tempo
        fig2 = px.line(dfc, x="mes", y="pct_investimento",
                        markers=True, title="% Investimento por mês")
        fig2.add_hline(y=meta_invest * 100, line_dash="dash",
                        line_color="red", annotation_text=f"Meta {meta_invest*100:.0f}%")
        fig2.update_layout(
            height=350,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis_ticksuffix="%"
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Acumulado investido no ano
        ano_atual = dfc["mes_ref"].str[:4].max()
        dfc_ano = dfc[dfc["mes_ref"].str[:4] == ano_atual]
        acumulado = dfc_ano["investimento"].cumsum()
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=dfc_ano["mes"], y=acumulado,
            mode="lines+markers+text",
            text=acumulado.apply(brl),
            textposition="top center",
            fill="tozeroy",
            line=dict(color="#22C55E", width=2)
        ))
        fig3.update_layout(
            title=f"Acumulado investido em {ano_atual}",
            height=350,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig3, use_container_width=True)
