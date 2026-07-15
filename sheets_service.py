import json

import gspread
from google.oauth2.service_account import Credentials

from config import GOOGLE_SERVICE_ACCOUNT_JSON, PLANILHAS


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_client():
    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON não configurado no Render."
        )

    try:
        info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON contém um JSON inválido."
        ) from error

    credentials = Credentials.from_service_account_info(
        info,
        scopes=SCOPES,
    )

    return gspread.authorize(credentials)


def obter_config_planilha(nome_planilha):
    nome_normalizado = str(nome_planilha).strip().lower()

    if nome_normalizado not in PLANILHAS:
        disponiveis = ", ".join(
            PLANILHAS.keys()
        ) or "nenhuma"

        raise ValueError(
            f'Planilha "{nome_planilha}" não configurada. '
            f"Disponíveis: {disponiveis}."
        )

    return PLANILHAS[nome_normalizado]


def obter_planilha(nome_planilha):
    client = get_client()

    configuracao = obter_config_planilha(
        nome_planilha
    )

    planilha_id = configuracao["id"]

    return client.open_by_key(planilha_id)


def descobrir_aba(planilha, nome_planilha, nome_aba=None):
    configuracao = obter_config_planilha(
        nome_planilha
    )

    candidatos = []

    if nome_aba:
        candidatos.append(nome_aba)

    abas_configuradas = configuracao.get(
        "abas",
        [],
    )

    if isinstance(abas_configuradas, str):
        abas_configuradas = [
            abas_configuradas
        ]

    candidatos.extend(abas_configuradas)

    candidatos.extend([
        "Farol",
        "FAROL",
        "farol",
        "Operação",
        "Operacao",
    ])

    nomes_testados = set()

    for candidato in candidatos:
        candidato = str(candidato).strip()

        if not candidato:
            continue

        candidato_normalizado = (
            candidato.lower()
        )

        if candidato_normalizado in nomes_testados:
            continue

        nomes_testados.add(
            candidato_normalizado
        )

        try:
            return planilha.worksheet(
                candidato
            )
        except gspread.WorksheetNotFound:
            continue

    abas_disponiveis = [
        aba.title
        for aba in planilha.worksheets()
    ]

    if len(abas_disponiveis) == 1:
        return planilha.worksheets()[0]

    raise ValueError(
        "Não foi possível identificar a aba do Farol. "
        f"Abas disponíveis: {', '.join(abas_disponiveis)}."
    )


def ler_aba(
    nome_planilha,
    nome_aba=None,
):
    planilha = obter_planilha(
        nome_planilha
    )

    aba = descobrir_aba(
        planilha=planilha,
        nome_planilha=nome_planilha,
        nome_aba=nome_aba,
    )

    valores = aba.get_all_values()

    if not valores:
        return []

    quantidade_colunas = max(
        len(linha)
        for linha in valores
    )

    cabecalhos_originais = (
        valores[0]
        + [""] * (
            quantidade_colunas
            - len(valores[0])
        )
    )

    cabecalhos = []
    cabecalhos_usados = {}

    for indice, cabecalho in enumerate(
        cabecalhos_originais,
        start=1,
    ):
        nome = str(cabecalho).strip()

        if not nome:
            nome = f"COLUNA_{indice}"

        chave = nome.lower()

        if chave in cabecalhos_usados:
            cabecalhos_usados[chave] += 1

            nome = (
                f"{nome}_"
                f"{cabecalhos_usados[chave]}"
            )
        else:
            cabecalhos_usados[chave] = 1

        cabecalhos.append(nome)

    registros = []

    for numero_linha, linha in enumerate(
        valores[1:],
        start=2,
    ):
        if not any(
            str(valor).strip()
            for valor in linha
        ):
            continue

        linha_completa = (
            linha
            + [""] * (
                quantidade_colunas
                - len(linha)
            )
        )

        registro = {
            cabecalhos[indice]:
                linha_completa[indice]
            for indice in range(
                quantidade_colunas
            )
        }

        registro["_LINHA"] = numero_linha
        registros.append(registro)

    print(
        f'Planilha "{nome_planilha}" consultada. '
        f'Aba: "{aba.title}". '
        f"Registros: {len(registros)}.",
        flush=True,
    )

    return registros
