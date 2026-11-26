# Modelo do config.py (o config.py verdadeiro não vai para o GitHub).
#
# Como usar:
#   1. Copie este arquivo e renomeie a cópia para config.py
#   2. Troque os caminhos abaixo pelos caminhos reais das pastas
#   3. Rode o instalar.bat (ou reinicie o sistema, se já estiver instalado)
#
# Normalmente só os caminhos precisam ser alterados.

# Pasta monitorada (onde os PDFs são colados)
PASTA_ENTRADA = r"C:\Exemplo\RENOMEACAO\ENTRADA"

# Pasta onde os PDFs já renomeados são colocados
PASTA_RESULTADOS = r"C:\Exemplo\RENOMEACAO\SAIDA"

# Nome da subpasta (dentro de PASTA_ENTRADA) para os PDFs que deram erro
PASTA_ERROS_PDF = "ERROS"

# ---------------------------------------------------------------------
# Daqui para baixo não é preciso mudar nada
# ---------------------------------------------------------------------

ARQUIVO_CONFIG_USUARIO = "config_user.txt"
ARQUIVO_HISTORICO = "historico.txt"
ARQUIVO_ERROS = "erros.txt"

# Segundos de espera para o arquivo terminar de ser copiado
TEMPO_ESPERA_ARQUIVO = 2

# De quantos em quantos segundos a pasta de entrada é verificada
INTERVALO_MONITORAMENTO = 3

EXTENSAO_MONITORADA = ".pdf"
