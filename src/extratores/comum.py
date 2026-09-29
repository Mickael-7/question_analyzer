"""Funções de extração independentes de fonte."""
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass

import pymupdf

# Caracteres da área de uso privado: aparecem quando fórmulas do MathType
# ou fontes de símbolos são extraídas como texto.
USO_PRIVADO = re.compile(r"[-]")
MARCADOR_ALTERNATIVA = r"(?:^|\s)\(?{letra}\)\s*"


@dataclass
class Linha:
    pagina: int  # a partir de 1
    y0: float
    y1: float
    texto: str


@dataclass
class Imagem:
    pagina: int
    y0: float
    y1: float
    xref: int

    @property
    def y_centro(self) -> float:
        return (self.y0 + self.y1) / 2


FLAG_SOBRESCRITO = 1
SOBRESCRITOS = str.maketrans("0123456789+-–()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻⁽⁾ⁿ")
RE_DENOMINADOR = re.compile(r"^\d{1,3}$")
TOLERANCIA_BASE = 3.0  # pontos; linhas com base mais próxima que isso estão na mesma altura


def _texto_span(span: dict) -> str:
    texto = span["text"]
    if span["flags"] & FLAG_SOBRESCRITO and texto.strip():
        convertido = texto.translate(SOBRESCRITOS)
        return convertido if convertido != texto or not texto.isalpha() else f"^{texto}"
    return texto


def _centro_x(bbox) -> float:
    return (bbox[0] + bbox[2]) / 2


def _juntar_fracoes(linhas: list[dict]) -> int:
    """Funde frações empilhadas em "numerador/denominador".

    O denominador vem como uma linha isolada só com dígitos, logo abaixo do
    numerador e centralizado com ele. Altera `linhas` e devolve quantas fundiu.
    """
    fundidas = 0
    for den in [l for l in linhas if len(l["spans"]) == 1]:
        texto_den = den["spans"][0]["text"].strip()
        if not RE_DENOMINADOR.match(texto_den):
            continue
        for num_linha in linhas:
            if num_linha is den or num_linha.get("removida"):
                continue
            for span in num_linha["spans"]:
                texto_num = span["text"].strip()
                if (
                    RE_DENOMINADOR.match(texto_num)
                    and "/" not in span["text"]
                    and abs(_centro_x(span["bbox"]) - _centro_x(den["bbox"])) < 4
                    and 0 <= den["bbox"][1] - span["bbox"][1] < 20
                    and den["bbox"][1] > span["bbox"][1] + 5
                ):
                    span["text"] = span["text"].replace(texto_num, f"{texto_num}/{texto_den}", 1)
                    den["removida"] = True
                    fundidas += 1
                    break
            if den.get("removida"):
                break
    return fundidas


def ler_linhas(
    doc: pymupdf.Document, paginas: range, ignorar: set[str], duas_colunas: bool = False
) -> list[Linha]:
    """Linhas de texto em ordem de leitura, sem as linhas vazias e sem as de `ignorar`.

    Expoentes marcados como sobrescritos viram caracteres sobrescritos (x²),
    frações empilhadas viram "a/b", e a ordem segue a base das linhas, para que
    o numerador de uma fração não passe à frente do texto da mesma linha.
    Com `duas_colunas`, lê a coluna esquerda inteira antes da direita.
    """
    linhas = []
    for n in paginas:
        pagina = doc[n - 1]
        meio = pagina.rect.width / 2
        brutas = [
            {"bbox": linha["bbox"], "spans": [dict(s) for s in linha["spans"]]}
            for bloco in pagina.get_text("dict")["blocks"]
            for linha in bloco.get("lines", [])
        ]
        _juntar_fracoes(brutas)
        da_pagina = []
        for linha in brutas:
            if linha.get("removida"):
                continue
            texto = "".join(_texto_span(s) for s in linha["spans"]).strip()
            if texto and texto not in ignorar:
                x0, y0, x1, y1 = linha["bbox"]
                coluna = int((x0 + x1) / 2 >= meio) if duas_colunas else 0
                da_pagina.append((coluna, y1, x0, Linha(n, y0, y1, texto)))
        da_pagina.sort(key=lambda t: (t[0], t[1]))
        linhas += _ordenar_por_base(da_pagina)
    return linhas


def _ordenar_por_base(da_pagina: list[tuple]) -> list[Linha]:
    """Agrupa linhas com a mesma base (dentro da tolerância) e ordena cada grupo por x."""
    grupos: list[list[tuple]] = []
    for item in da_pagina:
        coluna, base = item[0], item[1]
        if grupos and grupos[-1][0][0] == coluna and base - grupos[-1][0][1] < TOLERANCIA_BASE:
            grupos[-1].append(item)
        else:
            grupos.append([item])
    return [item[3] for grupo in grupos for item in sorted(grupo, key=lambda t: t[2])]


def xrefs_recorrentes(doc: pymupdf.Document, fracao: float = 0.5) -> set[int]:
    """Imagens presentes em mais de `fracao` das páginas (logotipos, cabeçalhos)."""
    contagem = Counter(
        xref for pagina in doc for xref in {img[0] for img in pagina.get_images()}
    )
    return {xref for xref, n in contagem.items() if n > fracao * doc.page_count}


def ler_imagens(doc: pymupdf.Document, paginas: range, ignorar_xrefs: set[int]) -> list[Imagem]:
    imagens = []
    for n in paginas:
        for info in doc[n - 1].get_image_info(xrefs=True):
            if info["xref"] not in ignorar_xrefs:
                _, y0, _, y1 = info["bbox"]
                imagens.append(Imagem(n, y0, y1, info["xref"]))
    return imagens


def normalizar_espacos(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def sem_acentos(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def termos_deiticos(texto: str, termos: list[str]) -> list[str]:
    alvo = sem_acentos(texto.lower())
    return sorted({
        t for t in termos
        if re.search(rf"\b{re.escape(sem_acentos(t.lower()))}\b", alvo)
    })


def separar_alternativas(texto: str, letras: str = "ABCD") -> tuple[str, dict[str, str]]:
    """Divide o texto do item em enunciado e alternativas.

    Aceita os formatos "A)" e "(A)", no início da linha ou no meio dela
    (alternativas lado a lado). As letras precisam aparecer em ordem;
    se alguma faltar, devolve o texto inteiro como enunciado e nenhuma alternativa.
    """
    posicoes = []
    inicio_busca = 0
    for letra in letras:
        m = re.compile(MARCADOR_ALTERNATIVA.format(letra=letra)).search(texto, inicio_busca)
        if not m:
            return texto.strip(), {}
        posicoes.append((letra, m.start(), m.end()))
        inicio_busca = m.end()

    enunciado = texto[: posicoes[0][1]].strip()
    alternativas = {}
    for i, (letra, _, fim) in enumerate(posicoes):
        proximo = posicoes[i + 1][1] if i + 1 < len(posicoes) else len(texto)
        alternativas[letra] = normalizar_espacos(texto[fim:proximo])
    return enunciado, alternativas


def formula_corrompida(texto: str) -> bool:
    """Heurística: caracteres de uso privado ou excesso de linhas de um só caractere."""
    if USO_PRIVADO.search(texto):
        return True
    linhas = [l for l in texto.splitlines() if l.strip()]
    curtas = sum(len(l.strip()) <= 2 for l in linhas)
    return len(linhas) >= 8 and curtas / len(linhas) > 0.3
