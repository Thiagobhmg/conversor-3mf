"""Linha de comando: conversor3mf <comando> ...

Comandos e opções funcionam em português, inglês e espanhol (converter / convert /
convertir); a ajuda aparece no idioma do sistema ou no pedido em --idioma.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import ace as modulo_ace
from . import ilhas, purga
from .conversor import converter, planejar
from .idiomas import VISTAS, detectar, nomes, texto, traduzir_argparse, vista_interna
from .projeto import ler_projeto
from .verificar import verificar


def _mapa(texto_mapa: str | None) -> dict[int, int]:
    """'1=3,2=1' -> {1: 3, 2: 1}"""
    if not texto_mapa:
        return {}
    mapa = {}
    for par in texto_mapa.split(","):
        origem, _, slot = par.partition("=")
        mapa[int(origem)] = int(slot)
    return mapa


def _mostrar(dados) -> None:
    print(json.dumps(dados, indent=2, ensure_ascii=False))


def montar_parser(idioma: str) -> argparse.ArgumentParser:
    t = lambda chave, **v: texto(chave, idioma, **v)  # noqa: E731
    traduzir_argparse(idioma)

    p = argparse.ArgumentParser(prog="conversor3mf", description=t("descricao"), epilog=t("rodape"))
    p.add_argument(*nomes("--idioma", idioma), dest="idioma", choices=["pt", "en", "es"], help=t("idioma"))
    sub = p.add_subparsers(title=t("comandos"), metavar="", required=True)

    def comando(pai, chave: str, campo: str = "comando", ajuda: str | None = None):
        principal, *apelidos = nomes(chave, idioma)
        s = pai.add_parser(principal, aliases=apelidos, help=t(ajuda or chave), description=t(ajuda or chave))
        s.set_defaults(**{campo: chave})
        return s

    def opcao(s, chave: str, **kw):
        s.add_argument(*nomes(chave, idioma), dest=chave.lstrip("-").replace("-", "_"), **kw)

    def arquivo(s):
        s.add_argument("arquivo", metavar=t("arquivo"), help=t("ajuda_arquivo"))

    def vista(valor: str) -> str:
        interna = vista_interna(valor)
        if interna is None:
            opcoes = ", ".join(v[idioma] for v in VISTAS.values())
            raise argparse.ArgumentTypeError(t("vista_invalida", valor=valor, opcoes=opcoes))
        return interna

    s = comando(sub, "inspecionar")
    arquivo(s)

    s = comando(sub, "planejar")
    arquivo(s)
    opcao(s, "--mapa", metavar=t("valor_mapa"), help=t("ajuda_mapa"))

    s = comando(sub, "converter")
    arquivo(s)
    opcao(s, "--mapa", metavar=t("valor_mapa"), help=t("ajuda_mapa"))
    opcao(s, "--saida", metavar=t("caminho"), help=t("ajuda_saida"))
    opcao(s, "--sem-verificar", action="store_true", help=t("ajuda_sem_verificar"))

    s = comando(sub, "verificar")
    arquivo(s)

    s = comando(sub, "ilhas")
    arquivo(s)
    opcao(s, "--vista", type=vista, default="cima",
          metavar="{" + ",".join(v[idioma] for v in VISTAS.values()) + "}", help=t("ajuda_vista"))
    opcao(s, "--objeto", metavar=t("id"), help=t("ajuda_objeto"))
    opcao(s, "--regiao", metavar="X0,Y0,X1,Y1", help=t("ajuda_regiao"))
    opcao(s, "--png", metavar=t("caminho"), help=t("ajuda_png"))

    s = comando(sub, "repintar")
    arquivo(s)
    s.add_argument("mudancas", metavar=t("mudancas"), help=t("ajuda_mudancas"))
    opcao(s, "--objeto", metavar=t("id"), help=t("ajuda_objeto"))
    opcao(s, "--saida", metavar=t("caminho"), help=t("ajuda_saida"))

    s = comando(sub, "ace")
    acoes = s.add_subparsers(metavar="", required=True)
    comando(acoes, "mostrar", "acao")
    a = comando(acoes, "definir", "acao")
    a.add_argument("projeto", metavar=t("projeto"), help=t("ajuda_projeto"))
    a = comando(acoes, "slot", "acao")
    a.add_argument("numero", type=int, metavar=t("numero"), help=t("ajuda_numero"))
    opcao(a, "--cor", metavar=t("valor_cor"), help=t("ajuda_cor"))
    opcao(a, "--tipo", metavar=t("valor_tipo"), help=t("ajuda_tipo"))
    opcao(a, "--nome", metavar=t("valor_nome"), help=t("ajuda_nome"))

    s = comando(sub, "purga")
    acoes = s.add_subparsers(metavar="", required=True)
    comando(acoes, "mostrar", "acao", ajuda="mostrar_purga")
    a = comando(acoes, "ajustar", "acao")
    a.add_argument("de", metavar=t("de"), help=t("ajuda_de"))
    a.add_argument("para", metavar=t("para"), help=t("ajuda_para"))
    a.add_argument("mudanca", metavar=t("mudanca"), help=t("ajuda_mudanca"))
    a = comando(acoes, "nivel", "acao")
    a.add_argument("valor", metavar=t("valor_nivel"), help=t("nivel"))
    a = comando(acoes, "aprender", "acao")
    a.add_argument("pastas", nargs="+", metavar=t("pastas"), help=t("ajuda_pastas"))
    a = comando(acoes, "aplicar", "acao")
    arquivo(a)
    opcao(a, "--saida", metavar=t("caminho"), help=t("ajuda_saida"))
    return p


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")  # mensagens de erro do argparse
    a = montar_parser(detectar(argv)).parse_args(argv)
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
    elif a.comando == "purga":
        cores_ace = [s.cor for s in modulo_ace.carregar().slots] if a.acao in ("mostrar", "ajustar") else []
        if a.acao == "mostrar":
            _mostrar(purga.relatorio(cores_ace))
        elif a.acao == "ajustar":
            _mostrar(purga.ajustar_par(a.de, a.para, a.mudanca, cores_ace))
        elif a.acao == "nivel":
            _mostrar({"fator_geral": purga.definir_nivel(a.valor)})
        elif a.acao == "aprender":
            _mostrar({"pares_aprendidos": purga.aprender(a.pastas)})
        else:
            _mostrar(purga.aplicar_em_arquivo(a.arquivo, a.saida))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
