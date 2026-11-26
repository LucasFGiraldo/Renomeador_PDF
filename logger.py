"""
Histórico de renomeações, gravado num banco SQLite (historico.db).

O SQLite já vem com o Python: não é preciso instalar nada. Para
consultar o banco fora do sistema, use qualquer visualizador de SQLite
(ex.: DB Browser for SQLite) ou a tela Histórico da interface.

Versões anteriores gravavam em historico.txt, erros.txt e
registros.jsonl. Na primeira vez que o banco é criado, esses arquivos
são importados para ele (e continuam na pasta, sem uso).
"""

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime

import config

ARQUIVO_BANCO = getattr(config, "ARQUIVO_BANCO", "historico.db")

_TABELA = """
CREATE TABLE IF NOT EXISTS registros (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora        TEXT NOT NULL,      -- ISO: 2026-11-25T13:23:38
    status           TEXT NOT NULL CHECK (status IN ('sucesso', 'erro')),
    arquivo_original TEXT NOT NULL,
    novo_nome        TEXT,               -- só em sucesso
    erro             TEXT,               -- só em erro
    cliente          TEXT,               -- dados lidos do PDF
    data             TEXT,
    valor            TEXT
);
CREATE INDEX IF NOT EXISTS idx_registros_data_hora ON registros (data_hora);
"""

# O monitor e a interface gravam ao mesmo tempo, em threads diferentes
_trava = threading.Lock()
_banco_pronto = None


def registrar_sucesso(arquivo_original, novo_nome, dados=None):
    _inserir("sucesso", arquivo_original, dados, novo_nome=novo_nome)


def registrar_erro(arquivo_original, erro, dados=None):
    _inserir("erro", arquivo_original, dados, erro=erro)


def buscar_registros(status=None, busca=None, limite=200):
    """Eventos do mais recente para o mais antigo.
    status: "sucesso" ou "erro"; busca: trecho do nome do arquivo."""
    sql = "SELECT * FROM registros WHERE 1 = 1"
    parametros = []
    if status:
        sql += " AND status = ?"
        parametros.append(status)
    if busca:
        sql += " AND (arquivo_original LIKE ? OR novo_nome LIKE ?)"
        parametros += [f"%{busca}%", f"%{busca}%"]
    sql += " ORDER BY data_hora DESC, id DESC LIMIT ?"
    parametros.append(limite)

    with _conectar() as conexao:
        return [_para_dict(linha) for linha in conexao.execute(sql, parametros)]


def contar_do_dia(dia=None):
    """Quantidade de sucessos e erros de um dia (padrão: hoje)."""
    dia = dia or datetime.now().date().isoformat()
    with _conectar() as conexao:
        contagem = dict(conexao.execute(
            "SELECT status, COUNT(*) FROM registros"
            " WHERE data_hora LIKE ? GROUP BY status",
            [f"{dia}%"],
        ).fetchall())
    return {"sucessos": contagem.get("sucesso", 0), "erros": contagem.get("erro", 0)}


def ultimo_erro_por_arquivo():
    """{nome do arquivo: último registro de erro dele}"""
    with _conectar() as conexao:
        linhas = conexao.execute(
            "SELECT * FROM registros WHERE status = 'erro'"
            " ORDER BY data_hora, id"
        ).fetchall()
    # Os mais recentes sobrescrevem os mais antigos
    return {linha["arquivo_original"]: _para_dict(linha) for linha in linhas}


# ---------------------------------------------------------------------
# Banco
# ---------------------------------------------------------------------

def _inserir(status, arquivo_original, dados, novo_nome=None, erro=None):
    dados = dados or {}
    with _conectar() as conexao:
        conexao.execute(
            "INSERT INTO registros (data_hora, status, arquivo_original,"
            " novo_nome, erro, cliente, data, valor)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                datetime.now().isoformat(timespec="seconds"), status,
                arquivo_original, novo_nome, erro,
                dados.get("cliente"), dados.get("data"), dados.get("valor"),
            ],
        )


@contextmanager
def _conectar():
    """Abre o banco (criando e importando o histórico antigo na 1ª vez).
    Ao sair do "with", confirma a gravação e fecha a conexão."""
    global _banco_pronto
    with _trava:
        if _banco_pronto != ARQUIVO_BANCO:
            novo = not os.path.exists(ARQUIVO_BANCO)
            conexao = _abrir()
            conexao.executescript(_TABELA)
            if novo:
                _importar_arquivos_antigos(conexao)
            conexao.commit()
            conexao.close()
            _banco_pronto = ARQUIVO_BANCO
    conexao = _abrir()
    try:
        yield conexao
        conexao.commit()
    finally:
        conexao.close()


def _abrir():
    conexao = sqlite3.connect(ARQUIVO_BANCO, timeout=10)
    conexao.row_factory = sqlite3.Row
    return conexao


def _para_dict(linha):
    registro = {
        "data_hora": linha["data_hora"],
        "status": linha["status"],
        "arquivo_original": linha["arquivo_original"],
        "dados": {
            campo: linha[campo]
            for campo in ("cliente", "data", "valor")
            if linha[campo]
        },
    }
    if linha["status"] == "sucesso":
        registro["novo_nome"] = linha["novo_nome"]
    else:
        registro["erro"] = linha["erro"]
    return registro


# ---------------------------------------------------------------------
# Importação do histórico em texto (versões anteriores)
# ---------------------------------------------------------------------

def _importar_arquivos_antigos(conexao):
    # Os .txt têm todos os eventos; o .jsonl (só da época da interface)
    # completa com os dados lidos do PDF
    dados_jsonl = _ler_jsonl(getattr(config, "ARQUIVO_REGISTROS", "registros.jsonl"))
    registros = (
        _ler_txt(getattr(config, "ARQUIVO_HISTORICO", "historico.txt"), "sucesso")
        + _ler_txt(getattr(config, "ARQUIVO_ERROS", "erros.txt"), "erro")
    )
    registros.sort(key=lambda r: r["data_hora"])

    for r in registros:
        dados = dados_jsonl.get((r["data_hora"], r["status"], r["arquivo_original"]), {})
        conexao.execute(
            "INSERT INTO registros (data_hora, status, arquivo_original,"
            " novo_nome, erro, cliente, data, valor)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                r["data_hora"], r["status"], r["arquivo_original"],
                r.get("novo_nome"), r.get("erro"),
                dados.get("cliente"), dados.get("data"), dados.get("valor"),
            ],
        )
    if registros:
        print(f"Histórico antigo importado para {ARQUIVO_BANCO}: {len(registros)} registros.")


def _ler_txt(caminho, status):
    """Lê os blocos gravados pelo logger antigo:

        ==============================
        Data/Hora: 25-11-2026 13:23:38
        Arquivo Original: comprovante.pdf
        Novo Nome: 02-02-2026_..._COMP.pdf     (ou "Erro: ...")
    """
    try:
        conteudo = open(caminho, encoding="utf-8").read()
    except FileNotFoundError:
        return []

    registros = []
    for bloco in conteudo.split("=" * 30):
        campos = {}
        chave = None
        for linha in bloco.strip().splitlines():
            if ": " in linha and linha.split(": ", 1)[0] in (
                "Data/Hora", "Arquivo Original", "Novo Nome", "Erro", "Status"
            ):
                chave, valor = linha.split(": ", 1)
                campos[chave] = valor
            elif chave == "Erro":
                campos["Erro"] += "\n" + linha  # mensagem com várias linhas
        if "Data/Hora" not in campos or "Arquivo Original" not in campos:
            continue
        try:
            data_hora = datetime.strptime(campos["Data/Hora"], "%d-%m-%Y %H:%M:%S")
        except ValueError:
            continue
        registros.append({
            "data_hora": data_hora.isoformat(timespec="seconds"),
            "status": status,
            "arquivo_original": campos["Arquivo Original"],
            "novo_nome": campos.get("Novo Nome"),
            "erro": campos.get("Erro"),
        })
    return registros


def _ler_jsonl(caminho):
    dados = {}
    try:
        for linha in open(caminho, encoding="utf-8"):
            if linha.strip():
                r = json.loads(linha)
                dados[(r["data_hora"], r["status"], r["arquivo_original"])] = r.get("dados") or {}
    except (FileNotFoundError, ValueError, KeyError):
        pass
    return dados
