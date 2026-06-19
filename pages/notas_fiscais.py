import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sheets import load_nfs, add_nf, update_nf_status, delete_nf
from utils.formatters import brl, mes_label


def render():
    st.title("📄 Notas Fiscais")

    tab_lista, tab_nova = st.tabs(["📋 Listagem", "➕ Registrar NF"])

    # ── Listagem ──────────────────────────────────────────────────────────────
    with tab_lista:
        nfs = load_nfs()

        if nfs.empty:
            st.info("Nenhuma NF registrada. Use a aba 'Registrar NF' para começar.")
        else:
            # Filtros
            col1, col2, col3 = st.columns(3)
            meses_disp = sorted(nfs["mes_competencia"].unique(), reverse=True)
            mes_filtro = col1.selectbox("Competência", ["Todos"] + list(meses_disp))
            status_filtro = col2.selectbox("Status", ["Todos", "pendente", "faturado", "cancelado"])
            cliente_filtro = col3.text_input("Cliente (busca)")

            df = nfs.copy()
            if mes_filtro != "Todos":
                df = df[df["mes_competencia"] == mes_filtro]
            if status_filtro != "Todos":
                df = df[df["status"] == status_filtro]
            if cliente_filtro:
                df = df[df["cliente"].str.contains(cliente_filtro, case=False, na=False)]

            # Totais
            col1, col2, col3 = st.columns(3)
            col1.metric("Total filtrado", brl(df["valor"].sum()))
            col2.metric("Faturadas", brl(df[df["status"] == "faturado"]["valor"].sum()))
            col3.metric("Pendentes", brl(df[df["status"] == "pendente"]["valor"].sum()))

            st.divider()

            # Tabela com ações
            for _, row in df.sort_values("mes_competencia", ascending=False).iterrows():
                with st.container():
                    c1, c2, c3, c4, c5 = st.columns([2, 3, 1.5, 1.5, 2])
                    c1.write(f"**{row['cliente']}**")
                    c2.write(row["descricao"])
                    c3.write(f"**{brl(row['valor'])}**")

                    status_color = {
                        "pendente": "🟡",
                        "faturado": "🟢",
                        "cancelado": "🔴"
                    }.get(row["status"], "⚪")
                    c4.write(f"{status_color} {row['status'].capitalize()}")

                    with c5:
                        col_a, col_b = st.columns(2)
                        if row["status"] == "pendente":
                            if col_a.button("✅", key=f"fat_{row['id']}",
                                            help="Marcar como faturado"):
                                update_nf_status(int(row["id"]), "faturado")
                                st.rerun()
                        if col_b.button("🗑️", key=f"del_{row['id']}",
                                        help="Excluir NF"):
                            delete_nf(int(row["id"]))
                            st.rerun()

                    st.caption(
                        f"Competência: {mes_label(row['mes_competencia'])} | "
                        f"Faturamento: {mes_label(row['mes_faturamento'])} | "
                        f"Registrado em: {row['criado_em']}"
                    )
                    st.divider()

    # ── Nova NF ───────────────────────────────────────────────────────────────
    with tab_nova:
        st.subheader("Registrar nova Nota Fiscal")

        with st.form("form_nf", clear_on_submit=True):
            col1, col2 = st.columns(2)
            cliente = col1.text_input("Cliente *", placeholder="Nome do cliente/empresa")
            valor = col2.number_input("Valor da NF (R$) *", min_value=0.01, step=100.0, format="%.2f")

            descricao = st.text_area("Descrição dos serviços", placeholder="Ex: Desenvolvimento de sistema...")

            hoje = datetime.now()
            col3, col4 = st.columns(2)

            # Mês de competência (quando o serviço foi prestado)
            mes_comp_opcoes = [
                (hoje.replace(day=1) - pd.Timedelta(days=30*i)).strftime("%Y-%m")
                for i in range(6)
            ]
            mes_competencia = col3.selectbox(
                "Mês de competência *",
                mes_comp_opcoes,
                format_func=mes_label,
                help="Mês em que o serviço foi prestado (NF emitida)"
            )

            # Mês de faturamento (quando vai receber)
            mes_fat_opcoes = [
                (hoje.replace(day=1) + pd.Timedelta(days=30*i)).strftime("%Y-%m")
                for i in range(-1, 5)
            ]
            mes_faturamento = col4.selectbox(
                "Mês de faturamento *",
                mes_fat_opcoes,
                index=1,
                format_func=mes_label,
                help="Mês em que o valor será recebido (geralmente mês seguinte)"
            )

            status = st.radio(
                "Status inicial",
                ["pendente", "faturado"],
                horizontal=True,
                help="Pendente = ainda não recebeu. Faturado = já entrou na conta."
            )

            submitted = st.form_submit_button("💾 Registrar NF", type="primary",
                                               use_container_width=True)

        if submitted:
            if not cliente:
                st.error("Informe o nome do cliente.")
            elif valor <= 0:
                st.error("Informe um valor válido.")
            else:
                add_nf(descricao, cliente, valor, mes_competencia, mes_faturamento, status)
                st.success(f"✅ NF de {brl(valor)} para **{cliente}** registrada com sucesso!")
                st.balloons()
