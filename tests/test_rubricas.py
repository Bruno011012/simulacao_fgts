from src import config
from src.parametrizacao import grupos as g
from src.parametrizacao.regras import PREVIDENCIA_MENSAL, REGRAS
from src.parametrizacao.rubricas import CATALOGO, POR_CODIGO
from src.processamento.folha import processar_arquivo


def test_codigos_e_descricoes_unicos():
    assert len({r.codigo for r in CATALOGO}) == len(CATALOGO)
    assert len({r.descricao for r in CATALOGO}) == len(CATALOGO)


def test_toda_rubrica_tem_regra_e_toda_regra_tem_rubrica():
    assert set(POR_CODIGO) == set(REGRAS)


def test_previdencia_mensal_aponta_para_rubricas_mensais_nao_irrf():
    for codigo in PREVIDENCIA_MENSAL:
        rubrica = POR_CODIGO[codigo]
        assert rubrica.referencia == "MENSAL" and rubrica.tributo != "IRRF"


def test_todo_grupo_contributivo_tem_rubrica():
    grupos_com_rubrica = {r.grupo for r in CATALOGO}
    for grupo in [g.RPPS, g.SPSM_MILITAR, g.RGPS_EMPREGADO, g.RGPS_CONTRIBUINTE_INDIVIDUAL]:
        assert grupo in grupos_com_rubrica
    assert g.SEM_CONTRIBUICAO not in grupos_com_rubrica


def test_processamento_da_amostra_e_consistente_e_reprodutivel():
    resultado = processar_arquivo(config.ARQUIVO_AMOSTRA, semente=42)
    consistencia = resultado.consistencia
    assert consistencia["servidores_com_mais_de_uma_previdencia_mensal"] == 0
    assert consistencia["servidores_nao_enquadrados_em_grupo"] == 0
    assert set(g.REGIMES_ANEXO_I) <= set(resultado.servidores["REGIME_TRABALHO"])
    assert set(resultado.lancamentos["CODIGO_RUBRICA"]) == set(POR_CODIGO)  # amostra exercita as 14 rubricas

    de_novo = processar_arquivo(config.ARQUIVO_AMOSTRA, semente=42)
    assert resultado.lancamentos.equals(de_novo.lancamentos)
