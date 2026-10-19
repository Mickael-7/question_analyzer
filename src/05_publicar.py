"""Passo 3.3, Etapa 6: consolidação do banco para publicação.

Entrada: 03_rotulados/itens_rotulados.csv, 04_preditos/itens_preditos.csv,
         referencia/fontes.csv
Saída:   06_publicacao/banco_questoes.csv   uma linha por item (listas separadas por "|")
         06_publicacao/banco_questoes.json  mesmo conteúdo, com listas e previsões aninhadas
         06_publicacao/FICHA_DESCRITIVA.md  ficha no modelo de Gebru et al. (2021)

O esquema segue o Quadro 2 do Capítulo 3. Os enunciados são publicados na
íntegra, com a origem de cada item e o registro de que a fonte não declara
condição de uso (decisão de 2026-10-19, com a orientadora).
"""
import json
import sys

import pandas as pd

import config

SEP = "|"
SAIDA = config.DADOS / "06_publicacao"
CONFIGURACOES = ["heuristica", "semantica", "combinada"]
VERSAO_BANCO = "1.0.0"
DOI = "10.5281/zenodo.23486009"
LICENCA_CONTRIBUICOES = "CC BY 4.0"
ALTERNATIVAS = ["a", "b", "c", "d"]

# Ordem das colunas do CSV publicado (Quadro 2, mais lote e expressao_vetorial).
COLUNAS = [
    "id", "enunciado", "alt_a", "alt_b", "alt_c", "alt_d", "gabarito", "gabarito_revisado",
    "etapa_ano", "descritor_origem", "codificacao_descritor", "origem_item",
    "habilidades_referencia", "unidade_tematica_esperada", "cadeia_traducao", "status_rotulo",
    *[f"{c}_{campo}" for c in CONFIGURACOES for campo in ("top5", "pontuacoes", "margem", "empate_top1")],
    "depende_figura", "formula_corrompida", "expressao_vetorial", "alternativas_completas",
    "apto_verificacao", "duplicata_de", "fonte", "fonte_titulo", "fonte_url", "data_acesso",
    "paginas", "lote", "licenca",
]


def carregar() -> pd.DataFrame:
    rotulados = pd.read_csv(config.ARQ_ROTULADOS, keep_default_na=False)
    preditos = pd.read_csv(config.ARQ_PREDITOS, keep_default_na=False).drop(columns=["fonte", "ano"])
    fontes = pd.read_csv(config.ARQ_FONTES, keep_default_na=False)
    df = rotulados.merge(preditos, on="item_id", how="left", validate="one_to_one")
    df = df.merge(
        fontes[["fonte_id", "titulo", "url", "data_acesso", "licenca_transcrita"]],
        left_on="fonte", right_on="fonte_id", how="left", validate="many_to_one",
    )
    if df["titulo"].eq("").any() or df["titulo"].isna().any():
        raise SystemExit("item com fonte ausente de fontes.csv")
    return df


def montar(df: pd.DataFrame) -> pd.DataFrame:
    paginas = df.apply(
        lambda r: str(r.pagina_inicio) if r.pagina_inicio == r.pagina_fim else f"{r.pagina_inicio}-{r.pagina_fim}",
        axis=1,
    )
    banco = pd.DataFrame({
        "id": df["item_id"],
        "enunciado": df["enunciado"],
        **{f"alt_{l}": df[f"alt_{l}"] for l in ALTERNATIVAS},
        "gabarito": df["gabarito"],
        "gabarito_revisado": df["gabarito_revisado"],
        "etapa_ano": "EF" + df["ano"].astype(str),
        "descritor_origem": df["descritor"],
        "codificacao_descritor": df["codificacao"],
        "origem_item": df["origem_item"],
        "habilidades_referencia": df["habilidades_referencia"],
        "unidade_tematica_esperada": df["unidade_tematica_esperada"],
        "cadeia_traducao": df["cadeia_traducao"],
        "status_rotulo": df["status_rotulo"],
        **{f"{c}_{campo}": df[f"{c}_{campo}"] for c in CONFIGURACOES
           for campo in ("top5", "pontuacoes", "margem", "empate_top1")},
        "depende_figura": df["depende_figura"],
        "formula_corrompida": df["formula_corrompida"],
        "expressao_vetorial": df["expressao_vetorial"],
        "alternativas_completas": df["alternativas_completas"],
        "apto_verificacao": df["apto_verificacao"],
        "duplicata_de": df["duplicata_de"],
        "fonte": df["fonte"],
        "fonte_titulo": df["titulo"],
        "fonte_url": df["url"],
        "data_acesso": df["data_acesso"],
        "paginas": paginas,
        "lote": df["lote"],
        "licenca": df["licenca_transcrita"],
    })
    return banco[COLUNAS]


def _lista(valor: str) -> list[str]:
    return [v for v in str(valor).split(SEP) if v]


def _booleano(valor) -> bool:
    return str(valor) == "True"


def para_json(banco: pd.DataFrame) -> list[dict]:
    registros = []
    for r in banco.to_dict("records"):
        registros.append({
            "id": r["id"],
            "enunciado": r["enunciado"],
            "alternativas": {l.upper(): r[f"alt_{l}"] for l in ALTERNATIVAS if r[f"alt_{l}"]},
            "gabarito": r["gabarito"] or None,
            "gabarito_revisado": r["gabarito_revisado"] or None,
            "etapa_ano": r["etapa_ano"],
            "descritor_origem": {"codigo": r["descritor_origem"], "codificacao": r["codificacao_descritor"]},
            "origem_item": r["origem_item"] or None,
            "habilidades_referencia": _lista(r["habilidades_referencia"]),
            "unidade_tematica_esperada": r["unidade_tematica_esperada"] or None,
            "cadeia_traducao": r["cadeia_traducao"] or None,
            "status_rotulo": r["status_rotulo"],
            "habilidades_preditas": {
                c: {
                    "candidatas": [
                        {"codigo": cod, "pontuacao": float(p)}
                        for cod, p in zip(_lista(r[f"{c}_top5"]), _lista(r[f"{c}_pontuacoes"]))
                    ],
                    "margem": float(r[f"{c}_margem"]),
                    "empate_top1": _booleano(r[f"{c}_empate_top1"]),
                }
                for c in CONFIGURACOES
            },
            "depende_figura": _booleano(r["depende_figura"]),
            "formula_corrompida": _booleano(r["formula_corrompida"]),
            "expressao_vetorial": _booleano(r["expressao_vetorial"]),
            "alternativas_completas": _booleano(r["alternativas_completas"]),
            "apto_verificacao": _booleano(r["apto_verificacao"]),
            "duplicata_de": r["duplicata_de"] or None,
            "fonte": {
                "id": r["fonte"], "titulo": r["fonte_titulo"], "url": r["fonte_url"],
                "data_acesso": r["data_acesso"], "paginas": r["paginas"],
            },
            "lote": int(r["lote"]),
            "licenca": r["licenca"],
        })
    return registros


def ficha(banco: pd.DataFrame) -> str:
    apto = banco["apto_verificacao"].astype(str) == "True"
    rotulado = banco["habilidades_referencia"] != ""
    por_ano = banco.groupby("etapa_ano").size()
    aptos_ano = banco[apto].groupby("etapa_ano").size()
    n_fontes = banco["fonte"].nunique()
    n_dup = (banco["duplicata_de"] != "").sum()
    n_revisado = (banco["gabarito_revisado"] != banco["gabarito"]).sum()
    return f"""# Ficha descritiva do banco de questões

Banco de questões de Matemática do Ensino Fundamental etiquetado por habilidades da BNCC,
versão {VERSAO_BANCO}, DOI [{DOI}](https://doi.org/{DOI}). Ficha no modelo de Gebru et al.
(2021), *Datasheets for Datasets*.

## Motivação

- **Finalidade.** Oferecer um conjunto de questões de Matemática em português, com
  rótulo curricular rastreável, para avaliar (e, em trabalhos futuros, treinar)
  modelos de IA quanto ao reconhecimento da habilidade da BNCC mobilizada por uma questão.
- **Autoria.** Mickael de Albuquerque Silva, Trabalho de Conclusão de Curso em
  Engenharia de Software, Universidade de Pernambuco, Campus Garanhuns, sob orientação
  da Profa. Aêda Monalliza Cunha de Sousa Brito (2026).
- **Financiamento.** Nenhum.

## Composição

- **Instâncias.** {len(banco)} itens de avaliação de Matemática: {por_ano.get('EF5', 0)} do
  5º ano e {por_ano.get('EF9', 0)} do 9º ano, extraídos de {n_fontes} publicações da
  Secretaria de Estado da Educação do Espírito Santo (SEDU-ES).
- **Campos.** Enunciado, alternativas, gabarito publicado e revisado, descritor de
  origem, avaliação de origem, rótulo de referência com a cadeia de traduções,
  habilidades previstas por três configurações automáticas, sinalização de aptidão e
  proveniência até a página. Dicionário completo no Quadro 2 do trabalho e no README do repositório.
- **Rótulo de referência.** {rotulado.sum()} itens têm rótulo de referência, obtido
  por cruzamento documental entre o descritor do item e documentos oficiais de
  alinhamento da SEDU-ES. É um rótulo derivado, e não padrão-ouro: não foi
  validado por especialista.
- **Aptidão.** {apto.sum()} itens ({aptos_ano.get('EF5', 0)} do 5º e {aptos_ano.get('EF9', 0)}
  do 9º ano) têm conteúdo textual integralmente recuperável. Os demais dependem de
  figura, têm fórmula corrompida ou desenhada como vetor, ou alternativas incompletas,
  e trazem o motivo nos campos correspondentes.
- **Duplicatas.** {n_dup} registros apontam, no campo `duplicata_de`, para o mesmo item
  publicado em outra fonte. Para contar cada questão uma vez, descarte os registros com
  esse campo preenchido.
- **Erros das fontes.** {n_revisado} itens têm `gabarito_revisado` diferente do gabarito
  publicado (gabarito incorreto ou recuperado de erro de digitação); a justificativa está
  em `dados/referencia/revisao_manual.csv`.
- **Dados pessoais.** Nenhum.

## Processo de coleta

Download das publicações no portal de currículo da SEDU-ES, entre 29 set. e 2 out. 2026,
com endereço e data registrados por item. Extração automática do texto (PyMuPDF),
conferência de amostra de 30 itens contra o documento original e decisões manuais
registradas em arquivo versionado, com responsável, método e data.

## Pré-processamento e etiquetagem

O pipeline completo está no repositório (`src/`), com versões fixadas em Docker.
O rótulo de referência vem de `src/02_cruzar.py`; as previsões, de `src/03_etiquetar.py`,
que não tem acesso ao rótulo. Os parâmetros foram fixados antes dos resultados.

## Usos

- **Recomendados.** Avaliação de classificadores de habilidade da BNCC; estudos sobre
  alinhamento entre descritores de avaliação e habilidades; ponto de partida para
  anotação por especialistas.
- **Não recomendados.** Uso do rótulo de referência como verdade curricular sem
  revisão humana; generalização dos resultados para outras redes ou etapas; uso dos
  itens com `apto_verificacao = False` em tarefas que dependam apenas do texto.
- **Limitações.** Fontes de uma única rede estadual; apenas o 9º ano tem rótulo de
  referência; cobertura desigual das unidades temáticas (Geometria e Probabilidade e
  Estatística sub-representadas entre os itens aptos).

## Distribuição e licença

- **Formato.** CSV (UTF-8, listas separadas por `|`) e JSON.
- **Enunciados.** Reproduzidos das publicações da SEDU-ES, que não declaram licença
  nem condição de uso e reúnem itens de outras avaliações. São redistribuídos para fins
  de pesquisa e ensino, com a fonte e a avaliação de origem de cada item. Os direitos
  sobre os enunciados permanecem com os respectivos titulares.
- **Contribuições do trabalho** (rótulos, previsões, sinalizações, revisões e
  metadados): {LICENCA_CONTRIBUICOES}.
- **Taxonomia BNCC.** bncc.dev, versão `{config.BNCC_VERSAO}`, CC BY 4.0.
- **Código.** Licença MIT (arquivo `LICENSE` na raiz do repositório).

## Manutenção

Mantido pelo autor no repositório do trabalho. Erros podem ser relatados por *issue*.
Novas versões recebem número próprio; a versão {VERSAO_BANCO} corresponde aos
resultados relatados no TCC.
"""


def main() -> int:
    SAIDA.mkdir(parents=True, exist_ok=True)
    banco = montar(carregar())
    banco.to_csv(SAIDA / "banco_questoes.csv", index=False)
    with open(SAIDA / "banco_questoes.json", "w", encoding="utf-8") as f:
        json.dump(
            {"versao": VERSAO_BANCO, "doi": DOI, "taxonomia_bncc": config.BNCC_VERSAO, "itens": para_json(banco)},
            f, ensure_ascii=False, indent=1,
        )
    (SAIDA / "FICHA_DESCRITIVA.md").write_text(ficha(banco), encoding="utf-8")
    apto = banco["apto_verificacao"].astype(str) == "True"
    print(f"{len(banco)} itens, {apto.sum()} aptos, "
          f"{(banco['habilidades_referencia'] != '').sum()} com rótulo de referência -> {SAIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
