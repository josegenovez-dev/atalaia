from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def home():
    return "🛡️ Atalaia Online"


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    challenge = request.args.get("seatalk_challenge")

    if not challenge and request.form:
        challenge = request.form.get("seatalk_challenge")

    if not challenge:
        data = request.get_json(silent=True) or {}
        challenge = data.get("seatalk_challenge")

    if challenge:
        return challenge, 200, {"Content-Type": "text/plain"}

    print("Evento recebido:", request.get_json(silent=True))
    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
