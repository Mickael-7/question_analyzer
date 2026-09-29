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
```

## Fontes de dados

- Taxonomia BNCC: [bncc.dev](https://bncc.dev) (`bncc-dev/bncc-dados`, tag `dados-2026.07.1`), licença CC BY 4.0.
- Questões e alinhamentos: ver `dados/referencia/fontes.csv`.
