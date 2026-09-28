"""Agrupamento dos regimes de trabalho pela FORMA DE CONTRIBUIÇÃO previdenciária.

É o ponto central do teste: regimes diferentes que seguem a mesma regra caem no mesmo
grupo, e cada rubrica passa a ter UMA regra por grupo (e não uma regra por regime).

    Regime de trabalho (Anexo I)        Vínculo / situação               Grupo previdenciário
    ---------------------------------   ------------------------------   ----------------------------
    ESTATUTÁRIO                         qualquer                         RPPS
    SERVIDOR PÚBLICO CIVIL              vínculo RPPS ou benefício        RPPS
    SERVIDOR PÚBLICO CIVIL              celetista (QT/CLT, empregado)    RGPS_EMPREGADO
    SERVIDOR PÚBLICO CIVIL              cedido / convênio                SEM_CONTRIBUICAO_NO_ENTE
    SERVIDOR PÚBLICO MILITAR            ativo, reformado, pensionista    SPSM_MILITAR
    SERVIDOR COMISSIONADO               ativo (cargo em comissão puro)   RGPS_EMPREGADO
    SERVIDOR COMISSIONADO               inativo pago pelo ente           RPPS
    TEMPORÁRIO                          qualquer                         RGPS_EMPREGADO
    PRESTADOR DE SERVIÇOS               qualquer                         RGPS_CONTRIBUINTE_INDIVIDUAL
    OUTROS (fora do Anexo I)            residência médica                RGPS_CONTRIBUINTE_INDIVIDUAL
    OUTROS (fora do Anexo I)            estágio, pensão especial         SEM_CONTRIBUICAO_NO_ENTE
"""

import numpy as np
import pandas as pd

# Regimes do Anexo I
ESTATUTARIO = "ESTATUTÁRIO"
CIVIL = "SERVIDOR PÚBLICO CIVIL"
MILITAR = "SERVIDOR PÚBLICO MILITAR"
COMISSIONADO = "SERVIDOR COMISSIONADO"
TEMPORARIO = "TEMPORÁRIO"
PRESTADOR = "PRESTADOR DE SERVIÇOS"
OUTROS = "OUTROS (FORA DO ANEXO I)"

REGIMES_ANEXO_I = [ESTATUTARIO, CIVIL, MILITAR, COMISSIONADO, TEMPORARIO, PRESTADOR]

# Situação funcional
ATIVO = "ATIVO"
INATIVO = "INATIVO"
PENSIONISTA = "PENSIONISTA"
BENEFICIARIOS = [INATIVO, PENSIONISTA]  # recebem benefício (aposentadoria/reforma/pensão)

# Grupos previdenciários
RPPS = "RPPS"
SPSM_MILITAR = "SPSM_MILITAR"
RGPS_EMPREGADO = "RGPS_EMPREGADO"
RGPS_CONTRIBUINTE_INDIVIDUAL = "RGPS_CONTRIBUINTE_INDIVIDUAL"
SEM_CONTRIBUICAO = "SEM_CONTRIBUICAO_NO_ENTE"
NAO_ENQUADRADO = "NAO_ENQUADRADO"

DESCRICAO_GRUPOS = {
    RPPS: "Regime Próprio dos servidores civis (GOIASPREV) — ativos, aposentados e pensionistas",
    SPSM_MILITAR: "Sistema de Proteção Social dos Militares (Lei 13.954/2019) — ativos, reserva/reforma e pensionistas",
    RGPS_EMPREGADO: "RGPS/INSS como segurado empregado — comissionado puro, temporário e celetista",
    RGPS_CONTRIBUINTE_INDIVIDUAL: "RGPS/INSS como contribuinte individual — prestador de serviço, conselheiro, médico residente",
    SEM_CONTRIBUICAO: "Sem contribuição previdenciária retida pelo Estado — estagiário, cedido/convênio, pensão especial",
}

# Subtipos de vínculo (coluna VINCULO) que alteram o grupo dentro de um mesmo regime
VINCULO_RPPS = "VINCULO_RPPS"
VINCULO_CELETISTA = "CELETISTA"
VINCULO_CEDIDO = "CEDIDO_CONVENIO"
VINCULO_ESTAGIO = "ESTAGIO"
VINCULO_RESIDENCIA = "RESIDENCIA_MEDICA"
VINCULO_PENSAO_ESPECIAL = "PENSAO_ESPECIAL"


def definir_grupo_previdenciario(frame: pd.DataFrame) -> pd.Series:
    """Recebe REGIME_TRABALHO, SITUACAO e VINCULO e devolve o grupo. A primeira regra que casar vence."""
    regime = frame["REGIME_TRABALHO"]
    situacao = frame["SITUACAO"]
    vinculo = frame["VINCULO"]
    beneficiario = situacao.isin(BENEFICIARIOS)

    regras = [
        # 1. quem não tem contribuição retida pelo Estado
        (regime.eq(OUTROS) & vinculo.isin([VINCULO_ESTAGIO, VINCULO_PENSAO_ESPECIAL]), SEM_CONTRIBUICAO),
        (regime.eq(CIVIL) & vinculo.eq(VINCULO_CEDIDO), SEM_CONTRIBUICAO),
        # 2. contribuinte individual
        (regime.eq(PRESTADOR), RGPS_CONTRIBUINTE_INDIVIDUAL),
        (regime.eq(OUTROS) & vinculo.eq(VINCULO_RESIDENCIA), RGPS_CONTRIBUINTE_INDIVIDUAL),
        # 3. militares (ativos e inativos) têm sistema próprio
        (regime.eq(MILITAR), SPSM_MILITAR),
        # 4. RPPS: efetivos, civis com vínculo RPPS e todo benefício civil pago pelo ente
        (regime.eq(ESTATUTARIO), RPPS),
        (regime.eq(CIVIL) & vinculo.eq(VINCULO_RPPS), RPPS),
        (regime.isin([CIVIL, COMISSIONADO]) & beneficiario, RPPS),
        # 5. RGPS segurado empregado
        (regime.isin([COMISSIONADO, TEMPORARIO]), RGPS_EMPREGADO),
        (regime.eq(CIVIL) & vinculo.eq(VINCULO_CELETISTA), RGPS_EMPREGADO),
    ]

    condicoes = [c.to_numpy(dtype=bool) for c, _ in regras]
    grupos = [g for _, g in regras]
    return pd.Series(np.select(condicoes, grupos, default=NAO_ENQUADRADO), index=frame.index)
