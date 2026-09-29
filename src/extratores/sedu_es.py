"""Adaptador: Banco de Atividades SAEB de Matemática, 9º ano, SEDU-ES (Volume 1, 2023).

Estrutura observada no PDF:
- p. 5-6: matriz de referência do SAEB (D1 a D37) com a descrição de cada descritor;
- p. 7: item comentado de exemplo (ignorado);
- p. 8-91: blocos por descritor. Cada bloco abre com um cabeçalho
  (DESCRITOR / CÓDIGOS / TÓPICO / descrição / "Dn – no Saeb" / conhecimento prévio),
  seguido de itens "QUESTÃO NN" cuja numeração reinicia a cada bloco;
- p. 92-95: gabarito por descritor ("GABARITO DESCRITOR:").
Alternativas vão de A a D, em geral no formato "A)", às vezes "(A)".
"""
import re
from dataclasses import dataclass, field

import pymupdf

from extratores import comum

FONTE = "sedu_es_9ef"
ANO = 9
CODIFICACAO = "SAEB_9EF"  # numeração D1-D37 da matriz de referência do SAEB, 9º ano
LETRAS = "ABCD"
PAGINAS_MATRIZ = range(5, 7)

CABECALHO = {
    "GOVERNO DO ESTADO DO ESPÍRITO SANTO",
    "SECRETARIA DE ESTADO DA EDUCAÇÃO",
    "SUBSECRETARIA DE EDUCAÇÃO BÁSICA E PROFISSIONAL",
}
RE_QUESTAO = re.compile(r"^QUEST[ÃA]O\s*(\d+)\s*(.*)$")
RE_DESCRITOR_BLOCO = re.compile(r"^(D)\s?(\d{1,2})\s*[–-]\s*no Saeb", re.I)
RE_TOPICO = re.compile(r"^TÓPICO:\s*(.+)$")
RE_RESPOSTA_INLINE = re.compile(r"\(\s*RESP\.?\s*([A-E])\s*\)", re.I)
RE_CODIGO_MATRIZ = re.compile(r"^D(\d{1,2})$")
RE_TEMA_MATRIZ = re.compile(r"^[IVX]+\.\s")


@dataclass
class ItemBruto:
    descritor: str
    topico: str
    numero: int
    numero_pdf: int
    inicio: tuple[int, float]
    fim: tuple[int, float] = (10**6, 0.0)
    linhas: list[comum.Linha] = field(default_factory=list)


def _codigo(numero: str) -> str:
    return f"D{int(numero)}"


def _paginas_itens(linhas: list[comum.Linha]) -> range:
    primeira = next(l.pagina for l in linhas if RE_QUESTAO.match(l.texto))
    gabarito = next(l.pagina for l in linhas if l.texto.startswith("GABARITOS"))
    return range(primeira, gabarito)


def ler_matriz(doc: pymupdf.Document) -> list[dict]:
    """Descritores D1-D37 com a descrição, das páginas da matriz de referência."""
    linhas = comum.ler_linhas(doc, PAGINAS_MATRIZ, CABECALHO)
    descritores, atual = [], None
    for linha in linhas:
        m = RE_CODIGO_MATRIZ.match(linha.texto)
        if m:
            atual = {"codificacao": CODIFICACAO, "descritor": _codigo(m.group(1)), "partes": []}
            descritores.append(atual)
        elif RE_TEMA_MATRIZ.match(linha.texto) or linha.texto.startswith("4. Item"):
            atual = None
        elif atual is not None:
            atual["partes"].append(linha.texto)
    return [
        {
            "codificacao": d["codificacao"],
            "descritor": d["descritor"],
            "descricao": comum.normalizar_espacos(" ".join(d["partes"])),
            "fonte": FONTE,
        }
        for d in descritores
    ]


def ler_itens(doc: pymupdf.Document, paginas: range) -> list[ItemBruto]:
    linhas = comum.ler_linhas(doc, paginas, CABECALHO)
    itens: list[ItemBruto] = []
    atual: ItemBruto | None = None
    descritor, topico, ordinal = None, "", 0

    def fechar(linha: comum.Linha) -> None:
        if atual is not None:
            atual.fim = (linha.pagina, linha.y0)

    # O cabeçalho do bloco nem sempre traz todas as linhas, nem na mesma ordem
    # (o bloco D6 não tem "DESCRITOR" em texto e abre com "D6 – no Saeb").
    # Qualquer linha de cabeçalho encerra o item corrente.
    for linha in linhas:
        texto = linha.texto
        if texto == "DESCRITOR":
            fechar(linha)
            atual = None
            continue
        if m := RE_TOPICO.match(texto):
            fechar(linha)
            atual = None
            topico = m.group(1).strip()
            continue
        if m := RE_DESCRITOR_BLOCO.match(texto):
            fechar(linha)
            atual = None
            descritor, ordinal = _codigo(m.group(2)), 0
            continue
        if m := RE_QUESTAO.match(texto):
            fechar(linha)
            ordinal += 1
            atual = ItemBruto(
                descritor=descritor, topico=topico, numero=ordinal,
                numero_pdf=int(m.group(1)), inicio=(linha.pagina, linha.y0),
            )
            itens.append(atual)
            if m.group(2):
                atual.linhas.append(comum.Linha(linha.pagina, linha.y0, linha.y1, m.group(2)))
            continue
        if atual is not None:
            atual.linhas.append(linha)
    return itens


def ler_gabarito(doc: pymupdf.Document, pagina_inicial: int) -> tuple[list[dict], list[str]]:
    # O gabarito é diagramado em duas colunas de descritores por página.
    linhas = comum.ler_linhas(
        doc, range(pagina_inicial, doc.page_count + 1), CABECALHO, duas_colunas=True
    )
    tokens = [l.texto for l in linhas]
    registros, avisos = [], []
    descritor, numero = None, None
    esperando_codigo = False
    for tok in tokens:
        if tok.startswith("GABARITO DESCRITOR"):
            esperando_codigo = True
            continue
        if esperando_codigo:
            m = re.fullmatch(r"(D?)\s?(\d{1,2})", tok)
            if not m:
                avisos.append(f"gabarito: código de descritor ilegível '{tok}'")
                descritor = None
            else:
                descritor = _codigo(m.group(2))
                if not m.group(1):
                    avisos.append(f"gabarito: descritor '{tok}' sem o prefixo D, lido como {descritor}")
            esperando_codigo = False
            continue
        if descritor and re.fullmatch(r"\d{1,2}", tok):
            numero = int(tok)
        elif descritor and numero is not None and re.fullmatch(r"[A-Z]", tok):
            if tok in LETRAS:
                registros.append({"descritor": descritor, "numero": numero, "gabarito": tok})
            else:
                avisos.append(f"gabarito: {descritor} questão {numero:02d} tem letra inválida '{tok}', descartada")
            numero = None
    return registros, avisos


def _imagens_do_item(item: ItemBruto, imagens: list[comum.Imagem]) -> list[comum.Imagem]:
    return [img for img in imagens if item.inicio <= (img.pagina, img.y_centro) < item.fim]


def extrair(caminho_pdf) -> dict:
    doc = pymupdf.open(caminho_pdf)
    todas = comum.ler_linhas(doc, range(1, doc.page_count + 1), CABECALHO)
    paginas = _paginas_itens(todas)
    logos = comum.xrefs_recorrentes(doc)
    imagens = comum.ler_imagens(doc, paginas, logos)

    itens = []
    avisos = []
    for bruto in ler_itens(doc, paginas):
        texto_original = "\n".join(l.texto for l in bruto.linhas)
        resp = RE_RESPOSTA_INLINE.search(texto_original)
        texto = RE_RESPOSTA_INLINE.sub("", texto_original)
        enunciado, alternativas = comum.separar_alternativas(texto, LETRAS)
        imgs = _imagens_do_item(bruto, imagens)
        observacoes = []
        if bruto.numero != bruto.numero_pdf:
            observacoes.append(f"numerado {bruto.numero_pdf:02d} no PDF; posição {bruto.numero} no bloco")
        if resp:
            observacoes.append("resposta impressa no enunciado, removida")
        if not alternativas:
            observacoes.append("alternativas não localizadas no texto")

        itens.append({
            "fonte": FONTE,
            "ano": ANO,
            "codificacao": CODIFICACAO,
            "descritor": bruto.descritor,
            "numero": bruto.numero,
            "numero_pdf": bruto.numero_pdf,
            "topico_saeb": bruto.topico,
            "pagina_inicio": bruto.inicio[0],
            "pagina_fim": bruto.linhas[-1].pagina if bruto.linhas else bruto.inicio[0],
            "enunciado": comum.normalizar_espacos(enunciado),
            **{f"alt_{l.lower()}": alternativas.get(l, "") for l in LETRAS},
            "gabarito_inline": resp.group(1).upper() if resp else "",
            "n_imagens": len(imgs),
            "formula_corrompida": comum.formula_corrompida(texto_original),
            "observacoes": "; ".join(observacoes),
            "texto_original": texto_original,
        })

    gabarito, avisos_gab = ler_gabarito(doc, paginas.stop)
    avisos.extend(avisos_gab)
    return {
        "itens": itens,
        "gabarito": gabarito,
        "descritores": ler_matriz(doc),
        "avisos": avisos,
    }
