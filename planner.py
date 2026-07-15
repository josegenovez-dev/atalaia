import json
import re
import unicodedata

from ai import perguntar_ia
from sheets_service import ler_aba


def normalizar_texto(texto):
    texto = str(texto or "").strip().lower()

    texto = unicodedata.normalize(
        "NFD",
        texto,
    )

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(
            caractere
        ) != "Mn"
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto.strip()


def usuario_pediu_resumo_operacao(
    mensagem,
):
    texto = normalizar_texto(
        mensagem
    )

    palavras_resumo = [
        "resumo",
        "resuma",
        "status",
        "situacao",
        "como esta",
        "como ta",
        "resultado",
        "numeros",
        "indicadores",
    ]

    palavras_operacao = [
        "operacao",
        "farol",
        "processo",
        "turno",
        "dados",
        "planilha",
    ]

    possui_resumo = any(
        palavra in texto
        for palavra in palavras_resumo
    )

    possui_operacao = any(
        palavra in texto
        for palavra in palavras_operacao
    )

    return (
        possui_resumo
        and possui_operacao
    )


def limitar_registros(
    registros,
    limite=500,
):
    if len(registros) <= limite:
        return registros

    return registros[-limite:]


def montar_contexto_farol(
    registros,
):
    registros_limitados = limitar_registros(
        registros
    )

    return json.dumps(
        registros_limitados,
        ensure_ascii=False,
        indent=2,
        default=str,
    )


def gerar_resumo_farol(
    pergunta,
):
    registros = ler_aba(
        nome_planilha="farol",
        nome_aba="Farol",
    )

    if not registros:
        return (
            "A planilha Farol foi consultada, "
            "mas não possui registros para resumir."
        )

    contexto = montar_contexto_farol(
        registros
    )

    instrucao = f"""
A planilha Farol possui {len(registros)} registros.

Analise os dados e apresente um resumo operacional.

Destaque, quando estiver disponível:
- total geral;
- volumes por status;
- pendências;
- concluídos;
- diferenças relevantes;
- pontos de atenção;
- informações mais recentes;
- possíveis riscos operacionais.

Pergunta do usuário:
{pergunta}
""".strip()

    return perguntar_ia(
        pergunta=instrucao,
        contexto=contexto,
    )


def processar_mensagem(
    mensagem,
):
    texto = str(mensagem or "").strip()

    if not texto:
        return (
            "Não recebi nenhuma mensagem "
            "para processar."
        )

    try:
        if usuario_pediu_resumo_operacao(
            texto
        ):
            return gerar_resumo_farol(
                texto
            )

        return perguntar_ia(
            pergunta=texto
        )

    except Exception as error:
        print(
            "ERRO NO PLANNER:",
            repr(error),
            flush=True,
        )

        return (
            "Não consegui concluir a consulta agora.\n\n"
            f"Erro: {error}"
        )
