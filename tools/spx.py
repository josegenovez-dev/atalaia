import os
import requests

SPX_API_URL = os.getenv(
    "SPX_API_URL",
    "",
).rstrip("/")


def consultar_spx(codigo):
    if not SPX_API_URL:
        return {
            "erro": (
                "SPX_API_URL não configurada "
                "no Render."
            )
        }

    codigo = str(codigo or "").strip()

    if not codigo:
        return {
            "erro": "Código de rastreio não informado."
        }

    url = f"{SPX_API_URL}/consultar"

    try:
        print(
            "CONSULTANDO SPX:",
            url,
            flush=True,
        )

        print(
            "CÓDIGO SPX:",
            codigo,
            flush=True,
        )

        resposta = requests.get(
            url,
            params={
                "rastreio": codigo,
            },
            timeout=120,
        )

        print(
            "SPX STATUS:",
            resposta.status_code,
            flush=True,
        )

        print(
            "SPX BODY:",
            resposta.text[:3000],
            flush=True,
        )

        resposta.raise_for_status()

        try:
            dados = resposta.json()
        except ValueError:
            return {
                "erro": (
                    "A API SPX não retornou "
                    "uma resposta JSON."
                ),
                "resposta": resposta.text[:1000],
            }

        return dados

    except requests.Timeout:
        return {
            "erro": (
                "A consulta ao SPX demorou "
                "mais de 120 segundos."
            )
        }

    except requests.RequestException as error:
        return {
            "erro": (
                "Falha ao consultar a API SPX: "
                f"{error}"
            )
        }

    except Exception as error:
        return {
            "erro": (
                "Erro inesperado na consulta SPX: "
                f"{error}"
            )
        }
