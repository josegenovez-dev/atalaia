from flask import Flask, request, jsonify
from seatalk import send_private_message
from planner import processar_mensagem

app = Flask(__name__)


@app.route("/")
def home():
    return "🛡️ Atalaia v2 Online"


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
        employee_code = event.get("employee_code")

        texto = (
            event.get("message", {})
            .get("text", {})
            .get("content", "")
        )

        if employee_code:
            resposta = processar_mensagem(texto)
            send_private_message(
                employee_code,
                f"🛡️ Atalaia Online\n\n{resposta}"
            )

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    print("🛡️ Atalaia v2 iniciando...")
    app.run(host="0.0.0.0", port=5000)
