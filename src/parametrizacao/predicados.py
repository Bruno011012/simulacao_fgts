"""Blocos lógicos reutilizados pelas regras de lançamento.

Cada predicado recebe o DataFrame de servidores (já classificado) e devolve uma Series
booleana — as regras de rubrica são apenas combinações (E / OU / NÃO) destes blocos.
"""

import pandas as pd

from src.parametrizacao import grupos as g
from src.parametrizacao.competencia import Competencia, vigente_na_competencia


def no_grupo(frame: pd.DataFrame, grupo: str) -> pd.Series:
    return frame["GRUPO_PREVIDENCIARIO"].eq(grupo)


def ativo(frame: pd.DataFrame) -> pd.Series:
    return frame["SITUACAO"].eq(g.ATIVO)


def beneficiario(frame: pd.DataFrame) -> pd.Series:
    """Aposentado, reformado/reserva ou pensionista."""
    return frame["SITUACAO"].isin(g.BENEFICIARIOS)


def vinculo_vigente(frame: pd.DataFrame, competencia: Competencia) -> pd.Series:
    return vigente_na_competencia(frame["DATA_INICIO_VINCULO"], frame["DATA_FIM_VINCULO"], competencia)


def possui_rendimento_mes(frame: pd.DataFrame) -> pd.Series:
    return frame["VALORPROVENTOMES"] > 0


def possui_decimo_terceiro(frame: pd.DataFrame) -> pd.Series:
    return frame["VALORDECIMOTERCEIRO"] > 0


def possui_ferias(frame: pd.DataFrame) -> pd.Series:
    return frame["VALORFERIAS"] > 0


def isencao_ir_vigente(frame: pd.DataFrame, competencia: Competencia) -> pd.Series:
    """Isenção de IR (Lei 7.713/88, art. 6º, XIV) só vale sobre proventos de aposentadoria,
    reforma ou pensão: exige ser beneficiário E ter laudo vigente na competência.
    Um servidor ATIVO com laudo continua sendo tributado."""
    laudo_vigente = vigente_na_competencia(
        frame["DATA_INICIO_ISENCAO_IR"], frame["DATA_FIM_ISENCAO_IR"], competencia
    )
    return beneficiario(frame) & laudo_vigente
