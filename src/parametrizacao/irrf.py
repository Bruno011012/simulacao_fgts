"""Regras de lançamento das rubricas de IRRF.

O IR independe do regime previdenciário: vale para todos os grupos. O único fator que
retira o lançamento é a isenção, que exige ser beneficiário E ter laudo vigente
(observação do Anexo I: "servidores inativos/aposentados que possuem isenção").
"""

from src.parametrizacao import predicados as p


def irrf_mensal(frame, competencia):                                  # 5401
    return (
        p.vinculo_vigente(frame, competencia)
        & p.possui_rendimento_mes(frame)
        & ~p.isencao_ir_vigente(frame, competencia)
    )


def irrf_13(frame, competencia):                                      # 5402
    return (
        p.vinculo_vigente(frame, competencia)
        & p.possui_decimo_terceiro(frame)
        & ~p.isencao_ir_vigente(frame, competencia)
    )


def irrf_ferias(frame, competencia):                                  # 5403
    # férias só existem para quem está em atividade; a isenção não se aplica a ativos
    return p.vinculo_vigente(frame, competencia) & p.ativo(frame) & p.possui_ferias(frame)
