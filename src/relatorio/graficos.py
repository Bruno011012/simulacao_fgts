"""Gráficos em SVG puro (sem bibliotecas externas): o HTML abre offline e fica leve.

Convenções visuais (validadas para o fundo escuro do relatório):
    * marcas finas: barras de 18px com ponta arredondada, linhas de 2px, marcadores de 8px;
    * grade e eixos em linhas finas e sólidas, um tom acima do fundo;
    * texto sempre nas cores de texto — a cor da série fica só na marca;
    * cada marca tem tooltip (atributo data-tip), tratado pelo JavaScript do relatório.
"""

import math
from html import escape

# Paleta categórica (ordem fixa, validada: faixa de luminosidade, croma, daltonismo e contraste)
CORES = {
    "ciano": "#19a3ad",
    "lavanda": "#8a78ec",
    "ambar": "#b8801a",
    "magenta": "#d65a9c",
}
ORDEM_CORES = ["ciano", "lavanda", "ambar", "magenta"]


def _num(valor: float, casas: int = 0) -> str:
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _escala_bonita(maximo: float, passos: int = 5) -> list[float]:
    if maximo <= 0:
        return [0, 1]
    bruto = maximo / passos
    potencia = 10 ** math.floor(math.log10(bruto))
    passo = next(m * potencia for m in (1, 2, 2.5, 5, 10) if m * potencia >= bruto)
    return [passo * i for i in range(int(math.ceil(maximo / passo)) + 1)]


def _barra_arredondada(x: float, y: float, largura: float, altura: float, raio: float = 4) -> str:
    """Retângulo ancorado na base (esquerda reta) com a ponta de dado arredondada."""
    r = min(raio, largura / 2, altura / 2)
    if largura <= 0:
        return ""
    return (
        f"M{x:.1f},{y:.1f} H{x + largura - r:.1f} Q{x + largura:.1f},{y:.1f} {x + largura:.1f},{y + r:.1f} "
        f"V{y + altura - r:.1f} Q{x + largura:.1f},{y + altura:.1f} {x + largura - r:.1f},{y + altura:.1f} "
        f"H{x:.1f} Z"
    )


def barras_horizontais(itens: list[dict], cores_categoria: dict[str, str], titulo_eixo: str) -> str:
    """itens: [{rotulo, valor, categoria, dica}] — já na ordem de exibição."""
    esq, dir_, topo, altura_linha, altura_barra = 330, 90, 16, 30, 18
    largura = 960
    area = largura - esq - dir_
    altura = topo + altura_linha * len(itens) + 44
    ticks = _escala_bonita(max(i["valor"] for i in itens))
    escala = area / ticks[-1]

    partes = [f'<svg class="grafico" viewBox="0 0 {largura} {altura}" role="img" aria-label="Lançamentos por rubrica">']
    base_eixo = topo + altura_linha * len(itens)
    for t in ticks:
        x = esq + t * escala
        partes.append(f'<line class="grade" x1="{x:.1f}" y1="{topo - 6}" x2="{x:.1f}" y2="{base_eixo}"/>')
        partes.append(f'<text class="eixo" x="{x:.1f}" y="{base_eixo + 18}" text-anchor="middle">{_num(t / 1000)}k</text>')
    partes.append(f'<text class="eixo-titulo" x="{esq + area / 2:.1f}" y="{altura - 4}" text-anchor="middle">{escape(titulo_eixo)}</text>')

    for i, item in enumerate(itens):
        y = topo + i * altura_linha + (altura_linha - altura_barra) / 2
        w = item["valor"] * escala
        cor = cores_categoria[item["categoria"]]
        partes.append(f'<g class="alvo" data-tip="{escape(item["dica"])}">')
        partes.append(f'<rect class="hit" x="0" y="{y - 5:.1f}" width="{largura}" height="{altura_barra + 10}"/>')
        partes.append(f'<text class="rotulo" x="{esq - 12}" y="{y + 13:.1f}" text-anchor="end">{escape(item["rotulo"])}</text>')
        partes.append(f'<path class="barra" d="{_barra_arredondada(esq, y, max(w, 2), altura_barra)}" fill="{cor}"/>')
        partes.append(f'<text class="valor" x="{esq + max(w, 2) + 8:.1f}" y="{y + 13:.1f}">{_num(item["valor"])}</text>')
        partes.append("</g>")
    partes.append(f'<line class="eixo-linha" x1="{esq}" y1="{topo - 6}" x2="{esq}" y2="{base_eixo}"/>')
    partes.append("</svg>")
    return "\n".join(partes)


def _afastar_rotulos(posicoes: list[tuple[str, float]], distancia: float = 15) -> dict[str, float]:
    """Empurra rótulos diretos que colidem verticalmente."""
    ordenados = sorted(posicoes, key=lambda p: p[1])
    ajustados: list[tuple[str, float]] = []
    for nome, y in ordenados:
        if ajustados and y - ajustados[-1][1] < distancia:
            y = ajustados[-1][1] + distancia
        ajustados.append((nome, y))
    return dict(ajustados)


def linhas(
    rotulos_x: list[str],
    series: dict[str, list[float]],
    cores_series: dict[str, str],
    formato_y,
    titulo_eixo_x: str,
    titulo_eixo_y: str,
    dicas_x: list[str] | None = None,
    marcar_cada: int = 1,
    referencia: tuple[float, str] | None = None,
    destaque: tuple[int, str] | None = None,
    rotulos_diretos: bool = True,
    y_max: float | None = None,
) -> str:
    """Gráfico de linhas com eixo x ordenado. Hover por coluna mostra todas as séries (crosshair)."""
    largura, altura = 960, 380
    esq, dir_, topo, base = 64, 150 if rotulos_diretos else 30, 24, 64
    area_w, area_h = largura - esq - dir_, altura - topo - base
    n = len(rotulos_x)
    maximo = y_max if y_max is not None else max(max(v) for v in series.values())
    ticks = _escala_bonita(maximo)
    passo_x = area_w / max(n - 1, 1)

    def px(i: int) -> float:
        return esq + i * passo_x

    def py(v: float) -> float:
        return topo + area_h - v / ticks[-1] * area_h

    partes = [f'<svg class="grafico" viewBox="0 0 {largura} {altura}" role="img" aria-label="{escape(titulo_eixo_y)}">']
    for t in ticks:
        partes.append(f'<line class="grade" x1="{esq}" y1="{py(t):.1f}" x2="{esq + area_w}" y2="{py(t):.1f}"/>')
        partes.append(f'<text class="eixo" x="{esq - 10}" y="{py(t) + 4:.1f}" text-anchor="end">{formato_y(t)}</text>')
    for i, rot in enumerate(rotulos_x):
        if i % marcar_cada == 0 or i == n - 1:
            partes.append(f'<text class="eixo" x="{px(i):.1f}" y="{topo + area_h + 20}" text-anchor="middle">{escape(rot)}</text>')
    partes.append(f'<line class="eixo-linha" x1="{esq}" y1="{topo + area_h}" x2="{esq + area_w}" y2="{topo + area_h}"/>')
    partes.append(f'<text class="eixo-titulo" x="{esq + area_w / 2:.1f}" y="{altura - 12}" text-anchor="middle">{escape(titulo_eixo_x)}</text>')
    partes.append(
        f'<text class="eixo-titulo" transform="translate(16 {topo + area_h / 2:.1f}) rotate(-90)" text-anchor="middle">{escape(titulo_eixo_y)}</text>'
    )

    if referencia:
        valor, texto = referencia
        partes.append(f'<line class="referencia" x1="{esq}" y1="{py(valor):.1f}" x2="{esq + area_w}" y2="{py(valor):.1f}"/>')
        partes.append(
            f'<text class="referencia-texto" x="{esq + area_w - 4}" y="{py(valor) + 16:.1f}" text-anchor="end">{escape(texto)}</text>'
        )

    # colunas de hover (atrás das linhas): crosshair + tooltip com todas as séries
    for i, rot in enumerate(rotulos_x):
        cabecalho = dicas_x[i] if dicas_x else rot
        corpo = "".join(
            f'<span class="tip-serie"><i style="background:{cores_series[nome]}"></i>{escape(nome)}: <b>{formato_y(vals[i])}</b></span>'
            for nome, vals in series.items()
        )
        dica = f"<strong>{escape(cabecalho)}</strong>{corpo}"
        x0 = px(i) - passo_x / 2
        partes.append(f'<g class="coluna" data-tip="{escape(dica)}">')
        partes.append(f'<rect class="hit" x="{max(x0, esq - 10):.1f}" y="{topo}" width="{passo_x:.1f}" height="{area_h}"/>')
        partes.append(f'<line class="guia" x1="{px(i):.1f}" y1="{topo}" x2="{px(i):.1f}" y2="{topo + area_h}"/>')
        partes.append("</g>")

    finais = []
    for nome, vals in series.items():
        cor = cores_series[nome]
        pontos = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(vals))
        partes.append(f'<polyline class="linha" points="{pontos}" stroke="{cor}"/>')
        for i, v in enumerate(vals):
            partes.append(f'<circle class="ponto" cx="{px(i):.1f}" cy="{py(v):.1f}" r="4" fill="{cor}"/>')
        finais.append((nome, py(vals[-1])))

    if destaque:
        i, texto = destaque
        (nome, vals), = list(series.items())[:1]
        partes.append(f'<circle class="ponto-destaque" cx="{px(i):.1f}" cy="{py(vals[i]):.1f}" r="7" stroke="{cores_series[nome]}"/>')
        partes.append(f'<text class="anotacao" x="{px(i) + 12:.1f}" y="{py(vals[i]) + 20:.1f}">{escape(texto)}</text>')

    if rotulos_diretos:
        for nome, y in _afastar_rotulos(finais).items():
            partes.append(f'<text class="rotulo-direto" x="{esq + area_w + 12}" y="{y + 4:.1f}">{escape(nome)}</text>')

    partes.append("</svg>")
    return "\n".join(partes)


def legenda(cores: dict[str, str]) -> str:
    itens = "".join(f'<span class="legenda-item"><i style="background:{c}"></i>{escape(n)}</span>' for n, c in cores.items())
    return f'<div class="legenda">{itens}</div>'
