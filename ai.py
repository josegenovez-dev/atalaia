from google import genai
from config import GEMINI_API_KEY


def perguntar_ia(pergunta, contexto=""):
    try:
        if not GEMINI_API_KEY:
            return "GEMINI_API_KEY não configurada no Render."

        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""
Você é o Atalaia, assistente operacional de logística da Shopee.

Regras:
- Responda em português do Brasil.
- Seja direto, útil e profissional.
- Não invente números.
- Quando houver contexto, use somente o contexto.
- Se não houver informação suficiente, diga isso claramente.

Contexto:
{contexto}

Pergunta:
{pergunta}
"""

        resposta = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return resposta.text or "Não consegui gerar resposta."

    except Exception as e:
        print("ERRO GEMINI:", repr(e))
        return f"Tive erro ao consultar a IA: {e}"
