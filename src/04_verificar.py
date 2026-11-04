"""Passo 5: verificação interna (V1-V6) e métricas do experimento-piloto.

Entrada: 03_rotulados/itens_rotulados.csv, 04_preditos/itens_preditos.csv,
         dados/referencia/bncc_matematica.csv
Saída:   05_resultados/relatorio_verificacao.md   relatório para o Capítulo 4
         05_resultados/*.csv                      tabelas
         05_resultados/fig_*.png                  figuras
         05_resultados/amostra_erros.md           erros para a análise qualitativa

Universo: itens aptos (apto_verificacao). Métricas contra o rótulo de referência
(acurácia top-1/top-3, F1 macro, V2) só nos anos de config.ANOS_COM_ROTULO.
Itens com `duplicata_de` preenchido são contados uma única vez nos totais que
somam os dois anos.

Definições:
- acurácia top-k: proporção de itens com alguma habilidade de referência entre as k primeiras previstas;
- F1 macro: multirrótulo, previsão = 1ª posição, classes = habilidades presentes na referência;
- fora do conjunto: proporção de 1ª posições que não pertencem a nenhuma habilidade de referência;
- V1: ano da habilidade prevista <= ano do item (EM conta como posterior);
- V2: unidade temática da 1ª posição = unidade temática esperada (documento de alinhamento);
- V3: 1ª posição da heurística = 1ª posição da semântica;
- V4: proporção de itens com margem (1ª - 2ª) abaixo de config.LIMIAR_MARGEM, ou empate;
- V5: habilidades distintas em 1ª posição sobre o total do espaço de rótulos.

Análises complementares, definidas após os resultados (não pré-registradas):
- top-k para k em KS, com posição no ranking completo e empate resolvido pela ordem do
  código, como na lista de candidatas do pipeline;
- linhas de base: aleatória (valor exato e simulação) e classe mais frequente (k habilidades
  mais frequentes na referência, calculadas no outro lote e no próprio conjunto);
- intervalo de Wilson de 95% e teste de McNemar exato, pareado nos mesmos itens.
"""
import sys
from collections import Counter
from math import comb, sqrt

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import f1_score
from sklearn.preprocessing import MultiLabelBinarizer

import config

SEP = "|"
CONFIGURACOES = ["heuristica", "semantica", "combinada"]
NOMES = {"heuristica": "Heurística", "semantica": "Semântica", "combinada": "Combinada"}
# Paleta de referência (skill dataviz), validada para 3 séries no tema claro.
CORES = {"heuristica": "#2a78d6", "semantica": "#eb6834", "combinada": "#1baf7a"}
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
SEQUENCIAL = ["#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
RESULTADOS = config.RESULTADOS
KS = [1, 3, 5, 10, 20, 30]  # k = 1 e 3 definidos a priori; os demais são complementares
N_SIM, SEMENTE = 2000, 42  # linha de base aleatória simulada
ALEATORIA = "Aleatória"
FREQ_CRUZADO = "Classe mais frequente (outro lote)"
FREQ_AMOSTRA = "Classe mais frequente (no conjunto)"


# ---------------------------------------------------------------- dados

def carregar():
    rot = pd.read_csv(config.ARQ_ROTULADOS, keep_default_na=False)
    pred = pd.read_csv(config.ARQ_PREDITOS, keep_default_na=False).drop(columns=["fonte", "ano"])
    tax = pd.read_csv(config.ARQ_BNCC, keep_default_na=False)
    df = rot.merge(pred, on="item_id", how="inner", validate="one_to_one")
    df = df[df["apto_verificacao"].astype(str) == "True"].copy()
    # Duplicata do mesmo ano cujo original também é apto: o item é contado uma vez só.
    ano_de = dict(zip(rot["item_id"], rot["ano"]))
    aptos = set(df["item_id"])
    repetido = df["duplicata_de"].map(lambda d: d in aptos) & (
        df["duplicata_de"].map(ano_de) == df["ano"]
    )
    df = df[~repetido].copy()
    for c in CONFIGURACOES:
        df[f"{c}_lista"] = df[f"{c}_top{config.TOP_K}"].str.split(SEP)
        df[f"{c}_top1"] = df[f"{c}_lista"].str[0]
        df[f"{c}_empate_top1"] = df[f"{c}_empate_top1"].astype(str) == "True"
    df["refs"] = df["habilidades_referencia"].map(lambda s: [h for h in s.split(SEP) if h])
    ano = dict(zip(tax["codigo"], tax["ano"].astype(int)))
    ut = dict(zip(tax["codigo"], tax["unidade_tematica"]))
    texto = dict(zip(tax["codigo"], tax["texto_habilidade"]))
    return df, tax, ano, ut, texto


def com_rotulo(df):
    return df[df["ano"].isin(config.ANOS_COM_ROTULO) & (df["status_rotulo"] == "rotulado")]


def unicos(df):
    """Sem as duplicatas confirmadas, para totais que somam os dois anos."""
    return df[df["duplicata_de"] == ""]


def nome_ano(a: int) -> str:
    return "EM" if a == config.ANO_EM else f"{a}º"


# ---------------------------------------------------------------- métricas

def wilson(acertos: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de confiança de Wilson para uma proporção binomial."""
    p = acertos / n
    d = 1 + z**2 / n
    centro = (p + z**2 / (2 * n)) / d
    meia = z * sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return max(0.0, centro - meia), min(1.0, centro + meia)


def ordenar(s: pd.Series) -> list[str]:
    """Ranking completo; empate resolvido pela ordem do código, como na Etapa 4."""
    return sorted(s.index, key=lambda h: (-s[h], h))


def pontuacoes() -> dict[str, pd.DataFrame]:
    return {c: pd.read_csv(config.PREDITOS / f"pontuacoes_{c}.csv", index_col=0) for c in CONFIGURACOES}


def rankings_pipeline(r, pont) -> dict[str, list[list[str]]]:
    return {NOMES[c]: [ordenar(pont[c].loc[item]) for item in r["item_id"]] for c in CONFIGURACOES}


def rankings_mais_frequente(r, todas: list[str], cruzado: bool) -> list[list[str]]:
    """Mesmo ranking para todos os itens: habilidades por frequência no rótulo de referência
    (empate pela ordem do código), seguidas das demais candidatas. Com `cruzado`, a
    frequência vem só do outro lote, para não usar os itens avaliados."""
    refs, lotes = list(r["refs"]), list(r["lote"])
    rankings = []
    for i in range(len(refs)):
        base = [refs[j] for j in range(len(refs)) if not cruzado or lotes[j] != lotes[i]]
        freq = Counter(h for R in base for h in R)
        topo = sorted(freq, key=lambda h: (-freq[h], h))
        rankings.append(topo + sorted(set(todas) - set(topo)))
    return rankings


def acertos_topk(rankings: list[list[str]], refs, k: int) -> np.ndarray:
    return np.array([any(h in R for h in rk[:k]) for rk, R in zip(rankings, refs)])


def aleatoria_exata(refs, n_candidatas: int, k: int) -> float:
    """P(alguma referência entre as k primeiras) = 1 - C(n - r, k) / C(n, k), média nos itens."""
    return float(np.mean([1 - comb(n_candidatas - len(R), k) / comb(n_candidatas, k) for R in refs]))


def aleatoria_simulada(refs, n_candidatas: int) -> np.ndarray:
    """Melhor posição da referência em N_SIM ordenações aleatórias (matriz simulações × itens)."""
    rng = np.random.default_rng(SEMENTE)
    melhor = np.empty((N_SIM, len(refs)))
    for j, R in enumerate(refs):
        posicoes = rng.random((N_SIM, n_candidatas)).argsort(axis=1)[:, :len(R)]
        melhor[:, j] = posicoes.min(axis=1) + 1
    return melhor


def metricas_referencia(df, todas: list[str], rk: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    r = com_rotulo(df)
    classes = sorted({h for refs in r["refs"] for h in refs})
    mlb = MultiLabelBinarizer(classes=classes)
    y_true = mlb.fit_transform(r["refs"])
    n = len(r)
    linhas, por_ut = [], []

    def linha(nome, acerto1, acerto3, top1, empates):
        i1, i3 = wilson(int(np.sum(acerto1)), n), wilson(int(np.sum(acerto3)), n)
        y_pred = mlb.transform([[t] if t in classes else [] for t in top1])
        return {
            "configuracao": nome, "itens": n,
            "acuracia_top1": np.mean(acerto1), "top1_ic_inf": i1[0], "top1_ic_sup": i1[1],
            "acuracia_top3": np.mean(acerto3), "top3_ic_inf": i3[0], "top3_ic_sup": i3[1],
            "f1_macro": f1_score(y_true, y_pred, average="macro", zero_division=0),
            "classes_f1": len(classes),
            "top1_fora_do_conjunto_referencia": np.mean([t not in classes for t in top1]),
            "empates_top1": empates,
        }

    # Linhas de base (complementares). A aleatória não tem previsão por item: valor exato,
    # intervalo de 2,5% a 97,5% da simulação, sem F1.
    melhor = aleatoria_simulada(list(r["refs"]), len(todas))
    sim1, sim3 = (melhor <= 1).mean(axis=1), (melhor <= 3).mean(axis=1)
    linhas.append({"configuracao": ALEATORIA, "itens": n,
                   "acuracia_top1": aleatoria_exata(r["refs"], len(todas), 1),
                   "top1_ic_inf": np.percentile(sim1, 2.5), "top1_ic_sup": np.percentile(sim1, 97.5),
                   "acuracia_top3": aleatoria_exata(r["refs"], len(todas), 3),
                   "top3_ic_inf": np.percentile(sim3, 2.5), "top3_ic_sup": np.percentile(sim3, 97.5)})
    for nome in (FREQ_CRUZADO, FREQ_AMOSTRA):
        rf = rk[nome]
        linhas.append(linha(nome, acertos_topk(rf, r["refs"], 1), acertos_topk(rf, r["refs"], 3),
                            [x[0] for x in rf], 0))
    for c in CONFIGURACOES:
        acerto1 = [lst[0] in refs for lst, refs in zip(r[f"{c}_lista"], r["refs"])]
        acerto3 = [any(h in refs for h in lst[:3]) for lst, refs in zip(r[f"{c}_lista"], r["refs"])]
        linhas.append(linha(NOMES[c], acerto1, acerto3, list(r[f"{c}_top1"]),
                            int(r[f"{c}_empate_top1"].sum())))
        tmp = r.assign(a1=acerto1, a3=acerto3)
        for u, g in tmp.groupby("unidade_tematica_esperada"):
            por_ut.append({"configuracao": NOMES[c], "unidade_tematica": u or "(não informada)",
                           "itens": len(g), "acuracia_top1": g["a1"].mean(), "acuracia_top3": g["a3"].mean()})
    contagem = (pd.Series([h for refs in r["refs"] for h in refs]).value_counts()
                .rename_axis("habilidade").reset_index(name="itens"))
    return (pd.DataFrame(linhas).astype({"classes_f1": "Int64", "empates_top1": "Int64"}),
            pd.DataFrame(por_ut), contagem)


def robustez_por_lote(df) -> pd.DataFrame:
    """Métricas do 9º ano separadas por lote. Definida antes da execução sobre o lote 2:
    os itens do lote 2 não influenciaram nenhuma escolha de método e funcionam como
    conjunto de verificação independente."""
    linhas = []
    for lote, g in com_rotulo(df).groupby("lote"):
        for c in CONFIGURACOES:
            linhas.append({
                "lote": int(lote), "configuracao": NOMES[c], "itens": len(g),
                "acuracia_top1": np.mean([l[0] in refs for l, refs in zip(g[f"{c}_lista"], g["refs"])]),
                "acuracia_top3": np.mean([any(h in refs for h in l[:3]) for l, refs in zip(g[f"{c}_lista"], g["refs"])]),
            })
    return pd.DataFrame(linhas)


def posicao_referencia(df, rk: dict) -> pd.DataFrame:
    """Análise complementar, definida após os resultados (não pré-registrada):
    posição, no ranking completo, da habilidade de referência mais bem colocada
    (empate resolvido pela ordem do código, como na lista de candidatas)."""
    r = com_rotulo(df)
    linhas = []
    for nome in map(NOMES.get, CONFIGURACOES):
        posicoes = np.array([min(rk_i.index(h) for h in R) + 1 for rk_i, R in zip(rk[nome], r["refs"])])
        linhas.append({"configuracao": nome, "itens": len(r),
                       "posicao_mediana": float(np.median(posicoes)),
                       "ate_10": float(np.mean(posicoes <= 10)), "ate_30": float(np.mean(posicoes <= 30))})
    return pd.DataFrame(linhas)


def topk(df, todas: list[str], rk: dict) -> pd.DataFrame:
    """Proporção de itens com alguma referência entre as k primeiras candidatas, para as três
    configurações e as linhas de base. IC de Wilson de 95%; na aleatória, valor exato e
    intervalo de 2,5% a 97,5% das simulações."""
    r = com_rotulo(df)
    n = len(r)
    melhor = aleatoria_simulada(list(r["refs"]), len(todas))
    linhas = []
    for k in KS:
        for nome in [NOMES[c] for c in CONFIGURACOES] + [FREQ_CRUZADO, FREQ_AMOSTRA]:
            a = int(acertos_topk(rk[nome], r["refs"], k).sum())
            inf, sup = wilson(a, n)
            linhas.append({"configuracao": nome, "k": k, "a_priori": k in (1, 3), "itens": n,
                           "acertos": a, "proporcao": a / n, "ic_inf": inf, "ic_sup": sup, "intervalo": "Wilson"})
        sim = (melhor <= k).mean(axis=1)
        linhas.append({"configuracao": ALEATORIA, "k": k, "a_priori": k in (1, 3), "itens": n,
                       "acertos": None, "proporcao": aleatoria_exata(r["refs"], len(todas), k),
                       "ic_inf": np.percentile(sim, 2.5), "ic_sup": np.percentile(sim, 97.5),
                       "intervalo": f"simulação ({N_SIM}, semente {SEMENTE})"})
    return pd.DataFrame(linhas).astype({"acertos": "Int64"})


def mcnemar(df, rk: dict) -> pd.DataFrame:
    """Teste de McNemar exato (binomial nos pares discordantes), pareado nos mesmos itens:
    heurística contra as demais configurações e a classe mais frequente."""
    r = com_rotulo(df)
    base = NOMES["heuristica"]
    linhas = []
    for outra in [NOMES["semantica"], NOMES["combinada"], FREQ_CRUZADO, FREQ_AMOSTRA]:
        for k in KS:
            a, b = acertos_topk(rk[base], r["refs"], k), acertos_topk(rk[outra], r["refs"], k)
            so_a, so_b = int((a & ~b).sum()), int((~a & b).sum())
            p = binomtest(so_a, so_a + so_b, 0.5).pvalue if so_a + so_b else 1.0
            linhas.append({"comparacao": f"{base} × {outra}", "k": k, "a_priori": k in (1, 3),
                           f"so_{base.lower()}": so_a, "so_outra": so_b, "p_valor": p})
    return pd.DataFrame(linhas)


def sensibilidade_empates(df, pont) -> pd.DataFrame:
    """Efeito da regra de desempate no top-k: ordem do código (a do pipeline), valor esperado
    com desempate aleatório e melhor caso (referência no topo do grupo empatado). Documenta
    por que a versão anterior da posição (rank mínimo) superestimava a heurística, que tem
    grupos grandes de habilidades com pontuação igual (em geral zero)."""
    r = com_rotulo(df)
    linhas = []
    for c in CONFIGURACOES:
        m = pont[c]
        grupos = []
        for item, R in zip(r["item_id"], r["refs"]):
            s = m.loc[item]
            melhor = s[list(R)].max()
            grupos.append(((s > melhor).sum(), (s == melhor).sum(), sum(s[h] == melhor for h in R),
                           min(ordenar(s).index(h) for h in R) + 1))
        for k in KS:
            esperado = [0.0 if k <= acima else 1.0 if k - acima >= g else
                        1 - comb(g - rin, k - acima) / comb(g, k - acima) for acima, g, rin, _ in grupos]
            linhas.append({"configuracao": NOMES[c], "k": k,
                           "ordem_do_codigo": np.mean([pos <= k for *_, pos in grupos]),
                           "desempate_aleatorio": float(np.mean(esperado)),
                           "melhor_caso": np.mean([acima < k for acima, *_ in grupos]),
                           "itens_com_referencia_em_pontuacao_zero": sum(
                               pont[c].loc[i, list(R)].max() == 0 for i, R in zip(r["item_id"], r["refs"]))})
    return pd.DataFrame(linhas)


def baseline_aleatorio(df, n_candidatas: int) -> pd.DataFrame:
    """Análise complementar, definida após os resultados: valor esperado das métricas de
    ranking para uma ordenação aleatória das candidatas, dado o número de habilidades de
    referência de cada item."""
    r = com_rotulo(df)
    return pd.DataFrame([{"configuracao": "Aleatória (valor esperado)", "itens": len(r),
                          "candidatas": n_candidatas,
                          **{f"top{k}": aleatoria_exata(r["refs"], n_candidatas, k) for k in KS}}])


def ablacao_anos_finais(df, ano_hab) -> pd.DataFrame:
    """Análise complementar, definida após os resultados: as mesmas pontuações, com as
    candidatas restritas às habilidades do 6º ao 9º ano. Não altera o método: as
    pontuações já calculadas são reordenadas dentro do subconjunto; na combinada, cada
    componente é renormalizado (min-max) no subconjunto, como no método original."""
    r = com_rotulo(df)
    pont = {c: pd.read_csv(config.PREDITOS / f"pontuacoes_{c}.csv", index_col=0)
            for c in ("heuristica", "semantica")}
    subconj = [h for h in pont["heuristica"].columns if 6 <= ano_hab[h] <= 9]

    def minmax(m):
        amp = (m.max(axis=1) - m.min(axis=1)).replace(0, 1)
        return m.sub(m.min(axis=1), axis=0).div(amp, axis=0)

    matrizes = {c: pont[c].loc[r["item_id"], subconj] for c in pont}
    matrizes["combinada"] = ((1 - config.PESO_SEMANTICA) * minmax(matrizes["heuristica"])
                             + config.PESO_SEMANTICA * minmax(matrizes["semantica"]))
    linhas = []
    for c in CONFIGURACOES:
        m = matrizes[c]
        a1, a3, posicoes = [], [], []
        for item, refs in zip(r["item_id"], r["refs"]):
            ordem = ordenar(m.loc[item])
            a1.append(ordem[0] in refs)
            a3.append(any(h in refs for h in ordem[:3]))
            posicoes.append(min(ordem.index(h) for h in refs if h in ordem) + 1)
        posicoes = np.array(posicoes)
        linhas.append({"configuracao": NOMES[c], "itens": len(r), "candidatas": len(subconj),
                       "acuracia_top1": float(np.mean(a1)), "acuracia_top3": float(np.mean(a3)),
                       "posicao_mediana": float(np.median(posicoes)),
                       "ate_10": float(np.mean(posicoes <= 10)), "ate_30": float(np.mean(posicoes <= 30))})
    return pd.DataFrame(linhas)


def v1(df, ano_hab) -> tuple[pd.DataFrame, pd.DataFrame]:
    linhas, dist = [], []
    for a, g in df.groupby("ano"):
        for c in CONFIGURACOES:
            anos = g[f"{c}_top1"].map(ano_hab)
            linhas.append({
                "ano_item": f"{a}º", "configuracao": NOMES[c], "itens": len(g),
                "compativel": ((anos <= a) & (anos != config.ANO_EM)).mean(),
                "ano_posterior_EF": ((anos > a) & (anos != config.ANO_EM)).mean(),
                "ensino_medio": (anos == config.ANO_EM).mean(),
            })
            for k, n in anos.value_counts().items():
                dist.append({"ano_item": f"{a}º", "configuracao": NOMES[c], "ano_previsto": int(k), "itens": int(n)})
    return pd.DataFrame(linhas), pd.DataFrame(dist)


def v2(df, ut_hab) -> tuple[pd.DataFrame, pd.DataFrame]:
    r = com_rotulo(df)
    r = r[r["unidade_tematica_esperada"] != ""]
    linhas, confusao = [], None
    for c in CONFIGURACOES:
        prevista = r[f"{c}_top1"].map(ut_hab)
        linhas.append({"configuracao": NOMES[c], "itens": len(r),
                       "coerencia_unidade_tematica": (prevista == r["unidade_tematica_esperada"]).mean()})
        if c == "combinada":
            confusao = pd.crosstab(r["unidade_tematica_esperada"], prevista,
                                   rownames=["esperada"], colnames=["prevista"])
    return pd.DataFrame(linhas), confusao


def v3(df) -> pd.DataFrame:
    linhas = [{"ano_item": f"{a}º", "itens": len(g),
               "concordancia_heuristica_semantica": (g["heuristica_top1"] == g["semantica_top1"]).mean()}
              for a, g in df.groupby("ano")]
    u = unicos(df)
    linhas.append({"ano_item": "total", "itens": len(u),
                   "concordancia_heuristica_semantica": (u["heuristica_top1"] == u["semantica_top1"]).mean()})
    return pd.DataFrame(linhas)


def v4(df) -> pd.DataFrame:
    linhas = []
    for c in CONFIGURACOES:
        for a, g in list(df.groupby("ano")) + [("total", unicos(df))]:
            m = g[f"{c}_margem"].astype(float)
            ambiguo = (m < config.LIMIAR_MARGEM) | g[f"{c}_empate_top1"]
            linhas.append({
                "configuracao": NOMES[c], "ano_item": f"{a}º" if a != "total" else a, "itens": len(g),
                "margem_q1": m.quantile(0.25), "margem_mediana": m.median(), "margem_q3": m.quantile(0.75),
                "ambiguos": ambiguo.mean(), "empates_top1": int(g[f"{c}_empate_top1"].sum()),
            })
    return pd.DataFrame(linhas)


def v5(df, tax, ano_hab) -> tuple[pd.DataFrame, pd.DataFrame]:
    u = unicos(df)
    linhas, dist = [], []
    for c in CONFIGURACOES:
        freq = u[f"{c}_top1"].value_counts()
        linhas.append({
            "configuracao": NOMES[c], "itens": len(u),
            "habilidades_distintas": freq.size,
            "fracao_espaco_rotulos": freq.size / len(tax),
            "parcela_5_mais_frequentes": freq.head(5).sum() / len(u),
            "mais_frequentes": "; ".join(f"{h} ({n})" for h, n in freq.head(5).items()),
        })
        for a, n in u[f"{c}_top1"].map(ano_hab).value_counts().items():
            dist.append({"configuracao": NOMES[c], "ano_previsto": int(a), "itens": int(n)})
    return pd.DataFrame(linhas), pd.DataFrame(dist)


def erros(df, ut_hab, ano_hab) -> pd.DataFrame:
    r = com_rotulo(df)
    linhas = []
    for row in r.itertuples():
        top = getattr(row, "combinada_lista")
        if top[0] in row.refs:
            continue
        if row.unidade_tematica_esperada and ut_hab[top[0]] == row.unidade_tematica_esperada:
            categoria = "mesma unidade temática"
        elif ano_hab[top[0]] == config.ANO_EM:
            categoria = "etapa posterior (EM)"
        else:
            categoria = "unidade temática diferente"
        linhas.append({
            "item_id": row.item_id, "categoria": categoria,
            "acerto_no_top3": any(h in row.refs for h in top[:3]),
            "referencia": SEP.join(row.refs), "previstas_top3": SEP.join(top[:3]),
            "ano_prevista": nome_ano(ano_hab[top[0]]), "enunciado": row.enunciado,
        })
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------- figuras

def estilo(ax):
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color("#c3c2b7")
    ax.tick_params(colors=INK2, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def fig_metricas(m: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
    largura, x = 0.24, np.arange(3)
    rotulos = ["Acurácia top-1", "Acurácia top-3", "F1 macro"]
    for i, c in enumerate(CONFIGURACOES):
        linha = m[m["configuracao"] == NOMES[c]].iloc[0]
        valores = [linha["acuracia_top1"], linha["acuracia_top3"], linha["f1_macro"]]
        barras = ax.bar(x + (i - 1) * (largura + 0.02), valores, largura, color=CORES[c], label=NOMES[c])
        ax.bar_label(barras, labels=[f"{v:.2f}" for v in valores], fontsize=8, color=INK2, padding=2)
    ax.set_xticks(x, rotulos)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Proporção", color=INK2, fontsize=9)
    estilo(ax)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper left")
    fig.tight_layout()
    fig.savefig(RESULTADOS / "fig_metricas_9ano.png")
    plt.close(fig)


def fig_topk(t: pd.DataFrame):
    """Figura 2: proporção de itens com a referência entre as k primeiras, por configuração e
    linha de base. Linhas de base em cinza tracejado/pontilhado; identidade nunca só pela cor."""
    series = [(NOMES[c], CORES[c], "-", "o") for c in CONFIGURACOES] + [
        (FREQ_AMOSTRA, INK2, ":", "s"), (FREQ_CRUZADO, INK2, "--", "D"), (ALEATORIA, MUTED, "--", "v")]
    fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=200)
    for nome, cor, estilo_linha, marcador in series:
        d = t[t["configuracao"] == nome].sort_values("k")
        ax.plot(d["k"], d["proporcao"] * 100, estilo_linha, color=cor, linewidth=1.6,
                marker=marcador, markersize=4.5, label=nome)
    ax.set_xticks(KS)
    ax.set_ylim(0, 100)
    ax.set_xlabel("k (número de candidatas recomendadas)", fontsize=9, color=INK2)
    ax.set_ylabel("Itens com a referência entre as k primeiras (%)", fontsize=8, color=INK2)
    estilo(ax)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    fig.tight_layout()
    fig.savefig(RESULTADOS / "fig_topk_9ano.png")
    plt.close(fig)


def fig_margens(df):
    fig, eixos = plt.subplots(1, 3, figsize=(7.2, 2.6), dpi=200, sharey=True)
    bins = np.linspace(0, 1, 21)
    for ax, c in zip(eixos, CONFIGURACOES):
        m = unicos(df)[f"{c}_margem"].astype(float)
        ax.hist(m, bins=bins, color=CORES[c], edgecolor="#fcfcfb", linewidth=1)
        ax.axvline(config.LIMIAR_MARGEM, color=INK, linewidth=1, linestyle="--")
        ax.set_title(NOMES[c], fontsize=9, color=INK)
        ax.set_xlabel("Margem (1ª − 2ª)", fontsize=8, color=INK2)
        estilo(ax)
    eixos[0].set_ylabel("Itens", fontsize=9, color=INK2)
    eixos[0].annotate(f"limiar {config.LIMIAR_MARGEM}", xy=(config.LIMIAR_MARGEM, 0.95),
                      xycoords=("data", "axes fraction"), xytext=(6, 0), textcoords="offset points",
                      fontsize=7, color=INK2, va="top")
    fig.tight_layout()
    fig.savefig(RESULTADOS / "fig_v4_margens.png")
    plt.close(fig)


def fig_anos_previstos(dist: pd.DataFrame):
    ordem = list(range(1, 10)) + [config.ANO_EM]
    fig, eixos = plt.subplots(1, 3, figsize=(7.2, 2.6), dpi=200, sharey=True)
    for ax, c in zip(eixos, CONFIGURACOES):
        d = dist[dist["configuracao"] == NOMES[c]].set_index("ano_previsto")["itens"].reindex(ordem, fill_value=0)
        ax.bar([nome_ano(a) for a in ordem], d.values, color=CORES[c], width=0.7)
        ax.set_title(NOMES[c], fontsize=9, color=INK)
        ax.tick_params(axis="x", labelsize=7)
        estilo(ax)
    eixos[0].set_ylabel("Itens (1ª posição)", fontsize=9, color=INK2)
    fig.supxlabel("Ano da habilidade prevista", fontsize=8, color=INK2)
    fig.tight_layout()
    fig.savefig(RESULTADOS / "fig_v5_anos_previstos.png")
    plt.close(fig)


def fig_confusao(conf: pd.DataFrame):
    from matplotlib.colors import LinearSegmentedColormap

    cmap = LinearSegmentedColormap.from_list("seq", SEQUENCIAL)
    fig, ax = plt.subplots(figsize=(6.4, 3.4), dpi=200)
    ax.imshow(conf.values, cmap=cmap, aspect="auto", vmin=0)
    ax.set_xticks(range(conf.shape[1]), conf.columns, rotation=25, ha="right", fontsize=8)
    ax.set_yticks(range(conf.shape[0]), conf.index, fontsize=8)
    limite = conf.values.max() * 0.55
    for i in range(conf.shape[0]):
        for j in range(conf.shape[1]):
            v = conf.values[i, j]
            ax.text(j, i, str(v), ha="center", va="center", fontsize=8,
                    color="#ffffff" if v > limite else INK)
    ax.set_xlabel("Unidade temática prevista (combinada)", fontsize=8, color=INK2)
    ax.set_ylabel("Esperada", fontsize=8, color=INK2)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.tight_layout()
    fig.savefig(RESULTADOS / "fig_v2_confusao.png")
    plt.close(fig)


# ---------------------------------------------------------------- relatório

def tabela_md(df: pd.DataFrame, pct: tuple = ()) -> str:
    def fmt(col, v):
        if not isinstance(v, str) and pd.isna(v):
            return "-"
        if col in pct:
            return f"{v * 100:.1f}%"
        if isinstance(v, float):
            return f"{v:.3f}"
        return str(v)

    cols = list(df.columns)
    linhas = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    linhas += ["| " + " | ".join(fmt(c, v) for c, v in zip(cols, row)) + " |" for row in df.itertuples(index=False)]
    return "\n".join(linhas)


def amostra_erros_md(e: pd.DataFrame, texto: dict) -> str:
    partes = ["# Erros da configuração combinada (9º ano, itens aptos)", "",
              "1ª posição fora do rótulo de referência. Para a análise qualitativa (seção 3.5).", ""]
    for r in e.itertuples():
        partes += [f"## {r.item_id} · {r.categoria}" + (" · acerto no top-3" if r.acerto_no_top3 else ""), "",
                   f"**Enunciado:** {r.enunciado}", "", "**Referência:**"]
        partes += [f"- {h}: {texto[h]}" for h in r.referencia.split(SEP)]
        partes += ["", "**Previstas (top-3):**"]
        partes += [f"- {h}: {texto[h]}" for h in r.previstas_top3.split(SEP)]
        partes.append("")
    return "\n".join(partes)


def main() -> int:
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    df, tax, ano_hab, ut_hab, texto = carregar()

    r = com_rotulo(df)
    todas = list(tax["codigo"])
    pont = pontuacoes()
    rk = rankings_pipeline(r, pont)
    rk[FREQ_CRUZADO] = rankings_mais_frequente(r, todas, cruzado=True)
    rk[FREQ_AMOSTRA] = rankings_mais_frequente(r, todas, cruzado=False)

    m, m_ut, contagem = metricas_referencia(df, todas, rk)
    pos = posicao_referencia(df, rk)
    tk = topk(df, todas, rk)
    mc = mcnemar(df, rk)
    emp = sensibilidade_empates(df, pont)
    rob = robustez_por_lote(df)
    base = pd.concat([baseline_aleatorio(df, len(tax)),
                      baseline_aleatorio(df, sum(6 <= a <= 9 for a in ano_hab.values()))])
    abl = ablacao_anos_finais(df, ano_hab)
    t1, t1_dist = v1(df, ano_hab)
    t2, conf = v2(df, ut_hab)
    t3 = v3(df)
    t4 = v4(df)
    t5, t5_dist = v5(df, tax, ano_hab)
    e = erros(df, ut_hab, ano_hab)

    for nome, tabela in [("metricas_9ano", m), ("metricas_por_unidade_tematica", m_ut),
                         ("itens_por_habilidade_referencia", contagem),
                         ("posicao_referencia_complementar", pos), ("robustez_por_lote", rob),
                         ("topk_linhas_de_base", tk), ("mcnemar_complementar", mc),
                         ("sensibilidade_empates_complementar", emp),
                         ("baseline_aleatorio_complementar", base), ("ablacao_anos_finais_complementar", abl),
                         ("v1_compatibilidade_ano", t1),
                         ("v1_distribuicao_anos_previstos", t1_dist), ("v2_coerencia_unidade", t2),
                         ("v3_concordancia", t3), ("v4_margem", t4), ("v5_cobertura", t5),
                         ("v5_anos_previstos", t5_dist), ("erros_combinada", e)]:
        tabela.to_csv(RESULTADOS / f"{nome}.csv", index=False, encoding="utf-8")
    conf.to_csv(RESULTADOS / "v2_matriz_confusao.csv", encoding="utf-8")
    fig_metricas(m)
    fig_topk(tk)
    fig_margens(df)
    fig_anos_previstos(t5_dist)
    fig_confusao(conf)
    (RESULTADOS / "amostra_erros.md").write_text(amostra_erros_md(e, texto), encoding="utf-8")

    universo = df.groupby("ano").size().to_dict()
    v6 = (config.ROTULADOS / "relatorio_cruzamento.md").read_text(encoding="utf-8")
    v6 = "\n".join(("#" + l if l.startswith("#") else l) for l in v6.splitlines()[1:])
    cat = e["categoria"].value_counts().to_dict() if len(e) else {}
    partes = [
        "# Relatório de verificação interna e experimento-piloto",
        "",
        f"Universo: itens aptos ({ {f'{k}º': v for k, v in universo.items()} }). "
        f"Métricas contra a referência nos anos {config.ANOS_COM_ROTULO}. "
        f"Limiar de margem (V4): {config.LIMIAR_MARGEM}, fixado a priori. "
        f"Espaço de rótulos: {len(tax)} habilidades.",
        "",
        "## Experimento-piloto (9º ano)", "",
        tabela_md(m, pct=("acuracia_top1", "top1_ic_inf", "top1_ic_sup", "acuracia_top3", "top3_ic_inf",
                          "top3_ic_sup", "top1_fora_do_conjunto_referencia")), "",
        "IC de Wilson de 95%; na linha aleatória, valor exato e intervalo de 2,5% a 97,5% de "
        f"{N_SIM} simulações (semente {SEMENTE}). As linhas de base são análise complementar, "
        "definida após os resultados. Classe mais frequente: as k habilidades mais frequentes no "
        "rótulo de referência, calculadas no outro lote ou no próprio conjunto (teto otimista).", "",
        f"Habilidades de referência por item: média {r['refs'].map(len).mean():.2f} "
        f"({r['refs'].map(len).sum()} pares em {len(r)} itens).", "",
        "Top-k por configuração e linha de base (k = 1 e 3 a priori; os demais, complementares; "
        "empate resolvido pela ordem do código):", "",
        tabela_md(tk.drop(columns=["itens", "intervalo"]), pct=("proporcao", "ic_inf", "ic_sup")), "",
        "Teste de McNemar exato, pareado nos mesmos itens (complementar):", "",
        tabela_md(mc), "",
        "Sensibilidade do top-k à regra de desempate (complementar). A versão anterior usava o "
        "melhor caso (rank mínimo), que superestimava a heurística:", "",
        tabela_md(emp, pct=("ordem_do_codigo", "desempate_aleatorio", "melhor_caso")), "",
        "Por unidade temática esperada:", "",
        tabela_md(m_ut, pct=("acuracia_top1", "acuracia_top3")), "",
        f"Habilidades no conjunto de referência: {len(contagem)}; itens por habilidade: "
        f"mín {contagem['itens'].min()}, mediana {contagem['itens'].median():.0f}, máx {contagem['itens'].max()} "
        "(tabela itens_por_habilidade_referencia.csv).", "",
        "Robustez por lote (definida antes da execução sobre o lote 2, que não influenciou o método):", "",
        tabela_md(rob, pct=("acuracia_top1", "acuracia_top3")), "",
        "Análise complementar, definida após os resultados (não pré-registrada): posição da habilidade "
        "de referência mais bem colocada no ranking completo de 290 candidatas (empate pela ordem do código).", "",
        tabela_md(pos, pct=("ate_10", "ate_30")), "",
        "Análise complementar, definida após os resultados: valor esperado de uma ordenação "
        "aleatória das candidatas (290 e, para comparação com a ablação, só 6º ao 9º ano).", "",
        tabela_md(base, pct=tuple(f"top{k}" for k in KS)), "",
        "Análise complementar, definida após os resultados: candidatas restritas ao 6º–9º ano, "
        "com as mesmas pontuações (o método não é alterado).", "",
        tabela_md(abl, pct=("acuracia_top1", "acuracia_top3", "ate_10", "ate_30")), "",
        "## V1 · compatibilidade de etapa e ano", "",
        tabela_md(t1, pct=("compativel", "ano_posterior_EF", "ensino_medio")), "",
        "No 9º ano, 'ano posterior' é impossível por construção; a V1 informa só as previsões do EM. "
        "Distribuição dos anos previstos em v1_distribuicao_anos_previstos.csv.", "",
        "## V2 · coerência de unidade temática (9º ano)", "",
        tabela_md(t2, pct=("coerencia_unidade_tematica",)), "",
        "Matriz de confusão (combinada, linhas = esperada):", "",
        tabela_md(conf.reset_index()), "",
        "## V3 · concordância heurística × semântica (1ª posição)", "",
        "Medida de estabilidade entre componentes do pipeline, não de correção.", "",
        tabela_md(t3, pct=("concordancia_heuristica_semantica",)), "",
        f"## V4 · margem de decisão (ambíguo: margem < {config.LIMIAR_MARGEM} ou empate na 1ª posição)", "",
        tabela_md(t4, pct=("ambiguos",)), "",
        "## V5 · cobertura e colapso (itens aptos únicos)", "",
        tabela_md(t5, pct=("fracao_espaco_rotulos", "parcela_5_mais_frequentes")), "",
        "## Erros da configuração combinada (9º ano)", "",
        f"{len(e)} itens com 1ª posição fora da referência; por categoria: {cat}; "
        f"com acerto no top-3: {int(e['acerto_no_top3'].sum()) if len(e) else 0}. Ver amostra_erros.md.", "",
        "## V6 · sanidade do cruzamento documental", "",
        v6,
    ]
    texto_rel = "\n".join(partes)
    (RESULTADOS / "relatorio_verificacao.md").write_text(texto_rel, encoding="utf-8")
    print(texto_rel.split("## V6")[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
