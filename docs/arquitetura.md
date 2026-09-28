# Arquitetura

## Fluxo

```
data/input/*.csv
      │
      ▼
dados/carregamento.py     lê o CSV e valida as colunas obrigatórias
      │
      ▼
dados/tratamento.py       converte valores (decimal ',') e cria textos normalizados *_NORM
      │
      ▼
cadastro/classificacao.py deduz REGIME_TRABALHO, VINCULO e SITUACAO
      │                   └─ parametrizacao/grupos.py → GRUPO_PREVIDENCIARIO
      ▼
cadastro/simulacao.py     completa datas de vínculo e laudos de IR (se ausentes no CSV)
      │
      ▼
processamento/lancamento.py  aplica parametrizacao/regras.py → 1 coluna booleana por rubrica
      │
      ▼
processamento/folha.py    orquestra tudo e exporta os CSVs para data/output/
      │
      ▼
relatorio/                lê os CSVs gerados → métricas → gráficos SVG → relatorios/*.html
      │
      ▼
webbrowser.open()         abre o relatório no navegador (desligável com --sem-abrir)
```

## Estrutura

```
.
├── README.md
├── requirements.txt
├── pytest.ini
├── .gitignore
│
├── src/
│   ├── main.py                    CLI: processa, imprime o resumo e exporta
│   ├── config.py                  caminhos relativos e semente da simulação
│   │
│   ├── dados/
│   │   ├── carregamento.py        leitura do CSV
│   │   └── tratamento.py          tipos numéricos e normalização de texto
│   │
│   ├── cadastro/
│   │   ├── classificacao.py       CSV → regime, vínculo, situação
│   │   └── simulacao.py           campos cadastrais ausentes no CSV
│   │
│   ├── parametrizacao/            ← o núcleo do teste
│   │   ├── competencia.py         competência e regra de vigência
│   │   ├── grupos.py              agrupamento regime → forma de contribuição
│   │   ├── rubricas.py            catálogo das 14 rubricas (código, descrição, eSocial)
│   │   ├── predicados.py          blocos lógicos reutilizáveis
│   │   ├── previdencia.py         regras RPPS / militar / INSS
│   │   ├── irrf.py                regras de IRRF e isenção
│   │   └── regras.py              registro código → regra
│   │
│   ├── processamento/
│   │   ├── lancamento.py          aplica regras, gera lançamentos, resumos e checagens
│   │   └── folha.py               pipeline completo + exportação
│   │
│   └── relatorio/
│       ├── metricas.py            lê os CSVs de data/output e calcula os indicadores
│       ├── graficos.py            barras e linhas em SVG puro (paleta validada)
│       └── gerador.py             narrativa, HTML/CSS/JS e abertura no navegador
│
├── data/
│   ├── input/
│   │   ├── folhapagamento_202607.csv   base completa (fora do Git)
│   │   └── amostra_folha.csv           727 linhas estratificadas e anonimizadas (no Git)
│   └── output/                         gerado pelo processamento (fora do Git)
│
├── relatorios/
│   └── relatorio_rubricas_AAAAMM.html  relatório visual gerado ao final da execução
│
├── tests/
│   ├── conftest.py                construtores de cenários
│   ├── test_competencia.py        vigência na competência (e o exemplo do PDF)
│   ├── test_classificacao.py      CSV → regime/grupo, caso a caso
│   ├── test_previdencia.py        rubricas 51xx, 52xx, 53xx
│   ├── test_irrf.py               rubricas 54xx e isenção
│   ├── test_rubricas.py           integridade do catálogo e execução ponta a ponta
│   └── test_relatorio.py          geração do HTML com os 3 gráficos
│
├── docs/
│   ├── regras_negocio.md          resposta ao teste: agrupamento, rubricas e critérios
│   ├── classificacao_cadastro.md  como o CSV vira regime/grupo e as premissas assumidas
│   ├── arquitetura.md             este arquivo
│   └── relatorio.md               o relatório HTML
│
└── legado/                        primeira versão do projeto (fora do Git)
```

## Decisões de projeto

| Decisão | Motivo |
|---|---|
| **Regras por rubrica, não por regime** | Era o critério de avaliação nº 1 ("agrupamento de grupos para uma mesma regra"). Um regime novo só precisa ser mapeado para um grupo, sem mexer em nenhuma regra. |
| **Grupo previdenciário como camada intermediária** | Separa "quem é o servidor" (cadastro) de "que rubrica recebe" (parametrização). |
| **Regras vetorizadas em pandas** | Cada regra é uma expressão booleana sobre colunas: legível como o "SE … ENTÃO" do teste e rápida (167 mil registros em cerca de 5 s). |
| **Sem módulo de cálculo** | O teste pede os critérios "independente da forma de cálculo". Alíquotas fixas seriam incorretas (IR e INSS são progressivos) e fora do escopo. Para calcular, basta criar `src/calculos/` consumindo a tabela de lançamentos. |
| **Simulação separada e desligável** | Deixa explícito o que é dado real e o que é premissa; se o CSV trouxer as datas, a simulação não é aplicada. |
| **Relatório lê os CSVs, e não a memória** | O relatório depende só dos arquivos de `data/output/`: pode ser regenerado a partir de qualquer execução e testado isoladamente. |
| **Gráficos em SVG gerado pelo Python** | Sem CDN nem bibliotecas de gráfico: o HTML abre offline e continua sendo um único arquivo para enviar. |
| **Catálogo com evento do eSocial** | O projeto da VOBYS inclui a substituição do transmissor eSocial; a rubrica já nasce ligada ao evento em que será informada. |

## Saídas

| Arquivo | Conteúdo |
|---|---|
| `servidores_classificados_AAAAMM.csv` | 1 linha por registro: classificação, datas e uma coluna `R<código>` (True/False) por rubrica |
| `lancamentos_rubricas_AAAAMM.csv` | 1 linha por servidor × rubrica lançada, com descrição, tributo e evento do eSocial |
| `resumo_rubricas_AAAAMM.csv` | quantidade de lançamentos por rubrica |
| `resumo_grupos_AAAAMM.csv` | quantidade de servidores por regime × vínculo × situação × grupo |
| `relatorios/relatorio_rubricas_AAAAMM.html` | relatório visual com indicadores, 3 gráficos e narrativa (ver [relatorio.md](relatorio.md)) |

## Como estender

- **Nova rubrica:** cadastre-a em `rubricas.CATALOGO`, escreva a função em `previdencia.py` ou `irrf.py` e registre em `regras.REGRAS`. O teste `test_toda_rubrica_tem_regra_e_toda_regra_tem_rubrica` acusa se faltar um dos lados.
- **Novo regime ou símbolo de cargo:** ajuste a lista em `classificacao._regras_regime` e acrescente um caso em `tests/test_classificacao.py`.
- **Cálculo dos valores:** crie `src/calculos/` recebendo `lancamentos_rubricas` e as tabelas vigentes (IR, INSS, alíquotas do RPPS e do SPSM).
