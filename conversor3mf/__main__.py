"""Linha de comando: python -m conversor3mf <comando> ..."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import ace as modulo_ace
from . import ilhas
from .conversor import converter, planejar
from .projeto import ler_projeto
from .verificar import verificar


def _mapa(texto: str | None) -> dict[int, int]:
    """'1=3,2=1' -> {1: 3, 2: 1}"""
    if not texto:
        return {}
    mapa = {}
    for par in texto.split(","):
        origem, _, slot = par.partition("=")
        mapa[int(origem)] = int(slot)
    return mapa


def _mostrar(dados) -> None:
    print(json.dumps(dados, indent=2, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="conversor3mf", description="Converte 3MF da Bambu para a Kobra X na ordem do seu ACE.")
    sub = p.add_subparsers(dest="comando", required=True)

    s = sub.add_parser("inspecionar", help="mostra filamentos, cores e onde cada um é usado")
    s.add_argument("arquivo")

    s = sub.add_parser("planejar", help="mostra em qual slot cada cor vai sair, sem gravar nada")
    s.add_argument("arquivo")
    s.add_argument("--mapa", help="força slots, ex.: 1=3,2=1 (filamento do modelo = slot do ACE)")

    s = sub.add_parser("converter", help="grava o 3MF convertido")
    s.add_argument("arquivo")
    s.add_argument("--mapa", help="força slots, ex.: 1=3,2=1")
    s.add_argument("--saida", help="caminho do arquivo convertido (padrão: <nome>_KobraX.3mf)")
    s.add_argument("--sem-verificar", action="store_true", help="não confere no slicer depois de gravar")

    s = sub.add_parser("verificar", help="abre o arquivo no Anycubic Slicer Next e confere")
    s.add_argument("arquivo")

    s = sub.add_parser("ilhas", help="desenha o objeto com o número de cada região de mesma cor")
    s.add_argument("arquivo")
    s.add_argument("--vista", default="cima", choices=["cima", "baixo", "frente", "tras", "esquerda", "direita"])
    s.add_argument("--objeto")
    s.add_argument("--regiao", help="zoom em mm: x0,y0,x1,y1")
    s.add_argument("--png", help="onde salvar a imagem (padrão: <nome>_ilhas_<vista>.png ao lado)")

    s = sub.add_parser("repintar", help="grava um 3MF novo com ilhas em outro slot")
    s.add_argument("arquivo")
    s.add_argument("mudancas", help="ilha=slot separados por vírgula, ex.: 32=4,3=3")
    s.add_argument("--objeto")
    s.add_argument("--saida")

    s = sub.add_parser("ace", help="mostra ou altera os slots do ACE")
    acoes = s.add_subparsers(dest="acao", required=True)
    acoes.add_parser("mostrar")
    d = acoes.add_parser("definir", help="usa um projeto salvo no slicer (com o ACE sincronizado) como molde")
    d.add_argument("projeto")
    t = acoes.add_parser("slot", help="troca cor/tipo/nome de um slot")
    t.add_argument("numero", type=int)
    t.add_argument("--cor")
    t.add_argument("--tipo")
    t.add_argument("--nome")

    a = p.parse_args(argv)
    if a.comando == "inspecionar":
        _mostrar(ler_projeto(a.arquivo).resumo())
    elif a.comando == "planejar":
        _mostrar(planejar(ler_projeto(a.arquivo), modulo_ace.carregar(), _mapa(a.mapa)).resumo())
    elif a.comando == "converter":
        resultado = converter(a.arquivo, a.saida, _mapa(a.mapa))
        dados = resultado.resumo()
        if not a.sem_verificar:
            dados["verificacao"] = verificar(resultado.destino)
        _mostrar(dados)
    elif a.comando == "verificar":
        _mostrar(verificar(a.arquivo))
    elif a.comando == "ilhas":
        regiao = [float(x) for x in a.regiao.split(",")] if a.regiao else None
        png, info = ilhas.mapa_de_ilhas(a.arquivo, a.objeto, a.vista, regiao)
        destino = Path(a.png) if a.png else Path(a.arquivo).with_name(f"{Path(a.arquivo).stem}_ilhas_{a.vista}.png")
        destino.write_bytes(png)
        _mostrar({"imagem": str(destino), **info})
    elif a.comando == "repintar":
        resultado = ilhas.repintar_ilhas(a.arquivo, _mapa(a.mudancas), a.objeto, a.saida)
        resultado["verificacao"] = verificar(resultado["arquivo_repintado"])
        _mostrar(resultado)
    elif a.comando == "ace":
        if a.acao == "mostrar":
            _mostrar(modulo_ace.carregar().resumo())
        elif a.acao == "definir":
            _mostrar(modulo_ace.definir_molde(a.projeto).resumo())
        else:
            _mostrar(modulo_ace.alterar_slot(a.numero, a.cor, a.tipo, a.nome).resumo())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
