"""Leitura da base de folha de pagamento (CSV do portal de transparência de Goiás)."""

from pathlib import Path

import pandas as pd

COLUNAS_OBRIGATORIAS = [
    "CODORGAO",
    "ANOMES",
    "ORGAO",
    "NOMESERVIDOR",
    "SIMBOLOCARGO",
    "NOMECARGO",
    "SIMBOLOCARGOSECUNDARIO",
    "NOMECARGOSECUNDARIO",
    "VALORPROVENTOMES",
    "VALORDECIMOTERCEIRO",
    "VALORFERIAS",
]


def carregar_folha(caminho: str | Path, limite_linhas: int | None = None) -> pd.DataFrame:
    """Lê o CSV (separador ';', decimal ',', UTF-8 com BOM) e valida as colunas."""
    caminho = Path(caminho)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo de folha não encontrado: {caminho}")

    frame = pd.read_csv(
        caminho,
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
        dtype={"CODORGAO": str, "ANOMES": str},
        nrows=limite_linhas,
    )

    faltantes = [c for c in COLUNAS_OBRIGATORIAS if c not in frame.columns]
    if faltantes:
        raise ValueError(f"Colunas obrigatórias ausentes no CSV: {faltantes}")

    return frame
