# ══════════════════════════════════════════════════════════════════════════════
# ABA CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
with aba_config:
    st.subheader("⚙️ Configurações do Sistema")
    cfg = load_config()

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏢 PJ")
        pro_labore = st.number_input("Pro-labore bruto (R$)", value=num(cfg.get("pro_labore","0")), step=100.0)
        prev_privada = st.number_input("Previdência Privada (R$)", value=num(cfg.get("prev_privada","0")), step=50.0)
        aliquota_das = st.slider("Alíquota DAS (%)", 1.0, 20.0, num(cfg.get("aliquota_simples","0,06"))*100, 0.1)
        aliquota_darf = st.number_input("Alíquota DARF (%)", 0.0, 20.0, num(cfg.get("aliquota_darf","0,11"))*100, 0.1)
        contador = st.number_input("Contador (R$)", value=num(cfg.get("contador","0")), step=50.0)

    with col2:
        st.markdown("### 👤 PF (Planos)")
        fies = st.number_input("FIES (R$)", value=num(cfg.get("fies","635,29")), step=10.0)
        meta_invest = st.slider("Meta de Investimentos (% da entrada)", 5, 60, int(num(cfg.get("meta_investimento_pct","0,20"))*100), 5)
        meta_casa = st.number_input("Meta Casa Própria (R$)", value=num(cfg.get("meta_casa_propria","4000")), step=100.0)

    st.divider()
    if st.button("💾 Salvar todas as configurações", type="primary", use_container_width=True):
        save_config("pro_labore", pro_labore)
        save_config("prev_privada", prev_privada)
        save_config("aliquota_simples", round(aliquota_das/100, 4))
        save_config("aliquota_darf", round(aliquota_darf/100, 4))
        save_config("contador", contador)
        save_config("fies", fies)
        save_config("meta_investimento_pct", round(meta_invest/100, 2))
        save_config("meta_casa_propria", meta_casa)
        st.success("Configurações atualizadas com sucesso!")
        st.rerun()
