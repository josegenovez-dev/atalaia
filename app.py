import os
import time

from flask import Flask, jsonify, request

from planner import processar_mensagem
from seatalk import send_group_message, send_private_message

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

EVENTOS_PROCESSADOS = {}
TTL_EVENTO = 600


def evento_ja_processado(event_id):
    agora = time.time()

    eventos_expirados = [
        chave
        for chave, horario in EVENTOS_PROCESSADOS.items()
        if agora - horario > TTL_EVENTO
    ]

    for chave in eventos_expirados:
        EVENTOS_PROCESSADOS.pop(chave, None)

    if not event_id:
        return False

    if event_id in EVENTOS_PROCESSADOS:
        return True

    EVENTOS_PROCESSADOS[event_id] = agora
    return False


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


def processar_texto_recebido(texto):
    pergunta = limpar_mencao(texto)

    if not pergunta:
        return "Pode falar. Como posso ajudar?"

    try:
        resposta = processar_mensagem(pergunta)

        if not resposta:
            return "Não consegui gerar uma resposta agora."

        return str(resposta).strip()

    except Exception as error:
        print(
            "ERRO NO PLANNER:",
            repr(error),
            flush=True,
        )

        return (
            "Tive um erro ao processar sua solicitação. "
            "Tente novamente em instantes."
        )


@app.route("/", methods=["GET"])
def home():
    return "🤖 Atalaia online", 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "ok": True,
            "service": "Atalaia",
            "seatalk": True,
            "planner": True,
            "gemini": True,
            "google_sheets": True,
            "spx": True,
            "private_chat": True,
            "group_chat": True,
            "deduplicacao": True,
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

    event_id = str(
        data.get("event_id") or ""
    ).strip()

    if evento_ja_processado(event_id):
        print(
            "EVENTO DUPLICADO IGNORADO:",
            event_id,
            flush=True,
        )

        return jsonify(
            {
                "ok": True,
                "duplicate": True,
            }
        ), 200

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
        print(
            "TEXTO:",
            texto,
            flush=True,
        )

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

        resposta = processar_texto_recebido(texto)

        print(
            "RESPOSTA PROCESSADA PRIVADO:",
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
        print(
            "GROUP ID:",
            group_id,
            flush=True,
        )
        print(
            "TEXTO:",
            texto,
            flush=True,
        )

        if not group_id:
            print(
                "Group ID não encontrado.",
                flush=True,
            )

            return jsonify(
                {
                    "ok": False,
                    "error": "group_id não encontrado",
                }
            ), 200

        if not texto:
            print(
                "Mensagem de grupo sem texto.",
                flush=True,
            )

            return jsonify({"ok": True}), 200

        resposta = processar_texto_recebido(texto)

        print(
            "RESPOSTA PROCESSADA GRUPO:",
            resposta,
            flush=True,
        )

        enviado = send_group_message(
            group_id=group_id,
            text=resposta,
        )

        return jsonify(
            {
                "ok": enviado,
                "type": "group",
                "group_id": group_id,
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
