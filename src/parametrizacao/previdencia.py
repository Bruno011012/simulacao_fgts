"""Regras de lançamento das rubricas previdenciárias (RPPS, proteção social militar e INSS).

Todas seguem o mesmo molde:
    SE grupo previdenciário = X
       E situação no público da rubrica (ativo ou beneficiário)
       E vínculo vigente na competência
       E existe a parcela na competência (rendimento do mês ou 13º)
    ENTÃO lança, SENÃO não lança.
"""

import pandas as pd

from src.parametrizacao import grupos as g
from src.parametrizacao import predicados as p
from src.parametrizacao.competencia import Competencia


def _base(frame: pd.DataFrame, competencia: Competencia, grupo: str) -> pd.Series:
    return p.no_grupo(frame, grupo) & p.vinculo_vigente(frame, competencia)


# ---------------------------------------------------------------- RPPS
def rpps_servidor_ativo(frame, competencia):                          # 5101
    return _base(frame, competencia, g.RPPS) & p.ativo(frame) & p.possui_rendimento_mes(frame)


def rpps_beneficiario(frame, competencia):                            # 5102
    return _base(frame, competencia, g.RPPS) & p.beneficiario(frame) & p.possui_rendimento_mes(frame)


def rpps_13_servidor_ativo(frame, competencia):                       # 5103
    return _base(frame, competencia, g.RPPS) & p.ativo(frame) & p.possui_decimo_terceiro(frame)


def rpps_13_beneficiario(frame, competencia):                         # 5104
    return _base(frame, competencia, g.RPPS) & p.beneficiario(frame) & p.possui_decimo_terceiro(frame)


# ---------------------------------------------------------------- Militares
def militar_ativo(frame, competencia):                                # 5201
    return _base(frame, competencia, g.SPSM_MILITAR) & p.ativo(frame) & p.possui_rendimento_mes(frame)


def militar_beneficiario(frame, competencia):                         # 5202
    return _base(frame, competencia, g.SPSM_MILITAR) & p.beneficiario(frame) & p.possui_rendimento_mes(frame)


def militar_13_ativo(frame, competencia):                             # 5203
    return _base(frame, competencia, g.SPSM_MILITAR) & p.ativo(frame) & p.possui_decimo_terceiro(frame)


def militar_13_beneficiario(frame, competencia):                      # 5204
    return _base(frame, competencia, g.SPSM_MILITAR) & p.beneficiario(frame) & p.possui_decimo_terceiro(frame)


# ---------------------------------------------------------------- RGPS / INSS
def inss_empregado(frame, competencia):                               # 5301
    return _base(frame, competencia, g.RGPS_EMPREGADO) & p.possui_rendimento_mes(frame)


def inss_13_empregado(frame, competencia):                            # 5302
    return _base(frame, competencia, g.RGPS_EMPREGADO) & p.possui_decimo_terceiro(frame)


def inss_contribuinte_individual(frame, competencia):                 # 5303
    return _base(frame, competencia, g.RGPS_CONTRIBUINTE_INDIVIDUAL) & p.possui_rendimento_mes(frame)
