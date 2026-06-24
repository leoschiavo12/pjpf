import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import date, datetime
import json

# ──────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Gestão PJ",
    page_icon="🧾",
    layout="wide",
)

# ──────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────
SHEET_ID = "1ZP8Qa7pfptri7NByWEcJHPXp1xA4fD3r_Pk7BHH17cA"  # <- substituir pelo ID real
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
FIES_FIXO = 635.29  # R$ destinados ao BB para FIES

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}

# ──────────────────────────────────────────────
# CONEXÃO COM GOOGLE SHEETS
# ──────────────────────────────────────────────
@st.cache_resource
def get_client():
    secret = st.secrets["gcp_service_account"]
    # Streamlit pode entregar como dict (formato TOML) ou string JSON
    if isinstance(secret, str):
        creds_dict = json.loads(secret)
    else:
        creds_dict = dict(secret)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

def get_sheet(tab_name: str):
    client = get_client()
    sh = client.open_by_key(SHEET_ID)
    try:
        return sh.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=tab_name, rows=1000, cols=20)
        _init_headers(ws, tab_name)
        return ws

def _init_headers(ws, tab_name: str):
    headers = {
        "notas_fiscais": [
            "id", "cliente", "descricao", "valor",
            "mes_emissao", "ano_emissao",
            "mes_faturamento", "ano_faturamento",
            "mesmo_mes", "data_registro"
        ],
        "taxa_prefeitura": ["ano", "valor", "data_registro"],
        "configuracoes": ["chave", "valor"],
    }
    if tab_name in headers:
        ws.append_row(headers[tab_name])
        if tab_name == "configuracoes":
            defaults = [
                ["aliquota_das", "5.0"],
                ["aliquota_darf", "11.0"],
                ["contador", "500.00"],
                ["prev_privada", "300.00"],
                ["pro_labore", "1500.00"],
            ]
            for row in defaults:
                ws.append_row(row)

# ──────────────────────────────────────────────
# LEITURA DE DADOS
# ──────────────────────────────────────────────
@st.cache_data(ttl=60)
def ler_configuracoes() -> dict:
    ws = get_sheet("configuracoes")
    rows = ws.get_all_values()
    cfg = {}
    for row in rows[1:]:
        if len(row) >= 2 and row[0]:
            try:
                cfg[row[0]] = float(row[1])
            except ValueError:
                cfg[row[0]] = row[1]
    return cfg

@st.cache_data(ttl=60)
def ler_notas() -> pd.DataFrame:
    ws = get_sheet("notas_fiscais")
    data = ws.get_all_records()
    if not data:
        return pd.DataFrame(columns=[
            "id", "cliente", "descricao", "valor",
            "mes_emissao", "ano_emissao",
            "mes_faturamento", "ano_faturamento",
            "mesmo_mes", "data_registro"
        ])
    df = pd.DataFrame(data)
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0)
    df["mes_emissao"] = pd.to_numeric(df["mes_emissao"], errors="coerce").fillna(0).astype(int)
    df["ano_emissao"] = pd.to_numeric(df["ano_emissao"], errors="coerce").fillna(0).astype(int)
    df["mes_faturamento"] = pd.to_numeric(df["mes_faturamento"], errors="coerce").fillna(0).astype(int)
    df["ano_faturamento"] = pd.to_numeric(df["ano_faturamento"], errors="coerce").fillna(0).astype(int)
    return df

@st.cache_data(ttl=60)
def ler_taxas_prefeitura() -> pd.DataFrame:
    ws = get_sheet("taxa_prefeitura")
    data = ws.get_all_records()
    if not data:
        return pd.DataFrame(columns=["ano", "valor", "data_registro"])
    df = pd.DataFrame(data)
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0)
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").fillna(0).astype(int)
    return df

def _novo_id(df: pd.DataFrame) -> int:
    if df.empty or "id" not in df.columns:
        return 1
    ids = pd.to_numeric(df["id"], errors="coerce").dropna()
    return int(ids.max()) + 1 if not ids.empty else 1

# ──────────────────────────────────────────────
# ESCRITA DE DADOS
# ──────────────────────────────────────────────
def salvar_nota(cliente, descricao, valor, mes_em, ano_em, mes_fat, ano_fat, mesmo_mes):
    df = ler_notas()
    novo_id = _novo_id(df)
    ws = get_sheet("notas_fiscais")
    ws.append_row([
        novo_id, cliente, descricao, str(valor).replace(".", ","),
        mes_em, ano_em, mes_fat, ano_fat,
        "Sim" if mesmo_mes else "Não",
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ])
    ler_notas.clear()

def deletar_nota(nota_id: int):
    ws = get_sheet("notas_fiscais")
    rows = ws.get_all_values()
    for i, row in enumerate(rows):
        if row and str(row[0]) == str(nota_id):
            ws.delete_rows(i + 1)
            break
    ler_notas.clear()

def salvar_taxa_prefeitura(ano: int, valor: float):
    ws = get_sheet("taxa_prefeitura")
    ws.append_row([ano, str(valor).replace(".", ","), datetime.now().strftime("%Y-%m-%d")])
    ler_taxas_prefeitura.clear()

def salvar_configuracoes(cfg_dict: dict):
    ws = get_sheet("configuracoes")
    ws.clear()
    ws.append_row(["chave", "valor"])
    for k, v in cfg_dict.items():
        ws.append_row([k, str(v)])
    ler_configuracoes.clear()

# ──────────────────────────────────────────────
# CÁLCULOS MENSAIS
# ──────────────────────────────────────────────
def calcular_mes(mes: int, ano: int, df_nf: pd.DataFrame,
                 df_taxa: pd.DataFrame, cfg: dict) -> dict:
    # Receita: NFs com faturamento neste mês/ano
    nfs_mes = df_nf[
        (df_nf["mes_faturamento"] == mes) & (df_nf["ano_faturamento"] == ano)
    ]
    receita_bruta = nfs_mes["valor"].sum()

    # Variáveis de config
    aliq_das = cfg.get("aliquota_das", 0) / 100
    aliq_darf = cfg.get("aliquota_darf", 0) / 100
    contador = cfg.get("contador", 0)
    prev_privada = cfg.get("prev_privada", 0)
    pro_labore = cfg.get("pro_labore", 0)

    # Custos
    custo_das = receita_bruta * aliq_das
    custo_darf = pro_labore * aliq_darf
    pro_labore_liquido = pro_labore * (1 - aliq_darf)  # custo PJ, receita PF

    taxa_prefeitura = 0.0
    if mes == 2:  # Fevereiro
        taxa_row = df_taxa[df_taxa["ano"] == ano]
        if not taxa_row.empty:
            taxa_prefeitura = taxa_row["valor"].iloc[-1]

    total_custos = (
        custo_das
        + contador
        + prev_privada
        + custo_darf
        + pro_labore_liquido
        + taxa_prefeitura
    )

    resultado_liquido = receita_bruta - total_custos

    # Distribuição
    fies_bb = min(FIES_FIXO, max(resultado_liquido, 0))
    distribuicao_nubank = max(resultado_liquido - fies_bb, 0)
    repasse_pf_total = pro_labore_liquido + fies_bb + distribuicao_nubank

    return {
        "receita_bruta": receita_bruta,
        "custo_das": custo_das,
        "contador": contador,
        "prev_privada": prev_privada,
        "custo_darf": custo_darf,
        "pro_labore_liquido": pro_labore_liquido,
        "taxa_prefeitura": taxa_prefeitura,
        "total_custos": total_custos,
        "resultado_liquido": resultado_liquido,
        "fies_bb": fies_bb,
        "distribuicao_nubank": distribuicao_nubank,
        "repasse_pf_total": repasse_pf_total,
        "nfs_mes": nfs_mes,
        "aliq_das": aliq_das,
        "aliq_darf": aliq_darf,
        "pro_labore": pro_labore,
    }

# ──────────────────────────────────────────────
# FORMATAÇÃO
# ──────────────────────────────────────────────
def fmt_brl(v: float) -> str:
    return f"R$ {v:_.2f}".replace(".", ",").replace("_", ".")

def fmt_pct(v: float) -> str:
    return f"{v:.1f}%".replace(".", ",")

def card(col, label: str, valor: str, delta: str = None):
    col.metric(label=label, value=valor, delta=delta)

# ──────────────────────────────────────────────
# PÁGINAS
# ──────────────────────────────────────────────

def pagina_dashboard():
    st.header("Dashboard Mensal")

    cfg = ler_configuracoes()
    df_nf = ler_notas()
    df_taxa = ler_taxas_prefeitura()

    hoje = date.today()
    col_mes, col_ano = st.columns([1, 1])
    with col_mes:
        mes_sel = st.selectbox(
            "Mês",
            options=list(MESES_PT.keys()),
            format_func=lambda m: MESES_PT[m],
            index=hoje.month - 1,
        )
    with col_ano:
        ano_sel = st.selectbox("Ano", options=list(range(2024, hoje.year + 2)), index=list(range(2024, hoje.year + 2)).index(hoje.year))

    r = calcular_mes(mes_sel, ano_sel, df_nf, df_taxa, cfg)

    st.divider()
    st.subheader(f"Resultado — {MESES_PT[mes_sel]}/{ano_sel}")

    # Linha 1: receita e resultado
    c1, c2, c3 = st.columns(3)
    card(c1, "💰 Receita Bruta", fmt_brl(r["receita_bruta"]))
    card(c2, "📉 Total de Custos", fmt_brl(r["total_custos"]))
    card(c3, "✅ Resultado Líquido", fmt_brl(r["resultado_liquido"]))

    st.divider()

    # Linha 2: repasses PF
    st.subheader("Repasses para PF")
    c4, c5, c6 = st.columns(3)
    card(c4, "🏦 Pró-labore Líq. (Nubank)", fmt_brl(r["pro_labore_liquido"]))
    card(c5, "🏛️ FIES (BB)", fmt_brl(r["fies_bb"]))
    card(c6, "💸 Distrib. Lucros (Nubank)", fmt_brl(r["distribuicao_nubank"]))

    st.divider()

    # DRE simplificado
    st.subheader("Detalhamento de Custos")
    col_dre, col_nfs = st.columns([1, 1])

    with col_dre:
        dados_dre = {
            "Item": [
                "Receita Bruta",
                f"(-) DAS ({fmt_pct(r['aliq_das']*100)})",
                "(-) Contador",
                "(-) Prev. Privada",
                f"(-) DARF Pró-labore ({fmt_pct(r['aliq_darf']*100)})",
                "(-) Pró-labore Líquido",
            ],
            "Valor": [
                fmt_brl(r["receita_bruta"]),
                fmt_brl(-r["custo_das"]),
                fmt_brl(-r["contador"]),
                fmt_brl(-r["prev_privada"]),
                fmt_brl(-r["custo_darf"]),
                fmt_brl(-r["pro_labore_liquido"]),
            ]
        }
        if r["taxa_prefeitura"] > 0:
            dados_dre["Item"].append("(-) Taxa Prefeitura")
            dados_dre["Valor"].append(fmt_brl(-r["taxa_prefeitura"]))

        dados_dre["Item"].append("= Resultado Líquido")
        dados_dre["Valor"].append(fmt_brl(r["resultado_liquido"]))

        df_dre = pd.DataFrame(dados_dre)
        st.dataframe(df_dre, use_container_width=True, hide_index=True)

    with col_nfs:
        st.markdown(f"**NFs faturadas em {MESES_PT[mes_sel]}/{ano_sel}**")
        if r["nfs_mes"].empty:
            st.info("Nenhuma NF faturada neste mês.")
        else:
            df_show = r["nfs_mes"][["cliente", "descricao", "valor"]].copy()
            df_show["valor"] = df_show["valor"].apply(fmt_brl)
            st.dataframe(df_show, use_container_width=True, hide_index=True)


def pagina_notas():
    st.header("Notas Fiscais")

    tab_nova, tab_lista = st.tabs(["➕ Nova NF", "📋 Listagem"])

    with tab_nova:
        st.subheader("Registrar Nota Fiscal")
        hoje = date.today()

        with st.form("form_nf", clear_on_submit=True):
            cliente = st.text_input("Cliente / Tomador")
            descricao = st.text_input("Descrição do serviço")
            valor = st.number_input("Valor da NF (R$)", min_value=0.01, step=0.01, format="%.2f")

            st.markdown("**Mês de emissão**")
            c1, c2 = st.columns(2)
            mes_em = c1.selectbox("Mês", list(MESES_PT.keys()), format_func=lambda m: MESES_PT[m],
                                  index=hoje.month - 1, key="mes_em")
            ano_em = c2.selectbox("Ano", list(range(2024, hoje.year + 2)),
                                  index=list(range(2024, hoje.year + 2)).index(hoje.year), key="ano_em")

            mesmo_mes = st.checkbox("Emitida e faturada no mesmo mês")

            if mesmo_mes:
                mes_fat, ano_fat = mes_em, ano_em
                st.info(f"Faturamento: {MESES_PT[mes_em]}/{ano_em}")
            else:
                st.markdown("**Mês de faturamento**")
                c3, c4 = st.columns(2)
                # Sugestão: mês seguinte
                prox_mes = mes_em % 12 + 1
                prox_ano = ano_em + 1 if mes_em == 12 else ano_em
                mes_fat = c3.selectbox("Mês", list(MESES_PT.keys()), format_func=lambda m: MESES_PT[m],
                                       index=prox_mes - 1, key="mes_fat")
                ano_fat = c4.selectbox("Ano", list(range(2024, hoje.year + 2)),
                                       index=list(range(2024, hoje.year + 2)).index(prox_ano)
                                       if prox_ano <= hoje.year + 1 else 0, key="ano_fat")

            submitted = st.form_submit_button("💾 Salvar NF")
            if submitted:
                if not cliente:
                    st.error("Informe o cliente.")
                elif valor <= 0:
                    st.error("Valor deve ser maior que zero.")
                else:
                    salvar_nota(cliente, descricao, valor, mes_em, ano_em, mes_fat, ano_fat, mesmo_mes)
                    st.success(f"NF de {fmt_brl(valor)} para {cliente} salva com sucesso!")

    with tab_lista:
        st.subheader("Todas as Notas Fiscais")
        df_nf = ler_notas()

        if df_nf.empty:
            st.info("Nenhuma NF registrada ainda.")
            return

        # Filtros
        cf1, cf2 = st.columns(2)
        anos_disp = sorted(df_nf["ano_faturamento"].unique(), reverse=True)
        ano_filtro = cf1.selectbox("Filtrar por ano de faturamento", ["Todos"] + [str(a) for a in anos_disp])
        mes_filtro = cf2.selectbox("Filtrar por mês de faturamento", ["Todos"] + [MESES_PT[m] for m in range(1, 13)])

        df_view = df_nf.copy()
        if ano_filtro != "Todos":
            df_view = df_view[df_view["ano_faturamento"] == int(ano_filtro)]
        if mes_filtro != "Todos":
            num_mes = [k for k, v in MESES_PT.items() if v == mes_filtro][0]
            df_view = df_view[df_view["mes_faturamento"] == num_mes]

        # Formatação para exibição
        df_show = df_view.copy()
        df_show["emissão"] = df_show.apply(
            lambda r: f"{MESES_PT.get(int(r['mes_emissao']), '?')}/{int(r['ano_emissao'])}", axis=1)
        df_show["faturamento"] = df_show.apply(
            lambda r: f"{MESES_PT.get(int(r['mes_faturamento']), '?')}/{int(r['ano_faturamento'])}", axis=1)
        df_show["valor_fmt"] = df_show["valor"].apply(fmt_brl)

        cols_show = ["id", "cliente", "descricao", "valor_fmt", "emissão", "faturamento", "mesmo_mes"]
        df_show = df_show[cols_show].rename(columns={
            "id": "ID", "cliente": "Cliente", "descricao": "Descrição",
            "valor_fmt": "Valor", "mesmo_mes": "Mesmo Mês"
        })

        st.dataframe(df_show, use_container_width=True, hide_index=True)

        total = df_view["valor"].sum()
        st.markdown(f"**Total filtrado: {fmt_brl(total)}**")

        # Deletar
        with st.expander("🗑️ Deletar NF"):
            ids_disp = df_view["id"].tolist()
            if ids_disp:
                id_del = st.selectbox("Selecionar NF pelo ID", ids_disp)
                nf_sel = df_view[df_view["id"] == id_del].iloc[0]
                st.write(f"**{nf_sel['cliente']}** — {fmt_brl(nf_sel['valor'])} — faturamento: "
                         f"{MESES_PT.get(int(nf_sel['mes_faturamento']), '?')}/{int(nf_sel['ano_faturamento'])}")
                if st.button("Confirmar exclusão", type="primary"):
                    deletar_nota(id_del)
                    st.success("NF deletada.")
                    st.rerun()


def pagina_relatorio():
    st.header("Relatório Mensal")

    cfg = ler_configuracoes()
    df_nf = ler_notas()
    df_taxa = ler_taxas_prefeitura()

    if df_nf.empty:
        st.info("Nenhuma NF registrada ainda.")
        return

    # Montar todos os meses/anos com dados
    combos = df_nf[["ano_faturamento", "mes_faturamento"]].drop_duplicates()
    combos = combos.sort_values(["ano_faturamento", "mes_faturamento"])

    rows = []
    for _, row in combos.iterrows():
        m, a = int(row["mes_faturamento"]), int(row["ano_faturamento"])
        r = calcular_mes(m, a, df_nf, df_taxa, cfg)
        rows.append({
            "Período": f"{MESES_PT[m]}/{a}",
            "Receita Bruta": r["receita_bruta"],
            "Total Custos": r["total_custos"],
            "Resultado Líquido": r["resultado_liquido"],
            "FIES (BB)": r["fies_bb"],
            "Distrib. Nubank": r["distribuicao_nubank"],
            "Pró-labore Líq.": r["pro_labore_liquido"],
        })

    df_rel = pd.DataFrame(rows)

    # Totais
    df_totais = df_rel.copy()
    numeric_cols = [c for c in df_rel.columns if c != "Período"]
    totais = {"Período": "**TOTAL**"}
    for c in numeric_cols:
        totais[c] = df_rel[c].sum()
    df_totais = pd.concat([df_rel, pd.DataFrame([totais])], ignore_index=True)

    # Formatar para exibição
    df_fmt = df_totais.copy()
    for c in numeric_cols:
        df_fmt[c] = df_fmt[c].apply(lambda v: fmt_brl(float(v)) if v != "" else "")

    st.dataframe(df_fmt, use_container_width=True, hide_index=True)

    # Gráfico receita vs resultado
    st.subheader("Receita × Resultado Líquido")
    df_chart = df_rel.set_index("Período")[["Receita Bruta", "Resultado Líquido"]]
    st.bar_chart(df_chart)


def pagina_prefeitura():
    st.header("Taxa de Prefeitura")
    df_taxa = ler_taxas_prefeitura()

    col_form, col_lista = st.columns([1, 1])

    with col_form:
        st.subheader("Registrar Taxa")
        with st.form("form_taxa"):
            ano_taxa = st.number_input("Ano", min_value=2020, max_value=2040,
                                       value=date.today().year, step=1)
            valor_taxa = st.number_input("Valor (R$)", min_value=0.01, step=0.01, format="%.2f")
            if st.form_submit_button("💾 Salvar"):
                salvar_taxa_prefeitura(int(ano_taxa), valor_taxa)
                st.success(f"Taxa de {fmt_brl(valor_taxa)} para {int(ano_taxa)} salva.")
                st.rerun()

    with col_lista:
        st.subheader("Histórico")
        if df_taxa.empty:
            st.info("Nenhuma taxa registrada.")
        else:
            df_show = df_taxa.copy()
            df_show["valor_fmt"] = df_show["valor"].apply(fmt_brl)
            st.dataframe(df_show[["ano", "valor_fmt", "data_registro"]].rename(columns={
                "ano": "Ano", "valor_fmt": "Valor", "data_registro": "Registro"
            }), use_container_width=True, hide_index=True)


def pagina_configuracoes():
    st.header("Configurações")
    cfg = ler_configuracoes()

    st.subheader("Variáveis Base")

    with st.form("form_cfg"):
        aliq_das = st.number_input(
            "Alíquota DAS (%)", min_value=0.0, max_value=100.0, step=0.1, format="%.1f",
            value=float(cfg.get("aliquota_das", 5.0)),
            help="Aplicada sobre a receita bruta (NFs faturadas no mês)"
        )
        aliq_darf = st.number_input(
            "Alíquota DARF — Pró-labore (%)", min_value=0.0, max_value=100.0, step=0.1, format="%.1f",
            value=float(cfg.get("aliquota_darf", 11.0)),
            help="INSS sobre o pró-labore"
        )
        contador = st.number_input(
            "Honorário Contador (R$)", min_value=0.0, step=10.0, format="%.2f",
            value=float(cfg.get("contador", 500.0))
        )
        prev_privada = st.number_input(
            "Previdência Privada (R$)", min_value=0.0, step=10.0, format="%.2f",
            value=float(cfg.get("prev_privada", 300.0))
        )
        pro_labore = st.number_input(
            "Pró-labore Bruto (R$)", min_value=0.0, step=50.0, format="%.2f",
            value=float(cfg.get("pro_labore", 1500.0))
        )

        if st.form_submit_button("💾 Salvar Configurações"):
            salvar_configuracoes({
                "aliquota_das": aliq_das,
                "aliquota_darf": aliq_darf,
                "contador": contador,
                "prev_privada": prev_privada,
                "pro_labore": pro_labore,
            })
            st.success("Configurações salvas!")

    st.divider()
    st.subheader("Resumo dos Parâmetros Atuais")
    cfg_atual = ler_configuracoes()

    pro_labore_val = cfg_atual.get("pro_labore", 0)
    aliq_darf_val = cfg_atual.get("aliquota_darf", 0) / 100

    st.markdown(f"""
| Parâmetro | Valor |
|---|---|
| Alíquota DAS | {fmt_pct(cfg_atual.get('aliquota_das', 0))} |
| Alíquota DARF | {fmt_pct(cfg_atual.get('aliquota_darf', 0))} |
| Contador | {fmt_brl(cfg_atual.get('contador', 0))} |
| Previdência Privada | {fmt_brl(cfg_atual.get('prev_privada', 0))} |
| Pró-labore Bruto | {fmt_brl(pro_labore_val)} |
| DARF (custo PJ) | {fmt_brl(pro_labore_val * aliq_darf_val)} |
| Pró-labore Líquido (→ Nubank) | {fmt_brl(pro_labore_val * (1 - aliq_darf_val))} |
| FIES fixo (→ BB) | {fmt_brl(FIES_FIXO)} |
""")

# ──────────────────────────────────────────────
# NAVEGAÇÃO
# ──────────────────────────────────────────────
def main():
    st.sidebar.title("🧾 Gestão PJ")
    paginas = {
        "📊 Dashboard": pagina_dashboard,
        "🗒️ Notas Fiscais": pagina_notas,
        "📈 Relatório": pagina_relatorio,
        "🏛️ Taxa Prefeitura": pagina_prefeitura,
        "⚙️ Configurações": pagina_configuracoes,
    }
    escolha = st.sidebar.radio("Navegação", list(paginas.keys()))
    paginas[escolha]()

if __name__ == "__main__":
    main()
