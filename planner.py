import re
import json
from ai import perguntar_ia
from tools.farol import consultar_farol, gerar_relatorio_farol
from tools.busca import buscar_codigo
from tools.spx import consultar_spx


def comando_ajuda():
    return """Pode perguntar normalmente:

- Quanto a ASM produziu?
- Qual a produtividade da ASM?
- Como está o Farol?
- Consulte BR269457066877P
- Onde está o pacote BR269457066877P?
- Gere um relatório da operação

Comandos:
/status
/ajuda
/relatorio
/buscar CÓDIGO
"""


def extrair_codigo(texto):
    match = re.search(r"\b[A-Za-z]{2}\d{8,}[A-Za-z0-9]*\b", texto)
    if match:
        return match.group(0)

    match = re.search(r"\b[A-Za-z0-9\-]*\d[A-Za-z0-9\-]{5,}\b", texto)
    return match.group(0) if match else None


def extrair_horario(texto):
    texto_lower = texto.lower()

    match = re.search(r"\b([01]?\d|2[0-3])[:h]([0-5]\d)\b", texto_lower)
    if match:
        return f"{int(match.group(1)):02d}:{match.group(2)}"

    match = re.search(r"\b([01]?\d|2[0-3])h\b", texto_lower)
    if match:
        return f"{int(match.group(1)):02d}:00"

    return None


def classificar_intencao(texto):
    texto_lower = texto.lower()

    if texto_lower in ["status", "online", "online?", "/status"]:
        return {"tipo": "status", "codigo": None, "horario": None}

    if texto_lower in ["ajuda", "/ajuda", "menu"]:
        return {"tipo": "ajuda", "codigo": None, "horario": None}

    codigo = extrair_codigo(texto)

    if codigo:
        return {"tipo": "spx", "codigo": codigo, "horario": None}

    if any(p in texto_lower for p in ["relatório", "relatorio", "resumo"]):
        return {"tipo": "relatorio_farol", "codigo": None, "horario": None}

    if any(p in texto_lower for p in [
        "farol", "esteira", "produção", "produziu",
        "produtividade", "capacidade", "volume",
        "volumes", "asm", "delta", "t1", "t2", "t3"
    ]):
        return {
            "tipo": "farol",
            "codigo": None,
            "horario": extrair_horario(texto)
        }

    return {"tipo": "conversa", "codigo": None, "horario": None}


def responder_spx(pergunta, codigo):
    dados = consultar_spx(codigo)

    if "erro" in dados:
        return f"Erro ao consultar o SPX:\n\n{dados['erro']}"

    contexto = f"""
Dados consultados diretamente no SPX:

{json.dumps(dados, ensure_ascii=False, indent=2)}
"""

    return perguntar_ia(
        f"""
O usuário perguntou:

{pergunta}

Responda como o Atalaia, de forma objetiva para um operador logístico.
Explique o status do pacote, informações principais e histórico se existir.
Não invente dados.
""",
        contexto
    )


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
        return "Status: online.\nSeatalk: conectado.\nGemini: conectado.\nGoogle Sheets: conectado.\nSPX API: configurada."

    if tipo == "spx":
        return responder_spx(texto, codigo)

    if tipo == "relatorio_farol":
        return gerar_relatorio_farol()

    if tipo == "farol":
        pergunta = texto

        if horario:
            pergunta += f"\nHorário solicitado: {horario}"

        return consultar_farol(pergunta)

    return perguntar_ia(texto)
