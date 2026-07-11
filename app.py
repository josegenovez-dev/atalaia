import os
from flask import Flask, jsonify, request

from ai import perguntar_ia
from seatalk import send_private_message

app = Flask(__name__)

BOT_NAME = os.getenv("BOT_NAME", "Atalaia")
PORT = int(os.getenv("PORT", "5000"))

EVENTOS_PRIVADOS = {
    "message_from_bot_subscriber",
    "new_message_received_from_bot_subscriber",
    "new_message_received_from_bot_subscriber_v2",
    "message_received",
    "single_chat_message_received",
}

EVENTOS_GRUPO = {
    "new_mentioned_message_received_from_group_chat",
    "mentioned_message_from_group_chat",
    "message_from_group_chat",
    "group_chat_message_received",
}

EVENTOS_INFORMATIVOS = {
    "user_enter_chatroom_with_bot",
    "bot_subscriber_added",
    "url_verification",
}


def extrair_texto(evento):
    message = evento.get("message") or {}
    text = message.get("text") or {}

    conteudo = (
        text.get("content")
        or text.get("plain_text")
        or message.get("content")
        or message.get("plain_text")
        or ""
    )

    return str(conteudo).strip()


def extrair_employee_code(evento):
    sender = evento.get("sender") or {}

    return (
        evento.get("employee_code")
        or sender.get("employee_code")
    )


def extrair_seatalk_id(evento):
    sender = evento.get("sender") or {}

    return (
        evento.get("seatalk_id")
        or sender.get("seatalk_id")
    )


def extrair_group_id(evento):
    return (
        evento.get("group_id")
        or evento.get("chat_id")
        or evento.get("chatroom_id")
        or evento.get("thread_id")
    )


def limpar_mencao(texto):
    texto_limpo = str(texto or "").strip()

    texto_limpo = texto_limpo.replace(
        f"@{BOT_NAME}",
        "",
    )

    texto_limpo = texto_limpo.replace(
        BOT_NAME,
        "",
    )

    return texto_limpo.strip()


def gerar_resposta(texto, contexto=""):
    pergunta = limpar_mencao(texto)

    if not pergunta:
        return "Pode falar. Como posso ajudar?"

    resposta = perguntar_ia(
        pergunta=pergunta,
        contexto=contexto,
    )

    return resposta


@app.route("/", methods=["GET"])
def home():
    return "🤖 Atalaia online", 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "ok": True,
            "service": "Atalaia",
            "gemini": True,
        }
    ), 200


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return jsonify(
            {
                "ok": True,
                "message": "Webhook do Atalaia online",
            }
        ), 200

    data = request.get_json(silent=True) or {}

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
        data.get("event_type") or ""
    ).strip()

    evento = data.get("event") or {}

    if not event_type:
        print(
            "Evento recebido sem event_type.",
            flush=True,
        )

        return jsonify(
            {
                "ok": False,
                "error": "event_type ausente",
            }
        ), 200

    if event_type in EVENTOS_INFORMATIVOS:
        print(
            "EVENTO INFORMATIVO:",
            event_type,
            flush=True,
        )

        return jsonify({"ok": True}), 200

    if event_type in EVENTOS_PRIVADOS:
        employee_code = extrair_employee_code(evento)
        seatalk_id = extrair_seatalk_id(evento)
        texto = extrair_texto(evento)

        print("TIPO: PRIVADO", flush=True)
        print(
            "EMPLOYEE CODE:",
            employee_code,
            flush=True,
        )
        print(
            "SEATALK ID:",
            seatalk_id,
            flush=True,
        )
        print("TEXTO:", texto, flush=True)

        if not employee_code:
            print(
                "Employee code não encontrado.",
                flush=True,
            )

            return jsonify(
                {
                    "ok": False,
                    "error": "employee_code não encontrado",
                }
            ), 200

        if not texto:
            print(
                "Mensagem privada sem texto.",
                flush=True,
            )

            return jsonify({"ok": True}), 200

        resposta = gerar_resposta(texto)

        print(
            "RESPOSTA GEMINI:",
            resposta,
            flush=True,
        )

        enviado = send_private_message(
            employee_code=employee_code,
            text=resposta,
        )

        return jsonify(
            {
                "ok": enviado,
                "type": "private",
            }
        ), 200

    if event_type in EVENTOS_GRUPO:
        group_id = extrair_group_id(evento)
        texto = extrair_texto(evento)

        print("TIPO: GRUPO", flush=True)
        print("GROUP ID:", group_id, flush=True)
        print("TEXTO:", texto, flush=True)

        if texto:
            resposta = gerar_resposta(texto)

            print(
                "RESPOSTA GEMINI PARA GRUPO:",
                resposta,
                flush=True,
            )

        # O evento do grupo será tratado para envio depois
        # que o SeaTalk realmente entregar o identificador
        # e o formato correto do evento.
        return jsonify(
            {
                "ok": True,
                "type": "group",
                "group_id": group_id,
                "message_received": bool(texto),
            }
        ), 200

    print(
        "EVENTO NÃO MAPEADO:",
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
def tratar_erro(error):
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
