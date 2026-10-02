"""Passo 2: extração dos itens dos PDFs.

Para cada fonte em config.FONTES, roda o adaptador correspondente em
src/extratores, junta o gabarito, marca dependência de figura e grava:
  02_extraidos/itens.csv            um item por linha
  02_extraidos/gabarito.csv         gabarito como extraído
  02_extraidos/descritores.csv      descrição dos descritores de cada fonte
  02_extraidos/relatorio_extracao.md  números para o Capítulo 4
  02_extraidos/amostra_conferencia.md itens sorteados para comparar com o PDF
"""
import importlib
import re
import sys
from difflib import SequenceMatcher

import pandas as pd

import config
from extratores import comum

CHAVE = ["fonte", "descritor", "numero"]


def item_id(linha: pd.Series) -> str:
    descritor = linha["descritor"]
    if re.fullmatch(r"D\d{1,2}", descritor):  # numeração do SAEB: D1 -> D01
        descritor = f"D{int(descritor[1:]):02d}"
    return f"{linha['fonte']}-{descritor}-{linha['numero']:02d}"


def extrair_fonte(fonte: str, spec: dict) -> dict:
    modulo = importlib.import_module(f"extratores.{spec['extrator']}")
    return modulo.extrair(config.BRUTOS / spec["arquivo"], fonte, spec["ano"])


def juntar_gabarito(itens: pd.DataFrame, gabarito: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    junto = itens.merge(gabarito, on=CHAVE, how="outer", indicator=True)
    orfaos = {
        "itens_sem_gabarito": junto.loc[junto["_merge"] == "left_only", CHAVE].to_dict("records"),
        "gabarito_sem_item": junto.loc[junto["_merge"] == "right_only", CHAVE].to_dict("records"),
    }
    junto = junto[junto["_merge"] != "right_only"].drop(columns="_merge")
    junto["gabarito"] = junto["gabarito"].fillna("")
    return junto, orfaos


def aplicar_revisao(df: pd.DataFrame) -> pd.DataFrame:
    """Incorpora dados/referencia/revisao_manual.csv sem alterar o gabarito da fonte.

    `gabarito` guarda o que está no PDF; `gabarito_revisado` é o que deve ser usado.
    `duplicata_de` aponta o mesmo item publicado em outra fonte.
    """
    df["gabarito_revisado"] = df["gabarito"]
    df["duplicata_de"] = ""
    df["revisao"] = ""
    if not config.ARQ_REVISAO.exists():
        return df
    revisao = pd.read_csv(config.ARQ_REVISAO, dtype=str, keep_default_na=False)
    desconhecidos = set(revisao["item_id"]) - set(df["item_id"])
    if desconhecidos:
        raise ValueError(f"revisao_manual.csv cita itens inexistentes: {sorted(desconhecidos)}")
    notas: dict[str, list[str]] = {}
    for r in revisao.itertuples():
        if r.tipo in ("gabarito_divergente", "gabarito_recuperado"):
            df.loc[df["item_id"] == r.item_id, "gabarito_revisado"] = r.valor
        elif r.tipo == "duplicata":
            df.loc[df["item_id"] == r.item_id, "duplicata_de"] = r.valor
        notas.setdefault(r.item_id, []).append(f"{r.tipo}: {r.descricao}")
    df["revisao"] = df["item_id"].map(lambda i: "; ".join(notas.get(i, [])))
    return df


LIMIAR_DUPLICATA = 0.9


def candidatos_duplicata(df: pd.DataFrame) -> list[dict]:
    """Pares de itens com enunciado e alternativas quase idênticos.

    O texto é normalizado (minúsculas, sem acentos, só letras e dígitos) e
    comparado por SequenceMatcher. Incluir as alternativas separa itens-modelo
    ("Observe a expressão no quadro abaixo...") que só diferem na figura.
    A confirmação é manual, em revisao_manual.csv (tipo "duplicata").
    """
    texto = (df["enunciado"] + " " + df[["alt_a", "alt_b", "alt_c", "alt_d"]].agg(" ".join, axis=1)).map(
        lambda t: re.sub(r"[^a-z0-9]", "", comum.sem_acentos(t.lower()))
    )
    ids, textos = df["item_id"].tolist(), texto.tolist()
    pares = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = textos[i], textos[j]
            if min(len(a), len(b)) < 40 or min(len(a), len(b)) / max(len(a), len(b)) < LIMIAR_DUPLICATA:
                continue
            razao = SequenceMatcher(None, a, b).ratio()
            if razao >= LIMIAR_DUPLICATA:
                pares.append({"item_a": ids[i], "item_b": ids[j], "semelhanca": round(razao, 3)})
    return pares


def marcar_figura(df: pd.DataFrame) -> pd.DataFrame:
    df["termos_deiticos"] = df["enunciado"].map(
        lambda t: "|".join(comum.termos_deiticos(t, config.TERMOS_DEITICOS))
    )
    df["sinal_imagem"] = df["n_imagens"] > 0
    df["sinal_deitico"] = df["termos_deiticos"] != ""
    df["depende_figura"] = df["sinal_imagem"] | df["sinal_deitico"]
    # Alternativas desenhadas como imagem ou vetor não chegam ao texto: o item fica incompleto.
    df["alternativas_completas"] = (df[["alt_a", "alt_b", "alt_c", "alt_d"]] != "").all(axis=1)
    df["apto_verificacao"] = (
        ~df["depende_figura"] & ~df["formula_corrompida"] & ~df["expressao_vetorial"] & df["alternativas_completas"]
    )
    return df


def tabela_md(df: pd.DataFrame) -> str:
    colunas = [str(c) for c in df.columns]
    linhas = ["| " + " | ".join(colunas) + " |", "|" + "---|" * len(colunas)]
    linhas += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(linhas)


def secao_duplicatas(df: pd.DataFrame, pares: list[dict]) -> list[str]:
    decisoes = {}
    if config.ARQ_REVISAO.exists():
        revisao = pd.read_csv(config.ARQ_REVISAO, dtype=str, keep_default_na=False)
        for r in revisao[revisao["tipo"].isin(["duplicata", "nao_duplicata"])].itertuples():
            decisoes[frozenset((r.item_id, r.valor))] = (
                "confirmada" if r.tipo == "duplicata" else "descartada (itens distintos)"
            )
    linhas = [
        f"- {p['item_a']} ~ {p['item_b']} (semelhança {p['semelhanca']}): "
        + decisoes.get(frozenset((p["item_a"], p["item_b"])), "PENDENTE de revisão")
        for p in pares
    ]
    return [
        f"## Candidatos a duplicata (semelhança >= {LIMIAR_DUPLICATA}, enunciado + alternativas)",
        "",
        *(linhas or ["- nenhum"]),
        "",
    ]


def relatorio(df: pd.DataFrame, orfaos: dict, avisos: list[str], pares: list[dict]) -> str:
    divergentes = df[(df["gabarito_inline"] != "") & (df["gabarito_inline"] != df["gabarito"])]
    por_topico = (
        df.groupby("topico_saeb")
        .agg(
            itens=("item_id", "count"),
            sinal_imagem=("sinal_imagem", "sum"),
            sinal_deitico=("sinal_deitico", "sum"),
            depende_figura=("depende_figura", "sum"),
            formula_corrompida=("formula_corrompida", "sum"),
            expressao_vetorial=("expressao_vetorial", "sum"),
            alternativas_incompletas=("alternativas_completas", lambda s: int((~s).sum())),
            aptos=("apto_verificacao", "sum"),
        )
        .reset_index()
    )
    total = por_topico.drop(columns="topico_saeb").sum()
    por_topico.loc[len(por_topico)] = ["**total**", *total.tolist()]

    partes = [
        "# Relatório de extração",
        "",
        "## Totais por fonte e ano",
        "",
        tabela_md(df.groupby(["fonte", "ano"]).agg(
            itens=("item_id", "count"),
            com_gabarito=("gabarito", lambda s: (s != "").sum()),
            depende_figura=("depende_figura", "sum"),
            aptos_verificacao=("apto_verificacao", "sum"),
        ).reset_index()),
        "",
        "## Dependência de figura por tópico da matriz SAEB",
        "",
        "Unidade temática da BNCC só é conhecida após o cruzamento (script 2).",
        "",
        tabela_md(por_topico),
        "",
        "## Conferências",
        "",
        f"- itens sem gabarito: {orfaos['itens_sem_gabarito'] or 'nenhum'}",
        f"- linhas de gabarito sem item: {orfaos['gabarito_sem_item'] or 'nenhuma'}",
        f"- itens sem alternativas no texto: {int((df['alt_a'] == '').sum())}",
        f"- gabarito impresso no enunciado divergente do gabarito final: "
        f"{divergentes['item_id'].tolist() or 'nenhum'}",
        "",
        "## Avisos e observações",
        "",
        *[f"- {a}" for a in avisos],
        *[f"- {r.item_id}: {r.observacoes}" for r in df[df["observacoes"] != ""].itertuples()],
        "",
        *secao_duplicatas(df, pares),
        "## Revisão manual (dados/referencia/revisao_manual.csv)",
        "",
        *[f"- {r.item_id}: {r.revisao}" for r in df[df["revisao"] != ""].itertuples()],
        "",
        conferencia(),
    ]
    return "\n".join(partes)


def conferencia() -> str:
    if not config.ARQ_CONFERENCIA.exists():
        return "## Conferência da amostra\n\nAinda não registrada em dados/referencia/conferencia_amostra.csv.\n"
    c = pd.read_csv(config.ARQ_CONFERENCIA, dtype=str, keep_default_na=False)
    campos = ["texto_ok", "alternativas_ok", "gabarito_ok", "figura_ok"]
    resumo = {campo: f"{(c[campo] == 'sim').sum()}/{len(c)}" for campo in campos}
    return "\n".join([
        "## Conferência da amostra (dados/referencia/conferencia_amostra.csv)",
        "",
        tabela_md(pd.DataFrame([resumo])),
        "",
        *[f"- {r.item_id}: {r.observacao}" for r in c[c["observacao"] != ""].itertuples()],
        "",
    ])


def amostra(df: pd.DataFrame) -> str:
    # Uma amostra por ano e lote: a amostra do lote 1 permanece a mesma já conferida.
    sorteio = pd.concat(
        grupo.sample(n=min(config.TAMANHO_AMOSTRA, len(grupo)), random_state=config.SEMENTE_AMOSTRA)
        for _, grupo in df.groupby(["ano", "lote"])
    )
    partes = [
        "# Amostra para conferência manual",
        "",
        f"Sorteio de {config.TAMANHO_AMOSTRA} itens por ano e lote com semente {config.SEMENTE_AMOSTRA}. "
        "Compare cada item com o PDF e anote as divergências.",
        "",
    ]
    for r in sorteio.sort_values("item_id").itertuples():
        partes += [
            f"## {r.item_id} (p. {r.pagina_inicio}-{r.pagina_fim})",
            "",
            f"**Enunciado:** {r.enunciado}",
            "",
            *[f"- {l}) {getattr(r, 'alt_' + l.lower())}" for l in "ABCD"],
            "",
            f"Gabarito: {r.gabarito} | imagens: {r.n_imagens} | dêiticos: {r.termos_deiticos or '-'}"
            f" | fórmula corrompida: {r.formula_corrompida} | apto: {r.apto_verificacao}",
            "",
            "Conferência: [ ] texto ok  [ ] alternativas ok  [ ] gabarito ok  [ ] marcação de figura ok",
            "",
        ]
    return "\n".join(partes)


def main() -> int:
    itens, gabaritos, descritores, avisos = [], [], [], []
    for fonte, spec in config.FONTES.items():
        print(f"extraindo {fonte}")
        r = extrair_fonte(fonte, spec)
        itens += r["itens"]
        gabaritos += [{"fonte": fonte, **g} for g in r["gabarito"]]
        descritores += r["descritores"]
        avisos += [f"{fonte}: {a}" for a in r["avisos"]]

    df = pd.DataFrame(itens)
    df["origem_item"] = df["origem_item"].fillna("")
    df["topico_saeb"] = df["topico_saeb"].replace("", "(fonte sem tópico SAEB)")
    gab = pd.DataFrame(gabaritos)
    df, orfaos = juntar_gabarito(df, gab)
    df.insert(0, "item_id", df.apply(item_id, axis=1))
    df["lote"] = df["fonte"].map(lambda f: config.FONTES[f]["lote"])
    df = aplicar_revisao(marcar_figura(df)).sort_values("item_id").reset_index(drop=True)

    if df["item_id"].duplicated().any():
        print(f"ERRO: item_id duplicado: {df.loc[df['item_id'].duplicated(), 'item_id'].tolist()}")
        return 1

    config.EXTRAIDOS.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.ARQ_ITENS, index=False, encoding="utf-8")
    gab.to_csv(config.EXTRAIDOS / "gabarito.csv", index=False, encoding="utf-8")
    pd.DataFrame(descritores).to_csv(config.EXTRAIDOS / "descritores.csv", index=False, encoding="utf-8")
    pares = candidatos_duplicata(df)
    texto_relatorio = relatorio(df, orfaos, avisos, pares)
    (config.EXTRAIDOS / "relatorio_extracao.md").write_text(texto_relatorio, encoding="utf-8")
    (config.EXTRAIDOS / "amostra_conferencia.md").write_text(amostra(df), encoding="utf-8")

    print(texto_relatorio)
    return 0


if __name__ == "__main__":
    sys.exit(main())
