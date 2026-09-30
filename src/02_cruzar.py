"""Passo 3.3/3.4: rótulo de referência por cruzamento documental e verificação V6.

Entrada: 02_extraidos/itens.csv e as tabelas de dados/referencia
Saída:   03_rotulados/itens_rotulados.csv
         03_rotulados/relatorio_cruzamento.md (V6)

Para cada item, o descritor de origem é traduzido em habilidades da BNCC:
- itens do 9º ano (SAEB D1-D37): o descritor SAEB é levado ao código Paebes
  pelo Detalhamento (2026) ou, na falta dele, pela Correlação (2023), e o
  código Paebes às habilidades pelo Detalhamento;
- itens do 5º ano (Paebes D0xx_M): alinhamento direto do Material do
  professor do 5º ano, quando o descritor consta dele.
Só entram habilidades que existem na BNCC; as exclusivas do Currículo do ES
ficam registradas à parte. O rótulo nunca é lido pelo script de etiquetagem.
"""
import sys

import pandas as pd

import config

SEP = "|"
# Ordem de preferência das fontes de equivalência SAEB -> Paebes.
PREFERENCIA_EQUIVALENCIA = [
    "detalhamento_paebes2025_saeb2001_9ano.pdf",
    "CORRELACAO-DE-DESCRITORES-9-ANO-EF-Matematica-1.pdf",
]
ETAPA_DO_ANO = {5: range(1, 6), 9: range(6, 10)}  # anos iniciais / anos finais


def carregar():
    itens = pd.read_csv(config.ARQ_ITENS, keep_default_na=False)
    alinhamento = pd.read_csv(config.ARQ_ALINHAMENTO, keep_default_na=False)
    alinhamento["na_bncc"] = alinhamento["na_bncc"].astype(str) == "True"
    equivalencia = pd.read_csv(config.ARQ_EQUIVALENCIA, keep_default_na=False)
    taxonomia = pd.read_csv(config.ARQ_BNCC, keep_default_na=False)
    return itens, alinhamento, equivalencia, taxonomia


def traduzir(item, alinhamento: pd.DataFrame, equivalencia: pd.DataFrame) -> dict:
    """Devolve as linhas de alinhamento que rotulam o item e a cadeia de tradução."""
    ano = item.ano
    base = alinhamento[alinhamento["ano_aplicacao"] == ano]

    direto = base[(base["codificacao"] == item.codificacao) & (base["descritor"] == item.descritor)]
    if len(direto):
        cadeia = f"{item.codificacao}:{item.descritor} -> BNCC [{direto['documento'].iloc[0]}]"
        return {"linhas": direto, "cadeia": cadeia, "saltos": 1}

    if item.codificacao == "SAEB_9EF":
        for documento in PREFERENCIA_EQUIVALENCIA:
            eq = equivalencia[
                (equivalencia["documento"] == documento)
                & (equivalencia["descritor_origem"] == item.descritor)
            ]
            if eq.empty:
                continue
            destino = eq["descritor_destino"].iloc[0]
            linhas = base[(base["codificacao"] == "PAEBES_M") & (base["descritor"] == destino)]
            if len(linhas):
                cadeia = (
                    f"SAEB_9EF:{item.descritor} -> PAEBES_M:{destino} [{documento}] "
                    f"-> BNCC [{linhas['documento'].iloc[0]}]"
                )
                saltos = 2 if documento == linhas["documento"].iloc[0] else 3
                return {"linhas": linhas, "cadeia": cadeia, "saltos": saltos}

    return {"linhas": base.iloc[0:0], "cadeia": "", "saltos": 0}


def rotular(itens, alinhamento, equivalencia, taxonomia) -> pd.DataFrame:
    unidade = dict(zip(taxonomia["codigo"], taxonomia["unidade_tematica"]))
    registros = []
    for item in itens.itertuples(index=False):
        t = traduzir(item, alinhamento, equivalencia)
        linhas = t["linhas"]
        bncc = sorted(set(linhas.loc[linhas["na_bncc"], "habilidade"]))
        fora = sorted(set(linhas.loc[~linhas["na_bncc"], "habilidade"]))
        uts_doc = sorted(set(linhas["unidade_tematica_doc"]) - {""})
        uts_bncc = sorted({unidade[h] for h in bncc})
        registros.append({
            "habilidades_referencia": SEP.join(bncc),
            "n_habilidades_referencia": len(bncc),
            "habilidades_fora_bncc": SEP.join(fora),
            "cadeia_traducao": t["cadeia"],
            "saltos_traducao": t["saltos"],
            # Unidade temática esperada (V2): a declarada pelo documento de
            # alinhamento; na falta dela, a das habilidades de referência, se única.
            "unidade_tematica_esperada": (
                uts_doc[0] if len(uts_doc) == 1 else (uts_bncc[0] if len(uts_bncc) == 1 else "")
            ),
            "status_rotulo": "rotulado" if bncc else "sem_alinhamento",
        })
    return pd.concat([itens.reset_index(drop=True), pd.DataFrame(registros)], axis=1)


def tabela_md(df: pd.DataFrame) -> str:
    colunas = [str(c) for c in df.columns]
    linhas = ["| " + " | ".join(colunas) + " |", "|" + "---|" * len(colunas)]
    linhas += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(linhas)


def relatorio_v6(rot, alinhamento, equivalencia, taxonomia) -> str:
    ano_hab = dict(zip(taxonomia["codigo"], taxonomia["ano"].astype(int)))
    unidade = dict(zip(taxonomia["codigo"], taxonomia["unidade_tematica"]))
    partes = [
        "# Relatório do cruzamento documental (V6)",
        "",
        f"Anos com rótulo de referência usado nas métricas (config.ANOS_COM_ROTULO): {config.ANOS_COM_ROTULO}. "
        "Os itens dos demais anos são etiquetados e entram em V1, V3, V4 e V5.",
        "",
    ]

    # 1. descritores e itens
    linhas = []
    for ano, grupo in rot.groupby("ano"):
        aptos = grupo[grupo["apto_verificacao"].astype(str) == "True"]
        desc = grupo.groupby("descritor")["status_rotulo"].first()
        linhas.append({
            "ano": ano,
            "descritores_na_fonte": len(desc),
            "descritores_com_habilidade": int((desc == "rotulado").sum()),
            "itens": len(grupo),
            "itens_sem_rotulo": int((grupo["status_rotulo"] != "rotulado").sum()),
            "aptos": len(aptos),
            "aptos_sem_rotulo": int((aptos["status_rotulo"] != "rotulado").sum()),
            "habilidades_por_item_rotulado": round(
                grupo.loc[grupo["status_rotulo"] == "rotulado", "n_habilidades_referencia"].mean(), 2
            ) if (grupo["status_rotulo"] == "rotulado").any() else "-",
        })
    partes += ["## Cobertura do alinhamento", "", tabela_md(pd.DataFrame(linhas)), ""]

    sem = rot[rot["status_rotulo"] != "rotulado"].groupby(["ano", "descritor"]).size()
    partes += ["Descritores sem habilidade correspondente (itens):", ""]
    partes += [f"- {ano}º ano, {d}: {n}" for (ano, d), n in sem.items()] or ["- nenhum"]
    partes.append("")

    # 2. habilidades inalcançáveis
    partes += ["## Habilidades inalcançáveis", "",
               "Habilidades da etapa que não figuram em nenhum descritor do alinhamento usado para a etapa.", ""]
    for ano, anos_etapa in ETAPA_DO_ANO.items():
        etapa = taxonomia[taxonomia["ano"].astype(int).isin(anos_etapa)]
        alcancaveis = set(alinhamento.loc[alinhamento["ano_aplicacao"] == ano, "habilidade"])
        inalc = etapa[~etapa["codigo"].isin(alcancaveis)]
        partes.append(
            f"- itens do {ano}º ano (etapa {min(anos_etapa)}º-{max(anos_etapa)}º): "
            f"{len(inalc)} de {len(etapa)} habilidades inalcançáveis"
        )
        por_ut = inalc.groupby("unidade_tematica").size().to_dict()
        partes.append(f"  - por unidade temática: {por_ut}")
    partes.append("")

    # 3. descritores com unidades temáticas incompatíveis
    partes += ["## Descritores que mapeiam para unidades temáticas diferentes", ""]
    bncc = alinhamento[alinhamento["na_bncc"]]
    alertas = []
    for (ano, cod, desc), g in bncc.groupby(["ano_aplicacao", "codificacao", "descritor"]):
        uts = sorted({unidade[h] for h in g["habilidade"]})
        if len(uts) > 1:
            alertas.append(f"- {ano}º ano, {desc}: {', '.join(f'{h} ({unidade[h]})' for h in g['habilidade'])}")
    partes += alertas or ["- nenhum"]
    partes.append("")

    # 4. distribuição por ano das habilidades de referência (decisão da seção 3.2.1)
    partes += ["## Distribuição por ano das habilidades de referência", "",
               "Base para decidir se as candidatas são restritas ao ano do item (seção 3.2.1).", ""]
    for ano, grupo in rot[rot["status_rotulo"] == "rotulado"].groupby("ano"):
        for nome, subset in [("todos os itens rotulados", grupo),
                             ("itens aptos", grupo[grupo["apto_verificacao"].astype(str) == "True"])]:
            anos = [ano_hab[h] for hs in subset["habilidades_referencia"] for h in hs.split(SEP) if h]
            if not anos:
                continue
            dist = {int(k): int(v) for k, v in pd.Series(anos).value_counts().sort_index().items()}
            fora_do_ano = sum(1 for a in anos if a != ano)
            itens_so_outros = sum(
                1 for hs in subset["habilidades_referencia"]
                if hs and all(ano_hab[h] != ano for h in hs.split(SEP))
            )
            partes.append(
                f"- {ano}º ano, {nome}: {dist} | pares habilidade-item fora do ano do item: "
                f"{fora_do_ano}/{len(anos)} | itens cujo rótulo não tem nenhuma habilidade do próprio ano: "
                f"{itens_so_outros}/{len(subset)}"
            )
    partes.append("")

    # 5. insumo documental
    fora = alinhamento[~alinhamento["na_bncc"]]
    partes += ["## Qualidade do insumo documental", "",
               f"- habilidades exclusivas do Currículo do ES citadas no alinhamento (fora da BNCC): "
               f"{sorted(set(fora['habilidade']))}, em {sorted(set(fora['descritor']))}",
               f"- itens com cadeia de 3 saltos (duas fontes de equivalência): "
               f"{int((rot['saltos_traducao'] == 3).sum())}", ""]
    piv = equivalencia.pivot_table(index="descritor_origem", columns="documento",
                                   values="descritor_destino", aggfunc="first")
    if piv.shape[1] == 2:
        a, b = piv.columns
        piv = piv.reindex(sorted(piv.index, key=lambda s: int(s[1:])))
        div = piv[piv[a].fillna("-") != piv[b].fillna("-")].fillna("-")
        partes += [f"Equivalências SAEB -> Paebes divergentes entre {a} e {b}:", "",
                   tabela_md(div.reset_index()), ""]
    return "\n".join(partes)


def main() -> int:
    itens, alinhamento, equivalencia, taxonomia = carregar()
    rot = rotular(itens, alinhamento, equivalencia, taxonomia)
    config.ROTULADOS.mkdir(parents=True, exist_ok=True)
    rot.to_csv(config.ARQ_ROTULADOS, index=False, encoding="utf-8")
    texto = relatorio_v6(rot, alinhamento, equivalencia, taxonomia)
    (config.ROTULADOS / "relatorio_cruzamento.md").write_text(texto, encoding="utf-8")
    print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
