import os
import time
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")

BASE_URL = "https://openapi.seatalk.io"

BOT_NAME = os.getenv("BOT_NAME", "Atalaia")
BOT_SEATALK_ID = os.getenv("BOT_SEATALK_ID", "9324018901")

PORT = int(os.getenv("PORT", "5050"))

_token_cache = {
    "token": None,
    "expires_at": 0,
}


def get_access_token():
    agora = time.time()

    if (
        _token_cache["token"]
        and agora < _token_cache["expires_at"]
    ):
        return _token_cache["token"]

    if not APP_ID or not APP_SECRET:
        raise RuntimeError(
            "APP_ID ou APP_SECRET não configurados nas variáveis de ambiente."
        )

    url = f"{BASE_URL}/auth/app_access_token"

    payload = {
        "app_id": APP_ID,
        "app_secret": APP_SECRET,
    }

    response = requests.post(
        url,
        json=payload,
        timeout=15,
    )

    print(
        "TOKEN STATUS:",
        response.status_code,
        response.text,
        flush=True,
    )

    response.raise_for_status()

    data = response.json()

    token = (
        data.get("app_access_token")
        or data.get("access_token")
    )

    if not token:
        raise RuntimeError(
            f"SeaTalk não retornou um access token: {data}"
        )

    expires_in = int(data.get("expire", data.get("expires_in", 7000)))

    _token_cache["token"] = token
    _token_cache["expires_at"] = agora + max(expires_in - 120, 60)

    return token


def get_headers():
    token = get_access_token()

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def send_message_to_private(seatalk_id, text):
    if not seatalk_id:
        print("ERRO: seatalk_id privado vazio.", flush=True)
        return None

    url = (
        f"{BASE_URL}/messaging/v2/"
        f"single_chat/{seatalk_id}/message"
    )

    payload = {
        "tag": "text",
        "text": {
            "content": text,
        },
    }

    try:
        response = requests.post(
            url,
            headers=get_headers(),
            json=payload,
            timeout=15,
        )

        print(
            "SEND PRIVATE STATUS:",
            response.status_code,
            response.text,
            flush=True,
        )

        return response

    except Exception as error:
        print(
            "ERRO AO ENVIAR MENSAGEM PRIVADA:",
            repr(error),
            flush=True,
        )
        return None


def send_message_to_group(group_id, text):
    if not group_id:
        print("ERRO: group_id vazio.", flush=True)
        return None

    headers = get_headers()

    tentativas = [
        {
            "url": f"{BASE_URL}/messaging/v2/group_chat/message",
            "payload": {
                "group_id": group_id,
                "message": {
                    "tag": "text",
                    "text": {
                        "content": text,
                    },
                },
            },
        },
        {
            "url": (
                f"{BASE_URL}/messaging/v2/"
                f"group_chat/{group_id}/message"
            ),
            "payload": {
                "tag": "text",
                "text": {
                    "content": text,
                },
            },
        },
    ]

    ultimo_response = None

    for tentativa in tentativas:
        try:
            response = requests.post(
                tentativa["url"],
                headers=headers,
                json=tentativa["payload"],
                timeout=15,
            )

            ultimo_response = response

            print(
                "SEND GROUP URL:",
                tentativa["url"],
                flush=True,
            )

            print(
                "SEND GROUP STATUS:",
                response.status_code,
                response.text,
                flush=True,
            )

            if 200 <= response.status_code < 300:
                return response

        except Exception as error:
            print(
                "ERRO AO ENVIAR MENSAGEM NO GRUPO:",
                repr(error),
                flush=True,
            )

    return ultimo_response


def extrair_texto(evento):
    message = evento.get("message") or {}
    text = message.get("text") or {}

    texto = (
        text.get("plain_text")
        or text.get("content")
        or message.get("plain_text")
        or message.get("content")
        or ""
    )

    return str(texto).strip()


def extrair_seatalk_id(evento):
    sender = evento.get("sender") or {}

    return (
        sender.get("seatalk_id")
        or sender.get("employee_id")
        or evento.get("seatalk_id")
        or evento.get("subscriber_id")
    )


def extrair_group_id(evento):
    return (
        evento.get("group_id")
        or evento.get("chat_id")
        or evento.get("chatroom_id")
    )


def foi_mencionado(evento):
    message = evento.get("message") or {}
    text = message.get("text") or {}

    mentioned_list = (
        text.get("mentioned_list")
        or message.get("mentioned_list")
        or []
    )

    for mention in mentioned_list:
        mention_id = str(
            mention.get("seatalk_id", "")
        ).strip()

        username = str(
            mention.get("username", "")
        ).strip().lower()

        if mention_id and mention_id == str(BOT_SEATALK_ID):
            return True

        if username and username == BOT_NAME.lower():
            return True

    texto = extrair_texto(evento).lower()

    return (
        f"@{BOT_NAME.lower()}" in texto
        or BOT_NAME.lower() in texto
    )


def limpar_texto(texto):
    texto_limpo = str(texto or "")

    texto_limpo = texto_limpo.replace(
        f"@{BOT_NAME}",
        "",
    )

    texto_limpo = texto_limpo.replace(
        BOT_NAME,
        "",
    )

    return texto_limpo.strip()


def gerar_resposta(texto):
    texto_limpo = limpar_texto(texto)
    texto_lower = texto_limpo.lower()

    if not texto_limpo:
        return "Fala comigo 👀"

    if "boa tarde" in texto_lower:
        return "Boa tarde! Atalaia online e na escuta 🛡️"

    if "bom dia" in texto_lower:
        return "Bom dia! Atalaia online e na escuta 🛡️"

    if "boa noite" in texto_lower:
        return "Boa noite! Atalaia ativo e na escuta 🛡️"

    if texto_lower in {"oi", "olá", "ola", "e aí", "eai"}:
        return "Olá! Atalaia online 🛡️"

    if "status" in texto_lower:
        return "Atalaia online e funcionando normalmente 🟢"

    return f"Recebi sua mensagem: {texto_limpo}"


@app.route("/", methods=["GET"])
def home():
    return "🤖 SPX API Online — Atalaia ativo", 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "ok": True,
            "service": "Atalaia",
            "port": PORT,
        }
    ), 200


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return jsonify(
            {
                "ok": True,
                "message": "Webhook Atalaia online",
            }
        ), 200

    data = request.get_json(
        silent=True,
    ) or {}

    print(
        "\n========== EVENTO RECEBIDO ==========",
        flush=True,
    )
    print(data, flush=True)
    print(
        "=====================================\n",
        flush=True,
    )

    event_type = str(
        data.get("event_type", "")
    ).strip()

    evento = data.get("event") or {}

    eventos_sem_resposta = {
        "user_enter_chatroom_with_bot",
        "bot_subscriber_added",
        "url_verification",
    }

    if event_type in eventos_sem_resposta:
        return jsonify({"ok": True}), 200

    eventos_privados = {
        "message_from_bot_subscriber",
        "new_message_received_from_bot_subscriber",
        "new_message_received_from_bot_subscriber_v2",
        "message_received",
        "single_chat_message_received",
    }

    eventos_grupo = {
        "new_mentioned_message_received_from_group_chat",
        "mentioned_message_from_group_chat",
        "message_from_group_chat",
        "group_chat_message_received",
    }

    if event_type in eventos_privados:
        seatalk_id = extrair_seatalk_id(evento)
        texto = extrair_texto(evento)

        print("TIPO: PRIVADO", flush=True)
        print("SEATALK ID:", seatalk_id, flush=True)
        print("TEXTO:", texto, flush=True)

        if not seatalk_id:
            print(
                "Não foi possível localizar o seatalk_id.",
                flush=True,
            )
            return jsonify(
                {
                    "ok": False,
                    "error": "seatalk_id não encontrado",
                }
            ), 200

        if not texto:
            print(
                "Mensagem privada sem texto.",
                flush=True,
            )
            return jsonify({"ok": True}), 200

        resposta = gerar_resposta(texto)

        resultado = send_message_to_private(
            seatalk_id,
            resposta,
        )

        return jsonify(
            {
                "ok": resultado is not None,
                "type": "private",
            }
        ), 200

    if event_type in eventos_grupo:
        group_id = extrair_group_id(evento)
        texto = extrair_texto(evento)
        mencionado = foi_mencionado(evento)

        print("TIPO: GRUPO", flush=True)
        print("GROUP ID:", group_id, flush=True)
        print("TEXTO:", texto, flush=True)
        print("FOI MENCIONADO:", mencionado, flush=True)

        if not group_id:
            print(
                "Não foi possível localizar o group_id.",
                flush=True,
            )
            return jsonify(
                {
                    "ok": False,
                    "error": "group_id não encontrado",
                }
            ), 200

        if not mencionado:
            print(
                "Mensagem do grupo ignorada porque "
                "o Atalaia não foi mencionado.",
                flush=True,
            )
            return jsonify({"ok": True}), 200

        resposta = gerar_resposta(texto)

        resultado = send_message_to_group(
            group_id,
            resposta,
        )

        return jsonify(
            {
                "ok": resultado is not None,
                "type": "group",
            }
        ), 200

    print(
        "EVENTO AINDA NÃO MAPEADO:",
        event_type,
        flush=True,
    )

    return jsonify(
        {
            "ok": True,
            "ignored_event": event_type,
        }
    ), 200


@app.errorhandler(Exception)
def handle_exception(error):
    print(
        "ERRO INTERNO:",
        repr(error),
        flush=True,
    )

    return jsonify(
        {
            "ok": False,
            "error": str(error),
        }
    ), 500


if __name__ == "__main__":
    print(
        f"Atalaia iniciando na porta {PORT}...",
        flush=True,
    )

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
    )
