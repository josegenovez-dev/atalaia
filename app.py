from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "🛡️ Atalaia Online"


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    challenge = request.args.get("seatalk_challenge")

    if challenge:
        return challenge

    data = request.get_json(silent=True)

    if data:
        print("Evento recebido:")
        print(data)

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
