import json
import os


APP_ID = os.getenv("APP_ID", "").strip()
APP_SECRET = os.getenv("APP_SECRET", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

BASE_URL = os.getenv(
    "SEATALK_BASE_URL",
    "https://openapi.seatalk.io",
).strip()

GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv(
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "",
).strip()


# Configuração padrão da planilha Farol.
# Caso exista PLANILHAS no Render, ela substitui esta configuração.
PLANILHAS_PADRAO = {
    "farol": {
        "id": "1LhUnFfCldo_KtKFKHSzNBOawJ3KOT0s-CKd8pRAyR2o",
        "abas": ["Farol"],
    }
}


def carregar_planilhas():
    planilhas_raw = os.getenv("PLANILHAS", "").strip()

    if not planilhas_raw:
        print(
            "PLANILHAS não configurada no Render. "
            "Usando configuração padrão.",
            flush=True,
        )

        return PLANILHAS_PADRAO

    try:
        dados = json.loads(planilhas_raw)
    except json.JSONDecodeError as error:
        print(
            f"ERRO AO LER PLANILHAS: {error}",
            flush=True,
        )

        print(
            "Usando configuração padrão da planilha Farol.",
            flush=True,
        )

        return PLANILHAS_PADRAO

    if not isinstance(dados, dict):
        print(
            "ERRO: PLANILHAS precisa ser um objeto JSON.",
            flush=True,
        )

        return PLANILHAS_PADRAO

    planilhas_normalizadas = {}

    for nome, configuracao in dados.items():
        nome_normalizado = str(nome).strip().lower()

        if not isinstance(configuracao, dict):
            continue

        planilha_id = str(
            configuracao.get("id", "")
        ).strip()

        if not planilha_id:
            continue

        planilhas_normalizadas[nome_normalizado] = configuracao

    if not planilhas_normalizadas:
        print(
            "Nenhuma planilha válida encontrada em PLANILHAS. "
            "Usando configuração padrão.",
            flush=True,
        )

        return PLANILHAS_PADRAO

    print(
        "PLANILHAS CARREGADAS:",
        list(planilhas_normalizadas.keys()),
        flush=True,
    )

    return planilhas_normalizadas


PLANILHAS = carregar_planilhas()
