"""Registro único: código da rubrica -> função booleana que decide o lançamento."""

from collections.abc import Callable

import pandas as pd

from src.parametrizacao import irrf, previdencia
from src.parametrizacao.competencia import Competencia

Regra = Callable[[pd.DataFrame, Competencia], pd.Series]

REGRAS: dict[str, Regra] = {
    "5101": previdencia.rpps_servidor_ativo,
    "5102": previdencia.rpps_beneficiario,
    "5103": previdencia.rpps_13_servidor_ativo,
    "5104": previdencia.rpps_13_beneficiario,
    "5201": previdencia.militar_ativo,
    "5202": previdencia.militar_beneficiario,
    "5203": previdencia.militar_13_ativo,
    "5204": previdencia.militar_13_beneficiario,
    "5301": previdencia.inss_empregado,
    "5302": previdencia.inss_13_empregado,
    "5303": previdencia.inss_contribuinte_individual,
    "5401": irrf.irrf_mensal,
    "5402": irrf.irrf_13,
    "5403": irrf.irrf_ferias,
}

# Rubricas previdenciárias mensais: um servidor pode ter no MÁXIMO uma delas
PREVIDENCIA_MENSAL = ["5101", "5102", "5201", "5202", "5301", "5303"]
