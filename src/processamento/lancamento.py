"""Aplica as regras de rubrica sobre os servidores classificados e monta as saídas."""

import pandas as pd

from src.parametrizacao import grupos as g
from src.parametrizacao.competencia import Competencia
from src.parametrizacao.regras import PREVIDENCIA_MENSAL, REGRAS
from src.parametrizacao.rubricas import CATALOGO, coluna_flag

COLUNAS_IDENTIFICACAO = [
    "CODORGAO",
    "ORGAO",
    "NOMESERVIDOR",
    "SIMBOLOCARGO",
    "NOMECARGO",
    "REGIME_TRABALHO",
    "VINCULO",
    "SITUACAO",
    "GRUPO_PREVIDENCIARIO",
]


def aplicar_regras(frame: pd.DataFrame, competencia: Competencia) -> pd.DataFrame:
    """Adiciona uma coluna booleana R<código> por rubrica (True = rubrica lançada)."""
    frame = frame.copy()
    for codigo, regra in REGRAS.items():
        frame[coluna_flag(codigo)] = regra(frame, competencia).astype(bool)
    return frame


def gerar_lancamentos(frame: pd.DataFrame) -> pd.DataFrame:
    """Formato 'longo': uma linha por servidor x rubrica lançada (como uma tabela de lançamentos)."""
    partes = []
    for rubrica in CATALOGO:
        selecionados = frame.loc[frame[coluna_flag(rubrica.codigo)], COLUNAS_IDENTIFICACAO].copy()
        selecionados["CODIGO_RUBRICA"] = rubrica.codigo
        selecionados["DESCRICAO_RUBRICA"] = rubrica.descricao
        selecionados["TRIBUTO"] = rubrica.tributo
        selecionados["EVENTO_ESOCIAL"] = rubrica.evento_esocial
        partes.append(selecionados)
    return pd.concat(partes).sort_index(kind="stable").reset_index(names="ID_REGISTRO")


def resumir_por_rubrica(frame: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for rubrica in CATALOGO:
        flag = frame[coluna_flag(rubrica.codigo)]
        linhas.append(
            {
                "CODIGO_RUBRICA": rubrica.codigo,
                "DESCRICAO_RUBRICA": rubrica.descricao,
                "TRIBUTO": rubrica.tributo,
                "QTD_LANCAMENTOS": int(flag.sum()),
            }
        )
    return pd.DataFrame(linhas)


def resumir_por_grupo(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby(["REGIME_TRABALHO", "VINCULO", "SITUACAO", "GRUPO_PREVIDENCIARIO"], dropna=False)
        .size()
        .rename("QTD_SERVIDORES")
        .reset_index()
        .sort_values(["GRUPO_PREVIDENCIARIO", "REGIME_TRABALHO", "SITUACAO"])
    )


def verificar_consistencia(frame: pd.DataFrame) -> dict[str, int]:
    """Checagens que devem dar zero (exceto as informativas)."""
    flags_prev = frame[[coluna_flag(c) for c in PREVIDENCIA_MENSAL]]
    todas_flags = frame[[coluna_flag(r.codigo) for r in CATALOGO]]
    isento_com_irrf = frame["SITUACAO"].isin(g.BENEFICIARIOS) & frame["DATA_INICIO_ISENCAO_IR"].notna() & frame[
        coluna_flag("5401")
    ]
    return {
        "servidores_com_mais_de_uma_previdencia_mensal": int((flags_prev.sum(axis=1) > 1).sum()),
        "servidores_nao_enquadrados_em_grupo": int(frame["GRUPO_PREVIDENCIARIO"].eq(g.NAO_ENQUADRADO).sum()),
        "info_servidores_sem_nenhuma_rubrica": int((~todas_flags.any(axis=1)).sum()),
        "info_beneficiarios_com_laudo_vencido_e_irrf": int(isento_com_irrf.sum()),
    }
