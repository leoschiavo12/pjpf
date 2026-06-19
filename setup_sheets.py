"""
Inicializa a estrutura do Google Sheets.
Execute UMA VEZ antes de rodar o app:

    python setup_sheets.py caminho/para/credentials.json ID_DA_PLANILHA
"""
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

TABS = {
    "config": [
        ["chave", "valor"],
        ["pro_labore", "0"],
        ["pro_labore_liquido", "1513"],
        ["prev_privada", "0"],
        ["contador", "0"],
        ["aliquota_simples", "0,06"],
        ["fies", "635,29"],
        ["meta_investimento_pct", "0,20"],
        ["meta_casa_propria", "4000"],
    ],
    "nfs": [
        ["id", "cliente", "descricao", "valor",
         "mes_competencia", "mes_faturamento", "status", "criado_em"]
    ],
    "custos_pj": [
        ["mes_ref", "receita_faturada", "simples_nacional", "pro_labore_bruto",
         "darf", "prev_privada", "contador", "total_custos",
         "saldo_pj", "distribuicao_lucros", "fechado"]
    ],
    "fluxo_pj": [
        ["mes_ref", "receita", "total_custos", "saldo_pj",
         "pro_labore_liq", "fies", "distribuicao_lucros",
         "total_nubank", "investimento", "casa_propria", "saldo_livre"]
    ],
    "fluxo_pf": [
        ["mes_ref", "pro_labore_liquido", "distribuicao_lucros",
         "total_nubank", "investimento", "casa_propria",
         "saldo_livre", "pct_investimento"]
    ],
}

def setup(credentials_path: str, spreadsheet_id: str):
    creds = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES
    )
    svc = build("sheets", "v4", credentials=creds).spreadsheets()

    # lê abas existentes
    meta = svc.get(spreadsheetId=spreadsheet_id).execute()
    abas_existentes = [s["properties"]["title"] for s in meta["sheets"]]
    print(f"Abas existentes: {abas_existentes}")

    for tab_name, rows in TABS.items():
        if tab_name in abas_existentes:
            print(f"  ⏭️  '{tab_name}' já existe — pulando.")
            continue

        # cria a aba
        svc.batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": tab_name}}}]}
        ).execute()

        # escreve cabeçalho e dados iniciais
        svc.values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{tab_name}!A1",
            valueInputOption="RAW",
            body={"values": rows}
        ).execute()

        print(f"  ✅ '{tab_name}' criada com {len(rows[0])} colunas.")

    print("\n🎉 Setup concluído!")
    print("⚠️  Lembre de compartilhar a planilha com o e-mail do service account.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python setup_sheets.py credentials.json ID_DA_PLANILHA")
        sys.exit(1)
    setup(sys.argv[1], sys.argv[2])
