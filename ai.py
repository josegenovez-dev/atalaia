from google import genai

from config import GEMINI_API_KEY


_client = None


def get_client():
    global _client

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY não configurada no Render."
        )

    if _client is None:
        _client = genai.Client(
            api_key=GEMINI_API_KEY
        )

    return _client


def perguntar_ia(
    pergunta,
    contexto="",
):
    client = get_client()

    prompt = f"""
Você é o Atalaia, assistente de operações logísticas.

Responda em português do Brasil.

Regras:
- Seja objetivo e operacional.
- Não invente dados.
- Use somente as informações fornecidas.
- Quando houver números, apresente-os de forma organizada.
- Não repita saudações.
- Não diga que é uma inteligência artificial.
- Se faltarem dados, informe claramente.

CONTEXTO:
{contexto}

PERGUNTA:
{pergunta}
""".strip()

    resposta = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    texto = getattr(
        resposta,
        "text",
        None,
    )

    if not texto:
        return (
            "Não consegui gerar a resposta "
            "neste momento."
        )

    return texto.strip()
