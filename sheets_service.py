import json
import gspread
from google.oauth2.service_account import Credentials
from config import GOOGLE_SERVICE_ACCOUNT_JSON, PLANILHAS


def get_client():
    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        raise Exception("GOOGLE_SERVICE_ACCOUNT_JSON não configurado.")

    info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)

    credentials = Credentials.from_service_account_info(
        info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )

    return gspread.authorize(credentials)


def ler_aba(nome_planilha, nome_aba):
    gc = get_client()
    config = PLANILHAS[nome_planilha]

    sheet = gc.open_by_key(config["id"])
    worksheet = sheet.worksheet(nome_aba)

    valores = worksheet.get_all_values()

    if not valores:
        return []

    linhas_formatadas = []

    for i, linha in enumerate(valores, start=1):
        if not any(linha):
            continue

        registro = {
            f"COLUNA_{idx + 1}": valor
            for idx, valor in enumerate(linha)
        }

        registro["_linha"] = i
        linhas_formatadas.append(registro)

    return linhas_formatadas


def ler_primeira_aba(nome_planilha):
    config = PLANILHAS[nome_planilha]
    primeira_aba = config["abas"][0]
    return ler_aba(nome_planilha, primeira_aba)


def buscar_texto_em_tudo(texto):
    resultados = []
    texto = texto.lower().strip()

    for nome_planilha, config in PLANILHAS.items():
        for aba in config["abas"]:
            try:
                linhas = ler_aba(nome_planilha, aba)

                for linha in linhas:
                    conteudo = " ".join(str(v).lower() for v in linha.values())

                    if texto in conteudo:
                        resultados.append({
                            "planilha": nome_planilha,
                            "aba": aba,
                            "linha": linha.get("_linha"),
                            "dados": linha
                        })

            except Exception as e:
                print(f"Erro lendo {nome_planilha}/{aba}:", repr(e))

    return resultados
