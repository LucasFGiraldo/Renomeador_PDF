import os
import config_leitor
import leitor_pdf
import extrator
import renomeador
import logger


def processar_pdf(caminho_pdf, dados_manuais=None):
    #dados_manuais: campos digitados pelo usuário (ex.: na interface, ao
    #corrigir um PDF que deu erro). Eles substituem os extraídos do PDF.
    nome_original = os.path.basename(caminho_pdf)
    dados_pdf = {}
    try:
        config_usuario = config_leitor.ler_config_usuario()

        dados_pdf = extrair_dados(caminho_pdf)

        for campo, valor in (dados_manuais or {}).items():
            if valor:
                dados_pdf[campo] = valor

        novo_nome = renomeador.criar_nome_arquivo(config_usuario, dados_pdf)

        destino = renomeador.mover_e_renomear(caminho_pdf, novo_nome)

        logger.registrar_sucesso(nome_original, os.path.basename(destino), dados_pdf)

        print(f"✔ Arquivo processado: {os.path.basename(destino)}")

        return destino

    except Exception as erro:
        logger.registrar_erro(nome_original, str(erro), dados_pdf)
        print(f"✖ Erro ao processar '{nome_original}': {erro}")
        raise


def extrair_dados(caminho_pdf):
    #Lê o PDF e devolve os dados encontrados, sem renomear nada.
    texto = leitor_pdf.ler_pdf(caminho_pdf)
    return extrator.extrair_informacoes(texto)
