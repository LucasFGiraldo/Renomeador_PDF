import config


def solicitar_configuracoes():
    """
    Solicita ao usuário as configurações fixas do sistema
    e sobrescreve o arquivo config_usuario.txt.
    """

    print("=" * 50)
    print("CONFIGURAÇÃO DO SISTEMA")
    print("=" * 50)

    sufixo = input(
        "Sufixo do nome do arquivo (Ex.: COMP, NF, PIX): "
    ).strip().upper()

    incluir_data = input(
        "Incluir DATA no nome? (S/N): "
    ).strip().upper()

    incluir_valor = input(
        "Incluir VALOR no nome? (S/N): "
    ).strip().upper()

    incluir_nome = input(
        "Incluir NOME do favorecido? (S/N): "
    ).strip().upper()

    with open(
        config.ARQUIVO_CONFIG_USUARIO,
        "w",
        encoding="utf-8"
    ) as arquivo:

        arquivo.write(f"sufixo={sufixo}\n")
        arquivo.write(f"incluir_data={incluir_data}\n")
        arquivo.write(f"incluir_valor={incluir_valor}\n")
        arquivo.write(f"incluir_nome={incluir_nome}\n")

    print("\nConfiguração salva com sucesso.\n")