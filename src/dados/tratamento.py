"""Padronização dos dados brutos antes da classificação cadastral."""

import unicodedata

import pandas as pd

COLUNAS_TEXTO = [
    "ORGAO",
    "NOMESERVIDOR",
    "SIMBOLOCARGO",
    "NOMECARGO",
    "SIMBOLOCARGOSECUNDARIO",
    "NOMECARGOSECUNDARIO",
]

COLUNAS_VALOR = [
    "VALORPROVENTOMES",
    "VALORPROVENTO",
    "VALORDECIMOTERCEIRO",
    "VALORFERIAS",
    "VALORDEMAISDESCONTOS",
    "VALORLIQUIDO",
    "VALORCORTETETO",
]


def normalizar_texto(valor) -> str:
    """Maiúsculas, sem acentos e sem espaços duplicados: 'Não se Aplica' -> 'NAO SE APLICA'."""
    if pd.isna(valor):
        return ""
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.upper().split())


def _para_numero(serie: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(serie):
        return serie.fillna(0.0).astype(float)
    return pd.to_numeric(serie.astype(str).str.replace(",", ".", regex=False), errors="coerce").fillna(0.0)


def tratar_folha(frame: pd.DataFrame) -> pd.DataFrame:
    """Converte valores para float e cria colunas *_NORM usadas nas regras de classificação."""
    frame = frame.copy()

    for coluna in COLUNAS_VALOR:
        if coluna in frame.columns:
            frame[coluna] = _para_numero(frame[coluna])

    for coluna in COLUNAS_TEXTO:
        frame[coluna] = frame[coluna].fillna("").astype(str).str.strip()
        # normaliza só os valores distintos (poucos milhares) e depois mapeia: rápido em 167 mil linhas
        distintos = frame[coluna].unique()
        mapa = {v: normalizar_texto(v) for v in distintos}
        frame[f"{coluna}_NORM"] = frame[coluna].map(mapa)

    frame["ANOMES"] = frame["ANOMES"].astype(str).str.strip()
    return frame
