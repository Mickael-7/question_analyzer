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
PADRAO_CODIGO_BNCC = r"^EF\d{2}MA\d{2}$"
ANOS = [5, 9]  # anos das questões (etapas avaliadas pelo SAEB)
# Anos incluídos na taxonomia. Todos do EF, porque a V1 mede se a previsão
# cai no ano do item ou em anos anteriores, e os descritores do SAEB
# se alinham a habilidades de anos anteriores ao avaliado.
ANOS_TAXONOMIA = list(range(1, 10))

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
TOP_K = 5
RESTRINGIR_AO_ANO = False  # decisão de escopo da seção 4.1: não restringir

# Peso da semântica na combinação; a heurística recebe (1 - PESO_SEMANTICA).
PESO_SEMANTICA = 0.5

# Limiar da verificação V4: diferença mínima entre 1ª e 2ª candidata
# (pontuação combinada, escala 0-1). DEVE ser definido antes de ver resultados.
# Enquanto for None, o script de etiquetagem se recusa a rodar.
LIMIAR_MARGEM = None
JUSTIFICATIVA_LIMIAR = ""

# Colunas que o script 3 pode ler. habilidades_referencia NUNCA entra aqui.
COLUNAS_ETIQUETAGEM = ["item_id", "fonte", "ano", "enunciado", "depende_figura"]
