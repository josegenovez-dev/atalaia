import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
BASE_URL = "https://openapi.seatalk.io"

BOT_NAME = "Atalaia"
BOT_SEATALK_ID = "9324018901"


def get_access_token():
    url = f"{BASE_URL}/auth/app_access_token"
    payload = {
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }

    r = requests.post(url, json=payload, timeout=15)
    print("TOKEN STATUS:", r.status_code, r.text)

    data = r.json()
    return data.get("app_access_token") or data.get("access_token")


def send_message_to_group(group_id, text):
    token = get_access_token()

    url = f"{BASE_URL}/messaging/v2/group_chat/{group_id}/message"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "tag": "text",
        "text": {
            "content": text
        }
    }

    r = requests.post(url, headers=headers, json=payload, timeout=15)
    print("SEND GROUP STATUS:", r.status_code, r.text)
    return r


def send_message_to_private(seatalk_id, text):
    token = get_access_token()

    url = f"{BASE_URL}/messaging/v2/single_chat/{seatalk_id}/message"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "tag": "text",
        "text": {
            "content": text
        }
    }

    r = requests.post(url, headers=headers, json=payload, timeout=15)
    print("SEND PRIVATE STATUS:", r.status_code, r.text)
    return r


def gerar_resposta(texto):
    texto_limpo = (
        texto.replace(f"@{BOT_NAME}", "")
        .replace(BOT_NAME, "")
        .strip()
        .lower()
    )

    if not texto_limpo:
        return "Fala comigo 👀"

    if "boa tarde" in texto_limpo:
        return "Boa tarde! Atalaia online e na escuta 🛡️"

    if "bom dia" in texto_limpo:
        return "Bom dia! Atalaia online 🛡️"

    if "boa noite" in texto_limpo:
        return "Boa noite! Atalaia ativo 🛡️"

    return f"Recebi sua mensagem: {texto_limpo}"


def foi_mencionado(evento):
    message = evento.get("message", {})
    text = message.get("text", {})
    mentioned_list = text.get("mentioned_list", [])

    for mention in mentioned_list:
        if mention.get("seatalk_id") == BOT_SEATALK_ID:
            return True

        if mention.get("username", "").lower() == BOT_NAME.lower():
            return True

    plain_text = text.get("plain_text", "")
    return f"@{BOT_NAME}".lower() in plain_text.lower()


@app.route("/", methods=["GET"])
def home():
    return "Atalaia online", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    print("Evento recebido:", data)

    event_type = data.get("event_type")
    evento = data.get("event", {})

    # Quando o bot entra no grupo
    if event_type == "user_enter_chatroom_with_bot":
        return jsonify({"ok": True}), 200

    # Mensagem marcada em grupo
    if event_type == "new_mentioned_message_received_from_group_chat":
        group_id = evento.get("group_id")
        message = evento.get("message", {})
        text = message.get("text", {})
        plain_text = text.get("plain_text", "")

        if group_id and foi_mencionado(evento):
            resposta = gerar_resposta(plain_text)
            send_message_to_group(group_id, resposta)

        return jsonify({"ok": True}), 200

    # Mensagem privada
    if event_type in ["new_message_received_from_bot_subscriber", "message_received"]:
        sender = evento.get("sender", {})
        seatalk_id = sender.get("seatalk_id")

        message = evento.get("message", {})
        text = message.get("text", {})
        plain_text = text.get("plain_text", "")

        if seatalk_id:
            resposta = gerar_resposta(plain_text)
            send_message_to_private(seatalk_id, resposta)

        return jsonify({"ok": True}), 200

    print("Evento ignorado:", event_type)
    return jsonify({"ok": True}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
