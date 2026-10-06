# -*- coding: utf-8 -*-

import os
import time
import shutil

import config
import processador


def _arquivo_esta_estavel(caminho):
    """
    Verifica se o arquivo parou de ser copiado/gravado na pasta,
    comparando o tamanho em dois instantes. Isso evita tentar ler um
    PDF que ainda está sendo colado na pasta (arquivo incompleto).
    """
    try:
        tamanho1 = os.path.getsize(caminho)
        time.sleep(config.TEMPO_ESPERA_ARQUIVO)
        tamanho2 = os.path.getsize(caminho)
        return tamanho1 == tamanho2 and tamanho1 > 0
    except (FileNotFoundError, PermissionError, OSError):
        # Arquivo pode ter sumido/estar bloqueado entre as duas checagens
        return False


def _mover_para_pasta_erro(caminho_pdf):
    """Move um PDF que falhou no processamento para uma subpasta
    dentro da própria PASTA_ENTRADA, evitando que ele seja
    reprocessado (e re-logado como erro) a cada nova varredura."""

    pasta_erro = os.path.join(config.PASTA_ENTRADA, config.PASTA_ERROS_PDF)
    os.makedirs(pasta_erro, exist_ok=True)

    destino = os.path.join(pasta_erro, os.path.basename(caminho_pdf))

    # Evita sobrescrever se já existir um arquivo de mesmo nome na pasta de erro
    base, ext = os.path.splitext(destino)
    contador = 2
    while os.path.exists(destino):
        destino = f"{base}_{contador}{ext}"
        contador += 1

    try:
        shutil.move(caminho_pdf, destino)
    except Exception as erro:
        print(f"✖ Não foi possível mover '{caminho_pdf}' para a pasta de erro: {erro}")


def _listar_pdfs_pendentes():
    """Lista os PDFs na PASTA_ENTRADA, ignorando a subpasta de erro."""

    if not os.path.isdir(config.PASTA_ENTRADA):
        return []

    pendentes = []
    for nome in os.listdir(config.PASTA_ENTRADA):
        if nome == config.PASTA_ERROS_PDF:
            continue

        if not nome.lower().endswith(config.EXTENSAO_MONITORADA):
            continue

        caminho = os.path.join(config.PASTA_ENTRADA, nome)
        if os.path.isfile(caminho):
            pendentes.append(caminho)

    return pendentes


def processar_pasta_uma_vez():
    """Faz uma única varredura da pasta de entrada, processando todos
    os PDFs estáveis encontrados no momento."""

    if not os.path.isdir(config.PASTA_ENTRADA):
        print(f"✖ Pasta de entrada não encontrada: {config.PASTA_ENTRADA}")
        return

    for caminho_pdf in _listar_pdfs_pendentes():

        if not _arquivo_esta_estavel(caminho_pdf):
            # Ainda sendo copiado/colado na pasta - tenta de novo na próxima varredura
            continue

        try:
            processador.processar_pdf(caminho_pdf)
        except Exception:
            # processador já registrou o erro em erros.txt
            _mover_para_pasta_erro(caminho_pdf)


def monitorar_pasta(intervalo=None):
    """Loop contínuo: varre a pasta de entrada a cada `intervalo`
    segundos, processando novos PDFs conforme chegam. Roda até o
    usuário interromper com CTRL+C."""

    intervalo = intervalo or config.INTERVALO_MONITORAMENTO

    print(f"👀 Monitorando pasta: {config.PASTA_ENTRADA}")
    print(f"📁 Arquivos renomeados irão para: {config.PASTA_RESULTADOS}")
    print("Pressione CTRL+C para encerrar.\n")

    try:
        while True:
            processar_pasta_uma_vez()
            time.sleep(intervalo)
    except KeyboardInterrupt:
        print("\nMonitoramento encerrado pelo usuário.")
