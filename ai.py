from openai import OpenAI
from config import GROQ_API_KEY


def perguntar_gemini(pergunta, contexto=""):
    return perguntar_ia(pergunta, contexto)


def perguntar_ia(pergunta, contexto=""):
    try:
        if not GROQ_API_KEY:
            return "GROQ_API_KEY não configurada no Render."

        client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )

        prompt = f"""
Você é o Atalaia, assistente interno de logística.

Regras:
- Responda em português do Brasil.
- Seja direto, útil e profissional.
- Não invente dados.
- Quando houver contexto, use somente os dados do contexto.
- Se não houver dados suficientes, diga isso claramente.

Contexto:
{contexto}

Pergunta:
{pergunta}
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        return response.choices[0].message.content

    except Exception as e:
        print("ERRO GROQ:", repr(e))
        return f"Tive erro ao consultar a IA Groq: {e}"
