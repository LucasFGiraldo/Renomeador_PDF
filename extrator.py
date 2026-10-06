# -*- coding: utf-8 -*-
"""
Responsável por extrair, do TEXTO do PDF, as informações que variam
de um arquivo para outro (cliente/favorecido, data, valor, etc.).

IMPORTANTE sobre o texto extraído pelo pypdf:
Dependendo de como o PDF foi gerado (tabelas, colunas), o pypdf pode
extrair o texto em ORDEM NORMAL:

    Nome: ADVOCACIA FERNANDO RUDGE LEITE

...ou em ORDEM INVERTIDA, com o valor colado ANTES do rótulo (comum em
comprovantes bancários com layout em tabela/células, como os do
Bradesco):

    ADVOCACIA FERNANDO RUDGE LEITENome:

Por isso, cada campo abaixo tenta primeiro o padrão "normal" e, se não
achar nada, tenta o padrão "invertido".
"""

import re


def extrair_informacoes(texto):
    """
    Recebe o texto extraído do PDF e devolve um dicionário com os
    campos variáveis encontrados. Campos não encontrados simplesmente
    não entram no dicionário (quem decide se isso é erro é o
    renomeador, com base no que o usuário marcou como obrigatório).
    """

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

_CANDIDATOS_CLIENTE = [
    r"Raz[ãa]o\s+Social\s+Benefici[áa]rio",
    r"Nome\s+Fantasia\s+Benefici[áa]rio",
    r"Raz[ãa]o\s+Social\s+Benefici[áa]rio\s+Final",
    r"Nome\s+Fantasia\s+Benefici[áa]rio\s+Final",
    r"Benefici[áa]rio\s+Final",
    r"Benefici[áa]rio",
    r"Concession[áa]ria",
    r"Nome\s+d[oe]\s+favorecido",
    r"Cliente",
    r"Favorecido",
    r"Nome",
]

_LABELS_DATA = r"Data(?:\s+d[aeo]\s+\w+)?|Vencimento|Emiss[ãa]o"
_LABELS_VALOR = r"Valor|Total"


def _extrair_cliente(texto):
    for label in _CANDIDATOS_CLIENTE:
        m = re.search(
            rf"(?:{label})[ \t]*:[ \t]*([^\n\r]+)",
            texto,
            re.IGNORECASE,
        )
        if m:
            valor = _limpar(m.group(1))
            if valor:
                return valor
        m = re.search(
            rf"^(.+?)(?:{label})[ \t]*:[ \t]*$",
            texto,
            re.IGNORECASE | re.MULTILINE,
        )
        if m:
            valor = _limpar(m.group(1))
            if valor:
                return valor

    return None


def _extrair_data(texto):
    m = re.search(
        rf"(?:{_LABELS_DATA})[ \t]*:[ \t]*(\d{{2}}/\d{{2}}/\d{{4}})",
        texto,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).replace("/", "-")
    m = re.search(
        rf"(\d{{2}}/\d{{2}}/\d{{4}})[^\n\r]*?(?:{_LABELS_DATA})[ \t]*:",
        texto,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).replace("/", "-")
    m = re.search(r"(\d{2}/\d{2}/\d{4})", texto)
    if m:
        return m.group(1).replace("/", "-")

    return None


def _extrair_valor(texto):
    m = re.search(
        rf"(?:{_LABELS_VALOR})[ \t]*:?[ \t]*R\$[ \t]*([\d\.,]+)",
        texto,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    m = re.search(
        rf"R\$[ \t]*([\d\.,]+)[ \t]*(?:{_LABELS_VALOR})[ \t]*:?[ \t]*$",
        texto,
        re.IGNORECASE | re.MULTILINE,
    )
    if m:
        return m.group(1).strip()

    return None


def _limpar(texto):
    """Remove espaços nas pontas e limita o tamanho para não gerar
    nomes de arquivo absurdamente longos."""
    texto = texto.strip()
    return texto[:60]
