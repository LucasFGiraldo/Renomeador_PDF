from pypdf import PdfReader

def ler_pdf(caminho_pdf):
    texto = ""
    leitor = PdfReader(caminho_pdf)

    for pagina in leitor.pages:
        texto += pagina.extract_text()

    return texto