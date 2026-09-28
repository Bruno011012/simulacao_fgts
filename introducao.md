# Introdução ao código

Este documento explica **como o programa insere as rubricas na base**: o caminho que o CSV da folha
percorre até cada servidor receber (ou não) cada rubrica. Ele cobre os módulos de previdência e de
predicados, todos os módulos que alteram a base e a lógica geral do programa.

Para as regras de negócio (a resposta ao teste), veja [docs/regras_negocio.md](docs/regras_negocio.md).
Para a estrutura de pastas e as decisões de projeto, veja [docs/arquitetura.md](docs/arquitetura.md).

---

## 1. A ideia central

A "base" é um único `pandas.DataFrame` com **uma linha por registro da folha**. O programa nunca
calcula valor de desconto. Ele responde apenas: **este servidor recebe esta rubrica nesta competência?**

Para isso, a base passa por etapas que **acrescentam colunas**, nunca apagam:

```
CSV bruto
  │  dados/carregamento.py     lê e valida as colunas
  ▼
  │  dados/tratamento.py       + valores em float, + colunas *_NORM
  ▼
  │  cadastro/classificacao.py + REGIME_TRABALHO, VINCULO, SITUACAO, GRUPO_PREVIDENCIARIO
  ▼
  │  cadastro/simulacao.py     + DATA_INICIO/FIM_VINCULO, DATA_INICIO/FIM_ISENCAO_IR, CADASTRO_SIMULADO
  ▼
  │  processamento/lancamento.py  aplicar_regras()  + R5101 … R5403  (uma coluna True/False por rubrica)
  ▼
servidores (formato "largo")  ──► gerar_lancamentos() ──► lancamentos (formato "longo", 1 linha por servidor × rubrica)
```

Quem orquestra tudo é `processar_dataframe()` em [src/processamento/folha.py](src/processamento/folha.py).
O ponto de entrada da linha de comando é [src/main.py](src/main.py).

**Toda função que altera a base começa com `frame = frame.copy()`.** Assim, cada etapa devolve um
DataFrame novo e não modifica o que recebeu. Isso facilita testar cada etapa isoladamente.

---

## 2. Como a rubrica entra na base

A inserção de uma rubrica envolve **três peças**, cada uma em um arquivo de `src/parametrizacao/`:

| Peça | Arquivo | O que define |
|---|---|---|
| Catálogo | [rubricas.py](src/parametrizacao/rubricas.py) | código, descrição, tributo, grupo, público, parcela e evento do eSocial |
| Regra | [previdencia.py](src/parametrizacao/previdencia.py) ou [irrf.py](src/parametrizacao/irrf.py) | a função booleana que decide quem recebe |
| Registro | [regras.py](src/parametrizacao/regras.py) | o dicionário `REGRAS` que liga o código à função |

### 2.1 O catálogo (`rubricas.py`)

Cada rubrica é um `Rubrica` (dataclass imutável) dentro da lista `CATALOGO`:

```python
Rubrica("5101", "CONTRIB. RPPS - SERVIDOR ATIVO", "RPPS", g.RPPS, "ATIVO", "MENSAL", "S-1200/S-1202")
```

O catálogo é **descritivo**: ele não decide nada. Serve para nomear a rubrica nas saídas e dar a
ordem das colunas. A função `coluna_flag("5101")` devolve o nome da coluna na base: `"R5101"`.

### 2.2 A regra (`previdencia.py` / `irrf.py`)

Toda regra tem a mesma assinatura:

```python
def regra(frame: pd.DataFrame, competencia: Competencia) -> pd.Series  # Series booleana, uma posição por servidor
```

A regra é **vetorizada**: ela avalia os 167 mil registros de uma vez, sem laço `for` por servidor.

### 2.3 O registro (`regras.py`)

```python
REGRAS: dict[str, Regra] = {
    "5101": previdencia.rpps_servidor_ativo,
    ...
    "5403": irrf.irrf_ferias,
}
```

Há também `PREVIDENCIA_MENSAL`, a lista das rubricas previdenciárias mensais. Um servidor pode ter
**no máximo uma** delas, e isso é verificado ao final.

### 2.4 A gravação na base (`lancamento.aplicar_regras`)

Este é o momento em que a rubrica é de fato inserida na base:

```python
def aplicar_regras(frame, competencia):
    frame = frame.copy()
    for codigo, regra in REGRAS.items():
        frame[coluna_flag(codigo)] = regra(frame, competencia).astype(bool)
    return frame
```

Para cada código do dicionário, a função da regra roda sobre a base inteira e o resultado vira a
coluna `R<código>`. Ao final, a base tem 14 colunas novas (`R5101` … `R5403`), com `True` onde a
rubrica é lançada.

Em seguida, `gerar_lancamentos()` transforma essas colunas em uma tabela de lançamentos: para cada
rubrica do `CATALOGO`, filtra as linhas com `True`, acrescenta `CODIGO_RUBRICA`, `DESCRICAO_RUBRICA`,
`TRIBUTO` e `EVENTO_ESOCIAL`, e empilha tudo. Esse é o arquivo `lancamentos_rubricas_AAAAMM.csv`.

### 2.5 Como incluir uma rubrica nova

1. Acrescente a `Rubrica(...)` em `CATALOGO` ([rubricas.py](src/parametrizacao/rubricas.py)).
2. Escreva a função da regra combinando predicados ([previdencia.py](src/parametrizacao/previdencia.py),
   [irrf.py](src/parametrizacao/irrf.py) ou um módulo novo).
3. Registre `"código": funcao` em `REGRAS` ([regras.py](src/parametrizacao/regras.py)). Se for uma
   previdência mensal, inclua o código também em `PREVIDENCIA_MENSAL`.
4. Crie o teste correspondente em `tests/`.

Nada mais precisa mudar: `aplicar_regras`, `gerar_lancamentos`, os resumos, a exportação e o
relatório percorrem `REGRAS` e `CATALOGO` automaticamente.

---

## 3. Predicados (`predicados.py`)

[src/parametrizacao/predicados.py](src/parametrizacao/predicados.py) contém os **blocos lógicos**
reutilizados pelas regras. Cada predicado recebe a base e devolve uma Series booleana. As regras
são apenas combinações desses blocos com `&` (E), `|` (OU) e `~` (NÃO).

| Predicado | Verdadeiro quando | Coluna lida |
|---|---|---|
| `no_grupo(frame, grupo)` | o servidor pertence ao grupo previdenciário informado | `GRUPO_PREVIDENCIARIO` |
| `ativo(frame)` | situação = ATIVO | `SITUACAO` |
| `beneficiario(frame)` | situação ∈ {INATIVO, PENSIONISTA} (aposentado, reformado, pensionista) | `SITUACAO` |
| `vinculo_vigente(frame, comp)` | o vínculo toca algum dia da competência | `DATA_INICIO_VINCULO`, `DATA_FIM_VINCULO` |
| `possui_rendimento_mes(frame)` | provento do mês > 0 | `VALORPROVENTOMES` |
| `possui_decimo_terceiro(frame)` | 13º > 0 | `VALORDECIMOTERCEIRO` |
| `possui_ferias(frame)` | férias > 0 | `VALORFERIAS` |
| `isencao_ir_vigente(frame, comp)` | é beneficiário **E** tem laudo de isenção vigente | `SITUACAO`, `DATA_INICIO_ISENCAO_IR`, `DATA_FIM_ISENCAO_IR` |

A vigência de qualquer período (vínculo ou laudo) usa `vigente_na_competencia()` de
[competencia.py](src/parametrizacao/competencia.py):

```
início NÃO nulo
E início <= último dia da competência
E (fim nulo OU fim >= primeiro dia da competência)
```

> O exemplo do teste compara `início >= início da competência`, o que excluiria quem começou antes
> do mês. A forma acima é a leitura correta de "vigente no mês" e está comentada no código.

A classe `Competencia` é criada a partir do `ANOMES` do CSV (`"202607"` → julho/2026) e fornece
`inicio` (dia 1) e `fim` (último dia do mês).

**Por que predicados?** Se o critério de "vínculo vigente" mudar, altera-se um único lugar e todas
as 14 rubricas passam a usar a regra nova.

---

## 4. Previdência (`previdencia.py`)

[src/parametrizacao/previdencia.py](src/parametrizacao/previdencia.py) contém as 11 regras
previdenciárias. Todas seguem o mesmo molde, montado pela função auxiliar `_base()`:

```python
def _base(frame, competencia, grupo):
    return p.no_grupo(frame, grupo) & p.vinculo_vigente(frame, competencia)
```

Sobre essa base, cada regra acrescenta **o público** (ativo ou beneficiário) e **a parcela**
(rendimento do mês ou 13º):

| Código | Função | Grupo | Público | Parcela |
|---|---|---|---|---|
| 5101 | `rpps_servidor_ativo` | RPPS | ativo | mês |
| 5102 | `rpps_beneficiario` | RPPS | beneficiário | mês |
| 5103 | `rpps_13_servidor_ativo` | RPPS | ativo | 13º |
| 5104 | `rpps_13_beneficiario` | RPPS | beneficiário | 13º |
| 5201 | `militar_ativo` | SPSM_MILITAR | ativo | mês |
| 5202 | `militar_beneficiario` | SPSM_MILITAR | beneficiário | mês |
| 5203 | `militar_13_ativo` | SPSM_MILITAR | ativo | 13º |
| 5204 | `militar_13_beneficiario` | SPSM_MILITAR | beneficiário | 13º |
| 5301 | `inss_empregado` | RGPS_EMPREGADO | (todos do grupo) | mês |
| 5302 | `inss_13_empregado` | RGPS_EMPREGADO | (todos do grupo) | 13º |
| 5303 | `inss_contribuinte_individual` | RGPS_CONTRIBUINTE_INDIVIDUAL | (todos do grupo) | mês |

Exemplo lido em linguagem natural (5102):

```
SE grupo = RPPS
   E vínculo vigente na competência
   E situação ∈ {INATIVO, PENSIONISTA}
   E provento do mês > 0
ENTÃO lança
```

Como cada servidor tem **um único grupo** e as rubricas mensais de um grupo separam ativo de
beneficiário, as regras são mutuamente exclusivas por construção. Isso garante no máximo uma
previdência mensal por servidor.

### IRRF (`irrf.py`)

O IR não depende do grupo previdenciário: vale para todos. O único fator que impede o lançamento é a
isenção.

| Código | Regra |
|---|---|
| 5401 | vínculo vigente **E** rendimento no mês **E NÃO** isenção vigente |
| 5402 | vínculo vigente **E** 13º > 0 **E NÃO** isenção vigente |
| 5403 | vínculo vigente **E** ativo **E** férias > 0 (a isenção não se aplica a ativos) |

---

## 5. Grupos previdenciários (`grupos.py`)

[src/parametrizacao/grupos.py](src/parametrizacao/grupos.py) define as constantes (regimes, situações,
vínculos, grupos) e a função `definir_grupo_previdenciario()`. É ela que permite ter **uma regra por
grupo** em vez de uma regra por regime.

A função usa `numpy.select` com uma lista ordenada de condições. **A primeira que casar vence:**

1. Sem contribuição no ente: estágio, pensão especial, civil cedido/convênio.
2. Contribuinte individual: prestador de serviços, residência médica.
3. Militar: todo regime militar (ativo, reserva, reforma, pensionista).
4. RPPS: estatutário, civil com vínculo RPPS, beneficiário civil ou comissionado inativo.
5. RGPS empregado: comissionado ativo, temporário, civil celetista.

Quem não casar com nenhuma regra recebe `NAO_ENQUADRADO`, e a verificação de consistência conta
esses casos (o esperado é zero).

---

## 6. Todos os módulos que alteram a base

| Ordem | Módulo / função | Colunas que acrescenta ou modifica |
|---|---|---|
| 1 | [dados/carregamento.py](src/dados/carregamento.py) `carregar_folha` | cria a base: lê o CSV (`;`, decimal `,`, UTF-8 com BOM) e falha se faltar coluna obrigatória |
| 2 | [dados/tratamento.py](src/dados/tratamento.py) `tratar_folha` | **modifica** `VALOR*` (para float, nulo = 0) e `ANOMES`; **cria** `ORGAO_NORM`, `NOMECARGO_NORM`, `SIMBOLOCARGO_NORM` etc. (maiúsculas, sem acento) |
| 3 | [cadastro/classificacao.py](src/cadastro/classificacao.py) `classificar_cadastro` | cria `REGIME_TRABALHO`, `VINCULO`, `SITUACAO` e, via `grupos.py`, `GRUPO_PREVIDENCIARIO` |
| 4 | [cadastro/simulacao.py](src/cadastro/simulacao.py) `completar_cadastro` | cria `DATA_INICIO_VINCULO`, `DATA_FIM_VINCULO`, `DATA_INICIO_ISENCAO_IR`, `DATA_FIM_ISENCAO_IR`, `CADASTRO_SIMULADO` |
| 5 | [processamento/lancamento.py](src/processamento/lancamento.py) `aplicar_regras` | cria `R5101` … `R5403` |
| 6 | [processamento/lancamento.py](src/processamento/lancamento.py) `gerar_lancamentos`, `resumir_por_rubrica`, `resumir_por_grupo` | não alteram a base: geram **tabelas novas** a partir dela |
| 7 | [processamento/folha.py](src/processamento/folha.py) `exportar` | não altera a base: seleciona colunas e grava os 4 CSVs em `data/output/` |

Os módulos de `src/parametrizacao/` (`predicados`, `previdencia`, `irrf`, `competencia`) **só leem**
a base e devolvem Series booleanas. A única exceção é `grupos.definir_grupo_previdenciario`, que
devolve a Series gravada como `GRUPO_PREVIDENCIARIO` pela etapa 3.

### Detalhes das etapas 3 e 4

**Classificação cadastral.** O CSV público não tem campo de regime. Ele é deduzido de
`SIMBOLOCARGO_NORM` e `NOMECARGO_NORM` por uma lista ordenada de regras (regex e `startswith`):
pensionista especial → estagiário → residente → prestador → temporário → militar → comissionado →
cedido → vínculo RPPS → celetista → (padrão) estatutário. A situação vem de palavras como
`PENSIONISTA`, `INATIVO`, `REFORMADO` e do órgão GOIASPREV, que paga os benefícios do Estado.
As premissas estão em [docs/classificacao_cadastro.md](docs/classificacao_cadastro.md).

**Simulação.** O CSV não traz datas de vínculo nem laudos de isenção de IR, mas as regras precisam
deles. Se o CSV **tiver** as quatro colunas, elas são usadas e `CADASTRO_SIMULADO = False`. Se não
tiver, são sorteadas com semente fixa (`SEMENTE_SIMULACAO = 42` em [config.py](src/config.py)), o que
torna o resultado reproduzível. Em produção esses dados viriam do cadastro funcional do RH.

---

## 7. Lógica do programa, do início ao fim

1. `main.py` lê os argumentos (`--entrada`, `--saida`, `--limite`, `--semente`, `--relatorios`,
   `--sem-abrir`). Sem `--entrada`, usa a base completa se existir, ou a amostra.
2. `processar_arquivo()` carrega o CSV e chama `processar_dataframe()`.
3. `processar_dataframe()`:
   - trata os dados;
   - exige **uma única competência** no arquivo e cria o objeto `Competencia`;
   - classifica o cadastro;
   - completa (ou simula) datas e laudos;
   - aplica as 14 regras (colunas `R<código>`);
   - gera lançamentos, resumos e verificações e devolve tudo em um `ResultadoFolha`.
4. `verificar_consistencia()` conta:
   - servidores com mais de uma previdência mensal (esperado 0);
   - servidores sem grupo previdenciário (esperado 0);
   - servidores sem nenhuma rubrica (informativo);
   - beneficiários com laudo vencido que receberam IRRF (informativo).
5. `main.py` imprime os quadros no terminal e `exportar()` grava os CSVs em `data/output/`.
6. `src/relatorio/` lê os CSVs, monta `relatorios/relatorio_rubricas_AAAAMM.html` e o abre no
   navegador (a menos que se use `--sem-abrir`).

```bash
python -m src.main --entrada data/input/amostra_folha.csv   # roda com a amostra
python -m pytest                                            # roda os testes
```
