import pytest

from src.parametrizacao import grupos as g
from tests.conftest import classificar_registros

SEDUC = "SECRETARIA DE ESTADO DA EDUCAÇÃO"
GOIASPREV = "GOIÁS PREVIDÊNCIA - GOIASPREV"

CASOS = [
    # (SIMBOLOCARGO, NOMECARGO, ORGAO) -> (REGIME, VINCULO, SITUACAO, GRUPO)
    (("P - IV", "Professor - IV", SEDUC), (g.ESTATUTARIO, "", g.ATIVO, g.RPPS)),
    (("P - IV", "Professor - IV", GOIASPREV), (g.ESTATUTARIO, "", g.INATIVO, g.RPPS)),
    (("A-2", "Auxiliar de Serviços Gerais A-2", SEDUC), (g.ESTATUTARIO, "", g.ATIVO, g.RPPS)),
    (("PCR - EST", "Assistente Administrativo - IPASGO", "IPASGO"), (g.ESTATUTARIO, "", g.ATIVO, g.RPPS)),
    (("PM/CBM", "Soldado - Lei 15.668", "POLÍCIA MILITAR"), (g.MILITAR, "", g.ATIVO, g.SPSM_MILITAR)),
    (("PM/CBM", "Soldado - Lei 15.668", GOIASPREV), (g.MILITAR, "", g.INATIVO, g.SPSM_MILITAR)),
    (("Reformado PM/CBM", "Cabo - PM - INATIVO", GOIASPREV), (g.MILITAR, "", g.INATIVO, g.SPSM_MILITAR)),
    (("CTEMPORÁRIO", "C. Temporário - Professor Nível Superior - SEDUC", SEDUC),
     (g.TEMPORARIO, "", g.ATIVO, g.RGPS_EMPREGADO)),
    (("A9", "Assessor A9", SEDUC), (g.COMISSIONADO, "", g.ATIVO, g.RGPS_EMPREGADO)),
    (("A9", "Assessor A9", GOIASPREV), (g.COMISSIONADO, "", g.ATIVO, g.RGPS_EMPREGADO)),
    (("COMISSIONADO - INATIVO", "Delegado Municipal de Polícia A - INATIVO", GOIASPREV),
     (g.COMISSIONADO, "", g.INATIVO, g.RPPS)),
    (("QT-PCR-CLT", "Assistente de Gestão Administrativa-QT-PCR-CLT-17.098-CAIXEGO", "SEAD"),
     (g.CIVIL, g.VINCULO_CELETISTA, g.ATIVO, g.RGPS_EMPREGADO)),
    (("EX-CAIXEGO - INATIVO", "Escriturário - CAIXEGO - INATIVO", GOIASPREV),
     (g.CIVIL, g.VINCULO_CELETISTA, g.INATIVO, g.RPPS)),
    (("QT-PCR-CLT-RPPS", "Analista de Transportes e Obras-QT-PCR-CLT-RPPS - 18.276", "GOINFRA"),
     (g.CIVIL, g.VINCULO_RPPS, g.ATIVO, g.RPPS)),
    (("CONVÊNIO", "Agente de Saúde Pública - FUNASA", "SAÚDE"),
     (g.CIVIL, g.VINCULO_CEDIDO, g.ATIVO, g.SEM_CONTRIBUICAO)),
    (("CROEE", "Professor C - Rondônia", GOIASPREV), (g.CIVIL, g.VINCULO_CEDIDO, g.ATIVO, g.SEM_CONTRIBUICAO)),
    (("Não se Aplica", "Prestador de Serviço - UEG", "UEG"),
     (g.PRESTADOR, "", g.ATIVO, g.RGPS_CONTRIBUINTE_INDIVIDUAL)),
    (("Não se Aplica", "Membro Conselho - JUCEG - RGPS", "JUCEG"),
     (g.PRESTADOR, "", g.ATIVO, g.RGPS_CONTRIBUINTE_INDIVIDUAL)),
    (("Não se Aplica", "Médico Residente", "SAÚDE"),
     (g.OUTROS, g.VINCULO_RESIDENCIA, g.ATIVO, g.RGPS_CONTRIBUINTE_INDIVIDUAL)),
    (("Não se Aplica", "Estagiário - Nível Superior - Livre Seleção", SEDUC),
     (g.OUTROS, g.VINCULO_ESTAGIO, g.ATIVO, g.SEM_CONTRIBUICAO)),
    (("Não se Aplica", "Pensionista Especial - Césio 137", GOIASPREV),
     (g.OUTROS, g.VINCULO_PENSAO_ESPECIAL, g.PENSIONISTA, g.SEM_CONTRIBUICAO)),
]


@pytest.mark.parametrize("entrada, esperado", CASOS, ids=[c[0][1][:40] for c in CASOS])
def test_classificacao(entrada, esperado):
    simbolo, nome, orgao = entrada
    linha = classificar_registros([{"SIMBOLOCARGO": simbolo, "NOMECARGO": nome, "ORGAO": orgao}]).iloc[0]
    obtido = (linha["REGIME_TRABALHO"], linha["VINCULO"], linha["SITUACAO"], linha["GRUPO_PREVIDENCIARIO"])
    assert obtido == esperado


def test_todos_os_regimes_do_anexo_i_tem_grupo():
    registros = [{"SIMBOLOCARGO": s, "NOMECARGO": n, "ORGAO": o} for (s, n, o), _ in CASOS]
    frame = classificar_registros(registros)
    assert set(g.REGIMES_ANEXO_I) <= set(frame["REGIME_TRABALHO"])
    assert not frame["GRUPO_PREVIDENCIARIO"].eq(g.NAO_ENQUADRADO).any()
