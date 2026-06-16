from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "🛡️ Atalaia Online"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    print("Evento recebido:", data)

    if data.get("event_type") == "event_verification":
        challenge = data.get("event", {}).get("seatalk_challenge")
        if challenge:
            return jsonify({
                "seatalk_challenge": challenge
            }), 200

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
