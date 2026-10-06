import os
import re
import shutil
import config


def criar_nome_arquivo(config_usuario, dados_pdf):
    """
    Monta o nome final do arquivo combinando:
      - a parte FIXA (informada pelo usuário no início da execução)
      - as partes VARIÁVEIS (extraídas do conteúdo do PDF), de acordo
        com o que o usuário marcou como "incluir" (S/N).

    Lança ValueError se um campo marcado como obrigatório (S) não foi
    encontrado no PDF - o chamador decide o que fazer (ex.: mover para
    pasta de erro).
    """

    partes = []

    
    if config_usuario.get("incluir_data") == "S":
        data = dados_pdf.get("data")
        if not data:
            raise ValueError(
                "Data não encontrada no PDF (campo marcado como obrigatório)."
            )
        partes.append(data)
        
    if config_usuario.get("incluir_nome") == "S":
        cliente = dados_pdf.get("cliente")
        if not cliente:
            raise ValueError(
                "Nome do favorecido/cliente não encontrado no PDF "
                "(campo marcado como obrigatório)."
            )
        partes.append(cliente)

    if config_usuario.get("incluir_valor") == "S":
        valor = dados_pdf.get("valor")
        if not valor:
            raise ValueError(
                "Valor não encontrado no PDF (campo marcado como obrigatório)."
            )
        partes.append(f"R${valor}")

    partes.append(config_usuario["sufixo"])
    nome_base = "_".join(partes)
    nome_base = _sanitizar(nome_base)

    return nome_base + ".pdf"


def _sanitizar(texto):
    """Remove/normaliza caracteres inválidos para nomes de arquivo no
    Windows e troca espaços por underscore."""
    texto = texto.strip()
    texto = re.sub(r"\s+", "_", texto)
    texto = re.sub(r'[\\/:*?"<>|]', "", texto)
    texto = re.sub(r"_+", "_", texto)
    return texto


def _resolver_duplicado(caminho_destino):
    """Se já existir um arquivo com esse nome em RESULTADOS, acrescenta
    um contador (_2, _3, ...) até achar um nome livre. Isso garante que
    nenhum arquivo seja sobrescrito por engano."""

    if not os.path.exists(caminho_destino):
        return caminho_destino

    base, ext = os.path.splitext(caminho_destino)
    contador = 2

    novo_caminho = f"{base}_{contador}{ext}"
    while os.path.exists(novo_caminho):
        contador += 1
        novo_caminho = f"{base}_{contador}{ext}"

    return novo_caminho


def mover_e_renomear(caminho_original, novo_nome):
    os.makedirs(config.PASTA_RESULTADOS, exist_ok=True)

    destino = os.path.join(config.PASTA_RESULTADOS, novo_nome)
    destino = _resolver_duplicado(destino)

    shutil.move(caminho_original, destino)

    return destino
