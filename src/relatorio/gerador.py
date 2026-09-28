"""Monta o relatório HTML (autocontido) a partir dos CSVs gerados e abre no navegador."""

import webbrowser
from datetime import datetime
from html import escape
from pathlib import Path

from src.parametrizacao import grupos as g
from src.relatorio import graficos as gr
from src.relatorio.metricas import ROTULOS_FAIXA, Metricas, calcular_metricas

CORES_TRIBUTO = {
    "RPPS": gr.CORES["ciano"],
    "SPSM": gr.CORES["lavanda"],
    "INSS": gr.CORES["ambar"],
    "IRRF": gr.CORES["magenta"],
}
NOMES_TRIBUTO = {"RPPS": "RPPS", "SPSM": "Proteção Social Militar", "INSS": "INSS (RGPS)", "IRRF": "IRRF"}
CORES_GRUPO_SERIE = {
    "RPPS": gr.CORES["ciano"],
    "Militares": gr.CORES["lavanda"],
    "INSS empregado": gr.CORES["ambar"],
    "Demais": gr.CORES["magenta"],
}
NOMES_GRUPO = {
    g.RPPS: "RPPS (servidores civis)",
    g.SPSM_MILITAR: "Proteção Social Militar",
    g.RGPS_EMPREGADO: "INSS – segurado empregado",
    g.RGPS_CONTRIBUINTE_INDIVIDUAL: "INSS – contribuinte individual",
    g.SEM_CONTRIBUICAO: "Sem contribuição no ente",
    g.NAO_ENQUADRADO: "Não enquadrado",
}
ROTULOS_CURTOS = {
    "5101": "RPPS · servidor ativo",
    "5102": "RPPS · aposentado/pensionista",
    "5103": "RPPS 13º · ativo",
    "5104": "RPPS 13º · aposentado/pensionista",
    "5201": "Militar · ativo",
    "5202": "Militar · reserva/reforma/pensão",
    "5203": "Militar 13º · ativo",
    "5204": "Militar 13º · reserva/reforma/pensão",
    "5301": "INSS · segurado empregado",
    "5302": "INSS 13º · segurado empregado",
    "5303": "INSS · contribuinte individual",
    "5401": "IRRF · rendimentos do mês",
    "5402": "IRRF · 13º salário",
    "5403": "IRRF · férias",
}

n = gr._num

MINUSCULAS = {"De", "Da", "Do", "Das", "Dos", "E"}


def _nome_orgao(nome: str) -> str:
    """'SECRETARIA DE ESTADO DA EDUCAÇÃO' -> 'Secretaria de Estado da Educação'."""
    return " ".join(p.lower() if i and p in MINUSCULAS else p for i, p in enumerate(nome.title().split()))


def _pct(parte: float, todo: float, casas: int = 1) -> str:
    return f"{n(parte / todo * 100 if todo else 0, casas)}%"


def _qtd(m: Metricas, codigo: str) -> int:
    linha = m.rubricas.loc[m.rubricas["CODIGO"] == codigo, "QTD"]
    return int(linha.iloc[0]) if len(linha) else 0


# ------------------------------------------------------------------ gráficos
def _grafico_rubricas(m: Metricas) -> str:
    itens = []
    for _, r in m.rubricas.sort_values("QTD", ascending=False).iterrows():
        rotulo = f'{r["CODIGO"]}  {ROTULOS_CURTOS.get(r["CODIGO"], r["DESCRICAO"][:38])}'
        dica = (
            f'<strong>{escape(r["CODIGO"])} · {escape(r["DESCRICAO"])}</strong>'
            f'<span>{n(r["QTD"])} lançamentos</span>'
            f'<span>{_pct(r["QTD"], m.total_registros)} dos registros da base</span>'
        )
        itens.append({"rotulo": rotulo, "valor": int(r["QTD"]), "categoria": r["TRIBUTO"], "dica": dica})
    cores = {NOMES_TRIBUTO[t]: c for t, c in CORES_TRIBUTO.items()}
    return gr.legenda(cores) + gr.barras_horizontais(itens, CORES_TRIBUTO, "quantidade de lançamentos")


def _grafico_faixas(m: Metricas) -> str:
    return gr.legenda(CORES_GRUPO_SERIE) + gr.linhas(
        ROTULOS_FAIXA,
        m.faixas,
        CORES_GRUPO_SERIE,
        formato_y=lambda v: f"{n(v, 0 if v == int(v) else 1)}%",
        titulo_eixo_x="faixa de provento mensal (R$)",
        titulo_eixo_y="% dos servidores do grupo",
        dicas_x=[f"Provento {r}" for r in ROTULOS_FAIXA],
    )


def _grafico_orgaos(m: Metricas) -> tuple[str, int]:
    acumulado = [round(v, 2) for v in m.orgaos["PCT_ACUMULADO"]]
    idx_80 = next(i for i, v in enumerate(acumulado) if v >= 80)
    dicas = [
        f"#{i + 1} {o} — {n(q)} registros ({n(p, 1)}%)"
        for i, (o, q, p) in enumerate(zip(m.orgaos["ORGAO"], m.orgaos["QTD"], m.orgaos["PCT"]))
    ]
    svg = gr.linhas(
        [str(i + 1) for i in range(len(acumulado))],
        {"% acumulado de registros": acumulado},
        {"% acumulado de registros": gr.CORES["ciano"]},
        formato_y=lambda v: f"{n(v, 0 if v == int(v) else 1)}%",
        titulo_eixo_x="órgãos ordenados do maior para o menor (posição no ranking)",
        titulo_eixo_y="% acumulado dos registros",
        dicas_x=dicas,
        marcar_cada=5,
        referencia=(80, "80% da base"),
        destaque=(idx_80, f"{idx_80 + 1} órgãos = {n(acumulado[idx_80], 1)}%"),
        rotulos_diretos=False,
        y_max=100,
    )
    return svg, idx_80 + 1


# ------------------------------------------------------------------ blocos de texto
def _kpis(m: Metricas) -> str:
    cartoes = [
        ("Registros analisados", n(m.total_registros), f"{m.total_orgaos} órgãos do executivo"),
        ("Lançamentos gerados", n(m.total_lancamentos), f"{n(m.total_lancamentos / m.total_registros, 2)} rubricas por registro"),
        ("Rubricas acionadas", f"{m.rubricas_distintas}/{len(m.rubricas)}", "catálogo de descontos"),
        ("Beneficiários", n(m.beneficiarios), f"{_pct(m.beneficiarios, m.total_registros)} são aposentados/pensionistas"),
        ("Isentos de IRRF", n(m.isentos_ir), "beneficiários com laudo vigente"),
    ]
    html = "".join(
        f'<div class="kpi"><span class="kpi-rotulo">{r}</span><span class="kpi-valor">{v}</span><span class="kpi-nota">{nota}</span></div>'
        for r, v, nota in cartoes
    )
    return f'<section class="kpis">{html}</section>'


def _tabela_grupos(m: Metricas) -> str:
    linhas = "".join(
        f'<tr><td>{escape(NOMES_GRUPO.get(r["GRUPO"], r["GRUPO"]))}</td><td class="num">{n(r["QTD"])}</td>'
        f'<td class="num">{n(r["PCT"], 1)}%</td><td><span class="barra-mini" style="width:{r["PCT"]:.1f}%"></span></td></tr>'
        for _, r in m.grupos.iterrows()
    )
    return (
        '<table class="tabela"><thead><tr><th>Grupo previdenciário</th><th class="num">Registros</th>'
        f'<th class="num">%</th><th>Participação</th></tr></thead><tbody>{linhas}</tbody></table>'
    )


def _tabela_rubricas(m: Metricas) -> str:
    linhas = "".join(
        f'<tr><td class="mono">{escape(r["CODIGO"])}</td><td>{escape(r["DESCRICAO"])}</td><td>{escape(r["TRIBUTO"])}</td>'
        f'<td class="num">{n(r["QTD"])}</td><td class="num">{_pct(r["QTD"], m.total_registros)}</td></tr>'
        for _, r in m.rubricas.iterrows()
    )
    return (
        '<details class="tabela-dados"><summary>Ver a tabela de dados das rubricas</summary>'
        '<table class="tabela"><thead><tr><th>Código</th><th>Descrição</th><th>Tributo</th>'
        f'<th class="num">Lançamentos</th><th class="num">% da base</th></tr></thead><tbody>{linhas}</tbody></table></details>'
    )


def _controles(m: Metricas) -> str:
    def item(ok: bool, titulo: str, detalhe: str, aviso: bool = False) -> str:
        classe, icone, status = ("ok", "✔", "OK") if ok else (("aviso", "!", "ATENÇÃO") if aviso else ("erro", "✖", "FALHA"))
        return (
            f'<li class="controle {classe}"><span class="selo"><b>{icone}</b> {status}</span>'
            f"<div><strong>{titulo}</strong><p>{detalhe}</p></div></li>"
        )

    return "<ul class='controles'>" + "".join(
        [
            item(m.multiplas_previdencias == 0, "Uma previdência por servidor",
                 f"{n(m.multiplas_previdencias)} registros receberam mais de uma rubrica previdenciária mensal."),
            item(m.nao_enquadrados == 0, "Todos os registros enquadrados",
                 f"{n(m.nao_enquadrados)} registros ficaram sem grupo previdenciário."),
            item(True, "Registros sem nenhuma rubrica",
                 f"{n(m.sem_rubrica)} registros ({_pct(m.sem_rubrica, m.total_registros, 2)}) — vínculo encerrado antes da "
                 "competência ou isentos sem contribuição (ex.: pensões especiais do Césio 137). Comportamento esperado."),
            item(not m.simulado, "Origem dos dados cadastrais",
                 "Datas de vínculo e laudos de isenção de IR não existem no CSV público e foram simulados com semente fixa. "
                 "Os volumes de IRRF e de contratos por prazo mudam com o cadastro real." if m.simulado
                 else "Datas de vínculo e laudos vieram do próprio arquivo de entrada.", aviso=True),
        ]
    ) + "</ul>"


def _narrativa(m: Metricas, orgaos_80: int) -> dict[str, str]:
    grupos = m.grupos.set_index("GRUPO")
    pct = lambda grupo: n(grupos["PCT"].get(grupo, 0), 1)
    rpps_ativo, rpps_benef = _qtd(m, "5101"), _qtd(m, "5102")
    mil_ativo, mil_benef = _qtd(m, "5201"), _qtd(m, "5202")
    irrf = _qtd(m, "5401")
    top = m.orgaos.head(2)
    med = m.faixas_medianas

    return {
        "abertura": (
            f"Em {m.competencia}, a folha do Estado de Goiás tem <b>{n(m.total_registros)}</b> registros espalhados por "
            f"<b>{m.total_orgaos}</b> órgãos. A pergunta deste relatório é a mesma do teste: <em>para cada pessoa, quais "
            f"rubricas de desconto devem ser lançadas?</em> A resposta gerou <b>{n(m.total_lancamentos)}</b> lançamentos."
        ),
        "grupos": (
            f"Seis regimes de trabalho se reduzem a cinco formas de contribuição. O <b>RPPS domina</b> com {pct(g.RPPS)}% dos "
            f"registros, seguido pelo INSS de segurados empregados ({pct(g.RGPS_EMPREGADO)}%), onde entram comissionados puros e "
            f"<b>temporários</b>, e pelos militares ({pct(g.SPSM_MILITAR)}%). Estagiários, cedidos e pensões especiais "
            f"({pct(g.SEM_CONTRIBUICAO)}%) não têm contribuição retida pelo Estado, só IRRF."
        ),
        "rubricas": (
            f"O IRRF é a única rubrica transversal: independe do regime e alcança <b>{_pct(irrf, m.total_registros)}</b> da base. "
            f"O dado que mais chama atenção está no RPPS: há <b>mais aposentados e pensionistas contribuindo ({n(rpps_benef)}) "
            f"do que servidores ativos ({n(rpps_ativo)})</b>. Nos militares a proporção é quase de 1 para 1 "
            f"({n(mil_ativo)} ativos × {n(mil_benef)} na reserva/reforma). Esse é o retrato de um regime próprio maduro, e é por isso "
            "que as rubricas de ativo e de benefício são separadas: a base de cálculo e o evento do eSocial (S-1200 × S-1207) são diferentes."
        ),
        "faixas": (
            f"As curvas mostram o perfil de renda de cada grupo. O INSS empregado se concentra nas faixas baixas "
            f"(mediana de <b>R$ {n(med['INSS empregado'])}</b>), puxado pelos contratos temporários da educação. O RPPS tem "
            f"mediana de <b>R$ {n(med['RPPS'])}</b>, e os militares ficam mais à direita (<b>R$ {n(med['Militares'])}</b>). "
            "Para a parametrização isso importa pouco (o lançamento independe do valor), mas é exatamente onde o cálculo "
            "vai trabalhar: faixas progressivas do IR e do INSS e o teto do RPPS para inativos."
        ),
        "orgaos": (
            f"A base é muito concentrada: <b>{escape(_nome_orgao(top.iloc[0]['ORGAO']))}</b> ({n(top.iloc[0]['PCT'], 1)}%) e "
            f"<b>{escape(_nome_orgao(top.iloc[1]['ORGAO']))}</b> ({n(top.iloc[1]['PCT'], 1)}%) somam "
            f"{n(top['PCT'].sum(), 1)}% dos registros, e apenas <b>{orgaos_80} órgãos</b> chegam a 80%. A GOIASPREV é quem "
            "paga as aposentadorias e pensões. Na implantação, validar as regras nesses poucos órgãos primeiro cobre "
            "quase toda a folha."
        ),
    }


# ------------------------------------------------------------------ montagem
def montar_html(m: Metricas) -> str:
    grafico_orgaos, orgaos_80 = _grafico_orgaos(m)
    texto = _narrativa(m, orgaos_80)
    gerado = datetime.now().strftime("%d/%m/%Y %H:%M")

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Relatório de Rubricas</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<main class="pagina">
  <header class="cabecalho">
    <p class="sobretitulo">// PARAMETRIZAÇÃO DE FOLHA · ESTADO DE GOIÁS · COMPETÊNCIA {escape(m.competencia)}</p>
    <h1>Relatório de <span>rubricas</span> de desconto</h1>
    <p class="lead">{texto['abertura']}</p>
  </header>

  {_kpis(m)}

  <section class="capitulo">
    <p class="capitulo-num">01 · QUEM ESTÁ NA FOLHA</p>
    <h2>Seis regimes, cinco formas de contribuição</h2>
    <p>{texto['grupos']}</p>
    {_tabela_grupos(m)}
  </section>

  <section class="capitulo">
    <p class="capitulo-num">02 · O QUE FOI LANÇADO</p>
    <h2>Lançamentos por rubrica</h2>
    <p>{texto['rubricas']}</p>
    <figure class="painel">{_grafico_rubricas(m)}</figure>
    {_tabela_rubricas(m)}
  </section>

  <section class="capitulo">
    <p class="capitulo-num">03 · PERFIL DE RENDA</p>
    <h2>Distribuição do provento mensal por grupo</h2>
    <p>{texto['faixas']}</p>
    <figure class="painel">{_grafico_faixas(m)}</figure>
  </section>

  <section class="capitulo">
    <p class="capitulo-num">04 · CONCENTRAÇÃO</p>
    <h2>Poucos órgãos respondem por quase toda a folha</h2>
    <p>{texto['orgaos']}</p>
    <figure class="painel">{grafico_orgaos}</figure>
  </section>

  <section class="capitulo">
    <p class="capitulo-num">05 · CONTROLES</p>
    <h2>Verificações de consistência</h2>
    {_controles(m)}
  </section>

  <footer class="rodape">
    Gerado em {gerado} por <code>python -m src.main</code> a partir dos arquivos de <code>data/output/</code>.
    Regras de negócio em <code>docs/regras_negocio.md</code>.
  </footer>
</main>
<div id="tip" role="tooltip"></div>
<script>{JS}</script>
</body>
</html>"""


def gerar_relatorio(arquivos: dict[str, Path], diretorio: str | Path) -> Path:
    m = calcular_metricas(arquivos)
    diretorio = Path(diretorio)
    diretorio.mkdir(parents=True, exist_ok=True)
    sufixo = m.competencia.replace("/", "")
    sufixo = sufixo[2:] + sufixo[:2] if len(sufixo) == 6 else sufixo  # MMAAAA -> AAAAMM
    destino = diretorio / f"relatorio_rubricas_{sufixo}.html"
    destino.write_text(montar_html(m), encoding="utf-8")
    return destino


def abrir_no_navegador(caminho: Path) -> bool:
    return webbrowser.open(Path(caminho).resolve().as_uri())


CSS = """
:root{
  color-scheme: dark;
  --fundo:#13111f; --painel:#1c1930; --painel-2:#221e3a; --borda:#2e2a48;
  --texto:#ece9ff; --texto-2:#b3adcf; --texto-3:#8a84a8; --grade:#2a2641;
  --ciano:#19a3ad; --lavanda:#8a78ec; --ambar:#b8801a; --magenta:#d65a9c;
  --ok:#0ca30c; --aviso:#fab219; --erro:#d03b3b;
}
*{box-sizing:border-box}
html,body{margin:0}
body{
  background:
    radial-gradient(1200px 600px at 100% -10%, rgba(214,90,156,.10), transparent 60%),
    radial-gradient(900px 500px at -10% 10%, rgba(25,163,173,.10), transparent 60%),
    linear-gradient(rgba(138,120,236,.035) 1px, transparent 1px) 0 0/100% 32px,
    var(--fundo);
  color:var(--texto); font:15px/1.65 Inter, "Segoe UI", system-ui, sans-serif;
}
.pagina{max-width:1100px; margin:0 auto; padding:48px 16px 64px}
.sobretitulo,.capitulo-num{font:600 12px/1.4 "JetBrains Mono", Consolas, monospace; letter-spacing:.14em; color:var(--ciano); margin:0 0 10px}
h1,h2{font-family:Orbitron, "Segoe UI", sans-serif; font-weight:700; letter-spacing:.02em; margin:0 0 14px}
h1{font-size:clamp(28px,4.4vw,44px); line-height:1.15}
h1 span{color:var(--magenta); text-shadow:0 0 18px rgba(214,90,156,.35)}
h2{font-size:clamp(19px,2.4vw,24px); font-weight:500}
.lead{font-size:17px; color:var(--texto-2); max-width:820px}
.lead b,.capitulo p b{color:var(--texto)}
.cabecalho{padding-bottom:28px; border-bottom:1px solid var(--borda); margin-bottom:28px}
.kpis{display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:14px; margin-bottom:12px}
.kpi{background:var(--painel); border:1px solid var(--borda); border-radius:12px; padding:16px 18px; display:flex; flex-direction:column; gap:4px;
     box-shadow:inset 0 1px 0 rgba(255,255,255,.03), 0 0 0 1px rgba(25,163,173,.04)}
.kpi-rotulo{font:600 11px "JetBrains Mono", monospace; letter-spacing:.1em; text-transform:uppercase; color:var(--texto-3)}
.kpi-valor{font:700 28px/1.2 Orbitron, "Segoe UI", sans-serif; color:var(--texto)}
.kpi-nota{font-size:13px; color:var(--texto-2)}
.capitulo{margin-top:48px}
.capitulo > p{color:var(--texto-2); max-width:860px}
.painel{margin:20px 0 0; background:var(--painel); border:1px solid var(--borda); border-radius:14px; padding:18px 18px 8px;
        box-shadow:0 0 40px rgba(138,120,236,.06)}
.grafico{width:100%; height:auto; display:block; overflow:visible}
.grafico text{font-family:Inter, "Segoe UI", sans-serif}
.grade{stroke:var(--grade); stroke-width:1}
.eixo-linha{stroke:#3a3558; stroke-width:1}
.eixo{fill:var(--texto-3); font-size:12px}
.eixo-titulo{fill:var(--texto-3); font-size:12px; letter-spacing:.04em}
.rotulo{fill:var(--texto-2); font-size:13px}
.valor{fill:var(--texto); font:600 12px "JetBrains Mono", monospace}
.rotulo-direto{fill:var(--texto); font-size:13px; font-weight:500}
.anotacao{fill:var(--texto); font:600 13px "JetBrains Mono", monospace}
.referencia{stroke:var(--texto-3); stroke-width:1}
.referencia-texto{fill:var(--texto-3); font-size:12px}
.linha{fill:none; stroke-width:2; stroke-linejoin:round; stroke-linecap:round; pointer-events:none}
.ponto{stroke:var(--painel); stroke-width:2; pointer-events:none}
.ponto-destaque{fill:none; stroke-width:2; pointer-events:none}
.hit{fill:transparent}
.guia{stroke:var(--texto-3); stroke-width:1; opacity:0}
.coluna:hover .guia{opacity:.8}
.alvo .barra{transition:opacity .15s}
.grafico:has(.alvo:hover) .alvo:not(:hover) .barra{opacity:.45}
.alvo:hover .hit{fill:rgba(138,120,236,.07)}
.legenda{display:flex; flex-wrap:wrap; gap:8px 18px; margin:0 0 10px; font-size:13px; color:var(--texto-2)}
.legenda-item{display:inline-flex; align-items:center; gap:8px}
.legenda-item i,.tip-serie i{width:12px; height:12px; border-radius:3px; display:inline-block}
.tabela{width:100%; border-collapse:collapse; margin-top:18px; font-size:14px}
.tabela th{font:600 11px "JetBrains Mono", monospace; letter-spacing:.08em; text-transform:uppercase; color:var(--texto-3); text-align:left; padding:8px 10px; border-bottom:1px solid var(--borda)}
.tabela td{padding:9px 10px; border-bottom:1px solid var(--grade); color:var(--texto-2)}
.tabela td:first-child{color:var(--texto)}
.num{text-align:right; font-family:"JetBrains Mono", monospace}
.mono{font-family:"JetBrains Mono", monospace}
.barra-mini{display:block; height:8px; border-radius:0 4px 4px 0; background:var(--ciano); min-width:2px}
.tabela-dados{margin-top:14px}
.tabela-dados summary{cursor:pointer; color:var(--ciano); font-size:14px}
.controles{list-style:none; padding:0; margin:18px 0 0; display:grid; gap:12px}
.controle{display:flex; gap:16px; align-items:flex-start; background:var(--painel); border:1px solid var(--borda); border-radius:12px; padding:14px 16px}
.controle p{margin:2px 0 0; color:var(--texto-2); font-size:14px}
.selo{flex:none; font:600 11px "JetBrains Mono", monospace; letter-spacing:.08em; padding:4px 10px; border-radius:999px; border:1px solid; white-space:nowrap}
.ok .selo{color:var(--ok); border-color:rgba(12,163,12,.45)}
.aviso .selo{color:var(--aviso); border-color:rgba(250,178,25,.45)}
.erro .selo{color:var(--erro); border-color:rgba(208,59,59,.5)}
.rodape{margin-top:56px; padding-top:20px; border-top:1px solid var(--borda); color:var(--texto-3); font-size:13px}
code{font-family:"JetBrains Mono", monospace; color:var(--texto-2)}
#tip{position:fixed; pointer-events:none; z-index:10; max-width:340px; background:rgba(28,25,48,.97); border:1px solid #3a3558;
     border-radius:10px; padding:10px 12px; font-size:13px; line-height:1.5; color:var(--texto-2); opacity:0; transition:opacity .12s;
     box-shadow:0 8px 30px rgba(0,0,0,.4), 0 0 18px rgba(25,163,173,.12)}
#tip strong{display:block; color:var(--texto); margin-bottom:4px}
#tip span{display:flex; align-items:center; gap:8px}
#tip b{color:var(--texto); font-family:"JetBrains Mono", monospace}
@media (max-width:640px){ .pagina{padding-top:28px} .controle{flex-direction:column; gap:8px} .painel{padding:12px 8px 4px} }
"""

JS = """
(() => {
  const tip = document.getElementById('tip');
  const esconder = () => { tip.style.opacity = 0; };
  document.addEventListener('pointermove', (e) => {
    const alvo = e.target.closest('[data-tip]');
    if (!alvo) return esconder();
    tip.innerHTML = alvo.dataset.tip;
    const r = tip.getBoundingClientRect();
    let x = e.clientX + 16, y = e.clientY + 16;
    if (x + r.width > innerWidth - 8) x = e.clientX - r.width - 16;
    if (y + r.height > innerHeight - 8) y = e.clientY - r.height - 16;
    tip.style.left = Math.max(8, x) + 'px';
    tip.style.top = Math.max(8, y) + 'px';
    tip.style.opacity = 1;
  });
  document.addEventListener('pointerleave', esconder);
})();
"""
