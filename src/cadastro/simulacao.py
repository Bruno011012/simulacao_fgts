"""Completa, de forma SIMULADA e reproduzível, os campos cadastrais que o CSV público não traz
mas que as regras de lançamento exigem:

    DATA_INICIO_VINCULO / DATA_FIM_VINCULO       -> vigência do vínculo na competência
    DATA_INICIO_ISENCAO_IR / DATA_FIM_ISENCAO_IR -> laudo de isenção de IR (moléstia grave)

Se o CSV de entrada já tiver essas colunas, elas são respeitadas e nada é simulado.
Em produção esses dados viriam do cadastro funcional do sistema de RH.
"""

import numpy as np
import pandas as pd

from src.parametrizacao import grupos as g
from src.parametrizacao.competencia import Competencia

COLUNAS_SIMULADAS = [
    "DATA_INICIO_VINCULO",
    "DATA_FIM_VINCULO",
    "DATA_INICIO_ISENCAO_IR",
    "DATA_FIM_ISENCAO_IR",
]

# Parâmetros da simulação
PROB_LAUDO_BENEFICIARIO = 0.08   # aposentados/pensionistas com laudo de isenção
PROB_LAUDO_ATIVO = 0.005         # ativos com laudo (não isentos: isenção só vale p/ benefício)
PROB_LAUDO_TEMPORARIO = 0.25     # laudos com data de fim (o restante é por prazo indeterminado)
PENSOES_RADIACAO = r"CESIO 137|RADIOATIVO"  # contaminação por radiação — Lei 7.713/88, art. 6º, XIV


def _datas(base: pd.Timestamp, deslocamento_dias: np.ndarray) -> pd.Series:
    return pd.Series(base + pd.to_timedelta(deslocamento_dias, unit="D"))


def completar_cadastro(frame: pd.DataFrame, competencia: Competencia, semente: int) -> pd.DataFrame:
    if all(c in frame.columns for c in COLUNAS_SIMULADAS):
        frame = frame.copy()
        for coluna in COLUNAS_SIMULADAS:
            frame[coluna] = pd.to_datetime(frame[coluna], errors="coerce", dayfirst=True)
        frame["CADASTRO_SIMULADO"] = False
        return frame

    frame = frame.copy()
    rng = np.random.default_rng(semente)
    n = len(frame)
    inicio_mes = competencia.inicio
    nulo = pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns]")

    # --- vínculo: todos começaram antes da competência
    contrato_prazo = frame["REGIME_TRABALHO"].isin([g.TEMPORARIO, g.PRESTADOR]) | frame["VINCULO"].isin(
        [g.VINCULO_ESTAGIO, g.VINCULO_RESIDENCIA]
    )
    dias_atras = np.where(contrato_prazo, rng.integers(30, 3 * 365, n), rng.integers(365, 35 * 365, n))
    frame["DATA_INICIO_VINCULO"] = _datas(inicio_mes, -dias_atras).set_axis(frame.index)

    # contratos por prazo têm data de término; parte deles já encerrou antes da competência
    fim_contrato = _datas(inicio_mes, rng.integers(-60, 730, n)).set_axis(frame.index)
    frame["DATA_FIM_VINCULO"] = fim_contrato.where(contrato_prazo, nulo)

    # --- laudo de isenção de IR
    beneficiario = frame["SITUACAO"].isin(g.BENEFICIARIOS)
    radiacao = frame["NOMECARGO_NORM"].str.contains(PENSOES_RADIACAO)
    sorteio = rng.random(n)
    tem_laudo = radiacao | (beneficiario & (sorteio < PROB_LAUDO_BENEFICIARIO)) | (
        ~beneficiario & (sorteio < PROB_LAUDO_ATIVO)
    )

    inicio_laudo = _datas(inicio_mes, -rng.integers(30, 10 * 365, n)).set_axis(frame.index)
    laudo_com_prazo = (rng.random(n) < PROB_LAUDO_TEMPORARIO) & ~radiacao
    fim_laudo = _datas(inicio_mes, rng.integers(-365, 730, n)).set_axis(frame.index)

    frame["DATA_INICIO_ISENCAO_IR"] = inicio_laudo.where(tem_laudo, nulo)
    frame["DATA_FIM_ISENCAO_IR"] = fim_laudo.where(tem_laudo & laudo_com_prazo, nulo)
    frame["CADASTRO_SIMULADO"] = True
    return frame
