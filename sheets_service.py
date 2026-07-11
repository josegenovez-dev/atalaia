import json

import gspread
from google.oauth2.service_account import Credentials

from config import GOOGLE_SERVICE_ACCOUNT_JSON, PLANILHAS


def normalizar_planilhas():
    """
    Aceita PLANILHAS como dicionário ou lista e sempre devolve
    um dicionário indexado pelo nome da planilha.
    """

    if isinstance(PLANILHAS, dict):
        return PLANILHAS

    if isinstance(PLANILHAS, list):
        resultado = {}

        for item in PLANILHAS:
            if not isinstance(item, dict):
                continue

            nome = (
                item.get("nome")
                or item.get("name")
                or item.get("chave")
                or item.get("key")
            )

            if nome:
                resultado[str(nome).lower().strip()] = item

        return resultado

    raise TypeError(
        "A variável PLANILHAS precisa ser um dicionário ou uma lista."
    )


def get_client():
    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON não configurado."
        )

    try:
        info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"GOOGLE_SERVICE_ACCOUNT_JSON contém JSON inválido: {error}"
        ) from error

    credentials = Credentials.from_service_account_info(
        info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )

    return gspread.authorize(credentials)


def obter_config_planilha(nome_planilha):
    planilhas = normalizar_planilhas()
    nome_normalizado = str(nome_planilha).lower().strip()

    config = (
        planilhas.get(nome_planilha)
        or planilhas.get(nome_normalizado)
    )

    if not config:
        nomes_disponiveis = ", ".join(planilhas.keys())

        raise KeyError(
            f"Planilha '{nome_planilha}' não configurada. "
            f"Disponíveis: {nomes_disponiveis or 'nenhuma'}."
        )

    if not isinstance(config, dict):
        raise TypeError(
            f"A configuração da planilha '{nome_planilha}' "
            "não é um dicionário."
        )

    if not config.get("id"):
        raise ValueError(
            f"A planilha '{nome_planilha}' não possui o campo 'id'."
        )

    return config


def obter_abas(config):
    abas = config.get("abas") or config.get("aba") or []

    if isinstance(abas, str):
        abas = [
            item.strip()
            for item in abas.split(",")
            if item.strip()
        ]

    if not isinstance(abas, list):
        raise TypeError(
            "O campo 'abas' precisa ser uma lista ou texto."
        )

    return abas


def ler_aba(nome_planilha, nome_aba):
    config = obter_config_planilha(nome_planilha)
    gc = get_client()

    print(
        "ABRINDO PLANILHA:",
        nome_planilha,
        config["id"],
        flush=True,
    )

    print(
        "ABRINDO ABA:",
        nome_aba,
        flush=True,
    )

    sheet = gc.open_by_key(config["id"])
    worksheet = sheet.worksheet(nome_aba)

    valores = worksheet.get_all_values()

    if not valores:
        return []

    linhas_formatadas = []

    for numero_linha, linha in enumerate(valores, start=1):
        if not any(str(valor).strip() for valor in linha):
            continue

        registro = {
            f"COLUNA_{indice + 1}": valor
            for indice, valor in enumerate(linha)
        }

        registro["_linha"] = numero_linha
        linhas_formatadas.append(registro)

    print(
        "LINHAS LIDAS:",
        len(linhas_formatadas),
        flush=True,
    )

    return linhas_formatadas


def ler_primeira_aba(nome_planilha):
    config = obter_config_planilha(nome_planilha)
    abas = obter_abas(config)

    if not abas:
        raise ValueError(
            f"A planilha '{nome_planilha}' não possui abas configuradas."
        )

    return ler_aba(
        nome_planilha=nome_planilha,
        nome_aba=abas[0],
    )


def buscar_texto_em_tudo(texto):
    resultados = []
    texto_normalizado = str(texto or "").lower().strip()

    if not texto_normalizado:
        return resultados

    planilhas = normalizar_planilhas()

    for nome_planilha, config in planilhas.items():
        try:
            abas = obter_abas(config)
        except Exception as error:
            print(
                f"Erro na configuração de {nome_planilha}:",
                repr(error),
                flush=True,
            )
            continue

        for aba in abas:
            try:
                linhas = ler_aba(
                    nome_planilha=nome_planilha,
                    nome_aba=aba,
                )

                for linha in linhas:
                    conteudo = " ".join(
                        str(valor).lower()
                        for valor in linha.values()
                    )

                    if texto_normalizado in conteudo:
                        resultados.append(
                            {
                                "planilha": nome_planilha,
                                "aba": aba,
                                "linha": linha.get("_linha"),
                                "dados": linha,
                            }
                        )

            except Exception as error:
                print(
                    f"Erro lendo {nome_planilha}/{aba}:",
                    repr(error),
                    flush=True,
                )

    return resultados
