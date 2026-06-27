import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

BASE_URL = "https://openapi.seatalk.io"


@app.route("/")
def home():
    return "🛡️ Atalaia Online com IA"


def get_openai_client():
    if not OPENAI_API_KEY:
        raise Exception("OPENAI_API_KEY não configurada no Render")
    return OpenAI(api_key=OPENAI_API_KEY)


def get_access_token():
    url = f"{BASE_URL}/auth/app_access_token"

    payload = {
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }

    response = requests.post(url, json=payload, timeout=20)

    print("TOKEN RESPONSE:", response.status_code)
    print("TOKEN BODY:", response.text)

    data = response.json()
    return data.get("app_access_token")


def send_private_message(employee_code, text):
    token = get_access_token()

    if not token:
        print("ERRO: token não gerado")
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
                "content": text[:3900]
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload, timeout=20)

    print("SEND RESPONSE:", response.status_code)
    print("SEND BODY:", response.text)


def gerar_resposta_ia(texto):
    try:
        client = get_openai_client()

        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions="""
Você é o Atalaia, assistente interno de logística.
Responda em português do Brasil.
Seja direto, útil e profissional.
Não invente dados operacionais.
Quando precisar consultar sistemas, diga claramente.
""",
            input=texto
        )

        return response.output_text

    except Exception as e:
        print("ERRO IA:", e)
        return "Tive erro ao consultar a IA. Verifique se a OPENAI_API_KEY está configurada no Render."


def comando_ajuda():
    return """Comandos disponíveis:

/ajuda - mostra os comandos
/status - verifica se o Atalaia está online
/lh CÓDIGO - consulta LH em modo teste
/relatorio - gera relatório teste

Também pode conversar comigo normalmente."""


def consultar_lh(texto):
    partes = texto.split()

    if len(partes) < 2:
        return "Informe o LH. Exemplo: /lh BR123456789"

    lh = partes[1]

    return f"""Consulta LH

LH: {lh}
Status: ainda não conectado ao sistema real.

Próximo passo:
integrar Selenium/Data Suite para buscar o status automaticamente."""


def gerar_relatorio():
    return """Relatório Operacional

Status: modelo pronto.
Dados reais: ainda não conectados.

Próximo passo:
conectar Google Sheets, Data Suite ou Selenium."""


def processar_mensagem(texto):
    texto = (texto or "").strip()

    if not texto:
        return "Não recebi nenhuma mensagem."

    texto_lower = texto.lower()

    if texto_lower in ["ajuda", "/ajuda", "menu"]:
        return comando_ajuda()

    if texto_lower == "/status":
        return "Status: online.\nSeatalk: conectado.\nIA: configurada se OPENAI_API_KEY estiver no Render."

    if texto_lower.startswith("/lh"):
        return consultar_lh(texto)

    if texto_lower == "/relatorio":
        return gerar_relatorio()

    return gerar_resposta_ia(texto)


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
            send_private_message(
                employee_code,
                f"🛡️ Atalaia Online\n\n{resposta}"
            )

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    print("🛡️ Atalaia iniciando...")
    app.run(host="0.0.0.0", port=5000)
