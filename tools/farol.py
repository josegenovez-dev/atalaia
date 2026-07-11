import json

from ai import perguntar_ia
from sheets_service import ler_primeira_aba


def preparar_contexto_farol(linhas):
    if not linhas:
        return ""

    linhas_limitadas = linhas[:150]

    return json.dumps(
        linhas_limitadas,
        ensure_ascii=False,
        indent=2,
        default=str,
    )


def consultar_farol(pergunta):
    try:
        print(
            "CONSULTANDO PLANILHA FAROL...",
            flush=True,
        )

        linhas = ler_primeira_aba("farol")

        if not linhas:
            return (
                "A planilha Farol está vazia "
                "ou não retornou dados."
            )

        print(
            "AMOSTRA FAROL:",
            repr(linhas[:3]),
            flush=True,
        )

        contexto_formatado = preparar_contexto_farol(
            linhas
        )

        contexto = f"""
Dados reais obtidos diretamente da aba Farol da planilha
Farol - SoC RJ2:

{contexto_formatado}

Orientações:
- Use somente os dados apresentados.
- Não invente valores.
- As colunas estão identificadas como COLUNA_1, COLUNA_2 etc.
- Algumas primeiras linhas podem conter títulos, horários ou cabeçalhos.
- Identifique a estrutura usando o conteúdo das próprias células.
- Quando um dado não estiver presente, diga claramente.
"""

        return perguntar_ia(
            pergunta=pergunta,
            contexto=contexto,
        )

    except Exception as error:
        print(
            "ERRO FAROL:",
            repr(error),
            flush=True,
        )

        return (
            "Erro ao consultar a planilha Farol:\n\n"
            f"{error}"
        )


def gerar_relatorio_farol():
    return consultar_farol(
        """
Gere um relatório operacional resumido da aba Farol.

Destaque somente quando estiver disponível:
- produção;
- produtividade;
- capacidade;
- ASM;
- Delta;
- T1;
- T2;
- T3;
- volumes;
- desvios;
- pontos de atenção.

Não invente valores.
Organize a resposta em tópicos curtos e objetivos.
""".strip()
    )
