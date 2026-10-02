"""Passo 4: etiquetagem automática.

Entrada: 03_rotulados/itens_rotulados.csv, lido SOMENTE nas colunas de
         config.COLUNAS_ETIQUETAGEM (o rótulo de referência nunca é carregado)
Saída:   04_preditos/itens_preditos.csv          top-K e margem das três configurações
         04_preditos/pontuacoes_<config>.csv     matriz item x habilidade normalizada
         04_preditos/execucao.json               parâmetros e versões da execução

Configurações (experimento-piloto, seção 3.5):
- heuristica: vocabulário curricular (src/heuristica.py, dados/referencia/vocabulario.csv)
- semantica:  similaridade de cossenos entre embeddings do enunciado e do texto da habilidade
- combinada:  média ponderada das duas, com peso config.PESO_SEMANTICA
Cada componente é normalizado por min-max sobre as habilidades candidatas do item.
"""
import json
import sys
from datetime import datetime, timezone
from importlib.metadata import version

import numpy as np
import pandas as pd

import config
import heuristica

CONFIGURACOES = ["heuristica", "semantica", "combinada"]
SEP = "|"


def carregar_itens() -> pd.DataFrame:
    itens = pd.read_csv(config.ARQ_ROTULADOS, usecols=config.COLUNAS_ETIQUETAGEM, keep_default_na=False)
    proibidas = {"habilidades_referencia", "habilidades_fora_bncc", "cadeia_traducao", "unidade_tematica_esperada"}
    vazadas = proibidas & set(itens.columns)
    if vazadas:
        raise RuntimeError(f"colunas do rótulo de referência carregadas na etiquetagem: {vazadas}")
    return itens.set_index("item_id")


def candidatas(taxonomia: pd.DataFrame, ano: int) -> pd.Series:
    """Máscara das habilidades candidatas para um item do `ano`."""
    if config.RESTRINGIR_AO_ANO:
        return taxonomia["ano"] == ano
    return pd.Series(True, index=taxonomia.index)


def similaridade(itens: pd.DataFrame, taxonomia: pd.DataFrame) -> pd.DataFrame:
    from sentence_transformers import SentenceTransformer

    modelo = SentenceTransformer(config.MODELO_EMBEDDING, revision=config.MODELO_REVISAO, device="cpu")
    e_itens = modelo.encode(itens["enunciado"].tolist(), normalize_embeddings=True, batch_size=32)
    e_hab = modelo.encode(taxonomia["texto_habilidade"].tolist(), normalize_embeddings=True, batch_size=32)
    return pd.DataFrame(e_itens @ e_hab.T, index=itens.index, columns=taxonomia["codigo"])


def normalizar(matriz: pd.DataFrame, mascaras: pd.DataFrame) -> pd.DataFrame:
    """Min-max por item, só sobre as candidatas; não candidatas recebem NaN."""
    m = matriz.where(mascaras)
    minimo, maximo = m.min(axis=1), m.max(axis=1)
    amplitude = (maximo - minimo).replace(0, np.nan)
    return m.sub(minimo, axis=0).div(amplitude, axis=0).fillna(0).where(mascaras)


def ranquear(pontuacoes: pd.DataFrame, k: int) -> pd.DataFrame:
    linhas = []
    for item_id, linha in pontuacoes.iterrows():
        ordem = linha.dropna().sort_values(ascending=False, kind="mergesort")
        top = ordem.iloc[:k]
        linhas.append({
            "item_id": item_id,
            "top": SEP.join(top.index),
            "pontuacoes": SEP.join(f"{v:.4f}" for v in top.values),
            "margem": round(float(ordem.iloc[0] - ordem.iloc[1]), 6),
        })
    return pd.DataFrame(linhas).set_index("item_id")


def main() -> int:
    if config.LIMIAR_MARGEM is None:
        print("ERRO: config.LIMIAR_MARGEM precisa ser fixado antes da etiquetagem.")
        return 1
    if not config.ARQ_VOCABULARIO.exists():
        print("ERRO: gere e versione o vocabulário antes (python src/heuristica.py).")
        return 1

    itens = carregar_itens()
    taxonomia = pd.read_csv(config.ARQ_BNCC, keep_default_na=False)
    vocab = pd.read_csv(config.ARQ_VOCABULARIO, keep_default_na=False)
    codigos = taxonomia["codigo"].tolist()
    mascaras = pd.DataFrame(
        [candidatas(taxonomia, ano).values for ano in itens["ano"]], index=itens.index, columns=codigos
    )

    print(f"{len(itens)} itens, {len(codigos)} habilidades candidatas por item "
          f"(restringir ao ano: {config.RESTRINGIR_AO_ANO})")
    brutas = {
        "heuristica": heuristica.pontuar(itens["enunciado"], vocab, codigos),
        "semantica": similaridade(itens, taxonomia),
    }
    norm = {nome: normalizar(m, mascaras) for nome, m in brutas.items()}
    norm["combinada"] = (
        config.PESO_SEMANTICA * norm["semantica"] + (1 - config.PESO_SEMANTICA) * norm["heuristica"]
    )

    config.PREDITOS.mkdir(parents=True, exist_ok=True)
    saida = itens[["fonte", "ano"]].copy()
    for nome in CONFIGURACOES:
        r = ranquear(norm[nome], config.TOP_K)
        saida[f"{nome}_top{config.TOP_K}"] = r["top"]
        saida[f"{nome}_pontuacoes"] = r["pontuacoes"]
        saida[f"{nome}_margem"] = r["margem"]
        norm[nome].round(6).to_csv(config.PREDITOS / f"pontuacoes_{nome}.csv", encoding="utf-8")
    saida["combinada_ambigua"] = saida["combinada_margem"] < config.LIMIAR_MARGEM
    saida.reset_index().to_csv(config.ARQ_PREDITOS, index=False, encoding="utf-8")

    execucao = {
        "data": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "modelo": config.MODELO_EMBEDDING,
        "modelo_revisao": config.MODELO_REVISAO,
        "peso_semantica": config.PESO_SEMANTICA,
        "limiar_margem": config.LIMIAR_MARGEM,
        "restringir_ao_ano": config.RESTRINGIR_AO_ANO,
        "top_k": config.TOP_K,
        "itens": len(itens),
        "habilidades_candidatas": len(codigos),
        "radical_heuristica": heuristica.RADICAL,
        "versoes": {p: version(p) for p in ["sentence-transformers", "torch", "pandas", "numpy"]},
    }
    (config.PREDITOS / "execucao.json").write_text(json.dumps(execucao, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"gravado {config.ARQ_PREDITOS}")
    for nome in CONFIGURACOES:
        top1 = saida[f"{nome}_top{config.TOP_K}"].str.split(SEP).str[0]
        print(f"  {nome}: {top1.nunique()} habilidades distintas em 1ª posição; "
              f"margem mediana {saida[f'{nome}_margem'].median():.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
