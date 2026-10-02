# Relatório de verificação interna e experimento-piloto

Universo: itens aptos ({'5º': 23, '9º': 45}). Métricas contra a referência nos anos [9]. Limiar de margem (V4): 0.05, fixado a priori. Espaço de rótulos: 290 habilidades.

## Experimento-piloto (9º ano)

| configuracao | itens | acuracia_top1 | acuracia_top3 | f1_macro | classes_f1 | top1_fora_do_conjunto_referencia | empates_top1 |
|---|---|---|---|---|---|---|---|
| Heurística | 45 | 8.9% | 13.3% | 0.069 | 31 | 82.2% | 1 |
| Semântica | 45 | 0.0% | 6.7% | 0.000 | 31 | 100.0% | 0 |
| Combinada | 45 | 6.7% | 8.9% | 0.044 | 31 | 80.0% | 0 |

Por unidade temática esperada:

| configuracao | unidade_tematica | itens | acuracia_top1 | acuracia_top3 |
|---|---|---|---|---|
| Heurística | Geometria | 6 | 16.7% | 16.7% |
| Heurística | Grandezas e medidas | 4 | 0.0% | 0.0% |
| Heurística | Números | 25 | 4.0% | 8.0% |
| Heurística | Álgebra | 10 | 20.0% | 30.0% |
| Semântica | Geometria | 6 | 0.0% | 16.7% |
| Semântica | Grandezas e medidas | 4 | 0.0% | 0.0% |
| Semântica | Números | 25 | 0.0% | 4.0% |
| Semântica | Álgebra | 10 | 0.0% | 10.0% |
| Combinada | Geometria | 6 | 16.7% | 16.7% |
| Combinada | Grandezas e medidas | 4 | 0.0% | 0.0% |
| Combinada | Números | 25 | 4.0% | 4.0% |
| Combinada | Álgebra | 10 | 10.0% | 20.0% |

Habilidades no conjunto de referência: 31; itens por habilidade: mín 1, mediana 3, máx 7 (tabela itens_por_habilidade_referencia.csv).

Análise complementar, definida após os resultados (não pré-registrada): posição da habilidade de referência mais bem colocada no ranking completo de 290 candidatas.

| configuracao | itens | posicao_mediana | ate_10 | ate_30 |
|---|---|---|---|---|
| Heurística | 45 | 15.000 | 37.8% | 71.1% |
| Semântica | 45 | 23.000 | 26.7% | 51.1% |
| Combinada | 45 | 24.000 | 37.8% | 55.6% |

## V1 · compatibilidade de etapa e ano

| ano_item | configuracao | itens | compativel | ano_posterior_EF | ensino_medio |
|---|---|---|---|---|---|
| 5º | Heurística | 23 | 52.2% | 30.4% | 17.4% |
| 5º | Semântica | 23 | 69.6% | 26.1% | 4.3% |
| 5º | Combinada | 23 | 73.9% | 21.7% | 4.3% |
| 9º | Heurística | 45 | 86.7% | 0.0% | 13.3% |
| 9º | Semântica | 45 | 97.8% | 0.0% | 2.2% |
| 9º | Combinada | 45 | 93.3% | 0.0% | 6.7% |

No 9º ano, 'ano posterior' é impossível por construção; a V1 informa só as previsões do EM. Distribuição dos anos previstos em v1_distribuicao_anos_previstos.csv.

## V2 · coerência de unidade temática (9º ano)

| configuracao | itens | coerencia_unidade_tematica |
|---|---|---|
| Heurística | 45 | 40.0% |
| Semântica | 45 | 42.2% |
| Combinada | 45 | 40.0% |

Matriz de confusão (combinada, linhas = esperada):

| esperada | Ensino Médio | Geometria | Grandezas e medidas | Números | Álgebra |
|---|---|---|---|---|---|
| Geometria | 0 | 4 | 2 | 0 | 0 |
| Grandezas e medidas | 2 | 0 | 2 | 0 | 0 |
| Números | 1 | 0 | 11 | 8 | 5 |
| Álgebra | 0 | 1 | 1 | 4 | 4 |

## V3 · concordância heurística × semântica (1ª posição)

Medida de estabilidade entre componentes do pipeline, não de correção.

| ano_item | itens | concordancia_heuristica_semantica |
|---|---|---|
| 5º | 23 | 8.7% |
| 9º | 45 | 6.7% |
| total | 67 | 7.5% |

## V4 · margem de decisão (ambíguo: margem < 0.05 ou empate na 1ª posição)

| configuracao | ano_item | itens | margem_q1 | margem_mediana | margem_q3 | ambiguos | empates_top1 |
|---|---|---|---|---|---|---|---|
| Heurística | 5º | 23 | 0.129 | 0.254 | 0.339 | 13.0% | 1 |
| Heurística | 9º | 45 | 0.089 | 0.205 | 0.302 | 17.8% | 1 |
| Heurística | total | 67 | 0.093 | 0.221 | 0.308 | 16.4% | 2 |
| Semântica | 5º | 23 | 0.021 | 0.040 | 0.068 | 56.5% | 0 |
| Semântica | 9º | 45 | 0.026 | 0.048 | 0.077 | 51.1% | 0 |
| Semântica | total | 67 | 0.024 | 0.042 | 0.076 | 53.7% | 0 |
| Combinada | 5º | 23 | 0.055 | 0.121 | 0.252 | 21.7% | 0 |
| Combinada | 9º | 45 | 0.037 | 0.083 | 0.171 | 28.9% | 0 |
| Combinada | total | 67 | 0.048 | 0.114 | 0.174 | 25.4% | 0 |

## V5 · cobertura e colapso (itens aptos únicos)

| configuracao | itens | habilidades_distintas | fracao_espaco_rotulos | parcela_5_mais_frequentes | mais_frequentes |
|---|---|---|---|---|---|
| Heurística | 67 | 56 | 19.3% | 17.9% | EF04MA25 (3); EF08MA06 (3); EM13MAT315 (2); EF08MA04 (2); EF08MA26 (2) |
| Semântica | 67 | 35 | 12.1% | 35.8% | EF03MA09 (8); EF08MA20 (7); EF06MA25 (3); EF02MA03 (3); EF01MA19 (3) |
| Combinada | 67 | 44 | 15.2% | 31.3% | EF08MA06 (5); EF02MA03 (4); EF04MA25 (4); EF05MA09 (4); EF03MA24 (4) |

## Erros da configuração combinada (9º ano)

42 itens com 1ª posição fora da referência; por categoria: {'unidade temática diferente': 24, 'mesma unidade temática': 15, 'etapa posterior (EM)': 3}; com acerto no top-3: 1. Ver amostra_erros.md.

## V6 · sanidade do cruzamento documental


Anos com rótulo de referência usado nas métricas (config.ANOS_COM_ROTULO): [9]. Os itens dos demais anos são etiquetados e entram em V1, V3, V4 e V5.

### Cobertura do alinhamento

| ano | descritores_na_fonte | descritores_com_habilidade | itens | itens_sem_rotulo | aptos | aptos_sem_rotulo | habilidades_por_item_rotulado |
|---|---|---|---|---|---|---|---|
| 5 | 17 | 2 | 77 | 65 | 23 | 23 | 1.0 |
| 9 | 37 | 36 | 148 | 4 | 45 | 0 | 2.0 |

Descritores sem habilidade correspondente (itens):

- 5º ano, D002_M: 3
- 5º ano, D005_M: 3
- 5º ano, D011_M: 3
- 5º ano, D013_M: 8
- 5º ano, D014_M: 3
- 5º ano, D022_M: 6
- 5º ano, D023_M: 6
- 5º ano, D024_M: 3
- 5º ano, D042_M: 3
- 5º ano, D044_M: 3
- 5º ano, D060_M: 3
- 5º ano, D065_M: 6
- 5º ano, D106_M: 3
- 5º ano, D113_M: 9
- 5º ano, D114_M: 3
- 9º ano, D7: 4

### Habilidades inalcançáveis

Habilidades da etapa que não figuram em nenhum descritor do alinhamento usado para a etapa.

- itens do 5º ano (etapa 1º-5º): 121 de 126 habilidades inalcançáveis
  - por unidade temática: {'Geometria': 20, 'Grandezas e medidas': 27, 'Números': 42, 'Probabilidade e estatística': 16, 'Álgebra': 16}
- itens do 9º ano (etapa 6º-9º): 67 de 121 habilidades inalcançáveis
  - por unidade temática: {'Geometria': 21, 'Grandezas e medidas': 6, 'Números': 16, 'Probabilidade e estatística': 14, 'Álgebra': 10}

### Descritores que mapeiam para unidades temáticas diferentes

- 9º ano, D057_M: EF06MA29 (Grandezas e medidas), EF09MA16 (Geometria)
- 9º ano, D077_M: EF08MA06 (Álgebra), EF08MA08 (Álgebra), EF08MA14 (Geometria)
- 9º ano, D116_M: EF07MA37 (Probabilidade e estatística), EF07MA24 (Geometria), EF09MA12 (Geometria)

### Distribuição por ano das habilidades de referência

Base para decidir se as candidatas são restritas ao ano do item (seção 3.2.1).

- 5º ano, todos os itens rotulados: {5: 12} | pares habilidade-item fora do ano do item: 0/12 | itens cujo rótulo não tem nenhuma habilidade do próprio ano: 0/12
- 9º ano, todos os itens rotulados: {6: 72, 7: 100, 8: 60, 9: 56} | pares habilidade-item fora do ano do item: 232/288 | itens cujo rótulo não tem nenhuma habilidade do próprio ano: 96/144
- 9º ano, itens aptos: {6: 20, 7: 36, 8: 16, 9: 16} | pares habilidade-item fora do ano do item: 72/88 | itens cujo rótulo não tem nenhuma habilidade do próprio ano: 29/45

### Qualidade do insumo documental

- habilidades exclusivas do Currículo do ES citadas no alinhamento (fora da BNCC): ['EF09MA24', 'EF09MA25', 'EF09MA26'], em ['D038_M', 'D049_M', 'D087_M']
- itens com cadeia de 3 saltos (duas fontes de equivalência): 4

Equivalências SAEB -> Paebes divergentes entre CORRELACAO-DE-DESCRITORES-9-ANO-EF-Matematica-1.pdf e detalhamento_paebes2025_saeb2001_9ano.pdf:

| descritor_origem | CORRELACAO-DE-DESCRITORES-9-ANO-EF-Matematica-1.pdf | detalhamento_paebes2025_saeb2001_9ano.pdf |
|---|---|---|
| D1 | - | D044_M |
| D6 | - | D144_M |
| D9 | D048_M | D043_M |
| D19 | D035_M | D148_M |
| D27 | D029_M | - |
| D29 | D042_M | D039_M |
| D31 | D122_M | D087_M |
| D35 | - | D154_M |