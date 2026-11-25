"""
Usado pelo atalho "Renomeador de PDFs" da Área de Trabalho.

Liga o servidor (api.py) em segundo plano, se ele ainda não estiver
rodando, e abre o sistema no navegador. Rode com pythonw para não
abrir nenhuma janela de terminal.
"""

import os
import subprocess
import sys
import time
import urllib.request
import webbrowser

ENDERECO = "http://localhost:8000/"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def servidor_no_ar():
    try:
        urllib.request.urlopen("http://127.0.0.1:8000/api/status", timeout=2)
        return True
    except Exception:
        return False


if not servidor_no_ar():
    subprocess.Popen(
        [sys.executable, os.path.join(RAIZ, "api.py")],
        cwd=RAIZ,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
    )
    for _ in range(40):
        time.sleep(0.5)
        if servidor_no_ar():
            break

webbrowser.open(ENDERECO)
