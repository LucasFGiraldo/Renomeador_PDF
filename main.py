import os
import config
import config_user
import monitor


def preparar_pastas():
    """Garante que as pastas necessárias existam antes de iniciar o
    monitoramento."""

    os.makedirs(config.PASTA_RESULTADOS, exist_ok=True)

    if not os.path.isdir(config.PASTA_ENTRADA):
        print(f"⚠ A pasta de entrada não existe, criando: {config.PASTA_ENTRADA}")
        os.makedirs(config.PASTA_ENTRADA, exist_ok=True)

def main():
    print("=" * 50)
    print("SISTEMA DE RENOMEAÇÃO AUTOMÁTICA DE PDFs")
    print("=" * 50)
    print()

    # Sempre solicita/atualiza as informações fixas no início da execução
    config_user.solicitar_configuracoes()

    preparar_pastas()

    monitor.monitorar_pasta()


if __name__ == "__main__":
    main()
