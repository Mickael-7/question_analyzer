"""Heurística lexical por vocabulário curricular (Passo 4.2).

Vocabulário de cada habilidade: palavras de conteúdo do objeto de conhecimento
e do texto da habilidade, sem palavras funcionais nem verbos genéricos de
enunciado de habilidade ("resolver", "identificar"...). As palavras são
normalizadas (minúsculas, sem acento) e reduzidas a um radical por truncamento
em RADICAL caracteres, para casar flexões ("fração", "frações", "fracionária").

Pontuação de um item para uma habilidade: soma do IDF dos radicais do
vocabulário da habilidade presentes no enunciado, dividida pela raiz do tamanho
do vocabulário (para não favorecer habilidades de texto longo). O IDF é
calculado sobre os vocabulários das habilidades: radicais comuns a muitas
habilidades pesam pouco.

Uso: python src/heuristica.py   -> grava dados/referencia/vocabulario.csv
O vocabulário é parte do método e é versionado; o script de etiquetagem só o lê.
"""
import math
import re
import sys

import pandas as pd

import config
from extratores.comum import sem_acentos

RADICAL = 6
TAMANHO_MINIMO = 3

PALAVRAS_FUNCIONAIS = set("""
a ao aos as com como da das de do dos e em entre era essa esse esta este isso isto
ja la mais mas me mesmo na nas nao nem no nos o os ou para pela pelas pelo pelos por
qual quais quando que se sem seu sua seus suas so sob sobre tambem tal tem ter um uma
umas uns ate cada outra outro outras outros sao ser sendo foi sera seja todo toda todos
todas tanto tanta muito muita pouco pouca quanto quanta onde lhe lhes ela ele elas eles
inclusive bem desde apos ante durante tais etc via meio partir modo forma
""".split())

# Verbos e termos recorrentes na redação das habilidades da BNCC, sem conteúdo matemático.
TERMOS_DE_ENUNCIADO = set("""
resolver elaborar identificar reconhecer utilizar compreender analisar descrever
comparar construir estabelecer interpretar representar associar aplicar empregar
produzir realizar apresentar explicar investigar planejar argumentar justificar
problemas problema envolvam envolvendo envolver envolve situacoes situacao
diferentes diversos diversas contextos contexto significados significado uso
estrategias estrategia recursos recurso tecnologias digitais digital
com sem apoio utilizando incluindo considerando tais como exemplo exemplos
relacoes relacao entre outros outras cotidiano vida real
""".split())


def tokens(texto: str) -> list[str]:
    palavras = re.findall(r"[a-z0-9]+", sem_acentos(texto.lower()))
    return [
        p[:RADICAL] for p in palavras
        if len(p) >= TAMANHO_MINIMO and not p.isdigit()
        and p not in PALAVRAS_FUNCIONAIS and p not in TERMOS_DE_ENUNCIADO
    ]


def gerar_vocabulario(taxonomia: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for h in taxonomia.itertuples(index=False):
        radicais = sorted(set(tokens(f"{h.objeto_conhecimento} {h.texto_habilidade}")))
        linhas += [{"habilidade": h.codigo, "radical": r} for r in radicais]
    vocab = pd.DataFrame(linhas)
    n = taxonomia["codigo"].nunique()
    df = vocab.groupby("radical")["habilidade"].nunique()
    vocab["idf"] = vocab["radical"].map(lambda r: round(math.log(n / df[r]), 6))
    return vocab


def pontuar(enunciados: pd.Series, vocab: pd.DataFrame, habilidades: list[str]) -> pd.DataFrame:
    """Matriz item x habilidade com a pontuação heurística bruta."""
    por_habilidade = {h: dict(zip(g["radical"], g["idf"])) for h, g in vocab.groupby("habilidade")}
    linhas = []
    for texto in enunciados:
        presentes = set(tokens(texto))
        linhas.append([
            sum(idf for r, idf in por_habilidade.get(h, {}).items() if r in presentes)
            / math.sqrt(max(len(por_habilidade.get(h, {})), 1))
            for h in habilidades
        ])
    return pd.DataFrame(linhas, index=enunciados.index, columns=habilidades)


def main() -> int:
    taxonomia = pd.read_csv(config.ARQ_BNCC, keep_default_na=False)
    vocab = gerar_vocabulario(taxonomia)
    vocab.to_csv(config.ARQ_VOCABULARIO, index=False, encoding="utf-8")
    por_hab = vocab.groupby("habilidade").size()
    print(f"gravado {config.ARQ_VOCABULARIO}: {len(vocab)} pares, {vocab['radical'].nunique()} radicais")
    print(f"radicais por habilidade: mín {por_hab.min()}, mediana {por_hab.median():.0f}, máx {por_hab.max()}")
    print("exemplo EF09MA13:", vocab.loc[vocab["habilidade"] == "EF09MA13", "radical"].tolist())
    return 0


if __name__ == "__main__":
    sys.exit(main())
