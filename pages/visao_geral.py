import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sheets import load_config, load_nfs, load_custos_pj, load_fluxo_pf, _num
from utils.formatters import brl, mes_label


def render():
    st.title("🏠 Visão Geral")

    cfg = load_config()
    hoje = datetime.now()
    mes_atual = hoje.strftime("%Y-%m")
    mes_anterior = (hoje.replace(day=1) - pd.Timedelta(days=1)).strftime("%Y-%m")

    with st.expander("⚙️ Parâmetros ativos", expanded=False):
        col1, col2, col3 = st.columns(3)
        col1.metric("Pro-labore bruto", brl(_num(cfg.get("pro_labore", "0"))))
        col1.metric("Pro-labore líquido", brl(_num(cfg.get("pro_labore_liquido", "1513"))))
        col2.metric("Prev. Privada", brl(_num(cfg.get("prev_privada", "0"))))
        col2.metric("Contador", brl(_num(cfg.get("contador", "0"))))
        col3.metric("FIES", brl(_num(cfg.get("fies", "635,29"))))
        col3.metric("Alíquota Simples", f"{_num(cfg.get('aliquota_simples', '0,06'))*100:.1f}%")

    st.divider()
    st.subheader(f"📅 {mes_label(mes_atual)} — mês atual")

    nfs = load_nfs()
    nfs_mes = nfs[nfs["mes_competencia"] == mes_atual] if not nfs.empty else pd.DataFrame()
    nfs_faturar = nfs[
        (nfs["mes_faturamento"] == mes_atual) & (nfs["status"] == "pendente")
    ] if not nfs.empty else pd.DataFrame()

    col1, col2, col3 = st.columns(3)
    total_emitido = nfs_mes["valor"].sum() if not nfs_mes.empty else 0
    col1.metric("NFs emitidas no mês", brl(total_emitido))
    col2.metric("NFs a faturar este mês", len(nfs_faturar))

    custos = load_custos_pj()
    fechamento_mes = custos[custos["mes_ref"] == mes_atual] if not custos.empty else pd.DataFrame()
    if not fechamento_mes.empty:
        col3.metric("Saldo PJ", brl(float(fechamento_mes.iloc[0]["saldo_pj"])))
    else:
        col3.metric("Saldo PJ", "—", help="Mês ainda não fechado")

    st.divider()
    st.subheader(f"📋 {mes_label(mes_anterior)} — fechamento")

    custos_ant = custos[custos["mes_ref"] == mes_anterior] if not custos.empty else pd.DataFrame()
    pf = load_fluxo_pf()
    pf_ant = pf[pf["mes_ref"] == mes_anterior] if not pf.empty else pd.DataFrame()

    if not custos_ant.empty:
        c = custos_ant.iloc[0]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Receita faturada", brl(float(c["receita_faturada"])))
        col2.metric("Total custos PJ", brl(float(c["total_custos"])))
        col3.metric("Saldo PJ", brl(float(c["saldo_pj"])))
        col4.metric("Dist. lucros", brl(float(c["distribuicao_lucros"])))
    else:
        st.info(f"Nenhum fechamento registrado para {mes_label(mes_anterior)}.")

    if not pf_ant.empty:
        p = pf_ant.iloc[0]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Nubank PF", brl(float(p["total_nubank"])))
        col2.metric("Investimento", brl(float(p["investimento"])),
                    delta=f"{float(p['pct_investimento']):.1f}% da entrada")
        col3.metric("Casa própria", brl(float(p["casa_propria"])))
        col4.metric("Saldo livre", brl(float(p["saldo_livre"])))

    st.divider()
    st.subheader("📄 Últimas NFs registradas")
    if not nfs.empty:
        df_show = nfs.sort_values("criado_em", ascending=False).head(5)[
            ["id", "cliente", "descricao", "valor", "mes_competencia",
             "mes_faturamento", "status"]
        ].copy()
        df_show["valor"] = df_show["valor"].apply(brl)
        df_show.columns = ["ID", "Cliente", "Descrição", "Valor",
                           "Competência", "Faturamento", "Status"]
        st.dataframe(df_show, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma NF registrada ainda.")
