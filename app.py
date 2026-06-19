import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

st.set_page_config(page_title="Financeiro PJ/PF", page_icon="💼", layout="wide")

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

# ── Conexão Google Sheets ─────────────────────────────────────────────────────

SHEET_ID = st.secrets["google_sheets"]["spreadsheet_id"]

def get_svc():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=creds).spreadsheets()

def ler(tab, colunas):
    try:
        n = len(colunas)
        col_fim = chr(ord('A') + n - 1)
        res  = get_svc().values().get(spreadsheetId=SHEET_ID, range=f"{tab}!A:{col_fim}").execute()
        rows = res.get("values", [])
        if len(rows) <= 1:
            return pd.DataFrame(columns=colunas)
        padded = [(r + ['']*n)[:n] for r in rows[1:]]
        return pd.DataFrame(padded, columns=colunas)
    except Exception as e:
        st.error(f"Erro ao ler '{tab}': {e}")
        return pd.DataFrame(columns=colunas)

def append(tab, row):
    get_svc().values().append(
        spreadsheetId=SHEET_ID, range=f"{tab}!A:A",
        valueInputOption="USER_ENTERED", body={"values": [row]}
    ).execute()

def update(tab, linha, row):
    col_fim = chr(ord('A') + len(row) - 1)
    get_svc().values().update(
        spreadsheetId=SHEET_ID, range=f"{tab}!A{linha}:{col_fim}{linha}",
        valueInputOption="USER_ENTERED", body={"values": [row]}
    ).execute()

def delete_row(tab, linha):
    svc = get_svc()
    meta = svc.get(spreadsheetId=SHEET_ID).execute()
    gid  = next((s["properties"]["sheetId"] for s in meta["sheets"]
                 if s["properties"]["title"] == tab), 0)
    svc.batchUpdate(spreadsheetId=SHEET_ID, body={"requests": [{"deleteDimension": {"range": {
        "sheetId": gid, "dimension": "ROWS",
        "startIndex": linha - 1, "endIndex": linha
    }}}]}).execute()

# ── Helpers ───────────────────────────────────────────────────────────────────

def num(s):
    try:
        if s is None or str(s).strip() in ('', 'nan', 'None'): return 0.0
        s = str(s).strip().replace('R$','').replace(' ','')
        if ',' in s and '.' in s:
            s = s.replace('.','').replace(',','.') if s.rindex(',') > s.rindex('.') else s.replace(',','')
        elif ',' in s:
            s = s.replace(',','.')
        return float(s)
    except:
        return 0.0

def fmt(v):
    return str(round(float(v), 2)).replace('.', ',')

def brl(v):
    s = f"{float(v):,.2f}".replace(',','X').replace('.',',').replace('X','.')
    return f"R$ {s}"

def mes_label(m):
    meses = {"01":"Jan","02":"Fev","03":"Mar","04":"Abr","05":"Mai","06":"Jun",
             "07":"Jul","08":"Ago","09":"Set","10":"Out","11":"Nov","12":"Dez"}
    try:
        p = m.split("-"); return f"{meses[p[1]]}/{p[0]}"
    except: return m

# ── Leitura das abas ──────────────────────────────────────────────────────────

def load_config():
    df = ler("config", ["chave","valor"])
    return {r["chave"]: r["valor"] for _, r in df.iterrows()}

def save_config(key, value):
    df = ler("config", ["chave","valor"])
    for i, r in df.iterrows():
        if r["chave"] == key:
            update("config", i+2, [key, fmt(value) if isinstance(value, float) else str(value)])
            return
    append("config", [key, fmt(value) if isinstance(value, float) else str(value)])

def load_nfs():
    cols = ["id","cliente","descricao","valor","mes_competencia","mes_faturamento","status","criado_em"]
    df = ler("nfs", cols)
    if df.empty: return df
    df["valor"] = df["valor"].apply(num)
    df["id"]    = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)
    return df

def add_nf(cliente, descricao, valor, mes_comp, mes_fat, status):
    df = load_nfs()
    nid = int(df["id"].max()) + 1 if not df.empty else 1
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    append("nfs", [nid, cliente, descricao, fmt(valor), mes_comp, mes_fat, status, now])

def update_nf_status(nf_id, new_status):
    df = load_nfs()
    for i, r in df.iterrows():
        if int(r["id"]) == nf_id:
            update("nfs", i+2, [r["id"], r["cliente"], r["descricao"], fmt(r["valor"]),
                                  r["mes_competencia"], r["mes_faturamento"], new_status, r["criado_em"]])
            return

def delete_nf(nf_id):
    df = load_nfs()
    for i, r in df.iterrows():
        if int(r["id"]) == nf_id:
            delete_row("nfs", i+2)
            return

def load_custos_pj():
    cols = ["mes_ref","receita_faturada","simples_nacional","pro_labore_bruto",
            "darf","prev_privada","contador","total_custos","saldo_pj","distribuicao_lucros","fechado"]
    df = ler("custos_pj", cols)
    if df.empty: return df
    for c in cols[1:-1]: df[c] = df[c].apply(num)
    return df

def load_fluxo_pj():
    cols = ["mes_ref","receita","total_custos","saldo_pj","pro_labore_liq",
            "fies","distribuicao_lucros","total_nubank","investimento","casa_propria","saldo_livre"]
    df = ler("fluxo_pj", cols)
    if df.empty: return df
    for c in cols[1:]: df[c] = df[c].apply(num)
    return df

def load_fluxo_pf():
    cols = ["mes_ref","pro_labore_liquido","distribuicao_lucros","total_nubank",
            "investimento","casa_propria","saldo_livre","pct_investimento"]
    df = ler("fluxo_pf", cols)
    if df.empty: return df
    for c in cols[1:]: df[c] = df[c].apply(num)
    return df

def salvar_fechamento(mes_ref, receita, cfg):
    pro_labore   = num(cfg.get("pro_labore","0"))
    aliquota     = num(cfg.get("aliquota_simples","0,06"))
    prev_privada = num(cfg.get("prev_privada","0"))
    contador_v   = num(cfg.get("contador","0"))
    fies         = num(cfg.get("fies","635,29"))
    pro_liq      = num(cfg.get("pro_labore_liquido","1513"))
    meta_invest  = num(cfg.get("meta_investimento_pct","0,20"))
    meta_casa    = num(cfg.get("meta_casa_propria","4000"))

    simples      = receita * aliquota
    darf         = pro_labore * 0.11
    total_custos = simples + darf + prev_privada + contador_v + pro_labore
    saldo_pj     = receita - total_custos
    dist_lucros  = max(0.0, saldo_pj - fies)
    total_nubank = pro_liq + dist_lucros
    investimento = total_nubank * meta_invest
    saldo_livre  = total_nubank - investimento - meta_casa
    pct          = round(meta_invest * 100, 1)

    row_c = [mes_ref, fmt(receita), fmt(simples), fmt(pro_labore), fmt(darf),
             fmt(prev_privada), fmt(contador_v), fmt(total_custos), fmt(saldo_pj), fmt(dist_lucros), "Sim"]
    df_c = load_custos_pj()
    salvo = False
    for i, r in df_c.iterrows():
        if r["mes_ref"] == mes_ref:
            update("custos_pj", i+2, row_c); salvo = True; break
    if not salvo: append("custos_pj", row_c)

    row_pj = [mes_ref, fmt(receita), fmt(total_custos), fmt(saldo_pj), fmt(pro_liq),
              fmt(fies), fmt(dist_lucros), fmt(total_nubank), fmt(investimento), fmt(meta_casa), fmt(saldo_livre)]
    df_pj = load_fluxo_pj()
    salvo = False
    for i, r in df_pj.iterrows():
        if r["mes_ref"] == mes_ref:
            update("fluxo_pj", i+2, row_pj); salvo = True; break
    if not salvo: append("fluxo_pj", row_pj)

    row_pf = [mes_ref, fmt(pro_liq), fmt(dist_lucros), fmt(total_nubank),
              fmt(investimento), fmt(meta_casa), fmt(saldo_livre), fmt(pct)]
    df_pf = load_fluxo_pf()
    salvo = False
    for i, r in df_pf.iterrows():
        if r["mes_ref"] == mes_ref:
            update("fluxo_pf", i+2, row_pf); salvo = True; break
    if not salvo: append("fluxo_pf", row_pf)

    return saldo_pj, dist_lucros, total_nubank, investimento, saldo_livre, pro_liq

# ── Interface ─────────────────────────────────────────────────────────────────

st.markdown("## 💼 Financeiro PJ/PF")

aba_pj, aba_pf, aba_config = st.tabs(["🏢 Gestão PJ", "👤 Finanças PF", "⚙️ Configurações"])

# ══════════════════════════════════════════════════════════════════════════════
# ABA PJ
# ══════════════════════════════════════════════════════════════════════════════
with aba_pj:
    cfg = load_config()
    sub_nfs, sub_fechar, sub_historico = st.tabs(["📄 Notas Fiscais", "📌 Fechar mês", "📋 Histórico"])

    # ── Notas Fiscais ─────────────────────────────────────────────────────────
    with sub_nfs:
        nfs = load_nfs()

        with st.expander("➕ Registrar nova NF", expanded=nfs.empty):
            hoje = datetime.now()
            col1, col2 = st.columns(2)
            cliente  = col1.text_input("Cliente *")
            valor_nf = col2.number_input("Valor (R$) *", min_value=0.01, step=100.0, format="%.2f")
            descricao = st.text_input("Descrição")

            meses_c  = [(hoje.replace(day=1) - pd.Timedelta(days=30*i)).strftime("%Y-%m") for i in range(6)]
            meses_f  = [(hoje.replace(day=1) + pd.Timedelta(days=30*i)).strftime("%Y-%m") for i in range(-1,5)]
            col3, col4 = st.columns(2)
            mes_comp = col3.selectbox("Mês competência", meses_c, format_func=mes_label)
            mes_fat  = col4.selectbox("Mês faturamento", meses_f, index=1, format_func=mes_label)
            status_nf = st.radio("Status", ["pendente","faturado"], horizontal=True)

            if st.button("💾 Salvar NF", type="primary"):
                if not cliente:
                    st.error("Informe o cliente.")
                else:
                    add_nf(cliente, descricao, valor_nf, mes_comp, mes_fat, status_nf)
                    st.success(f"NF de {brl(valor_nf)} para {cliente} registrada!")
                    st.rerun()

        if nfs.empty:
            st.info("Nenhuma NF registrada ainda.")
        else:
            col1, col2 = st.columns(2)
            meses_disp = sorted(nfs["mes_competencia"].unique(), reverse=True)
            mes_f2   = col1.selectbox("Filtrar competência", ["Todos"] + list(meses_disp))
            status_f = col2.selectbox("Filtrar status", ["Todos","pendente","faturado","cancelado"])

            df_nf = nfs.copy()
            if mes_f2 != "Todos":   df_nf = df_nf[df_nf["mes_competencia"] == mes_f2]
            if status_f != "Todos": df_nf = df_nf[df_nf["status"] == status_f]

            col1, col2, col3 = st.columns(3)
            col1.metric("Total", brl(df_nf["valor"].sum()))
            col2.metric("Faturadas", brl(df_nf[df_nf["status"]=="faturado"]["valor"].sum()))
            col3.metric("Pendentes", brl(df_nf[df_nf["status"]=="pendente"]["valor"].sum()))
            st.divider()

            for _, row in df_nf.sort_values("mes_competencia", ascending=False).iterrows():
                c1,c2,c3,c4,c5 = st.columns([2,3,1.5,1.5,1])
                c1.write(f"**{row['cliente']}**")
                c2.write(row["descricao"] or "—")
                c3.write(f"**{brl(row['valor'])}**")
                icone = {"pendente":"🟡","faturado":"🟢","cancelado":"🔴"}.get(row["status"],"⚪")
                c4.write(f"{icone} {row['status']}")
                with c5:
                    if row["status"] == "pendente":
                        if st.button("✅", key=f"fat_{row['id']}", help="Marcar faturado"):
                            update_nf_status(int(row["id"]), "faturado")
                            st.rerun()
                    if st.button("🗑️", key=f"del_{row['id']}", help="Excluir"):
                        delete_nf(int(row["id"]))
                        st.rerun()
                st.caption(f"Competência: {mes_label(row['mes_competencia'])} | Faturamento: {mes_label(row['mes_faturamento'])}")
                st.divider()

    # ── Fechar mês ────────────────────────────────────────────────────────────
    with sub_fechar:
        hoje = datetime.now()
        meses_opcoes = [(hoje.replace(day=1) - pd.Timedelta(days=30*i)).strftime("%Y-%m") for i in range(12)]
        mes_ref = st.selectbox("Mês de referência", meses_opcoes, format_func=mes_label)

        nfs2 = load_nfs()
        nfs_fat = nfs2[(nfs2["mes_faturamento"]==mes_ref) & (nfs2["status"]=="faturado")] if not nfs2.empty else pd.DataFrame()
        receita_auto = float(nfs_fat["valor"].sum()) if not nfs_fat.empty else 0.0
        st.metric(f"NFs faturadas em {mes_label(mes_ref)}", brl(receita_auto))
        receita = st.number_input("Receita do mês (R$)", value=receita_auto, min_value=0.0, step=100.0, format="%.2f")

        pro_labore   = num(cfg.get("pro_labore","0"))
        aliquota     = num(cfg.get("aliquota_simples","0,06"))
        prev_privada = num(cfg.get("prev_privada","0"))
        contador_v   = num(cfg.get("contador","0"))
        fies         = num(cfg.get("fies","635,29"))
        pro_liq      = num(cfg.get("pro_labore_liquido","1513"))
        meta_invest  = num(cfg.get("meta_investimento_pct","0,20"))
        meta_casa    = num(cfg.get("meta_casa_propria","4000"))

        simples      = receita * aliquota
        darf         = pro_labore * 0.11
        total_custos = simples + darf + prev_privada + contador_v + pro_labore
        saldo_pj     = receita - total_custos
        dist_lucros  = max(0.0, saldo_pj - fies)
        total_nubank = pro_liq + dist_lucros
        investimento = total_nubank * meta_invest
        saldo_livre  = total_nubank - investimento - meta_casa

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**PJ**")
            st.dataframe(pd.DataFrame({
                "Item":  ["Receita","Simples","DARF","Prev. Privada","Contador","Pro-labore","Saldo PJ","FIES","Dist. lucros"],
                "Valor": [brl(receita), f"- {brl(simples)}", f"- {brl(darf)}", f"- {brl(prev_privada)}",
                          f"- {brl(contador_v)}", f"- {brl(pro_labore)}", brl(saldo_pj), f"- {brl(fies)}", brl(dist_lucros)]
            }), hide_index=True, use_container_width=True)
        with col2:
            st.markdown("**PF — Nubank**")
            st.dataframe(pd.DataFrame({
                "Item":  ["Pro-labore líq.","Dist. lucros","Total Nubank",f"Investimento ({meta_invest*100:.0f}%)","Casa própria","Saldo livre"],
                "Valor": [brl(pro_liq), brl(dist_lucros), brl(total_nubank), f"- {brl(investimento)}", f"- {brl(meta_casa)}", brl(saldo_livre)]
            }), hide_index=True, use_container_width=True)

        if st.button("💾 Confirmar fechamento", type="primary", use_container_width=True):
            salvar_fechamento(mes_ref, receita, cfg)
            st.success(f"✅ Fechamento de {mes_label(mes_ref)} salvo!")
            st.balloons()

    # ── Histórico ─────────────────────────────────────────────────────────────
    with sub_historico:
        custos = load_custos_pj()
        if custos.empty:
            st.info("Nenhum fechamento registrado ainda.")
        else:
            df_hist = custos.sort_values("mes_ref", ascending=False).copy()
            df_hist["Mês"] = df_hist["mes_ref"].apply(mes_label)
            df_show = df_hist[["Mês","receita_faturada","total_custos","saldo_pj","distribuicao_lucros"]].copy()
            df_show.columns = ["Mês","Receita","Custos","Saldo PJ","Dist. Lucros"]
            for c in ["Receita","Custos","Saldo PJ","Dist. Lucros"]:
                df_show[c] = df_show[c].apply(brl)
            st.dataframe(df_show, hide_index=True, use_container_width=True)

            if len(custos) >= 2:
                dfc = custos.sort_values("mes_ref").copy()
                dfc["mes"] = dfc["mes_ref"].apply(mes_label)
                fig = go.Figure()
                fig.add_trace(go.Bar(name="Receita", x=dfc["mes"], y=dfc["receita_faturada"], marker_color="#22C55E"))
                fig.add_trace(go.Bar(name="Custos",  x=dfc["mes"], y=dfc["total_custos"],     marker_color="#EF4444"))
                fig.add_trace(go.Scatter(name="Saldo", x=dfc["mes"], y=dfc["saldo_pj"],
                                          mode="lines+markers", line=dict(color="#3B82F6", width=2)))
                fig.update_layout(title="Receita × Custos × Saldo", barmode="group", height=350,
                                  plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ABA PF
# ══════════════════════════════════════════════════════════════════════════════
with aba_pf:
    cfg = load_config()
    fies        = num(cfg.get("fies","635,29"))
    meta_invest = num(cfg.get("meta_investimento_pct","0,20"))
    meta_casa   = num(cfg.get("meta_casa_propria","4000"))

    sub_ultimo, sub_fluxo, sub_hist_pf = st.tabs(["📌 Último mês", "📊 Fluxo de Caixa", "📋 Histórico"])

    with sub_ultimo:
        pf = load_fluxo_pf()
        if pf.empty:
            st.info("Nenhum dado ainda. Faça o fechamento de um mês na aba Gestão PJ.")
        else:
            ultimo = pf.sort_values("mes_ref", ascending=False).iloc[0]
            st.subheader(f"Distribuição PF — {mes_label(ultimo['mes_ref'])}")

            col1, col2, col3 = st.columns(3)
            col1.metric("Total no Nubank", brl(float(ultimo["total_nubank"])))
            col2.metric("Pro-labore líquido", brl(float(ultimo["pro_labore_liquido"])))
            col3.metric("Dist. de lucros", brl(float(ultimo["distribuicao_lucros"])))
            st.divider()
            col1, col2, col3 = st.columns(3)
            col1.metric(f"🏦 Investimento ({meta_invest*100:.0f}%)", brl(float(ultimo["investimento"])))
            col2.metric("🏠 Casa própria", brl(float(ultimo["casa_propria"])))
            col3.metric("💳 Saldo livre", brl(float(ultimo["saldo_livre"])))
            st.divider()

            st.markdown("**Transferências do mês**")
            st.dataframe([
                {"Destino": "Nubank PF — Pro-labore",  "Valor": brl(float(ultimo["pro_labore_liquido"])), "Conta": "Nubank"},
                {"Destino": "Banco do Brasil — FIES",   "Valor": brl(fies),                               "Conta": "BB"},
                {"Destino": "Investimento (carteira)",  "Valor": brl(float(ultimo["investimento"])),       "Conta": "Corretora"},
                {"Destino": "Plano casa própria",       "Valor": brl(float(ultimo["casa_propria"])),       "Conta": "Reserva"},
                {"Destino": "Saldo livre (cartão)",     "Valor": brl(float(ultimo["saldo_livre"])),        "Conta": "Nubank"},
            ], hide_index=True, use_container_width=True)

    with sub_fluxo:
        nfs3   = load_nfs()
        fluxo  = load_fluxo_pj()
        hoje   = datetime.now()
        mes_atual = hoje.strftime("%Y-%m")

        nfs_pend       = nfs3[nfs3["status"]=="pendente"].copy() if not nfs3.empty else pd.DataFrame()
        meses_fechados = set(fluxo["mes_ref"].tolist()) if not fluxo.empty else set()
        meses_futuros  = set(nfs_pend["mes_faturamento"].tolist()) if not nfs_pend.empty else set()
        todos = sorted(meses_fechados | meses_futuros | {
            (hoje.replace(day=1) + pd.DateOffset(months=i)).strftime("%Y-%m") for i in range(3)
        })

        rows = []
        for mes in todos:
            if mes in meses_fechados and not fluxo.empty:
                f = fluxo[fluxo["mes_ref"]==mes].iloc[0]
                rows.append({"mes": mes_label(mes), "tipo": "Realizado",
                             "receita": float(f["receita"]), "total_nubank": float(f["total_nubank"]),
                             "investimento": float(f["investimento"]), "casa_propria": float(f["casa_propria"]),
                             "saldo_livre": float(f["saldo_livre"])})
            else:
                rec = float(nfs_pend[nfs_pend["mes_faturamento"]==mes]["valor"].sum()) if not nfs_pend.empty else 0.0
                pro_labore_v = num(cfg.get("pro_labore","0"))
                aliquota_v   = num(cfg.get("aliquota_simples","0,06"))
                prev_v       = num(cfg.get("prev_privada","0"))
                cont_v       = num(cfg.get("contador","0"))
                pro_liq_v    = num(cfg.get("pro_labore_liquido","1513"))
                simples_v    = rec * aliquota_v
                darf_v       = pro_labore_v * 0.11
                total_c      = simples_v + darf_v + prev_v + cont_v + pro_labore_v
                saldo_v      = rec - total_c
                dist_v       = max(0.0, saldo_v - fies)
                tnubank      = pro_liq_v + dist_v
                invest_v     = tnubank * meta_invest
                livre_v      = tnubank - invest_v - meta_casa
                tipo         = "Projetado" if rec > 0 else "Sem NFs"
                rows.append({"mes": mes_label(mes), "tipo": tipo,
                             "receita": rec, "total_nubank": tnubank if rec > 0 else 0,
                             "investimento": invest_v if rec > 0 else 0,
                             "casa_propria": meta_casa if rec > 0 else 0,
                             "saldo_livre": livre_v if rec > 0 else 0})

        if rows:
            dft = pd.DataFrame(rows)
            real = dft[dft["tipo"]=="Realizado"]
            proj = dft[dft["tipo"]=="Projetado"]
            col1, col2, col3 = st.columns(3)
            col1.metric("Receita realizada", brl(real["receita"].sum()) if not real.empty else brl(0))
            col2.metric("Receita projetada", brl(proj["receita"].sum()) if not proj.empty else brl(0))
            col3.metric("⚠️ Meses sem NFs", len(dft[dft["tipo"]=="Sem NFs"]))

            fig = go.Figure()
            for tipo, cor in [("Realizado","#22C55E"),("Projetado","#3B82F6"),("Sem NFs","#EF4444")]:
                sub = dft[dft["tipo"]==tipo]
                if not sub.empty:
                    fig.add_trace(go.Bar(name=tipo, x=sub["mes"], y=sub["receita"], marker_color=cor))
            fig.update_layout(title="Receita — Realizado vs Projetado", barmode="group", height=350,
                              plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

            dft_com = dft[dft["total_nubank"] > 0]
            if not dft_com.empty:
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(name="Investimento", x=dft_com["mes"], y=dft_com["investimento"], marker_color="#22C55E"))
                fig2.add_trace(go.Bar(name="Casa Própria", x=dft_com["mes"], y=dft_com["casa_propria"], marker_color="#3B82F6"))
                fig2.add_trace(go.Bar(name="Saldo Livre",  x=dft_com["mes"], y=dft_com["saldo_livre"],  marker_color="#F59E0B"))
                fig2.update_layout(title="Destinos PF por mês", barmode="stack", height=350,
                                   plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig2, use_container_width=True)

            if not nfs_pend.empty:
                st.divider()
                st.markdown("**🟡 NFs pendentes de faturamento**")
                dp = nfs_pend[["cliente","descricao","valor","mes_faturamento"]].copy()
                dp["valor"] = dp["valor"].apply(brl)
                dp.columns = ["Cliente","Descrição","Valor","Faturamento previsto"]
                st.dataframe(dp, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhum dado para exibir.")

    with sub_hist_pf:
        pf2 = load_fluxo_pf()
        if pf2.empty:
            st.info("Nenhum dado ainda.")
        else:
            df_pf = pf2.sort_values("mes_ref", ascending=False).copy()
            df_pf["Mês"] = df_pf["mes_ref"].apply(mes_label)
            rename = {"pro_labore_liquido":"Pro-labore","distribuicao_lucros":"Dist. Lucros",
                      "total_nubank":"Total Nubank","investimento":"Investimento",
                      "casa_propria":"Casa Própria","saldo_livre":"Saldo Livre","pct_investimento":"% Invest."}
            df_pf2 = df_pf[["Mês"]+list(rename.keys())].rename(columns=rename)
            for c in list(rename.values())[:-1]: df_pf2[c] = df_pf2[c].apply(brl)
            df_pf2["% Invest."] = df_pf2["% Invest."].apply(lambda x: f"{x:.1f}%")
            st.dataframe(df_pf2, hide_index=True, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ABA CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
with aba_config:
    cfg2 = load_config()
    st.caption("Parâmetros que mudam anualmente. Salve aqui e tudo é recalculado automaticamente.")

    col1, col2 = st.columns(2)
    pro_labore_c = col1.number_input("Pro-labore bruto (R$)",    value=num(cfg2.get("pro_labore","0")),              min_value=0.0, step=100.0, format="%.2f")
    pro_liq_c    = col2.number_input("Pro-labore líquido (R$)",  value=num(cfg2.get("pro_labore_liquido","1513")),   min_value=0.0, step=50.0,  format="%.2f", help="Valor que entra no Nubank")
    col3, col4   = st.columns(2)
    prev_c       = col3.number_input("Previdência privada (R$/mês)", value=num(cfg2.get("prev_privada","0")),        min_value=0.0, step=50.0,  format="%.2f")
    contador_c   = col4.number_input("Contador (R$/mês)",            value=num(cfg2.get("contador","0")),            min_value=0.0, step=50.0,  format="%.2f")
    aliquota_c   = st.slider("Alíquota Simples Nacional (%)", min_value=1.0, max_value=20.0,
                              value=num(cfg2.get("aliquota_simples","0,06"))*100, step=0.1, format="%.1f%%")
    st.divider()
    col5, col6   = st.columns(2)
    fies_c       = col5.number_input("FIES — parcela mensal (R$)", value=num(cfg2.get("fies","635,29")),            min_value=0.0, step=10.0,  format="%.2f", help="Banco do Brasil, vence dia 10")
    meta_casa_c  = col6.number_input("Plano casa própria (R$/mês)", value=num(cfg2.get("meta_casa_propria","4000")), min_value=0.0, step=100.0, format="%.2f")
    meta_inv_c   = st.slider("Meta de investimento (% da entrada Nubank)", min_value=5, max_value=60,
                              value=int(num(cfg2.get("meta_investimento_pct","0,20"))*100), step=5, format="%d%%")
    st.divider()

    if st.button("💾 Salvar configurações", type="primary", use_container_width=True):
        save_config("pro_labore",           pro_labore_c)
        save_config("pro_labore_liquido",   pro_liq_c)
        save_config("prev_privada",         prev_c)
        save_config("contador",             contador_c)
        save_config("aliquota_simples",     round(aliquota_c/100, 4))
        save_config("fies",                 fies_c)
        save_config("meta_casa_propria",    meta_casa_c)
        save_config("meta_investimento_pct", round(meta_inv_c/100, 2))
        st.success("✅ Configurações salvas!")
        st.rerun()

    darf_c = pro_labore_c * 0.11
    st.info(f"DARF mensal: **{brl(darf_c)}** | Custos fixos mín.: **{brl(darf_c + prev_c + contador_c)}** | Investimento mín.: **{brl(pro_liq_c * meta_inv_c/100)}**")
