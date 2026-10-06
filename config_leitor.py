import config


CAMPOS_OBRIGATORIOS = [
    "sufixo",
    "incluir_data",
    "incluir_valor",
    "incluir_nome"
]


def ler_config_usuario():

    configuracoes = {}

    with open(
        config.ARQUIVO_CONFIG_USUARIO,
        "r",
        encoding="utf-8"
    ) as arquivo:

        for linha in arquivo:

            linha = linha.strip()

            if not linha:
                continue

            chave, valor = linha.split("=", 1)

            configuracoes[chave] = valor

    validar(configuracoes)

    return configuracoes


def validar(configuracoes):

    for campo in CAMPOS_OBRIGATORIOS:

        if campo not in configuracoes:

            raise Exception(
                f"Configuração obrigatória ausente: {campo}"
            )