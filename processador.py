# -*- coding: utf-8 -*-

import os

import config_leitor
import leitor_pdf
import extrator
import renomeador
import logger


def processar_pdf(caminho_pdf):
    """
    Processa um único PDF:
      1. Lê as configurações fixas (arquivo config_user.txt)
      2. Extrai o texto do PDF
      3. Extrai as informações variáveis do texto
      4. Monta o novo nome e move o arquivo para PASTA_RESULTADOS
      5. Registra sucesso no histórico

    Em caso de falha, registra o erro em erros.txt e RELANÇA a
    exceção, para que quem chamou (o monitor) decida o que fazer com
    o arquivo (ex.: movê-lo para uma pasta de erro e não ficar
    tentando de novo a cada varredura).
    """

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
