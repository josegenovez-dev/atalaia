import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")

BASE_URL = "https://openapi.seatalk.io"


@app.route("/")
def home():
    return "🛡️ Atalaia Online"


def get_access_token():
    url = f"{BASE_URL}/auth/app_access_token"

    payload = {
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }

    response = requests.post(url, json=payload)
    print("TOKEN RESPONSE:", response.status_code, response.text)

    data = response.json()
    return data.get("app_access_token")


def send_private_message(seatalk_id, text):
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
        "seatalk_id": seatalk_id,
        "message": {
            "tag": "text",
            "text": {
                "content": text
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print("SEND RESPONSE:", response.status_code, response.text)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    print("Evento recebido:", data)

    if data.get("event_type") == "event_verification":
        challenge = data.get("event", {}).get("seatalk_challenge")
        if challenge:
            return challenge, 200

    if data.get("event_type") == "message_from_bot_subscriber":
        event = data.get("event", {})
        seatalk_id = event.get("seatalk_id")

        texto = (
            event.get("message", {})
            .get("text", {})
            .get("content", "")
        )

        resposta = f"🛡️ Atalaia Online\n\nRecebi sua mensagem: {texto}"

        send_private_message(seatalk_id, resposta)

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
