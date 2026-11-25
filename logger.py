import json
from datetime import datetime
import config

# Além dos .txt (fáceis de ler), cada evento é gravado também como uma
# linha JSON, para a interface conseguir listar e filtrar o histórico.
ARQUIVO_REGISTROS = getattr(config, "ARQUIVO_REGISTROS", "registros.jsonl")


def registrar_sucesso(arquivo_original, novo_nome, dados=None):
    data_hora = datetime.now()

    with open(config.ARQUIVO_HISTORICO, "a", encoding="utf-8") as arquivo:
        arquivo.write("\n==============================\n")
        arquivo.write(f"Data/Hora: {data_hora.strftime('%d-%m-%Y %H:%M:%S')}\n")
        arquivo.write(f"Arquivo Original: {arquivo_original}\n")
        arquivo.write(f"Novo Nome: {novo_nome}\n")
        arquivo.write("Status: RENOMEADO COM SUCESSO\n")

    _registrar_json({
        "data_hora": data_hora.isoformat(timespec="seconds"),
        "status": "sucesso",
        "arquivo_original": arquivo_original,
        "novo_nome": novo_nome,
        "dados": dados or {},
    })


def registrar_erro(arquivo_original, erro, dados=None):
    data_hora = datetime.now()

    with open(config.ARQUIVO_ERROS, "a", encoding="utf-8") as arquivo:
        arquivo.write("\n==============================\n")
        arquivo.write(f"Data/Hora: {data_hora.strftime('%d-%m-%Y %H:%M:%S')}\n")
        arquivo.write(f"Arquivo Original: {arquivo_original}\n")
        arquivo.write(f"Erro: {erro}\n")

    _registrar_json({
        "data_hora": data_hora.isoformat(timespec="seconds"),
        "status": "erro",
        "arquivo_original": arquivo_original,
        "erro": erro,
        "dados": dados or {},
    })


def ler_registros():
    #Lê todos os eventos gravados (mais recentes primeiro).
    registros = []
    try:
        with open(ARQUIVO_REGISTROS, "r", encoding="utf-8") as arquivo:
            for linha in arquivo:
                linha = linha.strip()
                if linha:
                    registros.append(json.loads(linha))
    except FileNotFoundError:
        pass
    registros.reverse()
    return registros


def _registrar_json(registro):
    with open(ARQUIVO_REGISTROS, "a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
