# Regras de negócio — lançamento de rubricas de IRRF, INSS e RPPS

Este documento é a resposta escrita ao *Teste para Analista de Folha de Pagamento e RH (VOBYS)*.
O teste pede três coisas, e cada uma tem uma seção:

1. [Agrupamento dos regimes](#1-agrupamento-dos-regimes-de-trabalho) pela forma de contribuição previdenciária e de IR
2. [Quantas e quais rubricas](#2-quantas-e-quais-rubricas-de-desconto) de desconto criar, com descrição
3. [Critérios lógicos de lançamento](#3-critérios-lógicos-de-lançamento) de cada rubrica, **independentemente da forma de cálculo**

> **Escopo:** aqui se decide **quem recebe qual rubrica** em uma competência. Alíquotas, faixas,
> tetos e o valor de cada desconto são *forma de cálculo* e ficam fora do escopo, como o próprio
> teste determina.

---

## 1. Agrupamento dos regimes de trabalho

O agrupamento parte da seguinte observação: **o regime de trabalho não determina, sozinho, a forma de contribuição.**
Regimes diferentes seguem a mesma regra, e um mesmo regime pode se dividir conforme o vínculo e a situação.
Por isso as rubricas são ligadas a **grupos previdenciários**, e não aos 6 regimes do Anexo I.

### 1.1 Grupos previdenciários

| Grupo | Forma de contribuição | Quem entra |
|---|---|---|
| **RPPS** | Regime Próprio dos servidores civis (GOIASPREV) | Estatutário; Servidor Público Civil com vínculo RPPS; todo aposentado ou pensionista civil pago pelo Estado |
| **SPSM_MILITAR** | Sistema de Proteção Social dos Militares (Lei 13.954/2019) | Servidor Público Militar: ativo, reserva ou reforma, pensionista |
| **RGPS_EMPREGADO** | INSS como segurado empregado | Servidor Comissionado (cargo em comissão puro); Temporário; Servidor Público Civil celetista |
| **RGPS_CONTRIBUINTE_INDIVIDUAL** | INSS como contribuinte individual | Prestador de Serviços (inclui conselheiros com jeton); médico residente |
| **SEM_CONTRIBUICAO_NO_ENTE** | Nenhuma retenção previdenciária pelo Estado | Estagiário; cedido/convênio (contribui na origem); pensão especial ou indenizatória |

### 1.2 Mapa regime → grupo

| Regime de trabalho (Anexo I) | Vínculo / situação | Grupo |
|---|---|---|
| ESTATUTÁRIO | ativo, aposentado ou pensionista | RPPS |
| SERVIDOR PÚBLICO CIVIL | vínculo RPPS (ex.: `QT-PCR-CLT-RPPS`, `CLT/IPASGO`) | RPPS |
| SERVIDOR PÚBLICO CIVIL | aposentado ou pensionista pago pelo Estado | RPPS |
| SERVIDOR PÚBLICO CIVIL | celetista ativo (quadro transitório, estatais incorporadas) | RGPS_EMPREGADO |
| SERVIDOR PÚBLICO CIVIL | cedido/convênio | SEM_CONTRIBUICAO_NO_ENTE |
| SERVIDOR PÚBLICO MILITAR | ativo, reformado ou pensionista | SPSM_MILITAR |
| SERVIDOR COMISSIONADO | ativo (sem cargo efetivo) — CF art. 40 §13 | RGPS_EMPREGADO |
| SERVIDOR COMISSIONADO | aposentado legado pago pelo Estado | RPPS |
| TEMPORÁRIO | ativo | RGPS_EMPREGADO |
| PRESTADOR DE SERVIÇOS | ativo | RGPS_CONTRIBUINTE_INDIVIDUAL |

> O servidor **efetivo** que ocupa cargo em comissão como função secundária continua **Estatutário/RPPS**.
> Só o comissionado sem vínculo efetivo vai para o RGPS.

### 1.3 Imposto de Renda

O IR **não depende do grupo previdenciário**: vale para todos. O único fator que retira o lançamento
é a **isenção**, que exige duas condições ao mesmo tempo:

- o servidor é **beneficiário** (aposentado, reformado ou pensionista), porque a isenção por moléstia grave
  (Lei 7.713/88, art. 6º, XIV) alcança só proventos de aposentadoria, reforma e pensão; **e**
- tem **laudo de isenção vigente** na competência.

Isso atende à observação do Anexo I ("independente do regime previdenciário, existem inativos/aposentados
com isenção de IR"): a isenção se aplica igualmente a aposentados do RPPS, militares reformados e pensionistas.

---

## 2. Quantas e quais rubricas de desconto

### 2.1 Núcleo mínimo — 5 rubricas

Uma rubrica por forma de contribuição, mais o IR:

| # | Rubrica |
|---|---|
| 1 | Contribuição RPPS |
| 2 | Contribuição de Proteção Social Militar |
| 3 | INSS – Segurado Empregado |
| 4 | INSS – Contribuinte Individual |
| 5 | IRRF |

### 2.2 Desdobramento recomendado — 14 rubricas (implementado)

Cada divisão abaixo existe porque muda a **base de cálculo** ou o **evento do eSocial** em que o valor é informado
(o eSocial faz parte do escopo do projeto da VOBYS):

- **ativo × beneficiário**: o aposentado ou pensionista do RPPS contribui só sobre a parcela que excede o limite;
  além disso, remuneração vai no S-1200/S-1202 e benefício vai no S-1207;
- **mensal × 13º**: o 13º tem base e apuração próprias (no IRRF, tributação exclusiva);
- **IRRF sobre férias**: apurado em separado no mês do pagamento.

| Código | Descrição | Grupo | Público | Parcela |
|---|---|---|---|---|
| 5101 | CONTRIB. RPPS - SERVIDOR ATIVO | RPPS | Ativo | Mensal |
| 5102 | CONTRIB. RPPS - APOSENTADO/PENSIONISTA | RPPS | Beneficiário | Mensal |
| 5103 | CONTRIB. RPPS S/ 13º - SERVIDOR ATIVO | RPPS | Ativo | 13º |
| 5104 | CONTRIB. RPPS S/ 13º - APOSENTADO/PENSIONISTA | RPPS | Beneficiário | 13º |
| 5201 | CONTRIB. PROTEÇÃO SOCIAL MILITAR - ATIVO | SPSM_MILITAR | Ativo | Mensal |
| 5202 | CONTRIB. PROTEÇÃO SOCIAL MILITAR - RESERVA/REFORMA/PENSÃO | SPSM_MILITAR | Beneficiário | Mensal |
| 5203 | CONTRIB. PROTEÇÃO SOCIAL MILITAR S/ 13º - ATIVO | SPSM_MILITAR | Ativo | 13º |
| 5204 | CONTRIB. PROTEÇÃO SOCIAL MILITAR S/ 13º - RESERVA/REFORMA/PENSÃO | SPSM_MILITAR | Beneficiário | 13º |
| 5301 | INSS - SEGURADO EMPREGADO | RGPS_EMPREGADO | Ativo | Mensal |
| 5302 | INSS S/ 13º - SEGURADO EMPREGADO | RGPS_EMPREGADO | Ativo | 13º |
| 5303 | INSS - CONTRIBUINTE INDIVIDUAL | RGPS_CONTRIBUINTE_INDIVIDUAL | Ativo | Mensal |
| 5401 | IRRF - RENDIMENTOS DO MÊS | todos | Todos | Mensal |
| 5402 | IRRF S/ 13º SALÁRIO (TRIBUTAÇÃO EXCLUSIVA) | todos | Todos | 13º |
| 5403 | IRRF S/ FÉRIAS | todos | Ativo | Férias |

O contribuinte individual não tem 13º, por isso não existe "INSS s/ 13º – contribuinte individual".
O grupo SEM_CONTRIBUICAO_NO_ENTE não tem rubrica previdenciária, só IRRF.

---

## 3. Critérios lógicos de lançamento

### 3.1 Blocos reutilizados

Todas as regras são combinações destes blocos (em [src/parametrizacao/predicados.py](../src/parametrizacao/predicados.py)):

| Bloco | Definição |
|---|---|
| `VINCULO_VIGENTE` | `Data Início Vínculo` não nula **E** `Data Início Vínculo <= último dia da competência` **E** (`Data Fim Vínculo` nula **OU** `Data Fim Vínculo >= primeiro dia da competência`) |
| `ATIVO` | `Situação = ATIVO` |
| `BENEFICIARIO` | `Situação ∈ {INATIVO, PENSIONISTA}` |
| `TEM_RENDIMENTO_MES` | valor de proventos do mês `> 0` |
| `TEM_13` | valor de 13º na competência `> 0` |
| `TEM_FERIAS` | valor de férias na competência `> 0` |
| `ISENCAO_IR_VIGENTE` | `BENEFICIARIO` **E** `Data Início Isenção` não nula **E** `Data Início Isenção <= último dia da competência` **E** (`Data Fim Isenção` nula **OU** `Data Fim Isenção >= primeiro dia da competência`) |

> **Sobre o exemplo do teste (contribuição sindical).** Ele usa "data de início **maior ou igual** ao início da
> competência" e "Data Fim nula **ou menor** que o início da competência". Tomada ao pé da letra, essa regra
> exclui quem se associou antes do mês e inclui quem já se desligou. A leitura correta de "vigente na
> competência" é a do bloco `VINCULO_VIGENTE` acima, e o teste `test_regra_literal_do_documento_seria_incorreta`
> demonstra a diferença.

### 3.2 Regras por rubrica

No formato do exemplo do teste: **SE** condição **ENTÃO** verdadeiro (lança), **SENÃO** falso.

**RPPS**
- **5101** — SE `Grupo = RPPS` E `ATIVO` E `VINCULO_VIGENTE` E `TEM_RENDIMENTO_MES` ENTÃO verdadeiro.
- **5102** — SE `Grupo = RPPS` E `BENEFICIARIO` E `VINCULO_VIGENTE` E `TEM_RENDIMENTO_MES` ENTÃO verdadeiro.
- **5103** — SE `Grupo = RPPS` E `ATIVO` E `VINCULO_VIGENTE` E `TEM_13` ENTÃO verdadeiro.
- **5104** — SE `Grupo = RPPS` E `BENEFICIARIO` E `VINCULO_VIGENTE` E `TEM_13` ENTÃO verdadeiro.

**Proteção Social Militar**
- **5201** — SE `Grupo = SPSM_MILITAR` E `ATIVO` E `VINCULO_VIGENTE` E `TEM_RENDIMENTO_MES` ENTÃO verdadeiro.
- **5202** — SE `Grupo = SPSM_MILITAR` E `BENEFICIARIO` E `VINCULO_VIGENTE` E `TEM_RENDIMENTO_MES` ENTÃO verdadeiro.
- **5203** — SE `Grupo = SPSM_MILITAR` E `ATIVO` E `VINCULO_VIGENTE` E `TEM_13` ENTÃO verdadeiro.
- **5204** — SE `Grupo = SPSM_MILITAR` E `BENEFICIARIO` E `VINCULO_VIGENTE` E `TEM_13` ENTÃO verdadeiro.

**INSS (RGPS)**
- **5301** — SE `Grupo = RGPS_EMPREGADO` E `VINCULO_VIGENTE` E `TEM_RENDIMENTO_MES` ENTÃO verdadeiro.
- **5302** — SE `Grupo = RGPS_EMPREGADO` E `VINCULO_VIGENTE` E `TEM_13` ENTÃO verdadeiro.
- **5303** — SE `Grupo = RGPS_CONTRIBUINTE_INDIVIDUAL` E `VINCULO_VIGENTE` E `TEM_RENDIMENTO_MES` ENTÃO verdadeiro.

**IRRF**
- **5401** — SE `VINCULO_VIGENTE` E `TEM_RENDIMENTO_MES` E **NÃO** `ISENCAO_IR_VIGENTE` ENTÃO verdadeiro.
- **5402** — SE `VINCULO_VIGENTE` E `TEM_13` E **NÃO** `ISENCAO_IR_VIGENTE` ENTÃO verdadeiro.
- **5403** — SE `VINCULO_VIGENTE` E `ATIVO` E `TEM_FERIAS` ENTÃO verdadeiro.

### 3.3 Garantias verificadas pelos testes

- Um servidor recebe **no máximo uma** rubrica previdenciária mensal (5101, 5102, 5201, 5202, 5301, 5303).
- Nenhum registro fica sem grupo previdenciário.
- Um ativo com laudo **não** fica isento; um beneficiário com laudo vencido volta a ser tributado.
- Um vínculo encerrado antes da competência não gera nenhuma rubrica; um vínculo encerrado **durante** a competência ainda gera.

---

## 4. Resultado na base real (07/2026 — Estado de Goiás)

167.466 registros, 41 órgãos (o teste cita 40 órgãos e cerca de 166.261 servidores).

| Grupo | Registros |
|---|---:|
| RPPS | 101.037 |
| RGPS_EMPREGADO | 34.528 |
| SPSM_MILITAR | 27.734 |
| SEM_CONTRIBUICAO_NO_ENTE | 3.660 |
| RGPS_CONTRIBUINTE_INDIVIDUAL | 507 |

| Rubrica | Lançamentos |
|---|---:|
| 5101 RPPS ativo | 41.735 |
| 5102 RPPS aposentado/pensionista | 59.301 |
| 5103 / 5104 RPPS 13º | 3.682 / 5.329 |
| 5201 / 5202 Militar ativo / inativo | 14.198 / 13.536 |
| 5203 / 5204 Militar 13º | 1.258 / 1.236 |
| 5301 / 5302 INSS empregado / 13º | 32.619 / 1.311 |
| 5303 INSS contribuinte individual | 470 |
| 5401 / 5402 / 5403 IRRF mês / 13º / férias | 159.418 / 12.394 / 1.294 |

> As datas de vínculo e os laudos de isenção **não existem no CSV público** e foram simulados (semente fixa).
> Por isso, os números de IRRF e das rubricas de temporários e prestadores mudam se esses campos vierem do cadastro real.
> Ver [classificacao_cadastro.md](classificacao_cadastro.md#3-campos-simulados).
