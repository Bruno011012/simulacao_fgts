"""Configurações centrais do projeto (caminhos relativos à raiz do repositório)."""

from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[1]

DIR_INPUT = RAIZ_PROJETO / "data" / "input"
DIR_OUTPUT = RAIZ_PROJETO / "data" / "output"
DIR_RELATORIOS = RAIZ_PROJETO / "relatorios"

ARQUIVO_FOLHA_PADRAO = DIR_INPUT / "folhapagamento_202607.csv"
ARQUIVO_AMOSTRA = DIR_INPUT / "amostra_folha.csv"

# Semente usada para simular os campos cadastrais que não existem no CSV
# (datas de vínculo e laudos de isenção de IR). Fixa = resultado reproduzível.
SEMENTE_SIMULACAO = 42
