from src import config
from src.processamento.folha import exportar, processar_arquivo
from src.relatorio import gerar_relatorio


def test_relatorio_html_e_gerado_a_partir_dos_arquivos(tmp_path):
    resultado = processar_arquivo(config.ARQUIVO_AMOSTRA, semente=42)
    arquivos = exportar(resultado, tmp_path / "output")

    caminho = gerar_relatorio(arquivos, tmp_path / "relatorios")

    assert caminho.exists() and caminho.name == "relatorio_rubricas_202607.html"
    html = caminho.read_text(encoding="utf-8")
    assert html.count('<svg class="grafico"') == 3          # 1 barras + 2 linhas
    assert html.count('<polyline class="linha"') == 5       # 4 grupos + curva acumulada
    assert html.count('<path class="barra"') == 14          # uma barra por rubrica
    assert "Verificações de consistência" in html
    assert "<script" in html and "http" not in html.split("<script>")[1]  # JS inline, sem dependência externa
