"""Servidor MCP: deixa o Claude inspecionar, planejar e converter 3MF para a Kobra X."""

from __future__ import annotations

import json
from pathlib import Path

from mcp.server.mcpserver import Image, MCPServer

from . import ace as modulo_ace
from . import ilhas, purga
from .conversor import converter, planejar
from .projeto import ler_projeto
from .verificar import verificar

mcp = MCPServer(
    "conversor-3mf-kobra-x",
    instructions=(
        "Converte projetos 3MF feitos para impressoras Bambu Lab (MakerWorld) para a Anycubic Kobra X "
        "com ACE, colocando cada cor do modelo no slot do ACE onde aquele carretel está. "
        "Fluxo: ver_ace para saber os carretéis carregados; planejar_conversao para mostrar ao usuário "
        "em qual slot cada cor vai sair; se alguma cor ficar 'ruim', pergunte se ele quer trocar o carretel "
        "(alterar_slot) ou forçar outro slot (mapa); só então converter_3mf. Converter nunca sobrescreve "
        "o original. "
        "Para recolorir partes de um modelo (ex.: 'folhas em verde'), use mapa_de_ilhas: ele devolve uma "
        "imagem com o número de cada região contínua de mesma cor (ilha). Olhe a imagem, escolha os números "
        "(use regiao para dar zoom se estiverem amontoados, e outra vista se a parte não aparecer de cima), "
        "confira tamanho/altura na lista e chame repintar_ilhas. Mostre a prévia ao usuário. "
        "Purga (filamento descartado em cada troca de cor): se o usuário disser que uma cor manchou "
        "depois de outra (ex.: 'o branco saiu acinzentado depois do preto'), chame ajustar_purga com "
        "de=cor anterior, para=cor que manchou, mudanca='mais', e depois aplicar_purga no arquivo. "
        "Se ele quiser economizar filamento, use nivel_purga('economia') ou ajuste pares com 'menos'. "
        "A conversão já usa a calibração salva. "
        "Na primeira vez, se ver_ace disser que não há molde, peça ao usuário para sincronizar o ACE no "
        "Anycubic Slicer Next, salvar um projeto e informar o caminho para definir_molde_ace. "
        "Responda no idioma do usuário."
    ),
)


def _mapa(mapa: dict[str, int] | None) -> dict[int, int]:
    return {int(k): int(v) for k, v in (mapa or {}).items()}


@mcp.tool()
def ver_ace() -> dict:
    """Mostra os slots do ACE (cor, tipo e nome de cada carretel) e de qual projeto o molde foi tirado."""
    return modulo_ace.carregar().resumo()


@mcp.tool()
def definir_molde_ace(projeto_3mf: str) -> dict:
    """Usa um projeto salvo pelo Anycubic Slicer Next, com o ACE sincronizado, como molde.

    Isso define impressora, perfis de filamento e a ordem real dos carretéis. Use quando o
    usuário trocar o tipo de material de algum slot ou na primeira configuração.
    """
    return modulo_ace.definir_molde(projeto_3mf).resumo()


@mcp.tool()
def alterar_slot_ace(slot: int, cor: str | None = None, tipo: str | None = None, nome: str | None = None) -> dict:
    """Atualiza um slot do ACE depois que o usuário troca o carretel.

    cor em hexadecimal (#RRGGBB); tipo precisa existir em algum slot do molde (ex.: PLA, PETG).
    """
    return modulo_ace.alterar_slot(slot, cor, tipo, nome).resumo()


@mcp.tool()
def listar_3mf(pasta: str) -> list[dict]:
    """Lista os arquivos .3mf de uma pasta com tamanho e data, do mais novo para o mais antigo."""
    arquivos = sorted(Path(pasta).glob("*.3mf"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [{"arquivo": str(p), "tamanho_mb": round(p.stat().st_size / 1e6, 1)} for p in arquivos]


@mcp.tool()
def inspecionar_3mf(arquivo: str) -> dict:
    """Mostra impressora original, placas e cada filamento do projeto: cor, tipo e onde é usado."""
    return ler_projeto(arquivo).resumo()


@mcp.tool()
def planejar_conversao(arquivo: str, mapa: dict[str, int] | None = None) -> dict:
    """Mostra em qual slot do ACE cada cor do modelo vai sair, sem gravar nada.

    mapa força slots: {"numero do filamento no modelo": slot do ACE}, ex.: {"1": 3, "2": 1}.
    Filamentos fora do mapa são escolhidos automaticamente pela cor mais parecida.
    """
    return planejar(ler_projeto(arquivo), modulo_ace.carregar(), _mapa(mapa)).resumo()


@mcp.tool()
def converter_3mf(arquivo: str, mapa: dict[str, int] | None = None, saida: str | None = None) -> dict:
    """Grava o projeto convertido para a Kobra X (padrão: <nome>_KobraX.3mf ao lado do original) e confere no slicer.

    mapa funciona como em planejar_conversao. Nunca sobrescreve arquivos existentes.
    """
    resultado = converter(arquivo, saida, _mapa(mapa))
    dados = resultado.resumo()
    dados["verificacao"] = verificar(resultado.destino)
    return dados


@mcp.tool()
def mapa_de_ilhas(
    arquivo: str,
    vista: str = "cima",
    objeto: str | None = None,
    regiao: list[float] | None = None,
    numeros: bool = True,
) -> list[Image | str]:
    """Desenha o objeto com as cores reais e o número de cada ilha (região contínua de mesma cor).

    vista: cima, baixo, frente, tras, esquerda ou direita (também em inglês: top, bottom,
    front, back, left, right; ou espanhol: arriba, abajo, frente, atras, izquierda, derecha).
    objeto: id do objeto (padrão: o maior; a resposta lista os outros).
    regiao: zoom [x0, y0, x1, y1] em mm nas coordenadas da vista (as mesmas de centro_mm na
    vista de cima: x e y; nas vistas laterais o eixo vertical é z).
    numeros=False desenha só a prévia, sem números.
    Devolve a imagem e a lista das ilhas rotuladas (slot, cor, tamanho, centro, altura do topo).
    """
    png, info = ilhas.mapa_de_ilhas(arquivo, objeto, vista, regiao, rotulos=numeros)
    return [Image(data=png, format="png"), json.dumps(info, ensure_ascii=False)]


@mcp.tool()
def repintar_ilhas(
    arquivo: str,
    mudancas: dict[str, int],
    objeto: str | None = None,
    saida: str | None = None,
) -> list[Image | str]:
    """Grava um 3MF novo com as ilhas escolhidas em outro slot e devolve uma prévia.

    mudancas: {"número da ilha": slot}, ex.: {"32": 4, "3": 3}. Use os números de mapa_de_ilhas
    do mesmo arquivo e objeto. Ilha inteira muda (topo e laterais); em triângulos com várias
    cores só a parte da cor da ilha muda. Padrão de saída: <nome>_repintado.3mf; nunca sobrescreve.
    """
    resultado = ilhas.repintar_ilhas(arquivo, {int(k): v for k, v in mudancas.items()}, objeto, saida)
    resultado["verificacao"] = verificar(resultado["arquivo_repintado"])
    png, _ = ilhas.mapa_de_ilhas(resultado["arquivo_repintado"], resultado["objeto"], "cima", rotulos=False)
    return [Image(data=png, format="png"), json.dumps(resultado, ensure_ascii=False)]


def _cores_ace() -> list[str]:
    return [s.cor for s in modulo_ace.carregar().slots]


@mcp.tool()
def ver_purga() -> dict:
    """Mostra quanto filamento cada troca de cor do ACE purga (mm³ e gramas) e os ajustes salvos."""
    return purga.relatorio(_cores_ace())


@mcp.tool()
def ajustar_purga(de: str, para: str, mudanca: str = "mais") -> dict:
    """Calibra a purga de uma troca de cor e guarda para as próximas conversões.

    de/para: número do slot do ACE ("2") ou cor (#RRGGBB). de = cor que estava no bico,
    para = cor que entra (a que saiu manchada). mudanca: "mais" (+20%), "menos" (-20%) ou
    um fator (ex.: "1.5"). Para valer num arquivo já convertido, chame aplicar_purga depois.
    """
    resultado = purga.ajustar_par(de, para, mudanca, _cores_ace())
    return resultado | {"tabela": purga.relatorio(_cores_ace())["trocas"]}


@mcp.tool()
def nivel_purga(nivel: str) -> dict:
    """Fator geral de purga: economia (0,85), normal (1,0), caprichado (1,25) ou um número."""
    return {"fator_geral": purga.definir_nivel(nivel)}


@mcp.tool()
def aprender_purga(pastas_ou_arquivos: list[str]) -> dict:
    """Aprende a purga que o Anycubic Slicer Next calculou em projetos salvos por ele (pastas ou .3mf)."""
    return {"pares_aprendidos": purga.aprender(pastas_ou_arquivos)}


@mcp.tool()
def aplicar_purga(arquivo: str, saida: str | None = None) -> dict:
    """Grava uma cópia do projeto (<nome>_purga.3mf) com a tabela de purga recalculada para as
    cores dele, usando a calibração salva. Nunca sobrescreve."""
    return purga.aplicar_em_arquivo(arquivo, saida)


@mcp.tool()
def verificar_3mf(arquivo: str) -> dict:
    """Abre o arquivo no Anycubic Slicer Next pela linha de comando e confere impressora, cores e pintura."""
    return verificar(arquivo)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
