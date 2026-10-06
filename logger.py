from datetime import datetime

import config

def registrar_sucesso(arquivo_original, novo_nome):
    data_hora = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    with open(config.ARQUIVO_HISTORICO, "a", encoding="utf-8") as arquivo:
        arquivo.write("\n==============================\n")
        arquivo.write(f"Data/Hora: {data_hora}\n")
        arquivo.write(f"Arquivo Original: {arquivo_original}\n")
        arquivo.write(f"Novo Nome: {novo_nome}\n")
        arquivo.write("Status: RENOMEADO COM SUCESSO\n")

def registrar_erro(arquivo_original, erro):
    data_hora = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    with open(config.ARQUIVO_ERROS, "a", encoding="utf-8") as arquivo:
        arquivo.write("\n==============================\n")
        arquivo.write(f"Data/Hora: {data_hora}\n")
        arquivo.write(f"Arquivo Original: {arquivo_original}\n")
        arquivo.write(f"Erro: {erro}\n")