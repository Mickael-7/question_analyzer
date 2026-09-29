"""Passo 1: taxonomia de referência da BNCC (Matemática, Ensino Fundamental).

Baixa os CSVs derivados do bncc.dev na versão fixada em config.BNCC_VERSAO,
resolve os identificadores de unidade temática e objeto de conhecimento
para os nomes oficiais, valida e grava dados/referencia/bncc_matematica.csv.
"""
import re
import sys
import urllib.request

import pandas as pd

import config

ARQUIVOS_FONTE = ["habilidades-ef.csv", "contextos-organizacao.csv"]
SEPARADOR_OC = " | "


def baixar(nome: str) -> pd.DataFrame:
    destino = config.CACHE / config.BNCC_VERSAO / nome
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        url = f"{config.BNCC_URL_BASE}/{nome}"
        print(f"baixando {url}")
        urllib.request.urlretrieve(url, destino)
    return pd.read_csv(destino, dtype=str, keep_default_na=False)


def montar(habilidades: pd.DataFrame, contextos: pd.DataFrame) -> pd.DataFrame:
    nomes = dict(zip(contextos["id"], contextos["nome"]))
    ma = habilidades[habilidades["componente"] == "ef-comp-ma"].copy()
    ma["ano"] = ma["anos"].astype(int)
    ma = ma[ma["ano"].isin(config.ANOS_TAXONOMIA)]

    def resolver_oc(ids: str) -> str:
        return SEPARADOR_OC.join(nomes[i.strip()] for i in ids.split("|") if i.strip())

    return pd.DataFrame({
        "codigo": ma["codigo"],
        "etapa": "EF",
        "ano": ma["ano"],
        "componente": "MA",
        "unidade_tematica": ma["unidade_tematica"].map(nomes),
        "objeto_conhecimento": ma["objetos_conhecimento"].map(resolver_oc),
        "texto_habilidade": ma["texto"].str.strip(),
        "vigencia": ma["vigencia_status"],
        "fonte_pdf": ma["fonte_localizador_pdf"],
        "versao_bncc_dev": config.BNCC_VERSAO,
    }).sort_values("codigo").reset_index(drop=True)


def validar(df: pd.DataFrame) -> list[str]:
    erros = []
    padrao = re.compile(config.PADRAO_CODIGO_BNCC)
    invalidos = df.loc[~df["codigo"].map(lambda c: bool(padrao.match(c))), "codigo"]
    if len(invalidos):
        erros.append(f"códigos fora do padrão: {list(invalidos)}")
    duplicados = df.loc[df["codigo"].duplicated(), "codigo"]
    if len(duplicados):
        erros.append(f"códigos duplicados: {list(duplicados)}")
    for coluna in ["texto_habilidade", "unidade_tematica", "objeto_conhecimento"]:
        vazios = df.loc[df[coluna].isna() | (df[coluna] == ""), "codigo"]
        if len(vazios):
            erros.append(f"{coluna} vazio em: {list(vazios)}")
    ano_no_codigo = df["codigo"].str[2:4].astype(int)
    divergentes = df.loc[ano_no_codigo != df["ano"], "codigo"]
    if len(divergentes):
        erros.append(f"ano do código diverge da coluna ano: {list(divergentes)}")
    return erros


def main() -> int:
    habilidades, contextos = (baixar(n) for n in ARQUIVOS_FONTE)
    df = montar(habilidades, contextos)

    erros = validar(df)
    if erros:
        print("FALHA NA VALIDAÇÃO:")
        for e in erros:
            print(f"  - {e}")
        return 1

    config.ARQ_BNCC.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.ARQ_BNCC, index=False, encoding="utf-8")

    print(f"gravado {config.ARQ_BNCC} ({len(df)} habilidades)\n")
    print(pd.crosstab(df["unidade_tematica"], df["ano"], margins=True, margins_name="total"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
