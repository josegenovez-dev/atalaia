import json

from ai import perguntar_ia
from sheets_service import ler_primeira_aba


def preparar_contexto_farol(linhas):
    """
    Converte os dados da planilha em texto organizado para o Gemini.
    Aceita lista de listas ou lista de dicionários.
    """

    if not linhas:
        return ""

    # Limita o volume enviado ao Gemini
    linhas_limitadas = linhas[:120]

    try:
        return json.dumps(
            linhas_limitadas,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    except Exception:
        return str(linhas_limitadas)


def consultar_farol(pergunta):
    try:
        print(
            "CONSULTANDO PLANILHA FAROL...",
            flush=True,
        )

        linhas = ler_primeira_aba("farol")

        print(
            "TIPO DOS DADOS DO FAROL:",
            type(linhas).__name__,
            flush=True,
        )

        print(
            "AMOSTRA DOS DADOS DO FAROL:",
            repr(linhas[:3]) if isinstance(linhas, list) else repr(linhas),
            flush=True,
        )

        if not linhas:
            return (
                "A planilha Farol está vazia "
                "ou não retornou dados."
            )

        contexto_formatado = preparar_contexto_farol(linhas)

        contexto = f"""
Dados reais obtidos diretamente da primeira aba da planilha Farol:

{contexto_formatado}

Orientações:
- Use somente os dados acima.
- Não invente valores.
- Identifique corretamente os cabeçalhos e suas respectivas linhas.
- Caso os dados estejam em formato de lista, considere a primeira linha como cabeçalho.
"""

        resposta = perguntar_ia(
            pergunta=pergunta,
            contexto=contexto,
        )

        return resposta

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

Destaque, quando estiverem disponíveis:
- produção;
- capacidade;
- produtividade;
- ASM;
- Delta;
- T1;
- T2;
- T3;
- desvios;
- pontos de atenção.

Não invente valores e deixe claro quando alguma informação
não estiver presente nos dados.
""".strip()
    )
