"""Inspeção manual de um PDF (Passo 2.1 do guia).

Uso: python src/inspecionar.py <arquivo.pdf> [pagina ...]
Sem páginas, mostra o resumo do documento e o texto das três primeiras.
Páginas são numeradas a partir de 1.
"""
import sys

import fitz  # PyMuPDF


def resumo(doc: fitz.Document) -> None:
    print(f"páginas: {doc.page_count}")
    for chave, valor in doc.metadata.items():
        if valor:
            print(f"{chave}: {valor}")
    total_imagens = sum(len(p.get_images()) for p in doc)
    sem_texto = [p.number + 1 for p in doc if not p.get_text().strip()]
    print(f"imagens embutidas: {total_imagens}")
    print(f"páginas sem camada de texto: {sem_texto or 'nenhuma'}")


def pagina(doc: fitz.Document, numero: int) -> None:
    p = doc[numero - 1]
    print(f"\n{'=' * 30} página {numero} {'=' * 30}")
    print(p.get_text())
    for info in p.get_image_info():
        x0, y0, x1, y1 = (round(v) for v in info["bbox"])
        print(f"[imagem bbox=({x0},{y0},{x1},{y1})]")


def main() -> None:
    doc = fitz.open(sys.argv[1])
    paginas = [int(n) for n in sys.argv[2:]]
    if not paginas:
        resumo(doc)
        paginas = [1, 2, 3]
    for n in paginas:
        pagina(doc, n)


if __name__ == "__main__":
    main()
