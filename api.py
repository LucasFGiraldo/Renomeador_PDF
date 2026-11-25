"""
API local (FastAPI) usada pela interface web do Renomeador de PDFs.

Ela reaproveita os mesmos módulos do modo terminal (main.py): o
monitor roda em segundo plano e pode ser ligado/desligado pela tela.

Como rodar:

    python api.py

(ou sem janela, como faz o atalho criado pelo instalar.bat: pythonw api.py)

Documentação interativa (dá para testar cada rota pelo navegador):

    http://localhost:8000/docs
"""

import os
import re
import sys
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

# Os arquivos config_user.txt, historico.txt etc. usam caminhos
# relativos, então a API sempre roda a partir da pasta do projeto.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Sem janela (pythonw) não existe terminal: as mensagens vão para o
# servidor.log. Ao passar de 1 MB, o log antigo vira servidor.log.1.
if sys.stdout is None or sys.stderr is None:
    if os.path.exists("servidor.log") and os.path.getsize("servidor.log") > 1_000_000:
        os.replace("servidor.log", "servidor.log.1")
    _log = open("servidor.log", "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stdout or _log
    sys.stderr = sys.stderr or _log

# Os print() do monitor usam emojis (👀, ✔). Fora de um terminal (ex.:
# saída redirecionada para arquivo), o Windows usa uma codificação sem
# esses caracteres e o print daria erro, derrubando o monitor.
for _fluxo in (sys.stdout, sys.stderr):
    if _fluxo is not None and hasattr(_fluxo, "reconfigure"):
        _fluxo.reconfigure(encoding="utf-8", errors="replace")

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

import config
import config_leitor
import config_user
import logger
import main
import monitor
import processador
import renomeador


@asynccontextmanager
async def _ciclo_de_vida(app):
    threading.Thread(target=_iniciar_automaticamente, daemon=True).start()
    yield


app = FastAPI(
    title="Renomeador de PDFs",
    description="API local da interface do sistema de renomeação de comprovantes.",
    lifespan=_ciclo_de_vida,
)

# Servidor de desenvolvimento do Angular (ng serve)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------
# Modelos (formato dos dados que entram e saem da API)
# ---------------------------------------------------------------------

class Configuracao(BaseModel):
    sufixo: str = Field(min_length=1, max_length=30, examples=["COMP"])
    incluir_data: bool = True
    incluir_valor: bool = True
    incluir_nome: bool = True


class DadosPdf(BaseModel):
    """Campos do comprovante. Na correção manual, os vazios são
    preenchidos com o que for extraído do PDF."""
    cliente: Optional[str] = None
    data: Optional[str] = Field(default=None, examples=["02-02-2026"])
    valor: Optional[str] = Field(default=None, examples=["2.898,00"])

    @field_validator("cliente")
    @classmethod
    def _validar_cliente(cls, valor):
        return valor.strip() or None if valor else None

    @field_validator("data")
    @classmethod
    def _validar_data(cls, valor):
        if not valor or not valor.strip():
            return None
        valor = valor.strip().replace("/", "-").replace(".", "-")
        if not re.fullmatch(r"\d{2}-\d{2}-\d{4}", valor):
            raise ValueError("use o formato DD-MM-AAAA")
        return valor

    @field_validator("valor")
    @classmethod
    def _validar_valor(cls, valor):
        if not valor or not valor.strip():
            return None
        valor = valor.replace("R$", "").strip()
        if not re.fullmatch(r"[\d.]+,\d{2}", valor):
            raise ValueError("use o formato 1.234,56")
        return valor


class PreviaNome(BaseModel):
    configuracao: Optional[Configuracao] = None
    dados: DadosPdf = DadosPdf(
        cliente="EMPRESA EXEMPLO SERVICOS LTDA",
        data="02-02-2026",
        valor="2.898,00",
    )


# ---------------------------------------------------------------------
# Monitor em segundo plano
# ---------------------------------------------------------------------

class _ControleMonitor:
    def __init__(self):
        self._thread = None
        self._parar = threading.Event()
        self.iniciado_em = None
        self.erro = None

    @property
    def ativo(self):
        return self._thread is not None and self._thread.is_alive()

    def iniciar(self):
        if self.ativo:
            return
        main.preparar_pastas()
        self._parar = threading.Event()
        self.erro = None
        self.iniciado_em = datetime.now().isoformat(timespec="seconds")
        self._thread = threading.Thread(target=self._rodar, daemon=True)
        self._thread.start()

    @property
    def parando(self):
        return self.ativo and self._parar.is_set()

    def parar(self):
        # A varredura em andamento termina antes de parar de vez
        self._parar.set()

    def _rodar(self):
        try:
            monitor.monitorar_pasta(parar=self._parar)
        except Exception as erro:
            self.erro = f"O monitor parou: {erro}"


_monitor = _ControleMonitor()


def _iniciar_automaticamente():
    """Ao subir o servidor, já liga o monitor se houver configuração.
    Logo após o login, a unidade de rede (Z:) pode ainda não estar
    conectada: nesse caso tenta de novo a cada 15 segundos."""
    while not _monitor.ativo:
        if _ler_configuracao() is None:
            return
        try:
            _monitor.iniciar()
            print("Monitor iniciado automaticamente.")
            return
        except OSError as erro:
            _monitor.erro = f"Aguardando as pastas ficarem acessíveis: {erro}"
            time.sleep(15)


# ---------------------------------------------------------------------
# Status e monitor
# ---------------------------------------------------------------------

@app.get("/api/status", tags=["Status"])
def status():
    hoje = datetime.now().date().isoformat()
    registros_hoje = [
        r for r in logger.ler_registros() if r["data_hora"].startswith(hoje)
    ]

    return {
        "monitor": {
            "ativo": _monitor.ativo,
            "parando": _monitor.parando,
            "iniciado_em": _monitor.iniciado_em if _monitor.ativo else None,
            "erro": _monitor.erro,
        },
        "configurado": _ler_configuracao() is not None,
        "pastas": {
            "entrada": _info_pasta(config.PASTA_ENTRADA),
            "saida": _info_pasta(config.PASTA_RESULTADOS),
            "erros": _info_pasta(monitor.pasta_erros()),
        },
        "fila": len(monitor.listar_pdfs_pendentes()),
        "com_erro": len(monitor.listar_pdfs_com_erro()),
        "hoje": {
            "sucessos": sum(r["status"] == "sucesso" for r in registros_hoje),
            "erros": sum(r["status"] == "erro" for r in registros_hoje),
        },
    }


@app.post("/api/monitor/iniciar", tags=["Status"])
def iniciar_monitor():
    if _ler_configuracao() is None:
        raise HTTPException(409, "Salve a configuração antes de iniciar o monitor.")
    try:
        _monitor.iniciar()
    except OSError as erro:
        raise HTTPException(500, f"Não foi possível acessar as pastas: {erro}")
    return status()


@app.post("/api/monitor/parar", tags=["Status"])
def parar_monitor():
    _monitor.parar()
    return status()


# ---------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------

@app.get("/api/configuracao", response_model=Configuracao, tags=["Configuração"])
def obter_configuracao():
    configuracao = _ler_configuracao()
    if configuracao is None:
        raise HTTPException(404, "Configuração ainda não foi salva.")
    return configuracao


@app.put("/api/configuracao", response_model=Configuracao, tags=["Configuração"])
def salvar_configuracao(configuracao: Configuracao):
    config_user.salvar_configuracoes(
        configuracao.sufixo,
        _s_n(configuracao.incluir_data),
        _s_n(configuracao.incluir_valor),
        _s_n(configuracao.incluir_nome),
    )
    return _ler_configuracao()


@app.post("/api/configuracao/previa", tags=["Configuração"])
def previa_nome(previa: PreviaNome):
    """Mostra como ficaria o nome do arquivo, sem renomear nada."""
    configuracao = previa.configuracao or _ler_configuracao()
    if configuracao is None:
        raise HTTPException(404, "Configuração ainda não foi salva.")
    try:
        nome = renomeador.criar_nome_arquivo(
            _para_config_usuario(configuracao),
            previa.dados.model_dump(exclude_none=True),
        )
    except ValueError as erro:
        raise HTTPException(422, str(erro))
    return {"nome": nome}


# ---------------------------------------------------------------------
# Histórico
# ---------------------------------------------------------------------

@app.get("/api/historico", tags=["Histórico"])
def historico(
    status: Optional[str] = None,
    busca: Optional[str] = None,
    limite: int = 200,
):
    """Eventos de renomeação, do mais recente para o mais antigo.
    status: "sucesso" ou "erro". busca: trecho do nome do arquivo."""
    registros = logger.ler_registros()
    if status:
        registros = [r for r in registros if r["status"] == status]
    if busca:
        termo = busca.lower()
        registros = [
            r for r in registros
            if termo in r["arquivo_original"].lower()
            or termo in (r.get("novo_nome") or "").lower()
        ]
    return registros[:limite]


# ---------------------------------------------------------------------
# PDFs com erro (correção manual e reprocessamento)
# ---------------------------------------------------------------------

@app.get("/api/erros", tags=["Erros"])
def listar_erros():
    """PDFs que estão hoje na pasta de erros, com o último erro registrado."""
    ultimos_erros = {}
    for registro in logger.ler_registros():
        if registro["status"] == "erro":
            ultimos_erros.setdefault(registro["arquivo_original"], registro)

    itens = []
    for caminho in monitor.listar_pdfs_com_erro():
        arquivo = os.path.basename(caminho)
        registro = ultimos_erros.get(arquivo, {})
        itens.append({
            "arquivo": arquivo,
            "tamanho": os.path.getsize(caminho),
            "modificado_em": datetime.fromtimestamp(
                os.path.getmtime(caminho)
            ).isoformat(timespec="seconds"),
            "erro": registro.get("erro"),
            "dados": registro.get("dados", {}),
        })

    itens.sort(key=lambda item: item["modificado_em"], reverse=True)
    return itens


@app.get("/api/erros/{arquivo}", tags=["Erros"])
def detalhar_erro(arquivo: str):
    """Lê o PDF de novo e mostra o que o extrator encontra nele."""
    caminho = _caminho_pdf_com_erro(arquivo)
    try:
        dados = processador.extrair_dados(caminho)
        leitura = None
    except Exception as erro:
        dados = {}
        leitura = f"Não foi possível ler o PDF: {erro}"
    return {"arquivo": arquivo, "dados": dados, "erro_leitura": leitura}


@app.get("/api/erros/{arquivo}/pdf", tags=["Erros"])
def abrir_pdf_com_erro(arquivo: str):
    """Devolve o próprio PDF, para exibir na tela ao lado do formulário."""
    return FileResponse(
        _caminho_pdf_com_erro(arquivo),
        media_type="application/pdf",
        content_disposition_type="inline",
        filename=arquivo,
    )


@app.post("/api/erros/{arquivo}/reprocessar", tags=["Erros"])
def reprocessar(arquivo: str, dados: Optional[DadosPdf] = None):
    """Tenta renomear de novo. Os campos enviados substituem os extraídos."""
    caminho = _caminho_pdf_com_erro(arquivo)
    if _ler_configuracao() is None:
        raise HTTPException(409, "Salve a configuração antes de reprocessar.")
    try:
        destino = processador.processar_pdf(
            caminho, dados.model_dump(exclude_none=True) if dados else None
        )
    except Exception as erro:
        # O PDF continua na pasta de erros
        raise HTTPException(422, str(erro))
    return {"novo_nome": os.path.basename(destino)}


# ---------------------------------------------------------------------
# Envio de PDFs pela tela
# ---------------------------------------------------------------------

@app.post("/api/pdfs", tags=["Envio"])
async def enviar_pdfs(arquivos: list[UploadFile] = File(...)):
    """Salva os PDFs na pasta de entrada; o monitor cuida do resto."""
    os.makedirs(config.PASTA_ENTRADA, exist_ok=True)
    salvos, recusados = [], []

    for arquivo in arquivos:
        nome = os.path.basename(arquivo.filename or "")
        if not nome.lower().endswith(config.EXTENSAO_MONITORADA):
            recusados.append({"arquivo": nome, "motivo": "Não é um PDF."})
            continue

        destino = renomeador._resolver_duplicado(
            os.path.join(config.PASTA_ENTRADA, nome)
        )
        # Grava com outra extensão e só depois renomeia para .pdf, para
        # o monitor nunca pegar um arquivo pela metade
        temporario = destino + ".enviando"
        with open(temporario, "wb") as saida:
            while bloco := await arquivo.read(1024 * 1024):
                saida.write(bloco)
        os.replace(temporario, destino)
        salvos.append(os.path.basename(destino))

    return {"salvos": salvos, "recusados": recusados}


# ---------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------

def _ler_configuracao():
    try:
        configuracao = config_leitor.ler_config_usuario()
    except Exception:
        # Arquivo ainda não existe ou está incompleto
        return None
    return Configuracao.model_construct(
        sufixo=configuracao["sufixo"],
        incluir_data=configuracao["incluir_data"] == "S",
        incluir_valor=configuracao["incluir_valor"] == "S",
        incluir_nome=configuracao["incluir_nome"] == "S",
    )


def _para_config_usuario(configuracao):
    return {
        "sufixo": configuracao.sufixo.strip().upper(),
        "incluir_data": _s_n(configuracao.incluir_data),
        "incluir_valor": _s_n(configuracao.incluir_valor),
        "incluir_nome": _s_n(configuracao.incluir_nome),
    }


def _s_n(valor):
    return "S" if valor else "N"


def _caminho_pdf_com_erro(arquivo):
    # Aceita só o nome do arquivo, nunca um caminho (evita "..\..\")
    if os.path.basename(arquivo) != arquivo:
        raise HTTPException(400, "Nome de arquivo inválido.")
    caminho = os.path.join(monitor.pasta_erros(), arquivo)
    if not os.path.isfile(caminho):
        raise HTTPException(404, "Arquivo não encontrado na pasta de erros.")
    return caminho


def _info_pasta(caminho):
    return {"caminho": caminho, "acessivel": os.path.isdir(caminho)}


# ---------------------------------------------------------------------
# Interface web (Angular já compilado na pasta "interface")
# ---------------------------------------------------------------------

PASTA_INTERFACE = os.path.abspath("interface")


@app.get("/{caminho:path}", include_in_schema=False)
def interface(caminho: str):
    # Fica por último: só responde o que não for rota da API
    if caminho.startswith("api/"):
        raise HTTPException(404, "Rota não encontrada.")
    indice = os.path.join(PASTA_INTERFACE, "index.html")
    if not os.path.isfile(indice):
        raise HTTPException(
            404, "Interface não encontrada. Rode 'npm run build' na pasta frontend."
        )
    arquivo = os.path.abspath(os.path.join(PASTA_INTERFACE, caminho))
    if (
        caminho
        and os.path.commonpath([arquivo, PASTA_INTERFACE]) == PASTA_INTERFACE
        and os.path.isfile(arquivo)
    ):
        return FileResponse(arquivo)
    # Rotas do Angular (/painel, /erros...) abrem sempre o index.html
    return FileResponse(indice)


if __name__ == "__main__":
    # Só aceita conexões deste computador
    uvicorn.run(app, host="127.0.0.1", port=8000)
