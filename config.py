import json
import os

from dotenv import load_dotenv

# Carrega o arquivo .env quando o projeto roda localmente
load_dotenv()


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

PLANILHAS_RAW = os.getenv(
    "PLANILHAS",
    "",
).strip()


def carregar_planilhas():
    if not PLANILHAS_RAW:
        print(
            "ERRO: variável de ambiente PLANILHAS não foi configurada.",
            flush=True,
        )
        return {}

    try:
        dados = json.loads(PLANILHAS_RAW)
    except json.JSONDecodeError as error:
        print(
            f"ERRO AO LER PLANILHAS: {error}",
            flush=True,
        )
        print(
            f"Conteúdo recebido: {PLANILHAS_RAW!r}",
            flush=True,
        )
        return {}

    if not isinstance(dados, dict):
        print(
            "ERRO: PLANILHAS precisa ser um objeto JSON.",
            flush=True,
        )
        return {}

    # Normaliza os nomes para minúsculo
    planilhas_normalizadas = {
        str(nome).strip().lower(): configuracao
        for nome, configuracao in dados.items()
    }

    print(
        "PLANILHAS CARREGADAS:",
        list(planilhas_normalizadas.keys()),
        flush=True,
    )

    return planilhas_normalizadas


PLANILHAS = carregar_planilhas()
