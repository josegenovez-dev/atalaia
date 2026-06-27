from google import genai
from config import GEMINI_API_KEY


def perguntar_gemini(pergunta, contexto=""):
    try:
        if not GEMINI_API_KEY:
            return "GEMINI_API_KEY não configurada."

        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""
Você é o Atalaia, assistente interno de logística.

Regras:
- Responda em português do Brasil.
- Seja direto.
- Não invente dados.
- Use somente o contexto quando ele existir.

Contexto:
{contexto}

Pergunta:
{pergunta}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text or "Não consegui gerar resposta."

    except Exception as e:
        print("ERRO GEMINI:", repr(e))
        return f"Tive erro ao consultar a IA: {e}"
