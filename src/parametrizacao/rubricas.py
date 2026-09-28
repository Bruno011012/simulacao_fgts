"""Catálogo das rubricas de DESCONTO geradas pela parametrização.

Núcleo mínimo = 5 rubricas (uma por forma de contribuição + IRRF):
    RPPS, contribuição militar, INSS empregado, INSS contribuinte individual, IRRF.

Desdobramento recomendado = 14 rubricas, porque cada divisão abaixo muda a base
de cálculo ou o evento do eSocial em que o valor é informado:
    * ativo x benefício (aposentado/reformado/pensionista): no RPPS o inativo contribui
      só sobre o que excede o limite, e no eSocial remuneração vai no S-1200 e benefício no S-1207;
    * mensal x 13º: o 13º tem base e apuração próprias (IRRF com tributação exclusiva);
    * férias: o IRRF sobre férias é apurado em separado no mês do pagamento.
"""

from dataclasses import dataclass

from src.parametrizacao import grupos as g


@dataclass(frozen=True)
class Rubrica:
    codigo: str
    descricao: str
    tributo: str           # RPPS | SPSM | INSS | IRRF
    grupo: str | None      # grupo previdenciário atendido (None = qualquer grupo)
    publico: str           # ATIVO | BENEFICIARIO | TODOS
    referencia: str        # parcela sobre a qual incide (mensal, 13º, férias)
    evento_esocial: str


CATALOGO: list[Rubrica] = [
    # --- RPPS (servidor civil) ---
    Rubrica("5101", "CONTRIB. RPPS - SERVIDOR ATIVO", "RPPS", g.RPPS, "ATIVO", "MENSAL", "S-1200/S-1202"),
    Rubrica("5102", "CONTRIB. RPPS - APOSENTADO/PENSIONISTA", "RPPS", g.RPPS, "BENEFICIARIO", "MENSAL", "S-1207"),
    Rubrica("5103", "CONTRIB. RPPS S/ 13º - SERVIDOR ATIVO", "RPPS", g.RPPS, "ATIVO", "13º", "S-1200/S-1202"),
    Rubrica("5104", "CONTRIB. RPPS S/ 13º - APOSENTADO/PENSIONISTA", "RPPS", g.RPPS, "BENEFICIARIO", "13º", "S-1207"),
    # --- Sistema de Proteção Social dos Militares ---
    Rubrica("5201", "CONTRIB. PROTEÇÃO SOCIAL MILITAR - ATIVO", "SPSM", g.SPSM_MILITAR, "ATIVO", "MENSAL", "S-1200/S-1202"),
    Rubrica("5202", "CONTRIB. PROTEÇÃO SOCIAL MILITAR - RESERVA/REFORMA/PENSÃO", "SPSM", g.SPSM_MILITAR, "BENEFICIARIO", "MENSAL", "S-1207"),
    Rubrica("5203", "CONTRIB. PROTEÇÃO SOCIAL MILITAR S/ 13º - ATIVO", "SPSM", g.SPSM_MILITAR, "ATIVO", "13º", "S-1200/S-1202"),
    Rubrica("5204", "CONTRIB. PROTEÇÃO SOCIAL MILITAR S/ 13º - RESERVA/REFORMA/PENSÃO", "SPSM", g.SPSM_MILITAR, "BENEFICIARIO", "13º", "S-1207"),
    # --- RGPS / INSS ---
    Rubrica("5301", "INSS - SEGURADO EMPREGADO", "INSS", g.RGPS_EMPREGADO, "ATIVO", "MENSAL", "S-1200"),
    Rubrica("5302", "INSS S/ 13º - SEGURADO EMPREGADO", "INSS", g.RGPS_EMPREGADO, "ATIVO", "13º", "S-1200"),
    Rubrica("5303", "INSS - CONTRIBUINTE INDIVIDUAL", "INSS", g.RGPS_CONTRIBUINTE_INDIVIDUAL, "ATIVO", "MENSAL", "S-1200"),
    # --- Imposto de Renda Retido na Fonte ---
    Rubrica("5401", "IRRF - RENDIMENTOS DO MÊS", "IRRF", None, "TODOS", "MENSAL", "S-1200/S-1202/S-1207"),
    Rubrica("5402", "IRRF S/ 13º SALÁRIO (TRIBUTAÇÃO EXCLUSIVA)", "IRRF", None, "TODOS", "13º", "S-1200/S-1202/S-1207"),
    Rubrica("5403", "IRRF S/ FÉRIAS", "IRRF", None, "ATIVO", "FÉRIAS", "S-1200/S-1202"),
]

POR_CODIGO: dict[str, Rubrica] = {r.codigo: r for r in CATALOGO}


def coluna_flag(codigo: str) -> str:
    """Nome da coluna booleana que indica o lançamento da rubrica: 5101 -> 'R5101'."""
    return f"R{codigo}"
