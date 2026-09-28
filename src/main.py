"""Ponto de entrada.

Uso (a partir da raiz do projeto):
    python -m src.main                                   # base completa em data/input
    python -m src.main --entrada data/input/amostra_folha.csv
    python -m src.main --limite 5000                     # só as primeiras N linhas
    python -m src.main --sem-abrir                       # gera o relatório HTML sem abrir o navegador
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

from src import config
from src.parametrizacao.grupos import DESCRICAO_GRUPOS
from src.processamento.folha import exportar, processar_arquivo
from src.relatorio import abrir_no_navegador, gerar_relatorio


def _argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lançamento de rubricas de IRRF, INSS e RPPS por regime de trabalho")
    padrao = config.ARQUIVO_FOLHA_PADRAO if config.ARQUIVO_FOLHA_PADRAO.exists() else config.ARQUIVO_AMOSTRA
    parser.add_argument("--entrada", type=Path, default=padrao, help="CSV da folha (sep ';')")
    parser.add_argument("--saida", type=Path, default=config.DIR_OUTPUT, help="Diretório de saída")
    parser.add_argument("--limite", type=int, default=None, help="Processar apenas as N primeiras linhas")
    parser.add_argument("--semente", type=int, default=config.SEMENTE_SIMULACAO, help="Semente da simulação cadastral")
    parser.add_argument("--relatorios", type=Path, default=config.DIR_RELATORIOS, help="Diretório do relatório HTML")
    parser.add_argument("--sem-abrir", action="store_true", help="Não abrir o relatório no navegador ao final")
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = _argumentos()
    pd.set_option("display.width", 200)
    pd.set_option("display.max_colwidth", 70)

    print(f"Lendo {args.entrada} ...")
    resultado = processar_arquivo(args.entrada, args.semente, args.limite)
    servidores = resultado.servidores

    print(f"\nCompetência: {resultado.competencia}  |  Registros: {len(servidores):,}".replace(",", "."))
    if servidores["CADASTRO_SIMULADO"].any():
        print("Aviso: datas de vínculo e laudos de isenção de IR foram SIMULADOS (não existem no CSV).")

    print("\n=== Servidores por regime de trabalho e grupo previdenciário ===")
    tabela = pd.crosstab(servidores["REGIME_TRABALHO"], servidores["GRUPO_PREVIDENCIARIO"], margins=True, margins_name="TOTAL")
    print(tabela.to_string())

    print("\n=== Grupos previdenciários ===")
    for grupo, descricao in DESCRICAO_GRUPOS.items():
        print(f"  {grupo:<30} {descricao}")

    print("\n=== Rubricas lançadas ===")
    print(resultado.resumo_rubricas.to_string(index=False))

    print("\n=== Verificações de consistência ===")
    for chave, valor in resultado.consistencia.items():
        print(f"  {chave:<50} {valor}")

    arquivos = exportar(resultado, args.saida)
    print("\nArquivos gerados:")
    for caminho in arquivos.values():
        print(f"  {caminho}")

    relatorio = gerar_relatorio(arquivos, args.relatorios)
    print(f"\nRelatório HTML: {relatorio}")
    if not args.sem_abrir:
        abrir_no_navegador(relatorio)


if __name__ == "__main__":
    main()
