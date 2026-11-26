"""
Responsável por extrair, do TEXTO do PDF, as informações que variam
de um arquivo para outro (favorecido, data, valor).

O extrator é genérico: não depende do banco, e sim de RÓTULOS
("Nome:", "Valor:", "Data Pagamento:"...) e de CABEÇALHOS de seção
("Favorecido", "Dados de quem recebeu"...). Cada rótulo é procurado
nas três disposições que o pypdf costuma gerar:

1. MESMA LINHA (layout comum):

       Nome: ESCRITORIO EXEMPLO DE ADVOCACIA

2. LINHA DE BAIXO, podendo continuar em mais linhas (ex.: banco XO):

       Nome:

        EMPRESA EXEMPLO PARTICIPACOES E
       NEGOCIOS LTDA

3. INVERTIDA, com o valor colado ANTES do rótulo (ex.: Bradesco):

       JOAO DA SILVA EXEMPLO MENome:

Comprovantes costumam ter DOIS nomes: o de quem pagou (a própria
empresa) e o de quem recebeu. Para pegar o certo, cada "Nome:" é
associado ao cabeçalho de seção mais próximo dele.

Para suportar um banco novo, normalmente basta acrescentar o rótulo
ou o cabeçalho que ele usa nas listas abaixo.

Obs.: alguns PDFs saem com "�" no lugar de letras acentuadas, por
isso os rótulos usam "." no lugar dos acentos (ex.: "Benefici.rio").
"""

import re


# ---------------------------------------------------------------------
# Rótulos e cabeçalhos (em ordem de prioridade)
# ---------------------------------------------------------------------

# Rótulos que, sozinhos, já indicam quem RECEBEU o pagamento
_ROTULOS_FAVORECIDO = [
    r"Raz.o\s+Social\s+Benefici.rio\s+Final",
    r"Nome\s+Fantasia\s+Benefici.rio\s+Final",
    r"Raz.o\s+Social\s+Benefici.rio",
    r"Nome\s+Fantasia\s+Benefici.rio",
    r"Benefici.rio\s+Final",
    r"Benefici.rio",
    r"Nome\s+d[oe]\s+favorecido",
    r"Favorecido",
    r"Nome\s+d[oe]\s+recebedor",
    r"Recebedor",
    r"Destinat.rio",
    r"Concession.ria",
]

# Rótulos genéricos de nome: precisam do cabeçalho da seção para
# saber se é o pagador ou o favorecido
_ROTULOS_NOME = [r"Nome", r"Raz.o\s+Social", r"Cliente"]

# Cabeçalhos de seção (linha sozinha, sem ":")
_CABECALHOS_FAVORECIDO = [
    r"Favorecido",
    r"Dados\s+d[oe]\s+favorecido",
    r"Dados\s+de\s+quem\s+recebeu",
    r"Quem\s+recebeu",
    r"Dados\s+d[oe]\s+recebedor",
    r"Recebedor",
    r"Destinat.rio",
    r"Destino",
    r"Para",
]
_CABECALHOS_PAGADOR = [
    r"Dados\s+d[oe]\s+cliente",
    r"Dados\s+d[oe]\s+pagador",
    r"Dados\s+de\s+quem\s+pagou",
    r"Quem\s+pagou",
    r"Pagador",
    r"Origem",
    r"De",
]

# Data: a de pagamento vem antes da de vencimento/emissão
_ROTULOS_DATA = [
    r"Data\s+(?:d[oae]\s+)?pagamento",
    r"Data\s+(?:d[oae]\s+)?opera..o",
    r"Data\s+(?:d[oae]\s+)?transa..o",
    r"Data\s+(?:d[oae]\s+)?transfer.ncia",
    r"Data\s+(?:d[oae]\s+)?d.bito",
    r"Data\s+(?:d[oae]\s+)?efetiva..o",
    r"Pago\s+em",
    r"Data",
    r"Emiss.o",
    r"Data\s+(?:d[oae]\s+)?vencimento",
    r"Vencimento",
]

# Valor: o efetivamente pago vem antes do valor "de face"
_ROTULOS_VALOR = [
    r"Valor\s+(?:total\s+)?pago",
    r"Total\s+pago",
    r"Valor\s+total",
    r"Valor\s+(?:d[oae]\s+)?pagamento",
    r"Valor\s+(?:d[oae]\s+)?transfer.ncia",
    r"Valor\s+(?:d[oae]\s+)?pix",
    r"Valor\s+(?:d[oae]\s+)?documento",
    r"Valor\s+(?:d[oae]\s+)?boleto",
    r"Valor",
    r"Total",
]

_REGEX_DATA = re.compile(r"(\d{2})[/.-](\d{2})[/.-](\d{4})")
_REGEX_VALOR = re.compile(r"(?<![\d,.])(\d{1,3}(?:\.\d{3})+,\d{2}|\d+,\d{2})(?![\d,])")


# Rótulo quebrado em duas linhas (ex.: boleto do Bradesco):
#     EMPRESA EXEMPLO LTDARazão Social
#     Beneficiário:
_INICIO_ROTULO_QUEBRADO = re.compile(
    r"(Raz.o\s+Social|Nome\s+Fantasia|CPF/CNPJ(\s+Benefici.rio)?)[ \t]*$", re.IGNORECASE
)
_FIM_ROTULO_QUEBRADO = re.compile(
    r"^[ \t]*(Benefici.rio(\s+Final)?|Final|Pagador|Recebedor)[ \t]*:[ \t]*$", re.IGNORECASE
)

# Valores que não identificam ninguém
_SEM_VALOR = re.compile(r"^(n.o\s+informado|-+|n/?a)$", re.IGNORECASE)


def extrair_informacoes(texto):
    texto = _juntar_rotulos_quebrados(texto)
    dados = {}

    cliente = _extrair_cliente(texto)
    if cliente:
        dados["cliente"] = cliente

    data = _extrair_data(texto)
    if data:
        dados["data"] = data

    valor = _extrair_valor(texto)
    if valor:
        dados["valor"] = valor

    return dados


# ---------------------------------------------------------------------
# Campos
# ---------------------------------------------------------------------

def _extrair_cliente(texto):
    # 1) Rótulos que já dizem "isto é o favorecido"
    for rotulo in _ROTULOS_FAVORECIDO:
        for _, valor in _buscar_rotulo(texto, rotulo):
            valor = _limpar(valor)
            if valor:
                return valor

    # 2) "Nome:" genérico, decidido pelo cabeçalho de seção mais próximo
    candidatos = []
    for rotulo in _ROTULOS_NOME:
        for linha, valor in _buscar_rotulo(texto, rotulo):
            valor = _limpar(valor)
            if valor:
                candidatos.append((linha, valor))
    if not candidatos:
        return None

    favorecido = _linhas_cabecalho(texto, _CABECALHOS_FAVORECIDO)
    pagador = _linhas_cabecalho(texto, _CABECALHOS_PAGADOR)
    if favorecido:
        for linha, valor in sorted(candidatos):
            if _distancia(linha, favorecido) < _distancia(linha, pagador):
                return valor
    if pagador:
        # Sem seção de favorecido identificada: descarta só o pagador
        for linha, valor in sorted(candidatos):
            if linha - 1 not in pagador and linha - 2 not in pagador:
                return valor

    return min(candidatos)[1]


def _extrair_data(texto):
    for rotulo in _ROTULOS_DATA:
        for _, valor in _buscar_rotulo(texto, rotulo):
            m = _REGEX_DATA.search(valor)
            if m:
                return "-".join(m.groups())

    # Nenhum rótulo conhecido: usa a primeira data do texto
    m = _REGEX_DATA.search(texto)
    if m:
        return "-".join(m.groups())

    return None


def _extrair_valor(texto):
    for rotulo in _ROTULOS_VALOR:
        for _, valor in _buscar_rotulo(texto, rotulo):
            m = _REGEX_VALOR.search(valor)
            if m:
                return m.group(1)

    return None


# ---------------------------------------------------------------------
# Busca de rótulos nas três disposições
# ---------------------------------------------------------------------

def _buscar_rotulo(texto, rotulo):
    """Devolve [(nº da linha, valor), ...] para cada ocorrência do rótulo."""
    achados = []
    linhas = texto.splitlines()
    rotulo_re = re.compile(rf"^(.*?)(?:{rotulo})[ \t]*:[ \t]*(.*)$", re.IGNORECASE)

    for i, linha in enumerate(linhas):
        m = rotulo_re.match(linha)
        if not m:
            continue
        antes, depois = m.group(1), m.group(2).strip()

        if antes.strip() == "":
            if depois:
                # 1) MESMA LINHA: "Rótulo: valor"
                achados.append((i, depois))
            else:
                # 2) LINHA DE BAIXO: "Rótulo:" e o valor nas próximas linhas
                valor = _valor_nas_linhas_seguintes(linhas, i + 1)
                if valor:
                    achados.append((i, valor))
        elif depois and antes[-1].isspace():
            # 1b) MESMA LINHA, com o rótulo no meio: "... | Rótulo: valor"
            achados.append((i, depois.split(" | ")[0]))
        elif not depois and not antes[-1].isspace():
            # 3) INVERTIDA: "valorRótulo:" (valor colado ao rótulo).
            # Se houver espaço antes do rótulo, ele é só o fim de um
            # rótulo maior (ex.: "Razão Social Beneficiário:").
            achados.append((i, antes))

    return achados


def _valor_nas_linhas_seguintes(linhas, inicio):
    """Pega o valor que fica abaixo de "Rótulo:", juntando as linhas de
    continuação (ex.: nome de empresa quebrado em duas linhas)."""
    i = inicio
    while i < len(linhas) and not linhas[i].strip():
        i += 1
    if i >= len(linhas) or linhas[i].rstrip().endswith(":"):
        return None

    partes = [linhas[i].strip()]
    i += 1
    # Continuação: linha que não começa com espaço (no XO, cabeçalhos
    # como " Favorecido" começam com espaço) e não é outro rótulo
    while (
        i < len(linhas)
        and linhas[i].strip()
        and not linhas[i][0].isspace()
        and not linhas[i].rstrip().endswith(":")
    ):
        partes.append(linhas[i].strip())
        i += 1

    return " ".join(partes)


def _linhas_cabecalho(texto, cabecalhos):
    """Nº das linhas onde aparece um dos cabeçalhos de seção (que podem
    estar quebrados em mais de uma linha, ex.: "Dados de quem\\nrecebeu")."""
    linhas = set()
    for cabecalho in cabecalhos:
        for m in re.finditer(
            rf"^[ \t]*(?:{cabecalho})[ \t]*$", texto, re.IGNORECASE | re.MULTILINE
        ):
            inicio = texto.count("\n", 0, m.start())
            fim = texto.count("\n", 0, m.end())
            linhas.update(range(inicio, fim + 1))
    return linhas


def _distancia(linha, linhas_cabecalho):
    if not linhas_cabecalho:
        return float("inf")
    return min(abs(linha - c) for c in linhas_cabecalho)


def _juntar_rotulos_quebrados(texto):
    linhas = texto.splitlines()
    resultado = []
    i = 0
    while i < len(linhas):
        linha = linhas[i]
        if (
            i + 1 < len(linhas)
            and _INICIO_ROTULO_QUEBRADO.search(linha)
            and _FIM_ROTULO_QUEBRADO.match(linhas[i + 1])
        ):
            linha = linha.rstrip() + " " + linhas[i + 1].strip()
            i += 1
        resultado.append(linha)
        i += 1
    return "\n".join(resultado)


def _limpar(texto):
    # Remove espaços extras e limita o tamanho para não gerar nomes de arquivo absurdamente longos.
    texto = re.sub(r"\s+", " ", texto).strip()
    if _SEM_VALOR.match(texto):
        return None
    return texto[:60].strip()
