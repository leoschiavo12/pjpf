import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from utils.sheets import load_config, load_nfs, load_fluxo_pj
from utils.formatters import brl, mes_label


def render():
    st.title("📊 Fluxo de Caixa")

    cfg = load_config()
    nfs = load_nfs()
    fluxo = load_fluxo_pj()

    fies = float(cfg.get("fies", 635.29))
    meta_casa = float(cfg.get("meta_casa_propria", 4000.0))

    hoje = datetime.now()
    mes_atual = hoje.strftime("%Y-%m")

    # ── Meses futuros com NFs pendentes ───────────────────────────────────────
    if not nfs.empty:
        nfs_pend = nfs[nfs["status"] == "pendente"].copy()
    else:
        nfs_pend = pd.DataFrame()

    # ── Construir timeline completa ────────────────────────────────────────────
    # Meses já fechados (do fluxo_pj)
    meses_fechados = set()
    if not fluxo.empty:
        meses_fechados = set(fluxo["mes_ref"].tolist())

    # Meses futuros com NFs pendentes
    meses_futuros = set()
    if not nfs_pend.empty:
        meses_futuros = set(nfs_pend["mes_faturamento"].tolist())

    todos_meses = sorted(meses_fechados | meses_futuros)

    # Adiciona próximos 3 meses mesmo sem NFs (para planejamento)
    for i in range(3):
        m = (datetime(hoje.year, hoje.month, 1) + pd.DateOffset(months=i)).strftime("%Y-%m")
        if m not in todos_meses:
            todos_meses.append(m)
    todos_meses = sorted(set(todos_meses))

    # ── Monta DataFrame de timeline ────────────────────────────────────────────
    rows = []
    for mes in todos_meses:
        is_fechado = mes in meses_fechados
        is_futuro = mes > mes_atual

        if is_fechado and not fluxo.empty:
            f = fluxo[fluxo["mes_ref"] == mes].iloc[0]
            rows.append({
                "mes_ref": mes,
                "mes": mes_label(mes),
                "tipo": "Realizado",
                "receita": float(f["receita"]),
                "total_custos": float(f["total_custos"]),
                "saldo_pj": float(f["saldo_pj"]),
                "total_nubank": float(f["total_nubank"]),
                "investimento": float(f["investimento"]),
                "casa_propria": float(f["casa_propria"]),
                "saldo_livre": float(f["saldo_livre"]),
            })
        else:
            # Projeção baseada nas NFs pendentes
            rec_proj = 0.0
            if not nfs_pend.empty:
                nfs_mes = nfs_pend[nfs_pend["mes_faturamento"] == mes]
                rec_proj = float(nfs_mes["valor"].sum())

            # Usa custos fixos da config
            pro_labore = float(cfg.get("pro_labore", 0))
            aliquota = float(cfg.get("aliquota_simples", 0.06))
            prev_privada = float(cfg.get("prev_privada", 0))
            contador = float(cfg.get("contador", 0))
            pro_labore_liq = float(cfg.get("pro_labore_liquido", 1513.0))
            meta_invest = float(cfg.get("meta_investimento_pct", 0.20))

            simples = rec_proj * aliquota
            darf = pro_labore * 0.11
            total_custos = simples + darf + prev_privada + contador + pro_labore
            saldo_pj = rec_proj - total_custos
            dist_lucros = max(0, saldo_pj - fies)
            total_nubank = pro_labore_liq + dist_lucros
            investimento = total_nubank * meta_invest
            saldo_livre = total_nubank - investimento - meta_casa

            rows.append({
                "mes_ref": mes,
                "mes": mes_label(mes),
                "tipo": "Projetado" if rec_proj > 0 else "Sem NFs",
                "receita": rec_proj,
                "total_custos": total_custos if rec_proj > 0 else 0,
                "saldo_pj": saldo_pj if rec_proj > 0 else 0,
                "total_nubank": total_nubank if rec_proj > 0 else 0,
                "investimento": investimento if rec_proj > 0 else 0,
                "casa_propria": meta_casa if rec_proj > 0 else 0,
                "saldo_livre": saldo_livre if rec_proj > 0 else 0,
            })

    df_timeline = pd.DataFrame(rows)

    if df_timeline.empty:
        st.info("Nenhum dado disponível para o fluxo de caixa.")
        return

    # ── KPIs rápidos ───────────────────────────────────────────────────────────
    realizados = df_timeline[df_timeline["tipo"] == "Realizado"]
    projetados = df_timeline[df_timeline["tipo"] == "Projetado"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Meses fechados", len(realizados))
    col2.metric("Receita realizada (total)", brl(realizados["receita"].sum()) if not realizados.empty else brl(0))
    col3.metric("Receita projetada (pendente)", brl(projetados["receita"].sum()) if not projetados.empty else brl(0))

    # Alerta meses sem NFs futuros
    sem_nf = df_timeline[(df_timeline["tipo"] == "Sem NFs") & (df_timeline["mes_ref"] >= mes_atual)]
    if not sem_nf.empty:
        col4.metric("⚠️ Meses sem NFs", len(sem_nf), delta="atenção", delta_color="inverse")
    else:
        col4.metric("✅ Cobertura futura", "OK")

    st.divider()

    # ── Gráfico principal: Receita Realizada vs Projetada ─────────────────────
    colors = df_timeline["tipo"].map({
        "Realizado": "#22C55E",
        "Projetado": "#3B82F6",
        "Sem NFs": "#EF4444"
    })

    fig1 = go.Figure()

    for tipo, color in [("Realizado", "#22C55E"), ("Projetado", "#3B82F6"), ("Sem NFs", "#EF4444")]:
        sub = df_timeline[df_timeline["tipo"] == tipo]
        if not sub.empty:
            fig1.add_trace(go.Bar(
                name=tipo, x=sub["mes"], y=sub["receita"],
                marker_color=color,
                text=sub["receita"].apply(lambda v: brl(v) if v > 0 else ""),
                textposition="auto"
            ))

    fig1.update_layout(
        title="Receita mensal — Realizado vs Projetado",
        barmode="group", height=400,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Mês", yaxis_title="R$"
    )
    st.plotly_chart(fig1, use_container_width=True)

    # ── Saldo PJ acumulado ─────────────────────────────────────────────────────
    df_com_saldo = df_timeline[df_timeline["saldo_pj"] != 0].copy()
    if not df_com_saldo.empty:
        df_com_saldo["saldo_acum"] = df_com_saldo["saldo_pj"].cumsum()

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df_com_saldo["mes"], y=df_com_saldo["saldo_acum"],
            mode="lines+markers",
            fill="tozeroy",
            name="Saldo acumulado",
            line=dict(color="#3B82F6", width=2),
            marker=dict(size=8)
        ))
        fig2.add_hline(y=0, line_dash="dash", line_color="red")
        fig2.update_layout(
            title="Saldo PJ acumulado",
            height=350,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Fluxo PF projetado ─────────────────────────────────────────────────────
    st.subheader("💳 Projeção PF — Nubank")

    df_pf = df_timeline[df_timeline["total_nubank"] > 0].copy()
    if not df_pf.empty:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Investimento", x=df_pf["mes"],
                               y=df_pf["investimento"], marker_color="#22C55E"))
        fig3.add_trace(go.Bar(name="Casa Própria", x=df_pf["mes"],
                               y=df_pf["casa_propria"], marker_color="#3B82F6"))
        fig3.add_trace(go.Bar(name="Saldo Livre", x=df_pf["mes"],
                               y=df_pf["saldo_livre"], marker_color="#F59E0B"))
        fig3.update_layout(
            title="Destinos PF por mês (realizado + projetado)",
            barmode="stack", height=400,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig3, use_container_width=True)

    # ── Tabela completa ────────────────────────────────────────────────────────
    with st.expander("📋 Ver tabela completa"):
        df_show = df_timeline.copy()
        for col in ["receita", "total_custos", "saldo_pj", "total_nubank",
                    "investimento", "casa_propria", "saldo_livre"]:
            df_show[col] = df_show[col].apply(brl)
        df_show = df_show.rename(columns={
            "mes": "Mês", "tipo": "Tipo",
            "receita": "Receita", "total_custos": "Custos",
            "saldo_pj": "Saldo PJ", "total_nubank": "Nubank",
            "investimento": "Invest.", "casa_propria": "Casa",
            "saldo_livre": "Livre"
        })[["Mês", "Tipo", "Receita", "Custos", "Saldo PJ",
            "Nubank", "Invest.", "Casa", "Livre"]]
        st.dataframe(df_show, hide_index=True, use_container_width=True)

    # ── NFs pendentes (aviso) ──────────────────────────────────────────────────
    if not nfs_pend.empty:
        st.divider()
        st.subheader("🟡 NFs pendentes de faturamento")
        df_p = nfs_pend[["cliente", "descricao", "valor",
                          "mes_competencia", "mes_faturamento"]].copy()
        df_p["valor"] = df_p["valor"].apply(brl)
        df_p.columns = ["Cliente", "Descrição", "Valor", "Competência", "Faturamento previsto"]
        st.dataframe(df_p, hide_index=True, use_container_width=True)
