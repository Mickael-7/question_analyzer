# Relatório de verificação interna e experimento-piloto

Universo: itens aptos ({'5º': 23, '9º': 88}). Métricas contra a referência nos anos [9]. Limiar de margem (V4): 0.05, fixado a priori. Espaço de rótulos: 290 habilidades.

## Experimento-piloto (9º ano)

| configuracao | itens | acuracia_top1 | top1_ic_inf | top1_ic_sup | acuracia_top3 | top3_ic_inf | top3_ic_sup | f1_macro | classes_f1 | top1_fora_do_conjunto_referencia | empates_top1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Aleatória | 84 | 0.7% | 0.0% | 3.6% | 2.2% | 0.0% | 6.0% | - | - | - | - |
| Classe mais frequente (outro lote) | 84 | 11.9% | 6.6% | 20.5% | 14.3% | 8.4% | 23.3% | 0.010 | 38 | 0.0% | 0 |
| Classe mais frequente (no conjunto) | 84 | 15.5% | 9.3% | 24.7% | 29.8% | 21.0% | 40.2% | 0.007 | 38 | 0.0% | 0 |
| Heurística | 84 | 7.1% | 3.3% | 14.7% | 9.5% | 4.9% | 17.7% | 0.056 | 38 | 84.5% | 1 |
| Semântica | 84 | 0.0% | 0.0% | 4.4% | 4.8% | 1.9% | 11.6% | 0.000 | 38 | 97.6% | 0 |
| Combinada | 84 | 4.8% | 1.9% | 11.6% | 6.0% | 2.6% | 13.2% | 0.034 | 38 | 84.5% | 0 |

IC de Wilson de 95%; na linha aleatória, valor exato e intervalo de 2,5% a 97,5% de 2000 simulações (semente 42). As linhas de base são análise complementar, definida após os resultados. Classe mais frequente: as k habilidades mais frequentes no rótulo de referência, calculadas no outro lote ou no próprio conjunto (teto otimista).

Habilidades de referência por item: média 2.17 (182 pares em 84 itens).

Top-k por configuração e linha de base (k = 1 e 3 a priori; os demais, complementares; empate resolvido pela ordem do código):

| configuracao | k | a_priori | acertos | proporcao | ic_inf | ic_sup |
|---|---|---|---|---|---|---|
| Heurística | 1 | True | 6 | 7.1% | 3.3% | 14.7% |
| Semântica | 1 | True | 0 | 0.0% | 0.0% | 4.4% |
| Combinada | 1 | True | 4 | 4.8% | 1.9% | 11.6% |
| Classe mais frequente (outro lote) | 1 | True | 10 | 11.9% | 6.6% | 20.5% |
| Classe mais frequente (no conjunto) | 1 | True | 13 | 15.5% | 9.3% | 24.7% |
| Aleatória | 1 | True | - | 0.7% | 0.0% | 3.6% |
| Heurística | 3 | True | 8 | 9.5% | 4.9% | 17.7% |
| Semântica | 3 | True | 4 | 4.8% | 1.9% | 11.6% |
| Combinada | 3 | True | 5 | 6.0% | 2.6% | 13.2% |
| Classe mais frequente (outro lote) | 3 | True | 12 | 14.3% | 8.4% | 23.3% |
| Classe mais frequente (no conjunto) | 3 | True | 25 | 29.8% | 21.0% | 40.2% |
| Aleatória | 3 | True | - | 2.2% | 0.0% | 6.0% |
| Heurística | 5 | False | 10 | 11.9% | 6.6% | 20.5% |
| Semântica | 5 | False | 10 | 11.9% | 6.6% | 20.5% |
| Combinada | 5 | False | 17 | 20.2% | 13.0% | 30.0% |
| Classe mais frequente (outro lote) | 5 | False | 25 | 29.8% | 21.0% | 40.2% |
| Classe mais frequente (no conjunto) | 5 | False | 34 | 40.5% | 30.6% | 51.2% |
| Aleatória | 5 | False | - | 3.7% | 0.0% | 8.3% |
| Heurística | 10 | False | 23 | 27.4% | 19.0% | 37.7% |
| Semântica | 10 | False | 19 | 22.6% | 15.0% | 32.6% |
| Combinada | 10 | False | 27 | 32.1% | 23.1% | 42.7% |
| Classe mais frequente (outro lote) | 10 | False | 40 | 47.6% | 37.3% | 58.2% |
| Classe mais frequente (no conjunto) | 10 | False | 48 | 57.1% | 46.5% | 67.2% |
| Aleatória | 10 | False | - | 7.3% | 2.4% | 13.1% |
| Heurística | 20 | False | 29 | 34.5% | 25.2% | 45.2% |
| Semântica | 20 | False | 34 | 40.5% | 30.6% | 51.2% |
| Combinada | 20 | False | 39 | 46.4% | 36.2% | 57.0% |
| Classe mais frequente (outro lote) | 20 | False | 57 | 67.9% | 57.3% | 76.9% |
| Classe mais frequente (no conjunto) | 20 | False | 66 | 78.6% | 68.7% | 86.0% |
| Aleatória | 20 | False | - | 14.2% | 7.1% | 21.4% |
| Heurística | 30 | False | 31 | 36.9% | 27.4% | 47.6% |
| Semântica | 30 | False | 42 | 50.0% | 39.5% | 60.5% |
| Combinada | 30 | False | 43 | 51.2% | 40.7% | 61.6% |
| Classe mais frequente (outro lote) | 30 | False | 73 | 86.9% | 78.1% | 92.5% |
| Classe mais frequente (no conjunto) | 30 | False | 82 | 97.6% | 91.7% | 99.3% |
| Aleatória | 30 | False | - | 20.8% | 13.1% | 29.8% |

Teste de McNemar exato, pareado nos mesmos itens (complementar):

| comparacao | k | a_priori | so_heurística | so_outra | p_valor |
|---|---|---|---|---|---|
| Heurística × Semântica | 1 | True | 6 | 0 | 0.031 |
| Heurística × Semântica | 3 | True | 7 | 3 | 0.344 |
| Heurística × Semântica | 5 | False | 6 | 6 | 1.000 |
| Heurística × Semântica | 10 | False | 14 | 10 | 0.541 |
| Heurística × Semântica | 20 | False | 12 | 17 | 0.458 |
| Heurística × Semântica | 30 | False | 9 | 20 | 0.061 |
| Heurística × Combinada | 1 | True | 2 | 0 | 0.500 |
| Heurística × Combinada | 3 | True | 3 | 0 | 0.250 |
| Heurística × Combinada | 5 | False | 3 | 10 | 0.092 |
| Heurística × Combinada | 10 | False | 1 | 5 | 0.219 |
| Heurística × Combinada | 20 | False | 0 | 10 | 0.002 |
| Heurística × Combinada | 30 | False | 0 | 12 | 0.000 |
| Heurística × Classe mais frequente (outro lote) | 1 | True | 6 | 10 | 0.454 |
| Heurística × Classe mais frequente (outro lote) | 3 | True | 7 | 11 | 0.481 |
| Heurística × Classe mais frequente (outro lote) | 5 | False | 8 | 23 | 0.011 |
| Heurística × Classe mais frequente (outro lote) | 10 | False | 17 | 34 | 0.024 |
| Heurística × Classe mais frequente (outro lote) | 20 | False | 12 | 40 | 0.000 |
| Heurística × Classe mais frequente (outro lote) | 30 | False | 5 | 47 | 0.000 |
| Heurística × Classe mais frequente (no conjunto) | 1 | True | 6 | 13 | 0.167 |
| Heurística × Classe mais frequente (no conjunto) | 3 | True | 7 | 24 | 0.003 |
| Heurística × Classe mais frequente (no conjunto) | 5 | False | 8 | 32 | 0.000 |
| Heurística × Classe mais frequente (no conjunto) | 10 | False | 13 | 38 | 0.001 |
| Heurística × Classe mais frequente (no conjunto) | 20 | False | 9 | 46 | 0.000 |
| Heurística × Classe mais frequente (no conjunto) | 30 | False | 1 | 52 | 0.000 |

Sensibilidade do top-k à regra de desempate (complementar). A versão anterior usava o melhor caso (rank mínimo), que superestimava a heurística:

| configuracao | k | ordem_do_codigo | desempate_aleatorio | melhor_caso | itens_com_referencia_em_pontuacao_zero |
|---|---|---|---|---|---|
| Heurística | 1 | 7.1% | 7.7% | 8.3% | 43 |
| Heurística | 3 | 9.5% | 9.5% | 9.5% | 43 |
| Heurística | 5 | 11.9% | 12.9% | 16.7% | 43 |
| Heurística | 10 | 27.4% | 27.6% | 34.5% | 43 |
| Heurística | 20 | 34.5% | 36.0% | 56.0% | 43 |
| Heurística | 30 | 36.9% | 40.2% | 65.5% | 43 |
| Semântica | 1 | 0.0% | 0.0% | 0.0% | 0 |
| Semântica | 3 | 4.8% | 4.8% | 4.8% | 0 |
| Semântica | 5 | 11.9% | 11.9% | 11.9% | 0 |
| Semântica | 10 | 22.6% | 22.6% | 22.6% | 0 |
| Semântica | 20 | 40.5% | 40.5% | 40.5% | 0 |
| Semântica | 30 | 50.0% | 50.0% | 50.0% | 0 |
| Combinada | 1 | 4.8% | 4.8% | 4.8% | 0 |
| Combinada | 3 | 6.0% | 6.0% | 6.0% | 0 |
| Combinada | 5 | 20.2% | 20.2% | 20.2% | 0 |
| Combinada | 10 | 32.1% | 32.1% | 32.1% | 0 |
| Combinada | 20 | 46.4% | 46.4% | 46.4% | 0 |
| Combinada | 30 | 51.2% | 51.2% | 51.2% | 0 |

Por unidade temática esperada:

| configuracao | unidade_tematica | itens | acuracia_top1 | acuracia_top3 |
|---|---|---|---|---|
| Heurística | Geometria | 7 | 28.6% | 28.6% |
| Heurística | Grandezas e medidas | 12 | 0.0% | 0.0% |
| Heurística | Números | 40 | 2.5% | 5.0% |
| Heurística | Álgebra | 25 | 12.0% | 16.0% |
| Semântica | Geometria | 7 | 0.0% | 14.3% |
| Semântica | Grandezas e medidas | 12 | 0.0% | 0.0% |
| Semântica | Números | 40 | 0.0% | 5.0% |
| Semântica | Álgebra | 25 | 0.0% | 4.0% |
| Combinada | Geometria | 7 | 28.6% | 28.6% |
| Combinada | Grandezas e medidas | 12 | 0.0% | 0.0% |
| Combinada | Números | 40 | 2.5% | 2.5% |
| Combinada | Álgebra | 25 | 4.0% | 8.0% |

Habilidades no conjunto de referência: 38; itens por habilidade: mín 1, mediana 4, máx 13 (tabela itens_por_habilidade_referencia.csv).

Robustez por lote (definida antes da execução sobre o lote 2, que não influenciou o método):

| lote | configuracao | itens | acuracia_top1 | acuracia_top3 |
|---|---|---|---|---|
| 1 | Heurística | 45 | 8.9% | 13.3% |
| 1 | Semântica | 45 | 0.0% | 6.7% |
| 1 | Combinada | 45 | 6.7% | 8.9% |
| 2 | Heurística | 39 | 5.1% | 5.1% |
| 2 | Semântica | 39 | 0.0% | 2.6% |
| 2 | Combinada | 39 | 2.6% | 2.6% |

Análise complementar, definida após os resultados (não pré-registrada): posição da habilidade de referência mais bem colocada no ranking completo de 290 candidatas (empate pela ordem do código).

| configuracao | itens | posicao_mediana | ate_10 | ate_30 |
|---|---|---|---|---|
| Heurística | 84 | 132.500 | 27.4% | 36.9% |
| Semântica | 84 | 30.500 | 22.6% | 50.0% |
| Combinada | 84 | 27.500 | 32.1% | 51.2% |

Análise complementar, definida após os resultados: valor esperado de uma ordenação aleatória das candidatas (290 e, para comparação com a ablação, só 6º ao 9º ano).

| configuracao | itens | candidatas | top1 | top3 | top5 | top10 | top20 | top30 |
|---|---|---|---|---|---|---|---|---|
| Aleatória (valor esperado) | 84 | 290 | 0.7% | 2.2% | 3.7% | 7.3% | 14.2% | 20.8% |
| Aleatória (valor esperado) | 84 | 121 | 1.8% | 5.3% | 8.7% | 16.9% | 31.7% | 44.6% |

Análise complementar, definida após os resultados: candidatas restritas ao 6º–9º ano, com as mesmas pontuações (o método não é alterado).

| configuracao | itens | candidatas | acuracia_top1 | acuracia_top3 | posicao_mediana | ate_10 | ate_30 |
|---|---|---|---|---|---|---|---|
| Heurística | 84 | 121 | 10.7% | 19.0% | 21.000 | 36.9% | 61.9% |
| Semântica | 84 | 121 | 3.6% | 16.7% | 12.000 | 46.4% | 71.4% |
| Combinada | 84 | 121 | 13.1% | 23.8% | 10.500 | 50.0% | 73.8% |

## V1 · compatibilidade de etapa e ano

| ano_item | configuracao | itens | compativel | ano_posterior_EF | ensino_medio |
|---|---|---|---|---|---|
| 5º | Heurística | 23 | 52.2% | 30.4% | 17.4% |
| 5º | Semântica | 23 | 69.6% | 26.1% | 4.3% |
| 5º | Combinada | 23 | 73.9% | 21.7% | 4.3% |
| 9º | Heurística | 88 | 88.6% | 0.0% | 11.4% |
| 9º | Semântica | 88 | 93.2% | 0.0% | 6.8% |
| 9º | Combinada | 88 | 92.0% | 0.0% | 8.0% |

No 9º ano, 'ano posterior' é impossível por construção; a V1 informa só as previsões do EM. Distribuição dos anos previstos em v1_distribuicao_anos_previstos.csv.

## V2 · coerência de unidade temática (9º ano)

| configuracao | itens | coerencia_unidade_tematica |
|---|---|---|
| Heurística | 84 | 36.9% |
| Semântica | 84 | 32.1% |
| Combinada | 84 | 34.5% |

Matriz de confusão (combinada, linhas = esperada):

| esperada | Ensino Médio | Geometria | Grandezas e medidas | Números | Probabilidade e estatística | Álgebra |
|---|---|---|---|---|---|---|
| Geometria | 0 | 5 | 2 | 0 | 0 | 0 |
| Grandezas e medidas | 4 | 2 | 6 | 0 | 0 | 0 |
| Números | 2 | 0 | 19 | 12 | 0 | 7 |
| Álgebra | 0 | 2 | 9 | 7 | 1 | 6 |

## V3 · concordância heurística × semântica (1ª posição)

Medida de estabilidade entre componentes do pipeline, não de correção.

| ano_item | itens | concordancia_heuristica_semantica |
|---|---|---|
| 5º | 23 | 8.7% |
| 9º | 88 | 6.8% |
| total | 108 | 7.4% |

## V4 · margem de decisão (ambíguo: margem < 0.05 ou empate na 1ª posição)

| configuracao | ano_item | itens | margem_q1 | margem_mediana | margem_q3 | ambiguos | empates_top1 |
|---|---|---|---|---|---|---|---|
| Heurística | 5º | 23 | 0.129 | 0.254 | 0.339 | 13.0% | 1 |
| Heurística | 9º | 88 | 0.052 | 0.161 | 0.262 | 25.0% | 1 |
| Heurística | total | 108 | 0.056 | 0.174 | 0.302 | 23.1% | 2 |
| Semântica | 5º | 23 | 0.021 | 0.040 | 0.068 | 56.5% | 0 |
| Semântica | 9º | 88 | 0.023 | 0.041 | 0.076 | 59.1% | 0 |
| Semântica | total | 108 | 0.021 | 0.039 | 0.076 | 60.2% | 0 |
| Combinada | 5º | 23 | 0.055 | 0.121 | 0.252 | 21.7% | 0 |
| Combinada | 9º | 88 | 0.033 | 0.077 | 0.165 | 35.2% | 0 |
| Combinada | total | 108 | 0.036 | 0.086 | 0.169 | 31.5% | 0 |

## V5 · cobertura e colapso (itens aptos únicos)

| configuracao | itens | habilidades_distintas | fracao_espaco_rotulos | parcela_5_mais_frequentes | mais_frequentes |
|---|---|---|---|---|---|
| Heurística | 108 | 70 | 24.1% | 23.1% | EF03MA23 (6); EF04MA25 (5); EF03MA24 (5); EF01MA17 (5); EF08MA06 (4) |
| Semântica | 108 | 54 | 18.6% | 29.6% | EF08MA20 (11); EF03MA09 (8); EF01MA19 (5); EF04MA25 (4); EF02MA20 (4) |
| Combinada | 108 | 57 | 19.7% | 28.7% | EF03MA24 (8); EF04MA25 (7); EF03MA23 (7); EF08MA06 (5); EF02MA03 (4) |

## Erros da configuração combinada (9º ano)

80 itens com 1ª posição fora da referência; por categoria: {'unidade temática diferente': 49, 'mesma unidade temática': 25, 'etapa posterior (EM)': 6}; com acerto no top-3: 1. Ver amostra_erros.md.

## V6 · sanidade do cruzamento documental


Anos com rótulo de referência usado nas métricas (config.ANOS_COM_ROTULO): [9]. Os itens dos demais anos são etiquetados e entram em V1, V3, V4 e V5.

### Cobertura do alinhamento

| ano | descritores_na_fonte | descritores_com_habilidade | itens | itens_sem_rotulo | aptos | aptos_sem_rotulo | habilidades_por_item_rotulado |
|---|---|---|---|---|---|---|---|
| 5 | 17 | 2 | 77 | 65 | 23 | 23 | 1.0 |
| 9 | 62 | 59 | 348 | 10 | 93 | 4 | 2.1 |

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
- 9º ano, D025_M: 3
- 9º ano, D030_M: 3
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
- 9º ano, todos os itens rotulados: {6: 145, 7: 280, 8: 132, 9: 154} | pares habilidade-item fora do ano do item: 557/711 | itens cujo rótulo não tem nenhuma habilidade do próprio ano: 219/338
- 9º ano, itens aptos: {6: 37, 7: 89, 8: 35, 9: 33} | pares habilidade-item fora do ano do item: 161/194 | itens cujo rótulo não tem nenhuma habilidade do próprio ano: 57/89

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