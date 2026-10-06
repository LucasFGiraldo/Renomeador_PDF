# -*- coding: utf-8 -*-

# Pasta monitorada (Servidor)
PASTA_ENTRADA = r"Z:\RENOMEAÇÃO ARQUIVOS (não mexer)\ENTRADA"

# Pasta onde ficarão os arquivos renomeados
PASTA_RESULTADOS = r"Z:\RENOMEAÇÃO ARQUIVOS (não mexer)\SAÍDA"

# Subpasta (dentro da PASTA_ENTRADA) para onde vão os PDFs que
# não puderam ser processados (erro de leitura/extração)
PASTA_ERROS_PDF = r"Z:\RENOMEAÇÃO ARQUIVOS (não mexer)\SAÍDA\ERRO_PROCESSAMENTO"

# Arquivos do sistema
ARQUIVO_CONFIG_USUARIO = "config_user.txt"
ARQUIVO_HISTORICO = "historico.txt"
ARQUIVO_ERROS = "erros.txt"

# Tempo (segundos) que o arquivo precisa manter o mesmo tamanho
# para ser considerado "estável" (cópia/upload concluído)
TEMPO_ESPERA_ARQUIVO = 2

# Intervalo (segundos) entre cada varredura da pasta de entrada
INTERVALO_MONITORAMENTO = 3

# Extensão monitorada
EXTENSAO_MONITORADA = ".pdf"
