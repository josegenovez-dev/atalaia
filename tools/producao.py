from sheets_service import ler_primeira_aba
from ai import perguntar_ia


def consultar_producao_farol(pergunta):
    try:
        linhas = ler_primeira_aba("farol")

        if not linhas:
            return "A planilha Farol está vazia ou não retornou dados."

        contexto = f"""
Dados da planilha Farol:
{linhas[:80]}
"""

        return perguntar_ia(pergunta, contexto)

    except Exception as e:
        print("ERRO PRODUÇÃO FAROL:", repr(e))
        return f"Erro ao consultar a produção na planilha Farol: {e}"
