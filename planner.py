import json
import re
from ai import perguntar_ia
from tools.producao import consultar_producao_farol
from tools.busca import buscar_codigo
from tools.relatorio import gerar_relatorio_farol


def comando_ajuda():
    return """Pode perguntar normalmente, por exemplo:

- Quanto a esteira produziu até agora?
- Quanto produziu até 9h?
- Como está o Farol?
- Gere um relatório da operação
- Consulte o pedido 123456

Comandos ainda funcionam:
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
    prompt = f"""
Você é o classificador de intenção do Atalaia, assistente operacional de logística.

Responda APENAS em JSON válido, sem markdown.

Tipos possíveis:
- status
- ajuda
- relatorio_farol
- producao_farol
- busca_codigo
- conversa

Regras:
- Se falar de produção, esteira, Farol, produtividade, capacidade, volumes, até agora, até 9h, até 10h: producao_farol.
- Se pedir relatório, resumo operacional, visão geral da operação: relatorio_farol.
- Se tiver código, pedido, LH, tracking ou número específico para consultar: busca_codigo.
- Se perguntar se está online ou status: status.
- Se pedir ajuda/menu: ajuda.
- Caso contrário: conversa.

Formato:
{{
  "tipo": "...",
  "codigo": null,
  "horario": null,
  "texto_original": "..."
}}

Mensagem:
{texto}
"""

    try:
        resposta = perguntar_ia(prompt)
        resposta = resposta.strip()
        resposta = resposta.replace("```json", "").replace("```", "").strip()
        return json.loads(resposta)

    except Exception as e:
        print("ERRO CLASSIFICADOR:", repr(e))

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
            "volumes"
        ]):
            horario = extrair_horario(texto)
            return {"tipo": "producao_farol", "codigo": None, "horario": horario}

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
    horario = intencao.get("horario") or extrair_horario(texto)

    print("INTENÇÃO:", intencao)

    if tipo == "ajuda":
        return comando_ajuda()

    if tipo == "status":
        return "Status: online.\nSeatalk: conectado.\nGroq IA: conectado.\nGoogle Sheets: conectado."

    if tipo == "relatorio_farol":
        return gerar_relatorio_farol()

    if tipo == "producao_farol":
        pergunta = texto

        if horario:
            pergunta += f"\nHorário solicitado: {horario}"

        return consultar_producao_farol(pergunta)

    if tipo == "busca_codigo":
        if not codigo:
            codigo = extrair_codigo(texto)

        if not codigo:
            return "Me envie o código, pedido, LH ou tracking que você quer consultar."

        return buscar_codigo(texto, codigo)

    return perguntar_ia(texto)
