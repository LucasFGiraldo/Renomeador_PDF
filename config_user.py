import config


def solicitar_configuracoes():
    #Solicita ao usuário (no terminal) as configurações fixas do sistema e sobrescreve o arquivo config_user.txt.

    print("=" * 50)
    print("CONFIGURAÇÃO DO SISTEMA")
    print("=" * 50)

    sufixo = input(
        "Sufixo do nome do arquivo (Ex.: COMP, NF, PIX): "
    )

    incluir_data = input(
        "Incluir DATA no nome? (S/N): "
    )

    incluir_valor = input(
        "Incluir VALOR no nome? (S/N): "
    )

    incluir_nome = input(
        "Incluir NOME do favorecido? (S/N): "
    )

    salvar_configuracoes(sufixo, incluir_data, incluir_valor, incluir_nome)

    print("\nConfiguração salva com sucesso.\n")


def salvar_configuracoes(sufixo, incluir_data, incluir_valor, incluir_nome):
    #Grava as configurações no config_user.txt (usado pelo terminal e pela API).

    configuracoes = {
        "sufixo": sufixo.strip().upper(),
        "incluir_data": incluir_data.strip().upper(),
        "incluir_valor": incluir_valor.strip().upper(),
        "incluir_nome": incluir_nome.strip().upper(),
    }

    with open(
        config.ARQUIVO_CONFIG_USUARIO,
        "w",
        encoding="utf-8"
    ) as arquivo:

        for chave, valor in configuracoes.items():
            arquivo.write(f"{chave}={valor}\n")

    return configuracoes
