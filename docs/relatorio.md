# Relatório HTML

Ao final de `python -m src.main`, o projeto gera um relatório visual da parametrização e o abre no navegador.

| Item | Valor |
|---|---|
| Arquivo | `relatorios/relatorio_rubricas_AAAAMM.html` |
| Fonte dos dados | os CSVs gerados em `data/output/` (`servidores_classificados` e `resumo_rubricas`) |
| Abertura | automática, via `webbrowser.open()`; desligue com `--sem-abrir` |
| Outra pasta | `--relatorios <diretório>` |
| Dependências | nenhuma: HTML, CSS, JS e SVG ficam no mesmo arquivo, que abre offline (as fontes do Google são opcionais, com fonte do sistema como alternativa) |

Código: [src/relatorio/](../src/relatorio/)

```
metricas.py  → lê os CSVs e calcula indicadores, faixas de provento e concentração por órgão
graficos.py  → desenha barras e linhas em SVG (com tooltip e rótulos diretos)
gerador.py   → escreve a narrativa, monta o HTML e abre no navegador
```

## Storytelling: os capítulos

O relatório não é só uma coleção de gráficos. Cada capítulo responde uma pergunta, e os textos
são gerados a partir dos números da execução (mudam se a base mudar).

| # | Pergunta | Visual | Mensagem principal (base 07/2026) |
|---|---|---|---|
| — | Qual o tamanho do problema? | 5 indicadores | 167.466 registros, 347.781 lançamentos, 14/14 rubricas acionadas |
| 01 | Quem está na folha? | tabela de grupos | 6 regimes viram 5 formas de contribuição; o RPPS tem 60% da base |
| 02 | O que foi lançado? | **barras** por rubrica, cor por tributo | o IRRF alcança 95% da base; no RPPS há **mais aposentados contribuindo do que ativos** |
| 03 | Quanto ganha cada grupo? | **linhas**: % do grupo por faixa de provento | o INSS empregado (temporários) concentra-se nas faixas baixas; os militares estão mais à direita |
| 04 | Onde a folha se concentra? | **linhas**: % acumulado por órgão (Pareto) | GOIASPREV + Educação = 70%; 4 órgãos chegam a 80% |
| 05 | Dá para confiar? | selos de controle | 0 servidores com duas previdências, 0 sem grupo; aviso de dados simulados |

## Gráficos

1. **Barras horizontais: lançamentos por rubrica.** São 14 barras ordenadas da maior para a menor. A cor indica o
   tributo (RPPS, Proteção Social Militar, INSS, IRRF), com legenda. O valor aparece na ponta de cada barra
   e o tooltip mostra a descrição completa e o % da base. A tabela de dados fica logo abaixo, recolhível.
2. **Linhas: distribuição do provento mensal.** O eixo x são 10 faixas ordenadas (até 2k … 30k+) e o eixo y é o % dos
   servidores **dentro de cada grupo**. O % é usado, e não a quantidade, para comparar formatos entre grupos de tamanhos
   muito diferentes. Os grupos pequenos (contribuinte individual e sem contribuição) são somados em "Demais".
   Ao passar o mouse, uma linha-guia mostra os 4 valores da faixa.
3. **Linhas: concentração por órgão.** Os 41 órgãos são ordenados do maior para o menor, e a linha mostra o % acumulado.
   Há uma linha de referência em 80% e um destaque no ponto em que ela é atingida. O tooltip mostra o nome do órgão.

## Paleta e visual

Estilo cyberpunk em tons suaves: fundo índigo escuro com leve grade e brilhos difusos, títulos em Orbitron e
números em fonte monoespaçada. As cores das séries foram **validadas** (faixa de luminosidade, croma, separação
para daltonismo e contraste sobre o fundo `#1c1930`):

| Ordem | Cor | Hex | Uso |
|---|---|---|---|
| 1 | ciano | `#19a3ad` | RPPS |
| 2 | lavanda | `#8a78ec` | Militares / Proteção Social Militar |
| 3 | âmbar | `#b8801a` | INSS |
| 4 | magenta | `#d65a9c` | IRRF / Demais |

Os selos de controle usam cores de status separadas (verde, amarelo, vermelho) sempre acompanhadas de ícone e texto.

## Como personalizar

- **Cores:** `CORES` em [graficos.py](../src/relatorio/graficos.py) e as variáveis `--*` no início do `CSS` em [gerador.py](../src/relatorio/gerador.py).
- **Faixas de provento:** `LIMITES_FAIXA` e `ROTULOS_FAIXA` em [metricas.py](../src/relatorio/metricas.py).
- **Textos da narrativa:** função `_narrativa` em [gerador.py](../src/relatorio/gerador.py).
- **Gerar só o relatório** a partir de CSVs já existentes:

```python
from pathlib import Path
from src.relatorio import gerar_relatorio, abrir_no_navegador

saida = Path("data/output")
arquivos = {
    "servidores": saida / "servidores_classificados_202607.csv",
    "resumo_rubricas": saida / "resumo_rubricas_202607.csv",
}
abrir_no_navegador(gerar_relatorio(arquivos, "relatorios"))
```
