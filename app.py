from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "🛡️ Atalaia Online"


@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    print("======== NOVA REQUISICAO ========")
    print("Metodo:", request.method)
    print("Args:", request.args)
    print("Headers:", dict(request.headers))

    try:
        print("JSON:", request.get_json(silent=True))
    except:
        pass

    challenge = request.args.get("seatalk_challenge")

    if challenge:
        return challenge

    if request.is_json:
        data = request.get_json(silent=True)

        if data and "seatalk_challenge" in data:
            return str(data["seatalk_challenge"])

    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
