"""Pipeline completo: carregar -> tratar -> classificar -> completar cadastro -> lançar rubricas."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.cadastro.classificacao import classificar_cadastro
from src.cadastro.simulacao import COLUNAS_SIMULADAS, completar_cadastro
from src.dados.carregamento import carregar_folha
from src.dados.tratamento import tratar_folha
from src.parametrizacao.competencia import Competencia
from src.parametrizacao.rubricas import CATALOGO, coluna_flag
from src.processamento import lancamento


@dataclass
class ResultadoFolha:
    competencia: Competencia
    servidores: pd.DataFrame        # 1 linha por registro, com classificação e flags R<código>
    lancamentos: pd.DataFrame       # 1 linha por servidor x rubrica lançada
    resumo_rubricas: pd.DataFrame
    resumo_grupos: pd.DataFrame
    consistencia: dict[str, int]


def processar_dataframe(bruto: pd.DataFrame, semente: int) -> ResultadoFolha:
    tratado = tratar_folha(bruto)

    anomes = tratado["ANOMES"].unique()
    if len(anomes) != 1:
        raise ValueError(f"O arquivo deve conter uma única competência; encontradas: {list(anomes)}")
    competencia = Competencia.de_anomes(anomes[0])

    classificado = classificar_cadastro(tratado)
    completo = completar_cadastro(classificado, competencia, semente)
    servidores = lancamento.aplicar_regras(completo, competencia)

    return ResultadoFolha(
        competencia=competencia,
        servidores=servidores,
        lancamentos=lancamento.gerar_lancamentos(servidores),
        resumo_rubricas=lancamento.resumir_por_rubrica(servidores),
        resumo_grupos=lancamento.resumir_por_grupo(servidores),
        consistencia=lancamento.verificar_consistencia(servidores),
    )


def processar_arquivo(caminho: str | Path, semente: int, limite_linhas: int | None = None) -> ResultadoFolha:
    return processar_dataframe(carregar_folha(caminho, limite_linhas), semente)


def exportar(resultado: ResultadoFolha, diretorio: str | Path) -> dict[str, Path]:
    diretorio = Path(diretorio)
    diretorio.mkdir(parents=True, exist_ok=True)
    sufixo = f"{resultado.competencia.ano}{resultado.competencia.mes:02d}"

    colunas_servidores = (
        lancamento.COLUNAS_IDENTIFICACAO
        + ["VALORPROVENTOMES", "VALORDECIMOTERCEIRO", "VALORFERIAS"]
        + COLUNAS_SIMULADAS
        + ["CADASTRO_SIMULADO"]
        + [coluna_flag(r.codigo) for r in CATALOGO]
    )

    arquivos = {
        "servidores": diretorio / f"servidores_classificados_{sufixo}.csv",
        "lancamentos": diretorio / f"lancamentos_rubricas_{sufixo}.csv",
        "resumo_rubricas": diretorio / f"resumo_rubricas_{sufixo}.csv",
        "resumo_grupos": diretorio / f"resumo_grupos_{sufixo}.csv",
    }
    opcoes = {"sep": ";", "decimal": ",", "index": False, "encoding": "utf-8-sig"}
    resultado.servidores[colunas_servidores].to_csv(arquivos["servidores"], **opcoes)
    resultado.lancamentos.to_csv(arquivos["lancamentos"], **opcoes)
    resultado.resumo_rubricas.to_csv(arquivos["resumo_rubricas"], **opcoes)
    resultado.resumo_grupos.to_csv(arquivos["resumo_grupos"], **opcoes)
    return arquivos
