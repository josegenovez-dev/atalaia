import json
import re

from ai import perguntar_ia
from tools.busca import buscar_codigo
from tools.farol import consultar_farol, gerar_relatorio_farol
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
    match = re.search(
        r"\b[A-Za-z]{2}\d{8,}[A-Za-z0-9]*\b",
        texto,
    )

    if match:
        return match.group(0)

    match = re.search(
        r"\b[A-Za-z0-9\-]*\d[A-Za-z0-9\-]{5,}\b",
        texto,
    )

    return match.group(0) if match else None


def extrair_horario(texto):
    texto_lower = texto.lower()

    match = re.search(
        r"\b([01]?\d|2[0-3])[:h]([0-5]\d)\b",
        texto_lower,
    )

    if match:
        return (
            f"{int(match.group(1)):02d}:"
            f"{match.group(2)}"
        )

    match = re.search(
        r"\b([01]?\d|2[0-3])h\b",
        texto_lower,
    )

    if match:
        return f"{int(match.group(1)):02d}:00"

    return None


def classificar_intencao(texto):
    texto_lower = texto.lower().strip()

    if texto_lower in {
        "status",
        "online",
        "online?",
        "/status",
    }:
        return {
            "tipo": "status",
            "codigo": None,
            "horario": None,
        }

    if texto_lower in {
        "ajuda",
        "/ajuda",
        "menu",
    }:
        return {
            "tipo": "ajuda",
            "codigo": None,
            "horario": None,
        }

    if texto_lower.startswith("/buscar "):
        codigo = texto.split(maxsplit=1)[1].strip()

        return {
            "tipo": "spx",
            "codigo": codigo,
            "horario": None,
        }

    codigo = extrair_codigo(texto)

    if codigo:
        return {
            "tipo": "spx",
            "codigo": codigo,
            "horario": None,
        }

    if any(
        palavra in texto_lower
        for palavra in [
            "relatório",
            "relatorio",
            "resumo",
        ]
    ):
        return {
            "tipo": "relatorio_farol",
            "codigo": None,
            "horario": None,
        }

    if any(
        palavra in texto_lower
        for palavra in [
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
            "t3",
        ]
    ):
        return {
            "tipo": "farol",
            "codigo": None,
            "horario": extrair_horario(texto),
        }

    return {
        "tipo": "conversa",
        "codigo": None,
        "horario": None,
    }


def responder_spx(pergunta, codigo):
    print(
        "CONSULTA SPX SOLICITADA:",
        codigo,
        flush=True,
    )

    dados = consultar_spx(codigo)

    if not isinstance(dados, dict):
        return (
            "A API SPX retornou uma resposta "
            "em formato inesperado."
        )

    if dados.get("erro"):
        return (
            "Erro ao consultar o SPX:\n\n"
            f"{dados['erro']}"
        )

    contexto = f"""
Dados reais consultados diretamente na API SPX.

Código consultado:
{codigo}

Resposta da API:
{json.dumps(dados, ensure_ascii=False, indent=2)}
"""

    return perguntar_ia(
        pergunta=f"""
O usuário perguntou:

{pergunta}

Explique de forma objetiva:
- o status atual;
- a última movimentação;
- a localização, se existir;
- datas e horários disponíveis;
- o histórico mais relevante;
- qualquer possível problema identificado.

Não invente informações.
Use somente os dados enviados no contexto.
""",
        contexto=contexto,
    )


def processar_mensagem(texto):
    texto = str(texto or "").strip()

    if not texto:
        return "Não recebi nenhuma mensagem."

    intencao = classificar_intencao(texto)

    tipo = intencao.get("tipo")
    codigo = intencao.get("codigo")
    horario = intencao.get("horario")

    print(
        "INTENÇÃO:",
        intencao,
        flush=True,
    )

    if tipo == "ajuda":
        return comando_ajuda()

    if tipo == "status":
        return (
            "Status: online.\n"
            "SeaTalk: conectado.\n"
            "Gemini: conectado.\n"
            "Google Sheets: conectado.\n"
            "SPX API: configurada."
        )

    if tipo == "spx":
        return responder_spx(
            pergunta=texto,
            codigo=codigo,
        )

    if tipo == "relatorio_farol":
        return gerar_relatorio_farol()

    if tipo == "farol":
        pergunta = texto

        if horario:
            pergunta += (
                f"\nHorário solicitado: {horario}"
            )

        return consultar_farol(pergunta)

    return perguntar_ia(
        pergunta=texto,
        contexto="",
    )
