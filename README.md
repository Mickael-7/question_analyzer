# question_analyzer

Banco público de questões de Matemática do Ensino Fundamental (5º e 9º ano) etiquetadas por habilidades da BNCC, com o pipeline reprodutível que o gera.

## Estrutura

```
dados/
  01_brutos/       PDFs originais (não versionados; ver dados/referencia/fontes.csv)
  02_extraidos/    itens.csv             saída de src/01_extrair.py
  03_rotulados/    itens_rotulados.csv   saída de src/02_cruzar.py
  04_preditos/     itens_preditos.csv    saída de src/03_etiquetar.py
  05_resultados/   tabelas e gráficos    saída de src/04_verificar.py
  06_publicacao/   banco publicado       saída de src/05_publicar.py
  referencia/      taxonomia BNCC, alinhamentos, equivalências, vocabulário, fontes
src/
  config.py        caminhos e parâmetros do método
```

Regra: nenhum script sobrescreve a entrada do anterior.

## Ambiente

O pipeline roda em Docker (Python 3.12, PyTorch CPU), com as versões fixadas em `requirements.txt`.

```bash
docker compose build
```

Para atualizar as dependências, edite `requirements.in` e gere o `requirements.txt` de novo dentro do container:

```bash
docker compose run --rm pipeline sh -c "pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.in && pip freeze > requirements.txt"
docker compose build
```

## Execução

```bash
docker compose run --rm pipeline python src/00_taxonomia.py
docker compose run --rm pipeline python src/01_extrair.py
docker compose run --rm pipeline python src/02_cruzar.py
docker compose run --rm pipeline python src/03_etiquetar.py
docker compose run --rm pipeline python src/04_verificar.py
docker compose run --rm pipeline python src/05_publicar.py
```

## Fontes de dados

- Taxonomia BNCC: [bncc.dev](https://bncc.dev) (`bncc-dev/bncc-dados`, tag `dados-2026.07.1`), licença CC BY 4.0.
- Questões e alinhamentos: ver `dados/referencia/fontes.csv`.

## Banco publicado

`dados/06_publicacao/` traz o banco em CSV (`banco_questoes.csv`, listas separadas por `|`)
e JSON (`banco_questoes.json`, listas e previsões aninhadas), com a ficha descritiva
em `FICHA_DESCRITIVA.md`. Versão 1.0.0: 425 itens (77 do 5º ano, 348 do 9º ano),
116 aptos às verificações e 350 com rótulo de referência.

| Campo | Descrição |
|---|---|
| `id` | fonte, descritor e posição do item no bloco |
| `enunciado`, `alt_a` a `alt_d` | texto do item e alternativas |
| `gabarito`, `gabarito_revisado` | gabarito publicado e gabarito após conferência (justificativa em `dados/referencia/revisao_manual.csv`) |
| `etapa_ano` | `EF5` ou `EF9` |
| `descritor_origem`, `codificacao_descritor` | descritor atribuído pela fonte e sua matriz (SAEB ou Paebes) |
| `origem_item` | avaliação de origem, quando a fonte a declara |
| `habilidades_referencia` | rótulo de referência por cruzamento documental |
| `unidade_tematica_esperada`, `cadeia_traducao`, `status_rotulo` | unidade temática, documentos e saltos que produziram o rótulo, e se há rótulo |
| `{heuristica,semantica,combinada}_top5`, `_pontuacoes`, `_margem`, `_empate_top1` | previsões das três configurações |
| `depende_figura`, `formula_corrompida`, `expressao_vetorial`, `alternativas_completas`, `apto_verificacao` | sinalização de aptidão |
| `duplicata_de` | registro equivalente em outra fonte |
| `fonte`, `fonte_titulo`, `fonte_url`, `data_acesso`, `paginas`, `lote` | proveniência |
| `licenca` | condição de uso declarada pela fonte (nenhuma declara) |

## Licença

- Código: MIT (`LICENSE`).
- Contribuições do trabalho no banco (rótulos, previsões, sinalizações, revisões e metadados): CC BY 4.0.
- Enunciados: reproduzidos de publicações da SEDU-ES que não declaram condição de uso;
  redistribuídos para pesquisa e ensino, com a fonte e a avaliação de origem de cada item.
  Os direitos sobre os enunciados permanecem com os respectivos titulares.
