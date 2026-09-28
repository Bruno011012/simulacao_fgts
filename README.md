# Parametrização de rubricas de IRRF, INSS e RPPS

Solução do **Teste para Analista de Folha de Pagamento e RH (VOBYS)**: uma lógica de lançamento das
rubricas de Imposto de Renda, Contribuição INSS (RGPS) e Contribuição Previdenciária do Regime Próprio (RPPS)
a partir dos dados cadastrais dos servidores. Ela foi aplicada à folha real do **Estado de Goiás**
(07/2026, 167.466 registros, 41 órgãos), o mesmo cenário do teste (40 órgãos e cerca de 166 mil servidores).

> O foco é **quem recebe qual rubrica** na competência, e não o valor. O teste pede os critérios
> "independente da forma de cálculo".

## Resposta ao teste, em resumo

**1. Agrupamento.** Os 6 regimes do Anexo I se reduzem a **5 formas de contribuição**. As rubricas se ligam ao grupo, e não ao regime:

| Grupo previdenciário | Regimes |
|---|---|
| RPPS | Estatutário · Servidor Público Civil com vínculo RPPS · aposentados e pensionistas civis |
| Proteção Social Militar | Servidor Público Militar (ativo, reserva ou reforma, pensionista) |
| RGPS – segurado empregado | Servidor Comissionado (sem cargo efetivo) · Temporário · Civil celetista |
| RGPS – contribuinte individual | Prestador de Serviços |
| Sem contribuição no ente | Estagiário · cedido/convênio · pensão especial |

O **IRRF vale para todos os grupos**. A isenção exige **ser beneficiário (aposentado, reformado ou pensionista) E ter laudo vigente**.

**2. Rubricas.** Núcleo mínimo de **5** (RPPS, Militar, INSS empregado, INSS contribuinte individual, IRRF),
desdobrado em **14**. O desdobramento separa ativo × beneficiário, mensal × 13º e IRRF de férias, porque cada divisão muda a base de cálculo ou o evento do eSocial.

**3. Critérios lógicos.** Uma regra por rubrica, no formato do exemplo do teste. Exemplo:

```
5102 CONTRIB. RPPS - APOSENTADO/PENSIONISTA
SE Grupo = RPPS
   E Situação ∈ {INATIVO, PENSIONISTA}
   E Data Início Vínculo <= fim da competência
   E (Data Fim Vínculo nula OU Data Fim Vínculo >= início da competência)
   E possui rendimento no mês
ENTÃO verdadeiro SENÃO falso
```

➡️ A resposta completa, com as 14 regras, está em **[docs/regras_negocio.md](docs/regras_negocio.md)**.

## Como executar

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt

python -m src.main                                      # base completa, se estiver em data/input/
python -m src.main --entrada data/input/amostra_folha.csv   # amostra que acompanha o repositório
python -m src.main --sem-abrir                          # gera tudo sem abrir o navegador
python -m pytest                                        # 74 testes
```

A base completa (`folhapagamento_202607.csv`, 36 MB) não vai para o Git. Coloque-a em `data/input/`.
Sem ela, o programa usa automaticamente a amostra anonimizada de 727 linhas, que cobre todos os regimes e as 14 rubricas.

Saídas em `data/output/`:
- `lancamentos_rubricas_AAAAMM.csv`: uma linha por servidor × rubrica lançada;
- `servidores_classificados_AAAAMM.csv`: classificação e uma coluna True/False por rubrica;
- `resumo_rubricas_AAAAMM.csv` e `resumo_grupos_AAAAMM.csv`.

## Relatório HTML

Ao final de cada execução, o programa lê os CSVs de `data/output/`, gera
**`relatorios/relatorio_rubricas_AAAAMM.html`** e o abre no navegador padrão (módulo `webbrowser`).
Use `--sem-abrir` para apenas gerar o arquivo.

O relatório é um arquivo único e autocontido (gráficos em SVG, sem bibliotecas externas, abre offline),
com visual cyberpunk em tons suaves, e conta a história dos dados em cinco capítulos:

| Capítulo | Conteúdo |
|---|---|
| Indicadores | registros, lançamentos, rubricas acionadas, beneficiários, isentos de IR |
| 01 · Quem está na folha | tabela dos 5 grupos previdenciários |
| 02 · O que foi lançado | **gráfico de barras**: lançamentos por rubrica, colorido por tributo |
| 03 · Perfil de renda | **gráfico de linhas**: distribuição do provento mensal por grupo |
| 04 · Concentração | **gráfico de linhas**: % acumulado de registros por órgão (curva de Pareto) |
| 05 · Controles | verificações de consistência com selo OK/ATENÇÃO |

Os textos de cada capítulo são gerados a partir dos números, e passar o mouse sobre as marcas mostra os valores.

## Resultado na base completa

| Rubrica | Lançamentos |
|---|---:|
| 5101 RPPS – servidor ativo | 41.735 |
| 5102 RPPS – aposentado/pensionista | 59.301 |
| 5201 / 5202 Militar – ativo / reserva e reforma | 14.198 / 13.536 |
| 5301 INSS – segurado empregado | 32.619 |
| 5303 INSS – contribuinte individual | 470 |
| 5401 IRRF – mês | 159.418 |
| 13º (5103, 5104, 5203, 5204, 5302, 5402) e férias (5403) | ver [docs](docs/regras_negocio.md#4-resultado-na-base-real-072026--estado-de-goiás) |

Verificações: **0** servidores com mais de uma previdência mensal e **0** servidores sem grupo previdenciário.

> ⚠️ O CSV público não traz datas de vínculo nem laudos de isenção de IR. Esses campos são **simulados**
> com semente fixa (resultado reproduzível) e substituídos automaticamente se o CSV os trouxer.
> Detalhes em [docs/classificacao_cadastro.md](docs/classificacao_cadastro.md#3-campos-simulados).

## Documentação

| Documento | Conteúdo |
|---|---|
| [docs/regras_negocio.md](docs/regras_negocio.md) | agrupamento, as 14 rubricas e os critérios lógicos (a resposta ao teste) |
| [docs/classificacao_cadastro.md](docs/classificacao_cadastro.md) | como o CSV vira regime, vínculo, situação e grupo; premissas a validar |
| [docs/arquitetura.md](docs/arquitetura.md) | fluxo, estrutura de pastas, decisões de projeto e como estender |
| [docs/relatorio.md](docs/relatorio.md) | o relatório HTML: capítulos, gráficos, paleta e como personalizar |

## Estrutura

```
src/
├── main.py, config.py
├── dados/            carregamento e tratamento do CSV
├── cadastro/         classificação cadastral e simulação de campos ausentes
├── parametrizacao/   grupos, catálogo de rubricas e regras de lançamento  ← núcleo
├── processamento/    aplicação das regras e exportação
└── relatorio/        métricas, gráficos SVG e montagem do HTML
tests/                74 testes (pytest)
docs/                 documentação
data/input, data/output
relatorios/           relatório HTML gerado
```
