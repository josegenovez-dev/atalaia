import os
import requests

SPX_API_URL = os.getenv("SPX_API_URL")


def consultar_spx(codigo):
    if not SPX_API_URL:
        return {"erro": "SPX_API_URL não configurada no Render."}

    try:
        resposta = requests.get(
            f"{SPX_API_URL}/consultar",
            params={"rastreio": codigo},
            timeout=120
        )

        resposta.raise_for_status()
        return resposta.json()

    except Exception as e:
        return {"erro": str(e)}
