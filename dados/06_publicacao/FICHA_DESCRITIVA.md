# Ficha descritiva do banco de questões

Banco de questões de Matemática do Ensino Fundamental etiquetado por habilidades da BNCC,
versão 1.0.0, DOI [10.5281/zenodo.23486009](https://doi.org/10.5281/zenodo.23486009). Ficha no modelo de Gebru et al.
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

- **Instâncias.** 425 itens de avaliação de Matemática: 77 do
  5º ano e 348 do 9º ano, extraídos de 10 publicações da
  Secretaria de Estado da Educação do Espírito Santo (SEDU-ES).
- **Campos.** Enunciado, alternativas, gabarito publicado e revisado, descritor de
  origem, avaliação de origem, rótulo de referência com a cadeia de traduções,
  habilidades previstas por três configurações automáticas, sinalização de aptidão e
  proveniência até a página. Dicionário completo no Quadro 2 do trabalho e no README do repositório.
- **Rótulo de referência.** 350 itens têm rótulo de referência, obtido
  por cruzamento documental entre o descritor do item e documentos oficiais de
  alinhamento da SEDU-ES. É um rótulo derivado, e não padrão-ouro: não foi
  validado por especialista.
- **Aptidão.** 116 itens (23 do 5º e 93
  do 9º ano) têm conteúdo textual integralmente recuperável. Os demais dependem de
  figura, têm fórmula corrompida ou desenhada como vetor, ou alternativas incompletas,
  e trazem o motivo nos campos correspondentes.
- **Duplicatas.** 19 registros apontam, no campo `duplicata_de`, para o mesmo item
  publicado em outra fonte. Para contar cada questão uma vez, descarte os registros com
  esse campo preenchido.
- **Erros das fontes.** 8 itens têm `gabarito_revisado` diferente do gabarito
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
  metadados): CC BY 4.0.
- **Taxonomia BNCC.** bncc.dev, versão `dados-2026.07.1`, CC BY 4.0.
- **Código.** Licença MIT (arquivo `LICENSE` na raiz do repositório).

## Manutenção

Mantido pelo autor no repositório do trabalho. Erros podem ser relatados por *issue*.
Novas versões recebem número próprio; a versão 1.0.0 corresponde aos
resultados relatados no TCC.
