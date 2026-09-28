# Classificação cadastral — do CSV ao grupo previdenciário

O teste pede o lançamento "a partir dos dados cadastrais dos servidores". O CSV do portal de
transparência não tem uma coluna "regime de trabalho", mas os campos `SIMBOLOCARGO`, `NOMECARGO` e
`ORGAO` permitem deduzir o regime com boa precisão. Este documento registra cada regra e cada premissa.

Código: [src/cadastro/classificacao.py](../src/cadastro/classificacao.py)

## 1. A base de dados

| Item | Valor |
|---|---|
| Arquivo | `data/input/folhapagamento_202607.csv` (36 MB, `;`, decimal `,`, UTF-8 com BOM) |
| Origem | Folha do **Estado de Goiás**, competência 07/2026 |
| Registros / órgãos | 167.466 / 41 |
| Colunas usadas | `ORGAO`, `SIMBOLOCARGO`, `NOMECARGO`, `ANOMES`, `VALORPROVENTOMES`, `VALORDECIMOTERCEIRO`, `VALORFERIAS` |

Antes de classificar, [src/dados/tratamento.py](../src/dados/tratamento.py) cria versões normalizadas dos
textos (maiúsculas, sem acento): `CONVÊNIO` vira `CONVENIO` e `Não se Aplica` vira `NAO SE APLICA`.

## 2. Regras de classificação

### 2.1 Regime de trabalho e vínculo

As regras são avaliadas **na ordem abaixo**; a primeira que casar vence. O que não casar com nenhuma é **ESTATUTÁRIO**.

| # | Condição (sobre os textos normalizados) | Regime | Vínculo | Registros |
|---|---|---|---|---:|
| 1 | `NOMECARGO` começa com "PENSIONISTA" | OUTROS | PENSAO_ESPECIAL | 1.555 |
| 2 | `NOMECARGO` começa com "ESTAGIARIO" | OUTROS | ESTAGIO | 1.000 |
| 3 | `NOMECARGO` contém "MEDICO RESIDENTE" | OUTROS | RESIDENCIA_MEDICA | 354 |
| 4 | `NOMECARGO` contém "PRESTADOR DE SERVICO" ou começa com "MEMBRO (DE) CONSELHO" | PRESTADOR DE SERVIÇOS | — | 153 |
| 5 | `SIMBOLOCARGO = CTEMPORARIO` ou `NOMECARGO` começa com "C. TEMPORARIO" | TEMPORÁRIO | — | 24.685 |
| 6 | `SIMBOLOCARGO` contém "PM/CBM" ou `NOMECARGO` contém "CARGO MILITAR" | SERVIDOR PÚBLICO MILITAR | — | 27.734 |
| 7 | `SIMBOLOCARGO` é símbolo de comissão (`CC-n`, `DAS-n`, `DAID-n`, `DAI-n`, `An`, `AEn`, `LAP`, `DSE-n`, `COMISSAO-RGPS`, `COMISSIONADO - INATIVO`) | SERVIDOR COMISSIONADO | — | 6.789 |
| 8 | `SIMBOLOCARGO` ∈ {`CONVENIO`, `VAPT VUPT`} ou começa com `CROE` | SERVIDOR PÚBLICO CIVIL | CEDIDO_CONVENIO | 1.105 |
| 9 | símbolo ou nome contém "RPPS" ou "CLT/IPASGO" | SERVIDOR PÚBLICO CIVIL | VINCULO_RPPS | 143 |
| 10 | símbolo ou nome contém "CLT", "QT", "EMPREGO PUBLICO" ou uma estatal incorporada (METROBUS, CAIXEGO, PRODAGO, METAGO, TRANSURB) | SERVIDOR PÚBLICO CIVIL | CELETISTA | 4.571 |
| — | nenhuma das anteriores (`P - IV`, `AAE-A`, `PCR`, `PCR - EST`, `NS-TC`, `AFRE`, …) | ESTATUTÁRIO | — | 99.377 |

Observações:
- `A-1`, `A-2` (com hífen) são níveis de carreira efetiva, e não assessoria. Por isso o padrão de comissão usa `^A\d$`.
- "IPASGO" sozinho é **nome de órgão** (cargos efetivos do instituto de saúde) e não indica regime. Só `CLT/IPASGO` indica vínculo RPPS.
- Quando o símbolo principal é efetivo e o cargo em comissão aparece apenas em `SIMBOLOCARGOSECUNDARIO`, o servidor continua Estatutário.

### 2.2 Situação funcional

| # | Condição | Situação |
|---|---|---|
| 1 | `NOMECARGO` contém "PENSIONISTA" | PENSIONISTA |
| 2 | nome ou símbolo contém "INATIVO", ou o símbolo contém "REFORMADO" | INATIVO |
| 3 | `ORGAO` = GOIASPREV **e** regime ∈ {Estatutário, Civil, Militar} **e** vínculo ≠ cedido | INATIVO |
| — | demais | ATIVO |

A **GOIASPREV** é o órgão que paga aposentadorias e pensões do Estado (72.942 registros na base). Um cargo efetivo
lançado nela é benefício. Comissionados, temporários, estagiários e requisitados de outros entes (`CROE*`)
lotados na GOIASPREV formam o quadro próprio do instituto e ficam como ATIVO.

### 2.3 Grupo previdenciário

Com regime, vínculo e situação definidos, [src/parametrizacao/grupos.py](../src/parametrizacao/grupos.py) aplica o
mapa descrito em [regras_negocio.md §1.2](regras_negocio.md#12-mapa-regime--grupo).

## 3. Campos simulados

As regras de lançamento precisam de datas que o CSV público **não traz**. Elas são geradas por
[src/cadastro/simulacao.py](../src/cadastro/simulacao.py) com semente fixa (`config.SEMENTE_SIMULACAO = 42`),
de modo que o resultado seja sempre o mesmo:

| Campo | Como é simulado |
|---|---|
| `DATA_INICIO_VINCULO` | 1 a 35 anos antes da competência (contratos por prazo: 1 mês a 3 anos) |
| `DATA_FIM_VINCULO` | nula para vínculos permanentes; para temporário, prestador, estágio e residência: entre 60 dias antes e 2 anos depois do início da competência (parte já encerrada, para exercitar a regra) |
| `DATA_INICIO_ISENCAO_IR` | laudo para 8% dos beneficiários, 0,5% dos ativos (para mostrar que ativo não fica isento) e 100% das pensões especiais do Césio 137 / acidente radioativo (contaminação por radiação — Lei 7.713/88, art. 6º, XIV) |
| `DATA_FIM_ISENCAO_IR` | 25% dos laudos têm prazo (parte já vencida); os demais são por prazo indeterminado |

**Se o CSV de entrada já tiver essas quatro colunas, elas são usadas e nada é simulado.** Em produção,
esses dados vêm do cadastro funcional do sistema de RH.

## 4. Premissas a validar com o cliente

| Premissa | Impacto se estiver errada |
|---|---|
| `CROE*`, `CONVÊNIO` e `VAPT VUPT` são cedidos cuja contribuição é recolhida na origem | passariam para RPPS ou RGPS_EMPREGADO |
| Quadro transitório celetista (`QT-PCR-CLT`) ativo contribui para o RGPS | passaria para RPPS |
| Conselheiros com jeton são contribuintes individuais | poderiam ficar sem contribuição (se o jeton não integrar base) |
| Pensões "Especial", "Judicial" e "Notarial" são indenizatórias, sem contribuição previdenciária | pensões do RPPS iriam para a rubrica 5102 |
| Militares têm sistema próprio (SPSM), separado do RPPS civil | 5201–5204 seriam fundidas com 5101–5104 |
