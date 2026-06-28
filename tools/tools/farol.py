from sheets_service import ler_primeira_aba
from ai import perguntar_ia


def consultar_farol(pergunta):
    try:
        linhas = ler_primeira_aba("farol")

        if not linhas:
            return "A planilha Farol está vazia ou não retornou dados."

        contexto = f"""
Dados da aba Farol:
{linhas[:120]}
"""

        return perguntar_ia(pergunta, contexto)

    except Exception as e:
        print("ERRO FAROL:", repr(e))
        return f"Erro ao consultar a planilha Farol: {e}"


def gerar_relatorio_farol():
    return consultar_farol(
        "Gere um relatório operacional resumido da aba Farol. Destaque produção, capacidade, ASM, Delta, T1, T2, T3 e qualquer ponto de atenção."
    )
