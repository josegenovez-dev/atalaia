import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
BASE_URL = "https://openapi.seatalk.io"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.route("/")
def home():
    return "🛡️ Atalaia Online com IA"


def get_access_token():
    response = requests.post(
        f"{BASE_URL}/auth/app_access_token",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
        timeout=20
    )

    print("TOKEN RESPONSE:", response.status_code)
    print("TOKEN BODY:", response.text)

    data = response.json()
    return data.get("app_access_token")


def send_private_message(employee_code, text):
    try:
        token = get_access_token()

        payload = {
            "employee_code": str(employee_code),
            "message": {
                "tag": "text",
                "text": {"content": text[:3900]}
            }
        }

        response = requests.post(
            f"{BASE_URL}/messaging/v2/single_chat",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=20
        )

        print("SEND RESPONSE:", response.status_code)
        print("SEND BODY:", response.text)

    except Exception as e:
        print("ERRO AO ENVIAR:", e)


def comando_ajuda():
    return """🛡️ Atalaia Online

Comandos disponíveis:

/ajuda
Mostra os comandos.

/status
Mostra o status do Atalaia.

/lh CÓDIGO
Consulta um LH. Ainda em modo teste.

/relatorio
Gera um resumo operacional. Ainda em modo teste.

Você também pode falar comigo normalmente."""


def consultar_lh(texto):
    partes = texto.split()

    if len(partes) < 2:
        return "Informe o LH. Exemplo: /lh BR123456789"

    lh = partes[1]

    return f"""Consulta LH

LH: {lh}
Status: ferramenta ainda não conectada ao sistema.
Próximo passo: integrar Selenium/Data Suite para buscar o status real."""


def gerar_relatorio():
    return """Relatório Operacional

Status: modelo de relatório pronto.
Dados reais: ainda não conectados.

Próximo passo:
- conectar Google Sheets
- conectar Data Suite
- puxar pendências
- gerar resumo automático"""


def gerar_resposta_ia(texto):
    try:
        response = client.responses.create(
            model="gpt-5.5",
            instructions="""
Você é o Atalaia, assistente interno de logística.
Responda em português do Brasil.
Seja direto, útil e profissional.
Não invente dados operacionais.
Se precisar consultar sistema, diga isso claramente.
""",
            input=texto
        )

        return response.output_text

    except Exception as e:
        print("ERRO IA:", e)
        return "Tive um erro ao consultar a IA. Verifique a OPENAI_API_KEY e os logs."


def processar_mensagem(texto):
    texto_limpo = texto.strip()

    if not texto_limpo:
        return "Não recebi nenhuma mensagem."

    texto_lower = texto_limpo.lower()

    if texto_lower in ["/ajuda", "ajuda", "menu"]:
        return comando_ajuda()

    if texto_lower == "/status":
        return "🛡️ Atalaia Online\n\nStatus: online.\nIA: conectada.\nSeatalk: conectado."

    if texto_lower.startswith("/lh"):
        return consultar_lh(texto_limpo)

    if texto_lower == "/relatorio":
        return gerar_relatorio()

    return gerar_resposta_ia(texto_limpo)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    print("Evento recebido:", data)

    if data.get("event_type") == "event_verification":
        challenge = data.get("event", {}).get("seatalk_challenge")
        if challenge:
            return challenge, 200

    if data.get("event_type") == "user_enter_chatroom_with_bot":
        event = data.get("event", {})
        employee_code = event.get("employee_code")

        if employee_code:
            send_private_message(
                employee_code,
                "🛡️ Atalaia Online\n\nEstou online. Digite /ajuda para ver os comandos."
            )

    if data.get("event_type") == "message_from_bot_subscriber":
        event = data.get("event", {})
        employee_code = event.get("employee_code")

        texto = (
            event.get("message", {})
            .get("text", {})
            .get("content", "")
        )

        if employee_code:
            resposta = processar_mensagem(texto)
            send_private_message(employee_code, f"🛡️ Atalaia Online\n\n{resposta}")

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    print("Atalaia iniciando...")
    app.run(host="0.0.0.0", port=5000)
