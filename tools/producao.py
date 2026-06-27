from sheets_service import ler_primeira_aba
from ai import perguntar_gemini


def consultar_producao_farol(pergunta):
    try:
        linhas = ler_primeira_aba("farol")

        if not linhas:
            return "A planilha Farol está vazia ou não retornou dados."

        contexto = f"""
Dados recentes da planilha Farol:
{linhas[:50]}
"""

        return perguntar_gemini(
            pergunta,
            contexto
        )

    except Exception as e:
        print("ERRO PRODUÇÃO FAROL:", repr(e))
        return f"Erro ao consultar a produção na planilha Farol: {e}"
