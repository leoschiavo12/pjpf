# 💼 Financeiro PJ/PF

App Streamlit para gestão financeira integrada PJ → PF, com Google Sheets como banco de dados.

## Estrutura

```
pj_financas/
├── app.py                  # Entry point
├── requirements.txt
├── setup_sheets.py         # Inicializa o Google Sheets
├── secrets.toml.template   # Template de credenciais
├── pages/
│   ├── visao_geral.py
│   ├── notas_fiscais.py
│   ├── gestao_pj.py
│   ├── financas_pf.py
│   ├── fluxo_caixa.py
│   └── configuracoes.py
└── utils/
    ├── sheets.py           # Conexão e CRUD com Google Sheets
    └── formatters.py       # Helpers de formatação
```

## Setup — passo a passo

### 1. Google Cloud — Service Account

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. Crie um projeto (ou use um existente)
3. Ative as APIs:
   - **Google Sheets API**
   - **Google Drive API**
4. Em _IAM & Admin → Service Accounts_, crie uma conta de serviço
5. Gere uma chave JSON e salve como `credentials.json`

### 2. Inicializar o Google Sheets

```bash
pip install -r requirements.txt
python setup_sheets.py credentials.json
```

O script cria a planilha `financeiro-pj-pf` com todas as abas e cabeçalhos.

**Importante:** compartilhe a planilha com o e-mail do service account (`...@....iam.gserviceaccount.com`) com permissão de Editor.

### 3. Configurar secrets

Crie a pasta `.streamlit/` e o arquivo `secrets.toml` baseado no template:

```bash
mkdir -p .streamlit
cp secrets.toml.template .streamlit/secrets.toml
```

Preencha com os dados do seu `credentials.json`.

### 4. Rodar o app

```bash
streamlit run app.py
```

### 5. Deploy no Streamlit Cloud (opcional)

1. Suba o projeto para um repositório GitHub (sem o `secrets.toml`)
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte o repositório
4. Em _Advanced settings → Secrets_, cole o conteúdo do `secrets.toml`

## Fluxo financeiro implementado

```
NFs emitidas (competência)
        ↓
NFs faturadas (mês seguinte, geralmente)
        ↓
Receita PJ
  - Simples Nacional (6%)
  - DARF (11% do pro-labore)
  - Previdência Privada
  - Contador
  - Pro-labore bruto
        ↓
Saldo PJ
  - FIES → Banco do Brasil (R$635,29)
  - Distribuição de lucros → Nubank PF
        ↓
Nubank PF (pro-labore liq. + dist. lucros)
  - 20% → Investimento (carteira)
  - R$4.000 → Plano casa própria
  - Restante → Saldo livre (cartão)
```

## .gitignore recomendado

```
.streamlit/secrets.toml
credentials.json
__pycache__/
*.pyc
.env
```
