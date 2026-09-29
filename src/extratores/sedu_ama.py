"""Adaptador: materiais de apoio à AMA (Avaliação de Monitoramento da Aprendizagem), SEDU-ES.

Cobre os cadernos de Matemática do 5º ano com a mesma estrutura:
- blocos por descritor da matriz Paebes/AMA (código D0xx_M), com a descrição
  no cabeçalho do bloco;
- itens "QUESTÃO N", numerados a partir de 1 em cada bloco, em geral
  precedidos da avaliação de origem entre parênteses, ex.: "(Saresp - 2010).";
- alternativas A a D;
- gabarito ao final, em um de três formatos: tabela descritor/questão/letra,
  linhas "Questão 1: A" ou "Questão 1" seguida de "A) texto".

Os PDFs de 2024 e 2025 foram exportados de um editor gráfico e trazem texto
oculto sob outras camadas; comum.ler_linhas descarta esse texto.
"""
import re
from dataclasses import dataclass, field

import pymupdf

from extratores import comum

CODIFICACAO = "PAEBES_M"  # códigos D0xx_M da matriz Paebes/AMA
LETRAS = "ABCD"
CABECALHO = {
    "GOVERNO DO ESTADO DO ESPÍRITO SANTO",
    "SECRETARIA DE ESTADO DA EDUCAÇÃO",
    "SUBSECRETARIA DE ESTADO DA EDUCAÇÃO BÁSICA E PROFISSIONAL",
    "GERÊNCIA DE EDUCAÇÃO INFANTIL E ENSINO FUNDAMENTAL",
    "SUGESTÃO QUESTÕES – MATEMÁTICA",
    "5º ANO",
}
RE_CODIGO = re.compile(r"^(?:D\s?)?(\d[\d\s]{0,3})_M$")
RE_QUESTAO = re.compile(r"^QUEST[ÃA]O\s*(\d+)\s*(.*)$")
RE_GABARITO = re.compile(r"^GABARITO", re.I)
# "(Saresp - 2010). Com...", "(PROVA BRASIL) Uma..."; o fechamento é o primeiro ")"
# seguido de ponto opcional e início de frase.
RE_ORIGEM = re.compile(r"^\((.{2,80}?)\)\.?\s+(?=[A-ZÀ-Ú0-9“\"(])")
# Distância acima da linha do código em que o cabeçalho do bloco começa
# (a descrição às vezes começa um pouco acima do código).
ALTURA_CABECALHO = 25


@dataclass
class ItemBruto:
    descritor: str
    numero: int
    numero_pdf: int
    inicio: tuple[int, float]
    fim: tuple[int, float] = (10**6, 0.0)
    linhas: list[comum.Linha] = field(default_factory=list)


def _codigo(linha: str) -> str | None:
    m = RE_CODIGO.match(linha.strip())
    return f"D{int(m.group(1).replace(' ', '')):03d}_M" if m else None


def _paginas(doc: pymupdf.Document) -> tuple[range, int]:
    linhas = comum.ler_linhas(doc, range(1, doc.page_count + 1), CABECALHO)
    primeira = next(l.pagina for l in linhas if RE_QUESTAO.match(l.texto))
    gabarito = next(l.pagina for l in linhas if l.pagina > primeira and RE_GABARITO.match(l.texto))
    return range(primeira, gabarito), gabarito


def ler_itens(doc: pymupdf.Document, paginas: range) -> tuple[list[ItemBruto], dict[str, str]]:
    linhas = comum.ler_linhas(doc, paginas, CABECALHO, numeros_na_margem=True)
    itens: list[ItemBruto] = []
    descricoes: dict[str, list[str]] = {}
    atual: ItemBruto | None = None
    descritor, ordinal = None, 0
    no_cabecalho = False
    soltas: list[comum.Linha] = []  # linhas fora de item e de cabeçalho

    for linha in linhas:
        if codigo := _codigo(linha.texto):
            # A descrição do descritor às vezes começa um pouco acima do código
            # e, na ordem de leitura, vem antes dele: recupera essas linhas.
            limite = linha.y0 - ALTURA_CABECALHO
            candidatas = (atual.linhas if atual is not None else []) + soltas
            derramadas = [l for l in candidatas if l.pagina == linha.pagina and l.y1 > limite]
            if atual is not None:
                atual.linhas = [l for l in atual.linhas if l not in derramadas]
                atual.fim = (linha.pagina, limite)
            atual, descritor, ordinal, no_cabecalho, soltas = None, codigo, 0, True, []
            descricoes.setdefault(codigo, [l.texto for l in derramadas])
            continue
        if m := RE_QUESTAO.match(linha.texto):
            if atual is not None:
                atual.fim = (linha.pagina, linha.y0)
            ordinal += 1
            no_cabecalho = False
            atual = ItemBruto(descritor, ordinal, int(m.group(1)), (linha.pagina, linha.y0))
            itens.append(atual)
            if m.group(2):
                atual.linhas.append(comum.Linha(linha.pagina, linha.y0, linha.y1, m.group(2)))
            continue
        if no_cabecalho:
            descricoes[descritor].append(linha.texto)
        elif atual is not None:
            atual.linhas.append(linha)
        else:
            soltas.append(linha)

    return itens, {c: comum.normalizar_espacos(" ".join(p)) for c, p in descricoes.items()}


def ler_gabarito(doc: pymupdf.Document, pagina_inicial: int) -> tuple[list[dict], list[str]]:
    linhas = comum.ler_linhas(
        doc, range(pagina_inicial, doc.page_count + 1), CABECALHO,
        duas_colunas=True, numeros_na_margem=True,
    )
    registros, avisos = [], []
    descritor, numero = None, None
    for linha in linhas:
        texto = linha.texto.strip()
        if codigo := _codigo(texto):
            descritor, numero = codigo, None
            continue
        if descritor is None:
            continue
        if m := re.match(r"^Quest[ãa]o\s*(\d+)\s*:?\s*([A-Z])?\b", texto, re.I):
            numero = int(m.group(1))
            letra = m.group(2)
        elif re.fullmatch(r"\d{1,2}", texto):
            numero, letra = int(texto), None
        elif numero is not None and (m := re.match(r"^([A-Z])(\)|$)", texto)):
            letra = m.group(1)
        else:
            continue
        if letra and numero is not None:
            if letra in LETRAS:
                registros.append({"descritor": descritor, "numero": numero, "gabarito": letra})
            else:
                avisos.append(f"gabarito: {descritor} questão {numero:02d} tem letra inválida '{letra}', descartada")
            numero = None
    return registros, avisos


def _imagens_do_item(item: ItemBruto, imagens: list[comum.Imagem]) -> list[comum.Imagem]:
    return [img for img in imagens if item.inicio <= (img.pagina, img.y_centro) < item.fim]


def extrair(caminho_pdf, fonte: str, ano: int) -> dict:
    doc = pymupdf.open(caminho_pdf)
    paginas, pagina_gabarito = _paginas(doc)
    logos = comum.xrefs_recorrentes(doc)
    imagens = comum.ler_imagens(doc, paginas, logos)
    brutos, descricoes = ler_itens(doc, paginas)

    itens = []
    for bruto in brutos:
        texto_original = "\n".join(l.texto for l in bruto.linhas)
        enunciado, alternativas = comum.separar_alternativas(texto_original, LETRAS)
        origem = RE_ORIGEM.match(enunciado)
        if origem:
            enunciado = enunciado[origem.end():]
        imgs = _imagens_do_item(bruto, imagens)
        observacoes = []
        if bruto.numero != bruto.numero_pdf:
            observacoes.append(f"numerado {bruto.numero_pdf:02d} no PDF; posição {bruto.numero} no bloco")
        if not alternativas:
            observacoes.append("alternativas não localizadas no texto")

        itens.append({
            "fonte": fonte,
            "ano": ano,
            "codificacao": CODIFICACAO,
            "descritor": bruto.descritor,
            "numero": bruto.numero,
            "numero_pdf": bruto.numero_pdf,
            "topico_saeb": "",
            "origem_item": origem.group(1).strip() if origem else "",
            "pagina_inicio": bruto.inicio[0],
            "pagina_fim": bruto.linhas[-1].pagina if bruto.linhas else bruto.inicio[0],
            "enunciado": comum.normalizar_espacos(enunciado),
            **{f"alt_{l.lower()}": alternativas.get(l, "") for l in LETRAS},
            "gabarito_inline": "",
            "n_imagens": len(imgs),
            "formula_corrompida": comum.formula_corrompida(texto_original),
            "observacoes": "; ".join(observacoes),
            "texto_original": texto_original,
        })

    gabarito, avisos = ler_gabarito(doc, pagina_gabarito)
    descritores = [
        {"codificacao": CODIFICACAO, "descritor": c, "descricao": d, "fonte": fonte}
        for c, d in descricoes.items()
    ]
    return {"itens": itens, "gabarito": gabarito, "descritores": descritores, "avisos": avisos}
