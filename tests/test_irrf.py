import pytest

from src.parametrizacao import grupos as g
from src.processamento.lancamento import aplicar_regras
from tests.conftest import quadro, servidor


def flag(frame, competencia, codigo) -> bool:
    return bool(aplicar_regras(frame, competencia).iloc[0][f"R{codigo}"])


@pytest.mark.parametrize(
    "grupo", [g.RPPS, g.SPSM_MILITAR, g.RGPS_EMPREGADO, g.RGPS_CONTRIBUINTE_INDIVIDUAL, g.SEM_CONTRIBUICAO]
)
def test_irrf_independe_do_regime_previdenciario(competencia, grupo):
    assert flag(quadro(servidor(grupo)), competencia, "5401")


@pytest.mark.parametrize("situacao", [g.INATIVO, g.PENSIONISTA])
def test_beneficiario_com_laudo_vigente_e_isento(competencia, situacao):
    frame = quadro(servidor(g.RPPS, situacao, inicio_isencao="2020-05-01", decimo=3000.0))
    assert not flag(frame, competencia, "5401")
    assert not flag(frame, competencia, "5402")


def test_militar_reformado_com_laudo_tambem_e_isento(competencia):
    frame = quadro(servidor(g.SPSM_MILITAR, g.INATIVO, inicio_isencao="2022-01-10"))
    assert not flag(frame, competencia, "5401")


def test_laudo_vencido_volta_a_tributar(competencia):
    frame = quadro(servidor(g.RPPS, g.INATIVO, inicio_isencao="2021-01-01", fim_isencao="2026-06-30"))
    assert flag(frame, competencia, "5401")


def test_laudo_que_vence_durante_a_competencia_ainda_isenta(competencia):
    frame = quadro(servidor(g.RPPS, g.INATIVO, inicio_isencao="2021-01-01", fim_isencao="2026-07-20"))
    assert not flag(frame, competencia, "5401")


def test_laudo_futuro_nao_isenta(competencia):
    frame = quadro(servidor(g.RPPS, g.INATIVO, inicio_isencao="2026-08-01"))
    assert flag(frame, competencia, "5401")


def test_ativo_com_laudo_nao_e_isento(competencia):
    """Isenção por moléstia grave só alcança proventos de aposentadoria, reforma ou pensão."""
    frame = quadro(servidor(g.RPPS, g.ATIVO, inicio_isencao="2020-01-01"))
    assert flag(frame, competencia, "5401")


def test_irrf_ferias_so_para_ativo_com_ferias(competencia):
    assert flag(quadro(servidor(g.RGPS_EMPREGADO, ferias=1800.0)), competencia, "5403")
    assert not flag(quadro(servidor(g.RGPS_EMPREGADO, ferias=0.0)), competencia, "5403")
    assert not flag(quadro(servidor(g.RPPS, g.INATIVO, ferias=1800.0)), competencia, "5403")


def test_irrf_13_exige_parcela(competencia):
    assert not flag(quadro(servidor(g.RPPS)), competencia, "5402")
    assert flag(quadro(servidor(g.RPPS, decimo=1000.0)), competencia, "5402")
