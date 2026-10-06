import os
import config_leitor
import leitor_pdf
import extrator
import renomeador
import logger


def processar_pdf(caminho_pdf):
    nome_original = os.path.basename(caminho_pdf)
    try:
        config_usuario = config_leitor.ler_config_usuario()

        texto = leitor_pdf.ler_pdf(caminho_pdf)

        dados_pdf = extrator.extrair_informacoes(texto)

        novo_nome = renomeador.criar_nome_arquivo(config_usuario, dados_pdf)

        destino = renomeador.mover_e_renomear(caminho_pdf, novo_nome)

        logger.registrar_sucesso(nome_original, os.path.basename(destino))

        print(f"✔ Arquivo processado: {os.path.basename(destino)}")

        return destino

    except Exception as erro:
        logger.registrar_erro(nome_original, str(erro))
        print(f"✖ Erro ao processar '{nome_original}': {erro}")
        raise
