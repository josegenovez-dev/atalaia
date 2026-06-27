import os
import json
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
    "stageout": {
        "id": "COLE_AQUI_O_ID_DA_PLANILHA_STAGEOUT",
        "abas": ["Base", "Resumo"]
    },
    "abs": {
        "id": "COLE_AQUI_O_ID_DA_PLANILHA_ABS",
        "abas": ["ABS", "Hoje"]
    },
    "labor": {
        "id": "COLE_AQUI_O_ID_DA_PLANILHA_LABOR",
        "abas": ["Labor", "HC"]
    },
    "inventario": {
        "id": "COLE_AQUI_O_ID_DA_PLANILHA_INVENTARIO",
        "abas": ["Inventário", "Base"]
    }
}


@app.route("/")
def home():
    return "🛡️ Atalaia Online com Gemini + Google Sheets"


def get_access_token():
    response = requests.post(
        f"{BASE_URL}/auth/app_access_token",
        json={
            "app_id": APP_ID,
            "app_secret": APP_SECRET
        },
        timeout=20
    )

    print("TOKEN RESPONSE:", response.status_code)
    print("TOKEN BODY:", response.text)

    data = response.json()
    return data.get("app_access_token")


def send_private_message(employee_code, text):
    try:
        token = get_access_token()

        if not token:
            print("ERRO: token não gerado")
            return

        payload = {
            "employee_code": str(employee_code),
            "message": {
                "tag": "text",
                "text": {
                    "content": text[:3900]
                }
            }
        }

        response = requests.post(
            f"{BASE_URL}/messaging/v2/single_chat",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=20
        )

        print("SEND RESPONSE:", response.status_code)
        print("SEND BODY:", response.text)

    except Exception as e:
        print("ERRO AO ENVIAR:", repr(e))


def get_sheets_client():
    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        raise Exception("GOOGLE_SERVICE_ACCOUNT_JSON não configurado no Render")

    info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_info(
        info,
        scopes=scopes
    )

    return gspread.authorize(credentials)


def ler_aba(nome_planilha, nome_aba):
    gc = get_sheets_client()

    config = PLANILHAS.get(nome_planilha)

    if not config:
        return []

    sheet = gc.open_by_key(config["id"])
    worksheet = sheet.worksheet(nome_aba)

    return worksheet.get_all_records()


def buscar_codigo_em_tudo(codigo):
    resultados = []

    for nome_planilha, config in PLANILHAS.items():
        if "COLE_AQUI" in config["id"]:
            continue

        for aba in config["abas"]:
            try:
                linhas = ler_aba(nome_planilha, aba)

                for i, linha in enumerate(linhas, start=2):
                    valores = [str(v).lower() for v in linha.values()]

                    if codigo.lower() in " ".join(valores):
                        resultados.append({
                            "planilha": nome_planilha,
                            "aba": aba,
                            "linha": i,
                            "dados": linha
                        })

            except Exception as e:
                print(f"ERRO lendo {nome_planilha}/{aba}:", repr(e))

    return resultados


def gerar_resposta_ia(texto, contexto=""):
    try:
        if not GEMINI_API_KEY:
            return "GEMINI_API_KEY não configurada no Render."

        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""
Você é o Atalaia, assistente interno de logística.

Responda em português do Brasil.
Seja direto, útil e profissional.
Não invente dados operacionais.
Use o contexto das planilhas quando existir.

Contexto:
{contexto}

Mensagem do usuário:
{texto}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text or "Não consegui gerar resposta."

    except Exception as e:
        print("ERRO GEMINI:", repr(e))
        return f"Tive erro ao consultar a IA Gemini: {e}"


def comando_ajuda():
    return """Comandos disponíveis:

/ajuda
/status
/lh CÓDIGO
/buscar CÓDIGO
/abs
/labor
/stageout
/inventario
/relatorio"""


def consultar_codigo(texto):
    partes = texto.split(maxsplit=1)

    if len(partes) < 2:
        return "Informe o código. Exemplo: /lh BR123456789"

    codigo = partes[1].strip()

    resultados = buscar_codigo_em_tudo(codigo)

    if not resultados:
        return f"Não encontrei registros para: {codigo}"

    resposta = f"Encontrei {len(resultados)} resultado(s) para {codigo}:\n\n"

    for item in resultados[:5]:
        resposta += f"Planilha: {item['planilha']}\n"
        resposta += f"Aba: {item['aba']}\n"
        resposta += f"Linha: {item['linha']}\n"
        resposta += f"Dados: {item['dados']}\n\n"

    return resposta


def resumo_aba(nome_planilha):
    config = PLANILHAS.get(nome_planilha)

    if not config:
        return "Planilha não cadastrada."

    if "COLE_AQUI" in config["id"]:
        return f"A planilha {nome_planilha} ainda não tem ID configurado."

    contexto = ""

    for aba in config["abas"]:
        try:
            linhas = ler_aba(nome_planilha, aba)
            contexto += f"\nAba {aba}: {linhas[:20]}\n"
        except Exception as e:
            contexto += f"\nErro lendo aba {aba}: {e}\n"

    return gerar_resposta_ia(
        f"Faça um resumo operacional da planilha {nome_planilha}.",
        contexto
    )


def gerar_relatorio():
    contexto = ""

    for nome_planilha, config in PLANILHAS.items():
        if "COLE_AQUI" in config["id"]:
            continue

        for aba in config["abas"]:
            try:
                linhas = ler_aba(nome_planilha, aba)
                contexto += f"\nPlanilha {nome_planilha} / Aba {aba}: {linhas[:10]}\n"
            except Exception as e:
                contexto += f"\nErro lendo {nome_planilha}/{aba}: {e}\n"

    if not contexto.strip():
        return "Nenhuma planilha configurada ainda."

    return gerar_resposta_ia(
        "Gere um relatório executivo da operação com base nos dados das planilhas.",
        contexto
    )


def processar_mensagem(texto):
    texto = (texto or "").strip()
    texto_lower = texto.lower()

    if not texto:
        return "Não recebi nenhuma mensagem."

    if texto_lower in ["ajuda", "/ajuda", "menu"]:
        return comando_ajuda()

    if texto_lower == "/status":
        return "Status: online.\nSeatalk: conectado.\nGemini: conectado.\nGoogle Sheets: configurado se GOOGLE_SERVICE_ACCOUNT_JSON estiver no Render."

    if texto_lower.startswith("/lh") or texto_lower.startswith("/buscar"):
        return consultar_codigo(texto)

    if texto_lower == "/abs":
        return resumo_aba("abs")

    if texto_lower == "/labor":
        return resumo_aba("labor")

    if texto_lower == "/stageout":
        return resumo_aba("stageout")

    if texto_lower == "/inventario":
        return resumo_aba("inventario")

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
