import os
import json
import re
import requests
from flask import Flask, request, jsonify
from google import genai
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

BASE_URL = "https://openapi.seatalk.io"

PLANILHAS = {
    "historico": {
        "id": "COLE_AQUI_O_ID_DA_PLANILHA",
        "abas": ["Histórico de Entregas"]
    }
}


@app.route("/")
def home():
    return "🛡️ Atalaia Online com Sheets"


def get_access_token():
    response = requests.post(
        f"{BASE_URL}/auth/app_access_token",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
        timeout=20
    )
    data = response.json()
    return data.get("app_access_token")


def send_private_message(employee_code, text):
    try:
        token = get_access_token()
        if not token:
            return

        payload = {
            "employee_code": str(employee_code),
            "message": {
                "tag": "text",
                "text": {"content": text[:3900]}
            }
        }

        requests.post(
            f"{BASE_URL}/messaging/v2/single_chat",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=20
        )

    except Exception as e:
        print("ERRO AO ENVIAR:", repr(e))


def get_sheets_client():
    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        raise Exception("GOOGLE_SERVICE_ACCOUNT_JSON não configurado")

    info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)

    credentials = Credentials.from_service_account_info(
        info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )

    return gspread.authorize(credentials)


def ler_aba(planilha_id, aba):
    gc = get_sheets_client()
    sheet = gc.open_by_key(planilha_id)
    worksheet = sheet.worksheet(aba)
    return worksheet.get_all_records()


def buscar_em_planilhas(codigo):
    resultados = []
    codigo = str(codigo).strip().lower()

    for nome, config in PLANILHAS.items():
        if "COLE_AQUI" in config["id"]:
            continue

        for aba in config["abas"]:
            try:
                linhas = ler_aba(config["id"], aba)

                for numero_linha, linha in enumerate(linhas, start=2):
                    texto_linha = " ".join(str(v).lower() for v in linha.values())

                    if codigo in texto_linha:
                        resultados.append({
                            "planilha": nome,
                            "aba": aba,
                            "linha": numero_linha,
                            "dados": linha
                        })

            except Exception as e:
                print(f"Erro lendo {nome}/{aba}:", repr(e))

    return resultados


def extrair_codigo(texto):
    match = re.search(r"[A-Za-z0-9\-]{5,}", texto)
    return match.group(0) if match else None


def gerar_resposta_ia(pergunta, contexto):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""
Você é o Atalaia, assistente interno de logística.
Responda em português do Brasil, de forma direta.

Pergunta do usuário:
{pergunta}

Dados encontrados nas planilhas:
{contexto}

Explique o resultado sem inventar informações.
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text or "Não consegui gerar resposta."

    except Exception as e:
        print("ERRO GEMINI:", repr(e))
        return f"Encontrei dados, mas tive erro ao organizar a resposta: {e}"


def consultar_codigo(texto):
    codigo = extrair_codigo(texto)

    if not codigo:
        return "Me envie um código, pedido, LH ou rastreio para eu buscar."

    resultados = buscar_em_planilhas(codigo)

    if not resultados:
        return f"Não encontrei nada para: {codigo}"

    contexto = json.dumps(resultados[:5], ensure_ascii=False, indent=2)

    return gerar_resposta_ia(texto, contexto)


def comando_ajuda():
    return """Comandos disponíveis:

/buscar CÓDIGO
/lh CÓDIGO
/pedido CÓDIGO
/status
/ajuda

Também pode perguntar naturalmente:
"onde está o pedido 12345?"
"""


def processar_mensagem(texto):
    texto = (texto or "").strip()
    texto_lower = texto.lower()

    if not texto:
        return "Não recebi nenhuma mensagem."

    if texto_lower in ["/ajuda", "ajuda", "menu"]:
        return comando_ajuda()

    if texto_lower == "/status":
        return "Status: online.\nSeatalk: conectado.\nGemini: conectado.\nGoogle Sheets: conectado."

    if texto_lower.startswith(("/buscar", "/lh", "/pedido")):
        return consultar_codigo(texto)

    if re.search(r"[A-Za-z0-9\-]{5,}", texto):
        return consultar_codigo(texto)

    return gerar_resposta_ia(texto, "Nenhuma consulta de planilha foi solicitada.")


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
            send_private_message(employee_code, f"🛡️ Atalaia Online\n\n{resposta}")

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    print("🛡️ Atalaia iniciando...")
    app.run(host="0.0.0.0", port=5000)
