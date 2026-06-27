import re
from ai import perguntar_gemini
from tools.producao import consultar_producao_farol
from tools.busca import buscar_codigo
from tools.relatorio import gerar_relatorio_farol


def comando_ajuda():
    return """Comandos disponíveis:

/status
/ajuda
/relatorio
/buscar CÓDIGO
/farol

Perguntas naturais:
- Consultar planilha de Farol
- Ver quanto a esteira produziu até agora
- Gerar relatório da Farol
"""


def extrair_codigo(texto):
    # Só considera código se tiver número
    match = re.search(r"\b[A-Za-z0-9\-]*\d[A-Za-z0-9\-]{3,}\b", texto)
    return match.group(0) if match else None


def processar_mensagem(texto):
    texto = (texto or "").strip()
    texto_lower = texto.lower()

    if not texto:
        return "Não recebi nenhuma mensagem."

    if texto_lower in ["ajuda", "/ajuda", "menu"]:
        return comando_ajuda()

    if texto_lower == "/status" or texto_lower in ["online", "online?", "status"]:
        return "Status: online.\nSeatalk: conectado.\nGemini: conectado.\nGoogle Sheets: conectado."

    if texto_lower in ["/relatorio", "relatorio", "relatório"]:
        return gerar_relatorio_farol()

    if texto_lower.startswith("/buscar"):
        codigo = texto.replace("/buscar", "").strip()
        if not codigo:
            return "Informe o código. Exemplo: /buscar 12345"
        return buscar_codigo(texto, codigo)

    palavras_farol = [
        "farol",
        "esteira",
        "produção",
        "produziu",
        "produzido",
        "produtividade",
        "planilha",
        "até agora",
        "momento"
    ]

    if any(p in texto_lower for p in palavras_farol):
        return consultar_producao_farol(texto)

    codigo = extrair_codigo(texto)

    if codigo:
        return buscar_codigo(texto, codigo)

    return perguntar_gemini(texto)
