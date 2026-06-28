import json
import re
from ai import perguntar_ia
from tools.farol import consultar_farol, gerar_relatorio_farol
from tools.busca import buscar_codigo


def comando_ajuda():
    return """Pode perguntar normalmente, por exemplo:

- Quanto a ASM produziu?
- Qual a produtividade da ASM?
- Quanto a esteira produziu até 9h?
- Como está o Farol?
- Gere um relatório da operação
- Consulte o pedido 123456

Comandos:
/status
/ajuda
/relatorio
/buscar CÓDIGO
"""


def extrair_codigo(texto):
    match = re.search(r"\b[A-Za-z0-9\-]*\d[A-Za-z0-9\-]{3,}\b", texto)
    return match.group(0) if match else None


def extrair_horario(texto):
    texto_lower = texto.lower()

    match = re.search(r"\b([01]?\d|2[0-3])[:h]([0-5]\d)\b", texto_lower)
    if match:
        return f"{int(match.group(1)):02d}:{match.group(2)}"

    match = re.search(r"\b([01]?\d|2[0-3])h\b", texto_lower)
    if match:
        return f"{int(match.group(1)):02d}:00"

    match = re.search(r"\bàs?\s*([01]?\d|2[0-3])\b", texto_lower)
    if match:
        return f"{int(match.group(1)):02d}:00"

    return None


def classificar_intencao(texto):
    texto_lower = texto.lower()

    if texto_lower in ["status", "online", "online?", "/status"]:
        return {"tipo": "status", "codigo": None, "horario": None}

    if texto_lower in ["ajuda", "/ajuda", "menu"]:
        return {"tipo": "ajuda", "codigo": None, "horario": None}

    if any(p in texto_lower for p in ["relatório", "relatorio", "resumo"]):
        return {"tipo": "relatorio_farol", "codigo": None, "horario": None}

    if any(p in texto_lower for p in [
        "farol",
        "esteira",
        "produção",
        "produziu",
        "produtividade",
        "capacidade",
        "volume",
        "volumes",
        "asm",
        "delta",
        "t1",
        "t2",
        "t3"
    ]):
        return {
            "tipo": "farol",
            "codigo": None,
            "horario": extrair_horario(texto)
        }

    codigo = extrair_codigo(texto)

    if codigo:
        return {"tipo": "busca_codigo", "codigo": codigo, "horario": None}

    return {"tipo": "conversa", "codigo": None, "horario": None}


def processar_mensagem(texto):
    texto = (texto or "").strip()

    if not texto:
        return "Não recebi nenhuma mensagem."

    intencao = classificar_intencao(texto)

    tipo = intencao.get("tipo")
    codigo = intencao.get("codigo")
    horario = intencao.get("horario")

    print("INTENÇÃO:", intencao)

    if tipo == "ajuda":
        return comando_ajuda()

    if tipo == "status":
        return "Status: online.\nSeatalk: conectado.\nGemini: conectado.\nGoogle Sheets: conectado."

    if tipo == "relatorio_farol":
        return gerar_relatorio_farol()

    if tipo == "farol":
        pergunta = texto

        if horario:
            pergunta += f"\nHorário solicitado: {horario}"

        return consultar_farol(pergunta)

    if tipo == "busca_codigo":
        return buscar_codigo(texto, codigo)

    return perguntar_ia(texto)
