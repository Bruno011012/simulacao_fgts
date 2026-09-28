import pandas as pd
import pytest

from src.cadastro.classificacao import classificar_cadastro
from src.dados.tratamento import tratar_folha
from src.parametrizacao import grupos as g
from src.parametrizacao.competencia import Competencia

COMPETENCIA = Competencia(2026, 7)


@pytest.fixture
def competencia() -> Competencia:
    return COMPETENCIA


def classificar_registros(registros: list[dict]) -> pd.DataFrame:
    """Monta um CSV 'bruto' mínimo a partir de (SIMBOLOCARGO, NOMECARGO, ORGAO) e classifica."""
    padrao = {
        "CODORGAO": "1",
        "ANOMES": "202607",
        "NOMESERVIDOR": "SERVIDOR TESTE",
        "SIMBOLOCARGOSECUNDARIO": "Não se Aplica",
        "NOMECARGOSECUNDARIO": "Não se Aplica",
        "VALORPROVENTOMES": 1000.0,
        "VALORDECIMOTERCEIRO": 0.0,
        "VALORFERIAS": 0.0,
    }
    bruto = pd.DataFrame([{**padrao, **r} for r in registros])
    return classificar_cadastro(tratar_folha(bruto))


def servidor(
    grupo: str,
    situacao: str = g.ATIVO,
    inicio_vinculo: str | None = "2015-03-01",
    fim_vinculo: str | None = None,
    inicio_isencao: str | None = None,
    fim_isencao: str | None = None,
    provento: float = 5000.0,
    decimo: float = 0.0,
    ferias: float = 0.0,
) -> dict:
    """Um servidor já classificado — usado para testar as regras de rubrica isoladamente."""
    return {
        "GRUPO_PREVIDENCIARIO": grupo,
        "SITUACAO": situacao,
        "DATA_INICIO_VINCULO": inicio_vinculo,
        "DATA_FIM_VINCULO": fim_vinculo,
        "DATA_INICIO_ISENCAO_IR": inicio_isencao,
        "DATA_FIM_ISENCAO_IR": fim_isencao,
        "VALORPROVENTOMES": provento,
        "VALORDECIMOTERCEIRO": decimo,
        "VALORFERIAS": ferias,
    }


def quadro(*servidores: dict) -> pd.DataFrame:
    frame = pd.DataFrame(list(servidores))
    for coluna in ["DATA_INICIO_VINCULO", "DATA_FIM_VINCULO", "DATA_INICIO_ISENCAO_IR", "DATA_FIM_ISENCAO_IR"]:
        frame[coluna] = pd.to_datetime(frame[coluna])
    return frame
