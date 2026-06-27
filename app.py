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
    url = f"{BASE_URL}/auth/app_access_token"

    payload = {
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }

    response = requests.post(url, json=payload)

    print("TOKEN RESPONSE:", response.status_code)
    print("TOKEN BODY:", response.text)

    try:
        data = response.json()
        return data.get("app_access_token")
    except Exception as e:
        print("ERRO TOKEN:", e)
        return None


def gerar_resposta_ia(texto):
    try:
        response = client.responses.create(
            model="gpt-5.5",
            instructions="""
Você é o Atalaia, assistente interno de logística da Shopee.
Responda em português do Brasil.
Seja direto, útil e profissional.
Quando não souber algo, diga que precisa consultar a base ou sistema.
""",
            input=texto
        )

        return response.output_text

    except Exception as e:
        print("ERRO IA:", e)
        return "🛡️ Atalaia Online\n\nTive um erro ao gerar a resposta com IA."


def send_private_message(employee_code, text):
    token = get_access_token()

    if not token:
        print("Erro: token não gerado")
        return

    url = f"{BASE_URL}/messaging/v2/single_chat"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "employee_code": str(employee_code),
        "message": {
            "tag": "text",
            "text": {
                "content": text
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    print("SEND RESPONSE:", response.status_code)
    print("SEND BODY:", response.text)


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
                "🛡️ Atalaia Online\n\nOlá! Estou online. Pode me mandar uma mensagem."
            )

    if data.get("event_type") == "message_from_bot_subscriber":
        event = data.get("event", {})
        employee_code = event.get("employee_code")

        texto = (
            event.get("message", {})
            .get("text", {})
            .get("content", "")
        )

        if employee_code and texto:
            resposta_ia = gerar_resposta_ia(texto)
            resposta = f"🛡️ Atalaia Online\n\n{resposta_ia}"
            send_private_message(employee_code, resposta)

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
