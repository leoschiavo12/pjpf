import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build

st.set_page_config(page_title="Financeiro PJ/PF", layout="wide")

# ── Conexão Google Sheets (Simplificada para foco na interface) ───────────────
def num(s):
    try:
        if s is None or str(s).strip() in ('', 'nan', 'None'): return 0.0
        return float(str(s).strip().replace('R$','').replace(' ','').replace(',','.'))
    except: return 0.0

def fmt(v): return str(round(float(v), 2)).replace('.', ',')

# ── Interface da Aba Configurações ──────────────────────────────────────────
st.markdown("## ⚙️ Configurações")
# (Presumindo que você está dentro da aba configurada com st.tabs)

# Para garantir que não haja pré-formatação, definimos o value com base na config, 
# mas usamos step=None para matar os botões + e -.
# Se quiser que o campo fique VAZIO quando não houver valor, 
# use value=None (mas lembre-se de tratar o None no salvamento).

col1, col2 = st.columns(2)

# Exemplo de como declarar cada campo para ser estritamente manual:
pro_labore_c = col1.number_input(
    "Pro-labore bruto (R$)", 
    value=num("0"), 
    step=None, 
    format="%f", 
    key="in_prolabore"
)

pro_liq_c = col2.number_input(
    "Pro-labore líquido (R$)", 
    value=num("0"), 
    step=None, 
    format="%f", 
    key="in_proliq"
)

# Repita o mesmo padrão para os outros campos:
# step=None -> remove botões
# format="%f" ou "%g" -> evita formatação de casas decimais fixas (como .2f)

col3, col4 = st.columns(2)
prev_c = col3.number_input("Previdência privada (R$)", value=num("0"), step=None, format="%f", key="in_prev")
contador_c = col4.number_input("Contador (R$)", value=num("0"), step=None, format="%f", key="in_cont")

aliquota_c = st.number_input("Alíquota Simples (%)", value=num("0"), step=None, format="%f", key="in_aliq")

# Se os valores ainda estiverem "pré-formatados" ao carregar do Sheets, 
# certifique-se de que a função num() está limpando a string antes de passar para o value.
