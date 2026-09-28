"""Deduz, a partir dos dados cadastrais do CSV, o regime de trabalho (Anexo I), o subtipo
de vínculo, a situação funcional e — com esses três — o grupo previdenciário.

Colunas usadas (versões normalizadas, sem acento e em maiúsculas, criadas em dados.tratamento):
    SIMBOLOCARGO_NORM, NOMECARGO_NORM, ORGAO_NORM

As regras são avaliadas em ordem e a primeira que casar vence. As premissas de cada uma
estão documentadas em docs/classificacao_cadastro.md.
"""

import numpy as np
import pandas as pd

from src.parametrizacao import grupos as g

# Símbolos de cargo em comissão / função de confiança (cargo principal = comissionado puro)
PADRAO_COMISSIONADO = r"^(?:CC-\d|DAS-\d|DAID-\d|DAI-\d|A\d$|AE\d$|LAP$|DSE-\d)"
SIMBOLOS_COMISSIONADO = {"COMISSAO-RGPS", "COMISSIONADO - INATIVO"}

# Cedidos / convênios: remuneração complementar, contribuição recolhida na origem
SIMBOLOS_CEDIDO = {"CONVENIO", "VAPT VUPT"}
PADRAO_CEDIDO = r"^CROE"

# Quadro transitório, celetistas e empregados de estatais incorporadas
PADRAO_CELETISTA = r"CLT|(?:^|[\s-])QT(?:[\s-]|$)|EMPREGO PUBLICO|METROBUS|CAIXEGO|PRODAGO|METAGO|TRANSURB|INCORPORACAO"
# "IPASGO" sozinho é nome de órgão (cargos efetivos do instituto); só indica vínculo RPPS em "CLT/IPASGO"
PADRAO_VINCULO_RPPS = r"RPPS|CLT/IPASGO"


def _regras_regime(frame: pd.DataFrame) -> list[tuple[pd.Series, str, str]]:
    """Lista ordenada de (condição, regime de trabalho, vínculo)."""
    nome = frame["NOMECARGO_NORM"]
    simb = frame["SIMBOLOCARGO_NORM"]
    texto = simb + " | " + nome

    return [
        (nome.str.startswith("PENSIONISTA"), g.OUTROS, g.VINCULO_PENSAO_ESPECIAL),
        (nome.str.startswith("ESTAGIARIO"), g.OUTROS, g.VINCULO_ESTAGIO),
        (nome.str.contains("MEDICO RESIDENTE", regex=False), g.OUTROS, g.VINCULO_RESIDENCIA),
        (nome.str.contains("PRESTADOR DE SERVICO", regex=False) | nome.str.match(r"^MEMBRO (?:DE )?CONSELHO"),
         g.PRESTADOR, ""),
        (simb.eq("CTEMPORARIO") | nome.str.match(r"^C\. ?TEMPORARIO"), g.TEMPORARIO, ""),
        (simb.str.contains("PM/CBM", regex=False) | nome.str.contains("CARGO MILITAR", regex=False), g.MILITAR, ""),
        (simb.str.match(PADRAO_COMISSIONADO) | simb.isin(SIMBOLOS_COMISSIONADO)
         | nome.str.contains("CARGO EM COMISSAO", regex=False), g.COMISSIONADO, ""),
        (simb.isin(SIMBOLOS_CEDIDO) | simb.str.match(PADRAO_CEDIDO), g.CIVIL, g.VINCULO_CEDIDO),
        (texto.str.contains(PADRAO_VINCULO_RPPS), g.CIVIL, g.VINCULO_RPPS),
        (texto.str.contains(PADRAO_CELETISTA), g.CIVIL, g.VINCULO_CELETISTA),
    ]


def classificar_regime(frame: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    regras = _regras_regime(frame)
    condicoes = [c.to_numpy(dtype=bool) for c, _, _ in regras]
    regime = np.select(condicoes, [r for _, r, _ in regras], default=g.ESTATUTARIO)
    vinculo = np.select(condicoes, [v for _, _, v in regras], default="")
    return pd.Series(regime, index=frame.index), pd.Series(vinculo, index=frame.index)


def classificar_situacao(frame: pd.DataFrame, regime: pd.Series, vinculo: pd.Series) -> pd.Series:
    nome = frame["NOMECARGO_NORM"]
    simb = frame["SIMBOLOCARGO_NORM"]
    # A GOIASPREV é quem paga aposentadorias e pensões do Estado: todo vínculo efetivo
    # lançado nela é benefício. Comissionados, temporários, estagiários e requisitados
    # de outros entes (cedidos) formam o quadro próprio do instituto.
    beneficio_goiasprev = (
        frame["ORGAO_NORM"].str.contains("GOIASPREV", regex=False)
        & regime.isin([g.ESTATUTARIO, g.CIVIL, g.MILITAR])
        & vinculo.ne(g.VINCULO_CEDIDO)
    )

    condicoes = [
        nome.str.contains("PENSIONISTA", regex=False),
        nome.str.contains("INATIVO", regex=False) | simb.str.contains("INATIVO|REFORMADO"),
        beneficio_goiasprev,
    ]
    valores = [g.PENSIONISTA, g.INATIVO, g.INATIVO]
    return pd.Series(
        np.select([c.to_numpy(dtype=bool) for c in condicoes], valores, default=g.ATIVO), index=frame.index
    )


def classificar_cadastro(frame: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta REGIME_TRABALHO, VINCULO, SITUACAO e GRUPO_PREVIDENCIARIO."""
    frame = frame.copy()
    frame["REGIME_TRABALHO"], frame["VINCULO"] = classificar_regime(frame)
    frame["SITUACAO"] = classificar_situacao(frame, frame["REGIME_TRABALHO"], frame["VINCULO"])
    frame["GRUPO_PREVIDENCIARIO"] = g.definir_grupo_previdenciario(frame)
    return frame
