import itertools

import pytest

from src.parametrizacao import grupos as g
from src.parametrizacao.regras import PREVIDENCIA_MENSAL, REGRAS
from src.processamento.lancamento import aplicar_regras
from tests.conftest import quadro, servidor


def rubricas_lancadas(frame, competencia, linha=0) -> set[str]:
    resultado = aplicar_regras(frame, competencia).iloc[linha]
    return {codigo for codigo in REGRAS if resultado[f"R{codigo}"]}


def previdencia(codigos: set[str]) -> set[str]:
    return {c for c in codigos if not c.startswith("54")}


@pytest.mark.parametrize(
    "grupo, situacao, esperado",
    [
        (g.RPPS, g.ATIVO, {"5101"}),
        (g.RPPS, g.INATIVO, {"5102"}),
        (g.RPPS, g.PENSIONISTA, {"5102"}),
        (g.SPSM_MILITAR, g.ATIVO, {"5201"}),
        (g.SPSM_MILITAR, g.INATIVO, {"5202"}),
        (g.RGPS_EMPREGADO, g.ATIVO, {"5301"}),
        (g.RGPS_CONTRIBUINTE_INDIVIDUAL, g.ATIVO, {"5303"}),
        (g.SEM_CONTRIBUICAO, g.ATIVO, set()),
        (g.SEM_CONTRIBUICAO, g.PENSIONISTA, set()),
    ],
)
def test_rubrica_previdenciaria_mensal_por_grupo(competencia, grupo, situacao, esperado):
    frame = quadro(servidor(grupo, situacao))
    assert previdencia(rubricas_lancadas(frame, competencia)) == esperado


@pytest.mark.parametrize(
    "grupo, situacao, esperado",
    [
        (g.RPPS, g.ATIVO, {"5101", "5103"}),
        (g.RPPS, g.INATIVO, {"5102", "5104"}),
        (g.SPSM_MILITAR, g.ATIVO, {"5201", "5203"}),
        (g.SPSM_MILITAR, g.INATIVO, {"5202", "5204"}),
        (g.RGPS_EMPREGADO, g.ATIVO, {"5301", "5302"}),
        (g.RGPS_CONTRIBUINTE_INDIVIDUAL, g.ATIVO, {"5303"}),  # contribuinte individual não tem 13º
    ],
)
def test_rubricas_de_13_so_quando_ha_parcela(competencia, grupo, situacao, esperado):
    frame = quadro(servidor(grupo, situacao, decimo=2500.0))
    assert previdencia(rubricas_lancadas(frame, competencia)) == esperado


def test_vinculo_encerrado_antes_da_competencia_nao_lanca_nada(competencia):
    frame = quadro(servidor(g.RGPS_EMPREGADO, inicio_vinculo="2025-01-01", fim_vinculo="2026-06-30", decimo=100))
    assert rubricas_lancadas(frame, competencia) == set()


def test_vinculo_encerrado_durante_a_competencia_ainda_lanca(competencia):
    frame = quadro(servidor(g.RGPS_EMPREGADO, inicio_vinculo="2025-01-01", fim_vinculo="2026-07-10"))
    assert "5301" in rubricas_lancadas(frame, competencia)


def test_sem_rendimento_no_mes_nao_lanca_previdencia_mensal(competencia):
    frame = quadro(servidor(g.RPPS, provento=0.0))
    assert previdencia(rubricas_lancadas(frame, competencia)) == set()


def test_no_maximo_uma_previdencia_mensal_por_servidor(competencia):
    todos_grupos = [g.RPPS, g.SPSM_MILITAR, g.RGPS_EMPREGADO, g.RGPS_CONTRIBUINTE_INDIVIDUAL, g.SEM_CONTRIBUICAO]
    todas_situacoes = [g.ATIVO, g.INATIVO, g.PENSIONISTA]
    frame = quadro(*[servidor(gr, s) for gr, s in itertools.product(todos_grupos, todas_situacoes)])
    flags = aplicar_regras(frame, competencia)[[f"R{c}" for c in PREVIDENCIA_MENSAL]]
    assert (flags.sum(axis=1) <= 1).all()
