"""Funções de extração independentes de fonte."""
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass

import pymupdf

# Caracteres da área de uso privado: aparecem quando fórmulas do MathType
# ou fontes de símbolos são extraídas como texto.
USO_PRIVADO = re.compile(r"[-]")
# Lookbehind em vez de consumir o espaço anterior: com alternativas vazias
# ("A)\nB) 3"), o espaço antes de "B)" não pode ter sido consumido por "A)".
MARCADOR_ALTERNATIVA = r"(?:^|(?<=\s))\(?{letra}\)"


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
CARACTERES_EXPOENTE = "0123456789+-–()"
SOBRESCRITOS = str.maketrans(CARACTERES_EXPOENTE, "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻⁽⁾")
RE_DENOMINADOR = re.compile(r"^\d{1,3}$")
TOLERANCIA_BASE = 3.0  # pontos; linhas com base mais próxima que isso estão na mesma altura


def _texto_span(span: dict) -> str:
    """Texto do span, com expoentes numéricos convertidos para sobrescrito.

    Só converte spans formados inteiramente por dígitos e sinais: alguns PDFs
    marcam trechos inteiros de texto comum como sobrescritos.
    """
    texto = span["text"]
    alvo = texto.strip()
    if span["flags"] & FLAG_SOBRESCRITO and alvo and all(c in CARACTERES_EXPOENTE for c in alvo):
        return texto.translate(SOBRESCRITOS)
    return texto


def _juntar_fracoes_na_linha(linhas: list[dict]) -> int:
    """Funde numerador e denominador que vêm como spans consecutivos da mesma linha."""
    fundidas = 0
    for linha in linhas:
        spans = linha["spans"]
        i = 0
        while i < len(spans) - 1:
            num, den = spans[i], spans[i + 1]
            if (
                RE_DENOMINADOR.match(num["text"].strip())
                and RE_DENOMINADOR.match(den["text"].strip())
                and abs(_centro_x(num["bbox"]) - _centro_x(den["bbox"])) < 4
                and 5 < den["bbox"][1] - num["bbox"][1] < 20
            ):
                num["text"] = f" {num['text'].strip()}/{den['text'].strip()} "
                del spans[i + 1]
                fundidas += 1
            i += 1
    return fundidas


def _centro_x(bbox) -> float:
    return (bbox[0] + bbox[2]) / 2


def _juntar_fracoes(linhas: list[dict]) -> int:
    """Funde frações empilhadas em "numerador/denominador".

    Um dos termos vem como linha isolada só com dígitos; o outro é um span de
    dígitos de outra linha, centralizado com ele, logo acima (o isolado é o
    denominador) ou logo abaixo (o isolado é o numerador). Altera `linhas`
    e devolve quantas fundiu.
    """
    fundidas = 0
    for isolada in [l for l in linhas if len(l["spans"]) == 1]:
        texto_isolado = isolada["spans"][0]["text"].strip()
        if isolada.get("removida") or not RE_DENOMINADOR.match(texto_isolado):
            continue
        y_isolado = isolada["spans"][0]["bbox"][1]
        for outra in linhas:
            if outra is isolada or outra.get("removida"):
                continue
            for span in outra["spans"]:
                texto = span["text"].strip()
                if (
                    not RE_DENOMINADOR.match(texto)
                    or "/" in span["text"]
                    or abs(_centro_x(span["bbox"]) - _centro_x(isolada["bbox"])) >= 4
                ):
                    continue
                distancia = y_isolado - span["bbox"][1]
                if 5 < distancia < 20:  # isolada abaixo: é o denominador
                    fracao = f"{texto}/{texto_isolado}"
                elif 5 < -distancia < 20:  # isolada acima: é o numerador
                    fracao = f"{texto_isolado}/{texto}"
                else:
                    continue
                span["text"] = span["text"].replace(texto, fracao, 1)
                isolada["removida"] = True
                fundidas += 1
                break
            if isolada.get("removida"):
                break
    return fundidas


SOBREPOSICAO_MAXIMA = 0.25


def _spans_sobrepostos(pagina: pymupdf.Page, spans: list[dict]) -> set[int]:
    """Índices de spans cobertos por outro texto desenhado depois deles.

    Editores gráficos deixam camadas antigas de texto sob o texto atual
    (ex.: um código de descritor de outro bloco sob o código correto). Na página
    só aparece o que foi desenhado por último. A ordem de desenho e o retângulo
    justo de cada trecho vêm de get_texttrace.
    """
    traco = [(t["seqno"], pymupdf.Rect(t["bbox"])) for t in pagina.get_texttrace()]
    posicoes = []
    for span in spans:
        r = pymupdf.Rect(span["bbox"])
        melhor = max(traco, key=lambda t: (t[1] & r).get_area(), default=None)
        posicoes.append(melhor if melhor and (melhor[1] & r).get_area() > 0 else None)

    cobertos = set()
    for i, pi in enumerate(posicoes):
        if pi is None:
            continue
        for j, pj in enumerate(posicoes):
            if j == i or pj is None or pj[0] <= pi[0]:
                continue
            menor = min(pi[1].get_area(), pj[1].get_area())
            if menor > 0 and (pi[1] & pj[1]).get_area() / menor > SOBREPOSICAO_MAXIMA:
                cobertos.add(i)
                break
    return cobertos


def _largura_zero(c: dict) -> bool:
    return c["bbox"][2] - c["bbox"][0] < 0.1


def _marcar_fantasmas(bloco: dict) -> None:
    """Marca o início da linha seguinte repetido, invisível, no fim de cada linha.

    Editores gráficos (ex.: Canva) terminam a linha com uma cauda de caracteres
    de largura zero: o fim real da palavra, um espaço e uma cópia do começo da
    linha seguinte ("dividiu" + " e" | "em 3 vezes"). Só a cópia é removida:
    o trecho da cauda depois de um espaço que coincide com o início da próxima
    linha do bloco.
    """
    linhas = [[c for s in l["spans"] for c in s["chars"]] for l in bloco.get("lines", [])]
    inicios = ["".join(c["c"] for c in chars).lstrip() for chars in linhas]
    for i, chars in enumerate(linhas[:-1]):
        k = len(chars)
        while k > 0 and _largura_zero(chars[k - 1]):
            k -= 1
        cauda = chars[k:]
        texto_cauda = "".join(c["c"] for c in cauda)
        for j, c in enumerate(cauda):
            copia = texto_cauda[j + 1:]
            if c["c"] == " " and copia and inicios[i + 1].startswith(copia):
                for fantasma in cauda[j:]:
                    fantasma["fantasma"] = True
                break


def _span_visivel(span_bruto: dict) -> dict:
    """Converte um span de rawdict em span com texto, sem os caracteres fantasmas."""
    span = {k: v for k, v in span_bruto.items() if k != "chars"}
    span["text"] = "".join(c["c"] for c in span_bruto["chars"] if not c.get("fantasma"))
    return span


RE_NUMERO_PAGINA = re.compile(r"^\d{1,3}(\s*/\s*\d{1,3})?$")
MARGEM_TOPO, MARGEM_BASE = 0.12, 0.92


def ler_linhas(
    doc: pymupdf.Document,
    paginas: range,
    ignorar: set[str],
    duas_colunas: bool = False,
    numeros_na_margem: bool = False,
) -> list[Linha]:
    """Linhas de texto em ordem de leitura, sem as linhas vazias e sem as de `ignorar`.

    Expoentes marcados como sobrescritos viram caracteres sobrescritos (x²),
    frações empilhadas viram "a/b", e a ordem segue a base das linhas, para que
    o numerador de uma fração não passe à frente do texto da mesma linha.
    Texto oculto sob outras camadas é descartado.
    Com `duas_colunas`, lê a coluna esquerda inteira antes da direita.
    Com `numeros_na_margem`, descarta linhas só com números no topo e no rodapé
    (numeração de página).
    """
    linhas = []
    for n in paginas:
        pagina = doc[n - 1]
        meio = pagina.rect.width / 2
        altura = pagina.rect.height
        blocos = pagina.get_text("rawdict")["blocks"]
        for bloco in blocos:
            _marcar_fantasmas(bloco)
        estrutura = [
            (linha["bbox"], [_span_visivel(s) for s in linha["spans"]])
            for bloco in blocos
            for linha in bloco.get("lines", [])
        ]
        todos = [s for _, spans in estrutura for s in spans if s["text"].strip()]
        cobertos = {id(todos[i]) for i in _spans_sobrepostos(pagina, todos)}
        brutas = []
        for bbox, spans in estrutura:
            visiveis = [s for s in spans if id(s) not in cobertos]
            if visiveis:
                brutas.append({"bbox": bbox, "spans": visiveis})
        _juntar_fracoes_na_linha(brutas)
        _juntar_fracoes(brutas)
        da_pagina = []
        for linha in brutas:
            if linha.get("removida"):
                continue
            texto = "".join(_texto_span(s) for s in linha["spans"]).strip()
            if numeros_na_margem and RE_NUMERO_PAGINA.match(texto):
                y0, y1 = linha["bbox"][1], linha["bbox"][3]
                if y1 < MARGEM_TOPO * altura or y0 > MARGEM_BASE * altura:
                    continue
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
    # Letras além da última alternativa ("E) 6,52 - 3,48 ... P)") indicam lista de
    # exercícios, e não questão de múltipla escolha.
    if re.search(r"(?:^|\s)\(?[E-Z]\)\s", alternativas[letras[-1]] + " "):
        return texto.strip(), {}
    # Citação de dados ("Fonte: https://...") impressa depois das alternativas
    # pertence ao texto-base: sai da alternativa e vai para o fim do enunciado.
    ultima = letras[-1]
    if "Fonte:" in alternativas[ultima]:
        resto, citacao = alternativas[ultima].split("Fonte:", 1)
        alternativas[ultima] = resto.strip()
        enunciado = f"{enunciado} Fonte: {citacao.strip()}"
    return enunciado, alternativas


def glifos_vetoriais(doc: pymupdf.Document, inicio: tuple[int, float], fim: tuple[int, float]) -> int:
    """Conta formas preenchidas do tamanho de um caractere coladas às linhas de texto do item.

    Alguns cadernos desenham frações e expoentes como vetores, e não como texto:
    o número some do enunciado extraído ("separar ___ da colheita"). Ilustrações
    também são vetoriais, mas ficam fora das linhas de texto e não são contadas.
    """
    total = 0
    ultima = min(fim[0], doc.page_count)
    for n in range(inicio[0], ultima + 1):
        pagina = doc[n - 1]
        y0 = inicio[1] if n == inicio[0] else 0
        y1 = fim[1] if n == fim[0] else pagina.rect.height
        # Compara com cada caractere visível, e não com o trecho inteiro: em texto
        # justificado, o retângulo do trecho cobre a linha toda, inclusive a fração.
        linhas = [
            (pymupdf.Rect(l["bbox"]), [pymupdf.Rect(c["bbox"]) for s in l["spans"] for c in s["chars"]
                                       if c["c"].strip() and not _largura_zero(c)])
            for b in pagina.get_text("rawdict")["blocks"] for l in b.get("lines", [])
        ]
        linhas = [(r, chars) for r, chars in linhas if chars]
        isolados = []  # glifos pretos fora das linhas de texto, por altura da base
        for d in pagina.get_drawings():
            r = d["rect"]
            if d.get("type") not in ("f", "fs") or not (y0 <= (r.y0 + r.y1) / 2 < y1):
                continue
            if not (1.5 <= r.width <= 12 and 3 <= r.height <= 14):
                continue
            # Sobreposição real com um caractere (as caixas das linhas vizinhas encostam nas bordas).
            area = r.get_area()
            if any((r & c).get_area() > 0.3 * area for _, chars in linhas for c in chars):
                continue
            cy = (r.y0 + r.y1) / 2
            if any(lr.y0 - 8 <= cy <= lr.y1 + 8 and lr.x0 - 15 <= r.x0 <= lr.x1 + 25 for lr, _ in linhas):
                total += 1
            elif d.get("fill") and max(d["fill"]) < 0.35:
                isolados.append((r.y1, round(r.width * 2) / 2))
        # Fórmula em linha própria: quatro ou mais glifos pretos na mesma base, com ao
        # menos três larguras diferentes (letras e algarismos variam; detalhes de
        # ilustrações, como barras e traços repetidos, têm larguras iguais).
        isolados.sort()
        for i in range(len(isolados)):
            grupo = [w for y, w in isolados[i:] if y - isolados[i][0] <= 3]
            if len(grupo) >= 4 and len(set(grupo)) >= 3:
                total += len(grupo)
                break
    return total


RE_OPERADOR_AUSENTE = re.compile(r"\d {3,}\d")


def operador_ausente(texto: str) -> bool:
    """Dois números separados por um vão ("64     4"): operador desenhado como vetor."""
    return any(RE_OPERADOR_AUSENTE.search(linha.strip()) for linha in texto.splitlines())


def formula_corrompida(texto: str) -> bool:
    """Heurística: caracteres de uso privado ou excesso de linhas de um só caractere."""
    if USO_PRIVADO.search(texto):
        return True
    linhas = [l for l in texto.splitlines() if l.strip()]
    curtas = sum(len(l.strip()) <= 2 for l in linhas)
    return len(linhas) >= 8 and curtas / len(linhas) > 0.3
