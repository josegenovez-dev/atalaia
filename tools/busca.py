import json
from sheets_service import buscar_texto_em_tudo
from ai import perguntar_gemini


def buscar_codigo(pergunta, codigo):
    resultados = buscar_texto_em_tudo(codigo)

    if not resultados:
        return f"Não encontrei nada para: {codigo}"

    contexto = json.dumps(
        resultados[:10],
        ensure_ascii=False,
        indent=2
    )

    return perguntar_gemini(pergunta, contexto)
