from sheets_service import ler_primeira_aba
from ai import perguntar_ia


def gerar_relatorio_farol():
    try:
        linhas = ler_primeira_aba("farol")

        if not linhas:
            return "A planilha Farol está vazia ou não retornou dados."

        contexto = f"""
Dados da planilha Farol:
{linhas[:100]}
"""

        return perguntar_ia(
            "Gere um relatório operacional resumido da planilha Farol.",
            contexto
        )

    except Exception as e:
        print("ERRO RELATÓRIO FAROL:", repr(e))
        return f"Erro ao gerar relatório da Farol: {e}"
