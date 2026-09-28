"""Lê os CSVs gerados em data/output e calcula os números que alimentam o relatório."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.parametrizacao import grupos as g

OPCOES_CSV = {"sep": ";", "decimal": ",", "encoding": "utf-8-sig"}

# Faixas de provento mensal (R$) usadas no gráfico de distribuição
LIMITES_FAIXA = [0, 2000, 4000, 6000, 8000, 10000, 12000, 15000, 20000, 30000, np.inf]
ROTULOS_FAIXA = ["até 2k", "2–4k", "4–6k", "6–8k", "8–10k", "10–12k", "12–15k", "15–20k", "20–30k", "30k+"]

# Séries do gráfico de distribuição: grupos pequenos são somados em "Demais"
SERIES_GRUPO = {
    "RPPS": [g.RPPS],
    "Militares": [g.SPSM_MILITAR],
    "INSS empregado": [g.RGPS_EMPREGADO],
    "Demais": [g.RGPS_CONTRIBUINTE_INDIVIDUAL, g.SEM_CONTRIBUICAO],
}


@dataclass
class Metricas:
    competencia: str
    total_registros: int
    total_orgaos: int
    total_lancamentos: int
    rubricas_distintas: int
    beneficiarios: int
    isentos_ir: int
    sem_rubrica: int
    multiplas_previdencias: int
    nao_enquadrados: int
    simulado: bool
    rubricas: pd.DataFrame            # CODIGO, DESCRICAO, TRIBUTO, QTD
    grupos: pd.DataFrame              # GRUPO, QTD, PCT
    regimes: pd.DataFrame             # REGIME_TRABALHO x GRUPO (contagens)
    faixas: dict[str, list[float]]    # série -> % do grupo em cada faixa
    faixas_medianas: dict[str, float]
    orgaos: pd.DataFrame              # ORGAO, QTD, PCT, PCT_ACUMULADO (ordenado)


def _competencia_do_nome(caminho: Path) -> str:
    sufixo = caminho.stem.rsplit("_", 1)[-1]
    return f"{sufixo[4:]}/{sufixo[:4]}" if len(sufixo) == 6 and sufixo.isdigit() else sufixo


def calcular_metricas(arquivos: dict[str, Path]) -> Metricas:
    servidores = pd.read_csv(arquivos["servidores"], **OPCOES_CSV)
    resumo = pd.read_csv(arquivos["resumo_rubricas"], dtype={"CODIGO_RUBRICA": str}, **OPCOES_CSV)

    flags = [c for c in servidores.columns if c.startswith("R") and c[1:].isdigit()]
    servidores[flags] = servidores[flags].astype(bool)
    prev_mensal = [c for c in ["R5101", "R5102", "R5201", "R5202", "R5301", "R5303"] if c in flags]

    beneficiario = servidores["SITUACAO"].isin(g.BENEFICIARIOS)
    laudo = pd.to_datetime(servidores["DATA_INICIO_ISENCAO_IR"], errors="coerce").notna()
    isentos = beneficiario & laudo & ~servidores["R5401"]

    grupos = servidores["GRUPO_PREVIDENCIARIO"].value_counts().rename_axis("GRUPO").reset_index(name="QTD")
    grupos["PCT"] = grupos["QTD"] / grupos["QTD"].sum() * 100

    regimes = pd.crosstab(servidores["REGIME_TRABALHO"], servidores["GRUPO_PREVIDENCIARIO"])

    faixa = pd.cut(servidores["VALORPROVENTOMES"], LIMITES_FAIXA, labels=ROTULOS_FAIXA, right=False)
    faixas, medianas = {}, {}
    for nome, membros in SERIES_GRUPO.items():
        no_grupo = servidores["GRUPO_PREVIDENCIARIO"].isin(membros)
        contagem = faixa[no_grupo].value_counts().reindex(ROTULOS_FAIXA, fill_value=0)
        total = max(int(no_grupo.sum()), 1)
        faixas[nome] = [round(v / total * 100, 2) for v in contagem]
        medianas[nome] = float(servidores.loc[no_grupo, "VALORPROVENTOMES"].median()) if no_grupo.any() else 0.0

    orgaos = servidores["ORGAO"].value_counts().rename_axis("ORGAO").reset_index(name="QTD")
    orgaos["PCT"] = orgaos["QTD"] / orgaos["QTD"].sum() * 100
    orgaos["PCT_ACUMULADO"] = orgaos["PCT"].cumsum()

    rubricas = resumo.rename(
        columns={"CODIGO_RUBRICA": "CODIGO", "DESCRICAO_RUBRICA": "DESCRICAO", "QTD_LANCAMENTOS": "QTD"}
    )

    return Metricas(
        competencia=_competencia_do_nome(Path(arquivos["resumo_rubricas"])),
        total_registros=len(servidores),
        total_orgaos=servidores["ORGAO"].nunique(),
        total_lancamentos=int(rubricas["QTD"].sum()),
        rubricas_distintas=int((rubricas["QTD"] > 0).sum()),
        beneficiarios=int(beneficiario.sum()),
        isentos_ir=int(isentos.sum()),
        sem_rubrica=int((~servidores[flags].any(axis=1)).sum()),
        multiplas_previdencias=int((servidores[prev_mensal].sum(axis=1) > 1).sum()),
        nao_enquadrados=int(servidores["GRUPO_PREVIDENCIARIO"].eq(g.NAO_ENQUADRADO).sum()),
        simulado=bool(servidores.get("CADASTRO_SIMULADO", pd.Series([False])).astype(bool).any()),
        rubricas=rubricas,
        grupos=grupos,
        regimes=regimes,
        faixas=faixas,
        faixas_medianas=medianas,
        orgaos=orgaos,
    )
