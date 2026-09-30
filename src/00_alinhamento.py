"""Passo 3.1/3.2: tabelas de alinhamento e de equivalência a partir dos documentos da SEDU-ES.

Lê os PDFs em dados/01_brutos/alinhamento (registrados em
dados/referencia/documentos_alinhamento.csv) e grava:
  dados/referencia/alinhamento_descritor_habilidade.csv
      codificacao, descritor, habilidade, ano_aplicacao, unidade_tematica_doc,
      documento, pagina, observacao
  dados/referencia/equivalencia_codificacoes.csv
      codificacao_origem, descritor_origem, codificacao_destino, descritor_destino,
      documento, pagina

Documentos:
- Detalhamento dos descritores das matrizes Paebes 2025 e Saeb 2001, 9º ano (2026):
  um descritor por página, com código Paebes (D0xx_M), descritor SAEB
  correspondente, habilidades BNCC associadas e unidade temática.
- Correlação de descritores, 9º ano (2023): tabela SAEB D1-D37 -> Paebes D0xx_M.
  Usada para a equivalência quando o Detalhamento não traz o descritor SAEB,
  e para verificação cruzada.
- Material do professor, 5º ano, Matemática, 2º trimestre (2026): tabelas
  "Habilidade | Descritor(es) do PAEBES".

Habilidades com o sufixo /ES (adaptação do currículo capixaba) são reduzidas ao
código BNCC e sinalizadas em `observacao`.
"""
import re
import sys

import pandas as pd
import pymupdf

import config

PASTA = config.BRUTOS / "alinhamento"
DETALHAMENTO = "detalhamento_paebes2025_saeb2001_9ano.pdf"
CORRELACAO = "CORRELACAO-DE-DESCRITORES-9-ANO-EF-Matematica-1.pdf"
MATERIAL_5ANO = "material_prof_5ano_mat_2tri_2026.pdf"

RE_PAEBES = re.compile(r"D(\d{3})\s?_M")
RE_SAEB = re.compile(r"\(Saeb\)\s*D(\d{1,2})\b")
RE_HABILIDADE = re.compile(r"(EF\d{2}MA\d{2})(/ES)?\s*\n?\s*-")
RE_UNIDADE = re.compile(
    r"^(Números|Álgebra|Geometria|Grandezas\s+e\s+[Mm]edidas|Probabilidade\s+e\s+[Ee]statística)\s*$",
    re.M,
)
UNIDADES = {
    "números": "Números", "álgebra": "Álgebra", "geometria": "Geometria",
    "grandezas e medidas": "Grandezas e medidas",
    "probabilidade e estatística": "Probabilidade e estatística",
}


def paebes(numero: str) -> str:
    return f"D{int(numero):03d}_M"


def ler_detalhamento() -> tuple[list[dict], list[dict]]:
    doc = pymupdf.open(PASTA / DETALHAMENTO)
    alinhamento, equivalencia = [], []
    for pagina in doc:
        texto = pagina.get_text()
        habilidades = RE_HABILIDADE.findall(texto)
        if not habilidades:
            continue
        m_paebes, m_saeb = RE_PAEBES.search(texto), RE_SAEB.search(texto)
        m_ut = RE_UNIDADE.search(texto)
        unidade = UNIDADES[re.sub(r"\s+", " ", m_ut.group(1)).lower()] if m_ut else ""
        n = pagina.number + 1
        # Descritores só da matriz Saeb 2001 ("Paebes - não avaliado") entram pela codificação SAEB.
        if m_paebes:
            chave = ("PAEBES_M", paebes(m_paebes.group(1)))
        else:
            chave = ("SAEB_9EF", f"D{int(m_saeb.group(1))}")
        for codigo, es in habilidades:
            alinhamento.append({
                "codificacao": chave[0], "descritor": chave[1], "habilidade": codigo,
                "ano_aplicacao": 9, "unidade_tematica_doc": unidade,
                "documento": DETALHAMENTO, "pagina": n,
                "observacao": "habilidade com adaptação /ES no documento" if es else "",
            })
        if m_paebes and m_saeb:
            equivalencia.append({
                "codificacao_origem": "SAEB_9EF", "descritor_origem": f"D{int(m_saeb.group(1))}",
                "codificacao_destino": "PAEBES_M", "descritor_destino": paebes(m_paebes.group(1)),
                "documento": DETALHAMENTO, "pagina": n,
            })
    return alinhamento, equivalencia


def ler_correlacao() -> list[dict]:
    """Pares SAEB -> Paebes. Cada linha da tabela traz 'Dn' (SAEB), 'Dn' (Paebes 2023)
    e, quando existe, o código da avaliação diagnóstica D0xx_M."""
    doc = pymupdf.open(PASTA / CORRELACAO)
    pares = []
    for pagina in doc:
        tokens = re.findall(r"^\s*(D\d{1,2}|D\d{3}\s?_M)\s*$", pagina.get_text(), re.M)
        i = 0
        while i + 1 < len(tokens):
            a, b = tokens[i], tokens[i + 1]
            if re.fullmatch(r"D\d{1,2}", a) and a == b:
                destino = tokens[i + 2] if i + 2 < len(tokens) and RE_PAEBES.fullmatch(tokens[i + 2]) else None
                if destino:
                    pares.append({
                        "codificacao_origem": "SAEB_9EF", "descritor_origem": a,
                        "codificacao_destino": "PAEBES_M",
                        "descritor_destino": paebes(RE_PAEBES.fullmatch(destino).group(1)),
                        "documento": CORRELACAO, "pagina": pagina.number + 1,
                    })
                i += 3 if destino else 2
            else:
                i += 1
    return pares


def ler_material_5ano() -> list[dict]:
    """Tabelas 'Habilidade | Descritor(es) do PAEBES': cada descritor pertence
    à habilidade que o precede na página."""
    doc = pymupdf.open(PASTA / MATERIAL_5ANO)
    linhas = []
    for pagina in doc:
        texto = pagina.get_text()
        if "Descritor(es) do PAEBES" not in texto:
            continue
        atual, es = None, None
        for m in re.finditer(r"(EF05MA\d{2})(/ES)?|D(\d{3})\s?_M|Não há descritor", texto):
            if m.group(1):
                atual, es = m.group(1), bool(m.group(2))
            elif m.group(3) and atual:
                linhas.append({
                    "codificacao": "PAEBES_M", "descritor": paebes(m.group(3)), "habilidade": atual,
                    "ano_aplicacao": 5, "unidade_tematica_doc": "",
                    "documento": MATERIAL_5ANO, "pagina": pagina.number + 1,
                    "observacao": "habilidade com adaptação /ES no documento" if es else "",
                })
    return linhas


def marcar_fora_da_bncc(alinhamento: pd.DataFrame, taxonomia: pd.DataFrame) -> list[str]:
    """Habilidades acrescentadas pelo Currículo do ES (ex.: EF09MA24) não existem
    na BNCC: ficam na tabela, sinalizadas, e não entram no rótulo de referência."""
    alinhamento["na_bncc"] = alinhamento["habilidade"].isin(taxonomia["codigo"])
    fora = sorted(set(alinhamento.loc[~alinhamento["na_bncc"], "habilidade"]))
    alinhamento.loc[~alinhamento["na_bncc"], "observacao"] = (
        "habilidade exclusiva do Currículo do ES, fora da BNCC"
    )
    return fora


def validar(alinhamento: pd.DataFrame) -> list[str]:
    erros = []
    duplicadas = alinhamento.duplicated(["codificacao", "descritor", "habilidade", "ano_aplicacao"])
    if duplicadas.any():
        erros.append(f"pares repetidos: {alinhamento[duplicadas].to_dict('records')}")
    return erros


def main() -> int:
    taxonomia = pd.read_csv(config.ARQ_BNCC, dtype=str)
    alinhamento_9, equivalencia_det = ler_detalhamento()
    equivalencia_cor = ler_correlacao()
    alinhamento = pd.DataFrame(alinhamento_9 + ler_material_5ano())
    equivalencia = pd.DataFrame(equivalencia_det + equivalencia_cor)

    fora = marcar_fora_da_bncc(alinhamento, taxonomia)
    if fora:
        print(f"aviso: habilidades fora da BNCC (Currículo do ES), mantidas e sinalizadas: {fora}")
    erros = validar(alinhamento)
    if erros:
        print("FALHA NA VALIDAÇÃO:")
        for e in erros:
            print(f"  - {e}")
        return 1

    alinhamento.to_csv(config.ARQ_ALINHAMENTO, index=False, encoding="utf-8")
    equivalencia.to_csv(config.ARQ_EQUIVALENCIA, index=False, encoding="utf-8")
    print(f"gravado {config.ARQ_ALINHAMENTO}: {len(alinhamento)} pares")
    print(alinhamento.groupby(["ano_aplicacao", "codificacao"]).agg(
        descritores=("descritor", "nunique"), habilidades=("habilidade", "nunique"), pares=("habilidade", "size")))
    print(f"\ngravado {config.ARQ_EQUIVALENCIA}: {len(equivalencia)} pares")
    print(equivalencia.groupby("documento").size())
    return 0


if __name__ == "__main__":
    sys.exit(main())
