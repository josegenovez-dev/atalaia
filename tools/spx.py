import os
import requests

SPX_API = os.getenv("SPX_API_URL")


def consultar_spx(codigo):

    try:

        r = requests.get(
            f"{SPX_API}/consultar",
            params={"rastreio": codigo},
            timeout=120
        )

        r.raise_for_status()

        return r.json()

    except Exception as e:

        return {
            "erro": str(e)
        }
