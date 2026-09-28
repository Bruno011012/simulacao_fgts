"""Competência da folha e o teste de vigência de períodos (vínculo, laudo, etc.)."""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Competencia:
    ano: int
    mes: int

    @classmethod
    def de_anomes(cls, anomes: str | int) -> "Competencia":
        texto = str(anomes).strip()
        if len(texto) != 6 or not texto.isdigit():
            raise ValueError(f"ANOMES inválido: {anomes!r} (esperado AAAAMM)")
        return cls(ano=int(texto[:4]), mes=int(texto[4:]))

    @property
    def inicio(self) -> pd.Timestamp:
        return pd.Timestamp(year=self.ano, month=self.mes, day=1)

    @property
    def fim(self) -> pd.Timestamp:
        return self.inicio + pd.offsets.MonthEnd(0)

    def __str__(self) -> str:
        return f"{self.mes:02d}/{self.ano}"


def vigente_na_competencia(inicio: pd.Series, fim: pd.Series, competencia: Competencia) -> pd.Series:
    """Um período está vigente se tocar qualquer dia da competência:

        inicio NÃO nulo
        E inicio <= último dia da competência
        E (fim nulo OU fim >= primeiro dia da competência)

    Obs.: o exemplo do teste (contribuição sindical) compara 'início >= início da competência'
    e 'fim < início da competência' — isso excluiria quem começou antes do mês e incluiria
    quem já saiu. A forma acima é a interpretação correta de "vigente no mês".
    """
    inicio = pd.to_datetime(inicio)
    fim = pd.to_datetime(fim)
    return inicio.notna() & (inicio <= competencia.fim) & (fim.isna() | (fim >= competencia.inicio))
