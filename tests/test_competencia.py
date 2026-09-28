import pandas as pd
import pytest

from src.parametrizacao.competencia import Competencia, vigente_na_competencia


def test_de_anomes_e_limites_do_mes():
    comp = Competencia.de_anomes("202402")
    assert comp.inicio == pd.Timestamp("2024-02-01")
    assert comp.fim == pd.Timestamp("2024-02-29")  # ano bissexto


@pytest.mark.parametrize("anomes", ["2026", "20260", "abcdef", ""])
def test_anomes_invalido(anomes):
    with pytest.raises(ValueError):
        Competencia.de_anomes(anomes)


@pytest.mark.parametrize(
    "inicio, fim, esperado",
    [
        ("2020-01-01", None, True),           # começou antes, sem fim -> vigente
        ("2020-01-01", "2026-06-30", False),  # encerrou no mês anterior
        ("2020-01-01", "2026-07-01", True),   # encerrou no 1º dia da competência
        ("2020-01-01", "2026-07-15", True),   # encerrou no meio do mês
        ("2026-07-31", None, True),           # começou no último dia
        ("2026-08-01", None, False),          # começa depois da competência
        (None, None, False),                  # sem data de início = sem cadastro
    ],
)
def test_vigencia(inicio, fim, esperado):
    comp = Competencia(2026, 7)
    resultado = vigente_na_competencia(pd.Series([inicio]), pd.Series([fim]), comp)
    assert bool(resultado.iloc[0]) is esperado


def test_regra_literal_do_documento_seria_incorreta():
    """O exemplo do teste pede 'início >= início da competência' e 'fim nulo ou < início da competência'.
    Um associado desde 2020 e ainda ativo ficaria FORA pela regra literal; na regra correta ele entra."""
    comp = Competencia(2026, 7)
    inicio, fim = pd.Timestamp("2020-01-01"), pd.NaT
    regra_literal = (inicio >= comp.inicio) and (pd.isna(fim) or fim < comp.inicio)
    assert regra_literal is False
    assert bool(vigente_na_competencia(pd.Series([inicio]), pd.Series([fim]), comp).iloc[0]) is True
