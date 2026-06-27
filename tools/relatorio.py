from sheets_service import ler_primeira_aba
from ai import perguntar_gemini


def gerar_relatorio_farol():
    try:
        linhas = ler_primeira_aba("farol")

        contexto = f"""
Dados da planilha Farol:
{linhas[:80]}
"""

        return perguntar_gemini(
            "Gere um relatório operacional resumido da planilha Farol.",
            contexto
        )

    except Exception as e:
        print("ERRO RELATÓRIO:", repr(e))
        return f"Erro ao gerar relatório: {e}"
