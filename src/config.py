"""Configuração central do pipeline.

Todos os scripts importam caminhos e parâmetros daqui. Parâmetros de método
(limiar de margem, peso da combinação, modelo) devem ser fixados e commitados
ANTES de qualquer resultado ser observado.
"""
from pathlib import Path

# Caminhos
RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"
BRUTOS = DADOS / "01_brutos"
EXTRAIDOS = DADOS / "02_extraidos"
ROTULADOS = DADOS / "03_rotulados"
PREDITOS = DADOS / "04_preditos"
RESULTADOS = DADOS / "05_resultados"
REFERENCIA = DADOS / "referencia"

ARQ_ITENS = EXTRAIDOS / "itens.csv"
ARQ_ROTULADOS = ROTULADOS / "itens_rotulados.csv"
ARQ_PREDITOS = PREDITOS / "itens_preditos.csv"

ARQ_BNCC = REFERENCIA / "bncc_matematica.csv"
ARQ_ALINHAMENTO = REFERENCIA / "alinhamento_descritor_habilidade.csv"
ARQ_EQUIVALENCIA = REFERENCIA / "equivalencia_codificacoes.csv"
ARQ_VOCABULARIO = REFERENCIA / "vocabulario.csv"
ARQ_FONTES = REFERENCIA / "fontes.csv"
ARQ_REVISAO = REFERENCIA / "revisao_manual.csv"
ARQ_CONFERENCIA = REFERENCIA / "conferencia_amostra.csv"

# Taxonomia: bncc.dev (github.com/bncc-dev/bncc-dados), CC BY 4.0
BNCC_VERSAO = "dados-2026.07.1"
BNCC_URL_BASE = (
    f"https://raw.githubusercontent.com/bncc-dev/bncc-dados/{BNCC_VERSAO}/derivados/csv"
)
CACHE = RAIZ / ".cache"
PADRAO_CODIGO_BNCC = r"^(EF\d{2}MA\d{2}|EM13MAT\d{3})$"
ANOS = [5, 9]  # anos das questões (etapas avaliadas pelo SAEB)
# Anos incluídos na taxonomia. Todos do EF, porque a V1 mede se a previsão
# cai no ano do item ou em anos anteriores, e os descritores do SAEB
# se alinham a habilidades de anos anteriores ao avaliado. O EM entra
# inteiro, para que a V1 detecte previsões de etapa posterior.
ANOS_TAXONOMIA = list(range(1, 10))
ANO_EM = 10  # posição de ordenação das habilidades do EM (valem para as 3 séries)
UNIDADE_EM = "Ensino Médio"

# Fontes de questões: fonte_id -> arquivo em dados/01_brutos e módulo em src/extratores
FONTES = {
    "sedu_es_9ef": {"arquivo": "sedu_es_saeb_mat_9ano.pdf", "extrator": "sedu_es", "ano": 9},
    "sedu_ama5_2023t1": {"arquivo": "sedu_es_ama_mat_5ano_1tri_2023.pdf", "extrator": "sedu_ama", "ano": 5},
    "sedu_ama5_2024t3": {"arquivo": "sedu_es_ama_mat_5ano_3tri_2024.pdf", "extrator": "sedu_ama", "ano": 5},
    "sedu_ama5_2025t3": {"arquivo": "sedu_es_ama_mat_5ano_3tri_2025.pdf", "extrator": "sedu_ama", "ano": 5},
}
SEMENTE_AMOSTRA = 2026
TAMANHO_AMOSTRA = 10

# Extração: marcadores de dependência de figura (seção 2.4 do guia)
TERMOS_DEITICOS = [
    "figura", "imagem", "malha", "gráfico", "grafico", "tabela", "desenho",
    "planta", "croqui", "mapa", "abaixo", "a seguir", "ao lado",
]

# Etiquetagem
MODELO_EMBEDDING = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
MODELO_REVISAO = "4328cf26390c98c5e3c738b4460a05b95f4911f5"  # commit no Hugging Face (2025-08-19)
TOP_K = 5
# Decisão da seção 3.2.1, tomada em 2026-09-29 com a V6 (03_rotulados/relatorio_cruzamento.md),
# antes da etiquetagem: não restringir. Nos itens aptos do 9º ano, 72 de 88 pares
# item-habilidade de referência são de anos anteriores e 29 de 45 itens não têm
# nenhuma habilidade do 9º ano no rótulo; restringir tornaria esses acertos inalcançáveis.
RESTRINGIR_AO_ANO = False

# Peso da semântica na combinação; a heurística recebe (1 - PESO_SEMANTICA).
PESO_SEMANTICA = 0.5

# Limiar da verificação V4: diferença mínima entre 1ª e 2ª candidata na
# pontuação combinada. Definido em 2026-09-29, antes da existência do script de
# etiquetagem e de qualquer resultado. Normalização fixada junto: cada
# componente (semântico e heurístico) é levado a [0, 1] por min-max sobre todas
# as habilidades candidatas do item; a combinada é a média ponderada por
# PESO_SEMANTICA; margem = combinada(1ª) - combinada(2ª).
LIMIAR_MARGEM = 0.05
JUSTIFICATIVA_LIMIAR = (
    "5% da amplitude da escala normalizada: diferença abaixo da qual a ordem entre "
    "as duas primeiras candidatas pode ser invertida por variações pequenas do "
    "texto do enunciado ou do vocabulário, e a decisão é tratada como ambígua."
)

# Colunas que o script 3 pode ler. habilidades_referencia NUNCA entra aqui.
COLUNAS_ETIQUETAGEM = ["item_id", "fonte", "ano", "enunciado", "depende_figura"]
