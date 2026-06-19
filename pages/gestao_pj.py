import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.sheets import (
    load_config, load_nfs, load_custos_pj, load_fluxo_pf,
    save_fechamento_pj, save_fluxo_pf, save_fluxo_pj_resumo
)
from utils.formatters import brl, mes_label


def render():
    st.title("🏢 Gestão PJ")

    cfg = load_config()
    tab_fechar, tab_historico, tab_graficos = st.tabs([
        "📌 Fechar mês", "📋 Histórico", "📊 Gráficos"
    ])

    # ── Fechar mês ─────────────────────────────────────────────────────────────
    with tab_fechar:
        st.subheader("Fechamento mensal")

        hoje = datetime.now()
        meses_opcoes = [
            (hoje.replace(day=1) - pd.Timedelta(days=30*i)).strftime("%Y-%m")
            for i in range(12)
        ]

        col1, col2 = st.columns([1, 2])
        mes_ref = col1.selectbox("Mês de referência", meses_opcoes, format_func=mes_label)

        # Busca NFs faturadas neste mês
        nfs = load_nfs()
        nfs_fat = nfs[
            (nfs["mes_faturamento"] == mes_ref) & (nfs["status"] == "faturado")
        ] if not nfs.empty else pd.DataFrame()

        receita_auto = nfs_fat["valor"].sum() if not nfs_fat.empty else 0.0

        col2.metric(
            f"Receita das NFs faturadas em {mes_label(mes_ref)}",
            brl(receita_auto),
            help="Soma das NFs com status 'faturado' neste mês"
        )

        if not nfs_fat.empty:
            with st.expander("Ver NFs consideradas"):
                st.dataframe(
                    nfs_fat[["cliente", "descricao", "valor"]].assign(
                        valor=nfs_fat["valor"].apply(brl)
                    ),
                    hide_index=True, use_container_width=True
                )

        receita_manual = st.number_input(
            "Ajustar receita manualmente (se necessário)",
            value=float(receita_auto),
            min_value=0.0,
            step=100.0,
            format="%.2f",
            help="Use se houver receitas não registradas como NF"
        )

        # Preview do cálculo
        pro_labore = float(cfg.get("pro_labore", 0))
        aliquota = float(cfg.get("aliquota_simples", 0.06))
        prev_privada = float(cfg.get("prev_privada", 0))
        contador = float(cfg.get("contador", 0))
        fies = float(cfg.get("fies", 635.29))
        pro_labore_liq = float(cfg.get("pro_labore_liquido", 1513.0))
        meta_invest = float(cfg.get("meta_investimento_pct", 0.20))
        meta_casa = float(cfg.get("meta_casa_propria", 4000.0))

        receita = receita_manual
        simples = receita * aliquota
        darf = pro_labore * 0.11
        total_custos = simples + darf + prev_privada + contador + pro_labore
        saldo_pj = receita - total_custos
        dist_lucros = max(0, saldo_pj - fies)
        total_nubank = pro_labore_liq + dist_lucros
        investimento = total_nubank * meta_invest
        saldo_livre = total_nubank - investimento - meta_casa

        st.divider()
        st.markdown("#### 🔍 Preview do fechamento")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**PJ — Custos**")
            dados_pj = {
                "Item": ["Receita", "Simples Nacional", "DARF (11% pro-labore)",
                          "Previdência Privada", "Contador", "Pro-labore bruto",
                          "— Saldo PJ —", "FIES (BB)", "Dist. lucros"],
                "Valor": [
                    brl(receita), f"- {brl(simples)}", f"- {brl(darf)}",
                    f"- {brl(prev_privada)}", f"- {brl(contador)}", f"- {brl(pro_labore)}",
                    brl(saldo_pj), f"- {brl(fies)}", brl(dist_lucros)
                ]
            }
            st.dataframe(pd.DataFrame(dados_pj), hide_index=True, use_container_width=True)

        with col2:
            st.markdown("**PF — Distribuição (Nubank)**")
            dados_pf = {
                "Item": ["Pro-labore líquido", "Dist. lucros",
                          "= Total Nubank", "Investimento (20%)",
                          "Casa própria", "Saldo livre"],
                "Valor": [
                    brl(pro_labore_liq), brl(dist_lucros),
                    brl(total_nubank), f"- {brl(investimento)}",
                    f"- {brl(meta_casa)}", brl(saldo_livre)
                ]
            }
            st.dataframe(pd.DataFrame(dados_pf), hide_index=True, use_container_width=True)

        st.divider()

        # Waterfall chart
        fig = go.Figure(go.Waterfall(
            name="Fluxo", orientation="v",
            measure=["absolute", "relative", "relative", "relative",
                     "relative", "relative", "total",
                     "relative", "total"],
            x=["Receita", "Simples", "DARF", "Prev. Priv.",
               "Contador", "Pro-labore", "Saldo PJ",
               "FIES", "Dist. Lucros"],
            y=[receita, -simples, -darf, -prev_privada,
               -contador, -pro_labore, 0,
               -fies, 0],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": "#EF4444"}},
            increasing={"marker": {"color": "#22C55E"}},
            totals={"marker": {"color": "#3B82F6"}},
        ))
        fig.update_layout(
            title=f"Waterfall — {mes_label(mes_ref)}",
            height=400,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

        if st.button("💾 Confirmar fechamento", type="primary", use_container_width=True):
            dist_lucros_salvo, pro_liq_salvo = save_fechamento_pj(mes_ref, receita, cfg)
            save_fluxo_pf(mes_ref, pro_liq_salvo, dist_lucros_salvo, cfg)
            save_fluxo_pj_resumo(
                mes_ref, receita, total_custos, saldo_pj,
                pro_labore_liq, fies, dist_lucros,
                total_nubank, investimento, meta_casa, saldo_livre
            )
            st.success(f"✅ Fechamento de {mes_label(mes_ref)} salvo com sucesso!")
            st.balloons()

    # ── Histórico ──────────────────────────────────────────────────────────────
    with tab_historico:
        custos = load_custos_pj()
        if custos.empty:
            st.info("Nenhum fechamento registrado ainda.")
        else:
            df = custos.sort_values("mes_ref", ascending=False).copy()
            df["mes"] = df["mes_ref"].apply(mes_label)
            show_cols = {
                "mes": "Mês",
                "receita_faturada": "Receita",
                "simples_nacional": "Simples",
                "darf": "DARF",
                "prev_privada": "Prev. Priv.",
                "contador": "Contador",
                "total_custos": "Total Custos",
                "saldo_pj": "Saldo PJ",
                "distribuicao_lucros": "Dist. Lucros",
            }
            df_show = df[list(show_cols.keys())].rename(columns=show_cols)
            for col in list(show_cols.values())[1:]:
                df_show[col] = df_show[col].apply(brl)
            st.dataframe(df_show, hide_index=True, use_container_width=True)

    # ── Gráficos ───────────────────────────────────────────────────────────────
    with tab_graficos:
        custos = load_custos_pj()
        if custos.empty or len(custos) < 2:
            st.info("Registre pelo menos 2 meses para visualizar os gráficos.")
        else:
            df = custos.sort_values("mes_ref").copy()
            df["mes"] = df["mes_ref"].apply(mes_label)

            # Receita vs Custos
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(name="Receita", x=df["mes"],
                                   y=df["receita_faturada"], marker_color="#22C55E"))
            fig1.add_trace(go.Bar(name="Total Custos", x=df["mes"],
                                   y=df["total_custos"], marker_color="#EF4444"))
            fig1.add_trace(go.Scatter(name="Saldo PJ", x=df["mes"],
                                       y=df["saldo_pj"], mode="lines+markers",
                                       line=dict(color="#3B82F6", width=2)))
            fig1.update_layout(
                title="Receita × Custos × Saldo PJ",
                barmode="group", height=400,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig1, use_container_width=True)

            # Composição dos custos
            ultimo = df.iloc[-1]
            fig2 = px.pie(
                names=["Simples Nacional", "DARF", "Prev. Privada",
                        "Contador", "Pro-labore"],
                values=[ultimo["simples_nacional"], ultimo["darf"],
                        ultimo["prev_privada"], ultimo["contador"],
                        ultimo["pro_labore_bruto"]],
                title=f"Composição de custos — {ultimo['mes']}",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig2, use_container_width=True)
