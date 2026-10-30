"""Nomes de comandos, opções e textos de ajuda em português, inglês e espanhol.

Todos os nomes funcionam em qualquer idioma; o idioma só decide qual nome aparece
primeiro na ajuda e em que língua os textos de ajuda são mostrados.
"""

from __future__ import annotations

import locale
import os
import sys

__all__ = ["IDIOMAS", "detectar", "nomes", "texto", "VISTAS"]

IDIOMAS = ("pt", "en", "es")

# comando/opção interno -> nome em cada idioma
NOMES = {
    # comandos
    "inspecionar": {"pt": "inspecionar", "en": "inspect", "es": "inspeccionar"},
    "planejar": {"pt": "planejar", "en": "plan", "es": "planificar"},
    "converter": {"pt": "converter", "en": "convert", "es": "convertir"},
    "verificar": {"pt": "verificar", "en": "verify", "es": "verificar"},
    "ilhas": {"pt": "ilhas", "en": "islands", "es": "islas"},
    "repintar": {"pt": "repintar", "en": "repaint", "es": "repintar"},
    "ace": {"pt": "ace", "en": "ace", "es": "ace"},
    "mostrar": {"pt": "mostrar", "en": "show", "es": "mostrar"},
    "definir": {"pt": "definir", "en": "setup", "es": "configurar"},
    "slot": {"pt": "slot", "en": "slot", "es": "ranura"},
    # opções
    "--mapa": {"pt": "--mapa", "en": "--map", "es": "--mapa"},
    "--saida": {"pt": "--saida", "en": "--output", "es": "--salida"},
    "--sem-verificar": {"pt": "--sem-verificar", "en": "--no-verify", "es": "--sin-verificar"},
    "--vista": {"pt": "--vista", "en": "--view", "es": "--vista"},
    "--objeto": {"pt": "--objeto", "en": "--object", "es": "--objeto"},
    "--regiao": {"pt": "--regiao", "en": "--region", "es": "--region"},
    "--png": {"pt": "--png", "en": "--png", "es": "--png"},
    "--cor": {"pt": "--cor", "en": "--color", "es": "--color"},
    "--tipo": {"pt": "--tipo", "en": "--type", "es": "--tipo"},
    "--nome": {"pt": "--nome", "en": "--name", "es": "--nombre"},
    "--idioma": {"pt": "--idioma", "en": "--language", "es": "--idioma"},
}

# vistas do mapa de ilhas: nome em cada idioma -> nome interno
VISTAS = {
    "cima": {"pt": "cima", "en": "top", "es": "arriba"},
    "baixo": {"pt": "baixo", "en": "bottom", "es": "abajo"},
    "frente": {"pt": "frente", "en": "front", "es": "frente"},
    "tras": {"pt": "tras", "en": "back", "es": "atras"},
    "esquerda": {"pt": "esquerda", "en": "left", "es": "izquierda"},
    "direita": {"pt": "direita", "en": "right", "es": "derecha"},
}

TEXTOS = {
    "descricao": {
        "pt": "Converte 3MF da Bambu/MakerWorld para a Anycubic Kobra X na ordem dos slots do seu ACE.",
        "en": "Convert Bambu/MakerWorld 3MF files to the Anycubic Kobra X in your ACE slot order.",
        "es": "Convierte archivos 3MF de Bambu/MakerWorld para la Anycubic Kobra X en el orden de las ranuras de tu ACE.",
    },
    "rodape": {
        "pt": "Os comandos também funcionam em inglês e espanhol (ex.: convert, convertir).",
        "en": "Commands also work in Portuguese and Spanish (e.g. converter, convertir).",
        "es": "Los comandos también funcionan en portugués e inglés (ej.: converter, convert).",
    },
    "comandos": {"pt": "comandos", "en": "commands", "es": "comandos"},
    "idioma": {
        "pt": "idioma da ajuda: pt, en ou es (padrão: o do sistema)",
        "en": "help language: pt, en or es (default: system language)",
        "es": "idioma de la ayuda: pt, en o es (por defecto: el del sistema)",
    },
    "inspecionar": {
        "pt": "mostra filamentos, cores e onde cada um é usado",
        "en": "show filaments, colors and where each one is used",
        "es": "muestra filamentos, colores y dónde se usa cada uno",
    },
    "planejar": {
        "pt": "mostra em qual slot cada cor vai sair, sem gravar nada",
        "en": "show which ACE slot each color goes to, without writing anything",
        "es": "muestra en qué ranura del ACE saldrá cada color, sin guardar nada",
    },
    "converter": {
        "pt": "grava o 3MF convertido (<nome>_KobraX.3mf)",
        "en": "write the converted 3MF (<name>_KobraX.3mf)",
        "es": "guarda el 3MF convertido (<nombre>_KobraX.3mf)",
    },
    "verificar": {
        "pt": "abre o arquivo no Anycubic Slicer Next e confere",
        "en": "reopen the file in Anycubic Slicer Next and check it",
        "es": "abre el archivo en Anycubic Slicer Next y lo comprueba",
    },
    "ilhas": {
        "pt": "desenha o objeto com o número de cada região de mesma cor",
        "en": "draw the object with a number on each same-color region",
        "es": "dibuja el objeto con el número de cada región del mismo color",
    },
    "repintar": {
        "pt": "grava um 3MF novo com ilhas em outro slot",
        "en": "write a new 3MF with islands moved to another slot",
        "es": "guarda un 3MF nuevo con islas en otra ranura",
    },
    "ace": {
        "pt": "mostra ou altera os slots do ACE",
        "en": "show or change your ACE slots",
        "es": "muestra o cambia las ranuras del ACE",
    },
    "mostrar": {"pt": "mostra os slots", "en": "show the slots", "es": "muestra las ranuras"},
    "definir": {
        "pt": "usa um projeto salvo no slicer (com o ACE sincronizado) como molde",
        "en": "use a project saved in the slicer (with the ACE synced) as the template",
        "es": "usa un proyecto guardado en el slicer (con el ACE sincronizado) como plantilla",
    },
    "slot": {
        "pt": "troca cor, tipo ou nome de um slot",
        "en": "change a slot's color, type or name",
        "es": "cambia el color, tipo o nombre de una ranura",
    },
    "arquivo": {"pt": "arquivo", "en": "file", "es": "archivo"},
    "projeto": {"pt": "projeto", "en": "project", "es": "proyecto"},
    "numero": {"pt": "numero", "en": "number", "es": "numero"},
    "mudancas": {"pt": "mudancas", "en": "changes", "es": "cambios"},
    "ajuda_arquivo": {
        "pt": "arquivo .3mf",
        "en": ".3mf file",
        "es": "archivo .3mf",
    },
    "ajuda_projeto": {
        "pt": "projeto .3mf salvo no Anycubic Slicer Next",
        "en": ".3mf project saved in Anycubic Slicer Next",
        "es": "proyecto .3mf guardado en Anycubic Slicer Next",
    },
    "ajuda_numero": {"pt": "número do slot", "en": "slot number", "es": "número de ranura"},
    "ajuda_mudancas": {
        "pt": "ilha=slot separados por vírgula, ex.: 32=4,3=3",
        "en": "island=slot, comma separated, e.g. 32=4,3=3",
        "es": "isla=ranura separados por comas, ej.: 32=4,3=3",
    },
    "ajuda_mapa": {
        "pt": "força slots: filamento do modelo=slot do ACE, ex.: 1=3,2=1",
        "en": "force slots: model filament=ACE slot, e.g. 1=3,2=1",
        "es": "fuerza ranuras: filamento del modelo=ranura del ACE, ej.: 1=3,2=1",
    },
    "ajuda_saida": {
        "pt": "caminho do arquivo gravado",
        "en": "path of the file to write",
        "es": "ruta del archivo a guardar",
    },
    "ajuda_sem_verificar": {
        "pt": "não confere no slicer depois de gravar",
        "en": "don't check the file in the slicer after writing",
        "es": "no comprobar en el slicer después de guardar",
    },
    "ajuda_vista": {"pt": "vista", "en": "view", "es": "vista"},
    "id": {"pt": "ID", "en": "ID", "es": "ID"},
    "caminho": {"pt": "CAMINHO", "en": "PATH", "es": "RUTA"},
    "valor_cor": {"pt": "#RRGGBB", "en": "#RRGGBB", "es": "#RRGGBB"},
    "valor_tipo": {"pt": "MATERIAL", "en": "MATERIAL", "es": "MATERIAL"},
    "valor_nome": {"pt": "NOME", "en": "NAME", "es": "NOMBRE"},
    "valor_mapa": {"pt": "FIL=SLOT,...", "en": "FIL=SLOT,...", "es": "FIL=RANURA,..."},
    "ajuda_objeto": {
        "pt": "id do objeto (padrão: o maior)",
        "en": "object id (default: the largest)",
        "es": "id del objeto (por defecto: el más grande)",
    },
    "ajuda_regiao": {
        "pt": "zoom em mm: x0,y0,x1,y1",
        "en": "zoom in mm: x0,y0,x1,y1",
        "es": "zoom en mm: x0,y0,x1,y1",
    },
    "ajuda_png": {
        "pt": "onde salvar a imagem (padrão: ao lado do arquivo)",
        "en": "where to save the image (default: next to the file)",
        "es": "dónde guardar la imagen (por defecto: junto al archivo)",
    },
    "ajuda_cor": {"pt": "cor, ex.: #FFD700", "en": "color, e.g. #FFD700", "es": "color, ej.: #FFD700"},
    "ajuda_tipo": {"pt": "material, ex.: PLA", "en": "material, e.g. PLA", "es": "material, ej.: PLA"},
    "ajuda_nome": {"pt": "nome do slot", "en": "slot name", "es": "nombre de la ranura"},
    "vista_invalida": {
        "pt": "vista inválida: {valor} (use {opcoes})",
        "en": "invalid view: {valor} (use {opcoes})",
        "es": "vista no válida: {valor} (usa {opcoes})",
    },
}


# textos do próprio argparse (o Python não traz traduções)
ARGPARSE = {
    "usage: ": {"pt": "uso: ", "es": "uso: "},
    "options": {"pt": "opções", "es": "opciones"},
    "positional arguments": {"pt": "argumentos", "es": "argumentos"},
    "show this help message and exit": {"pt": "mostra esta ajuda e sai", "es": "muestra esta ayuda y sale"},
    "the following arguments are required: %s": {
        "pt": "faltam os argumentos: %s", "es": "faltan los argumentos: %s"},
    "unrecognized arguments: %s": {"pt": "argumentos desconhecidos: %s", "es": "argumentos desconocidos: %s"},
    "expected one argument": {"pt": "esperava um valor", "es": "se esperaba un valor"},
    "%(prog)s: error: %(message)s\n": {"pt": "%(prog)s: erro: %(message)s\n", "es": "%(prog)s: error: %(message)s\n"},
    "invalid choice: %(value)r (choose from %(choices)s)": {
        "pt": "opção inválida: %(value)r (escolha entre %(choices)s)",
        "es": "opción no válida: %(value)r (elige entre %(choices)s)"},
    "argument %(argument_name)s: %(message)s": {
        "pt": "argumento %(argument_name)s: %(message)s", "es": "argumento %(argument_name)s: %(message)s"},
    "invalid %(type)s value: %(value)r": {
        "pt": "valor inválido: %(value)r", "es": "valor no válido: %(value)r"},
}


def traduzir_argparse(idioma: str) -> None:
    import argparse

    def _(mensagem: str) -> str:
        return ARGPARSE.get(mensagem, {}).get(idioma, mensagem)

    argparse._ = _  # o argparse busca o "_" do módulo na hora de montar cada texto


def detectar(argv: list[str] | None = None) -> str:
    """Escolhe o idioma, nesta ordem:

    1. --idioma/--language na linha de comando;
    2. a variável CONVERSOR3MF_IDIOMA;
    3. a língua em que a pessoa digitou o comando (ex.: "islands" -> en, "convertir" -> es);
    4. o idioma do sistema.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    for i, item in enumerate(argv):
        for opcao in set(NOMES["--idioma"].values()):
            if item == opcao and i + 1 < len(argv):
                return _normalizar(argv[i + 1])
            if item.startswith(opcao + "="):
                return _normalizar(item.split("=", 1)[1])
    if os.environ.get("CONVERSOR3MF_IDIOMA"):
        return _normalizar(os.environ["CONVERSOR3MF_IDIOMA"])
    for item in argv:
        idioma = _idioma_do_nome(item.split("=", 1)[0])
        if idioma:
            return idioma
    for chave in ("LC_ALL", "LC_MESSAGES", "LANG"):
        if os.environ.get(chave):
            return _normalizar(os.environ[chave])
    if sys.platform == "win32":
        try:
            import ctypes

            primario = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
            return {0x16: "pt", 0x0A: "es"}.get(primario, "en")
        except (AttributeError, OSError):
            pass
    return _normalizar(locale.getlocale()[0] or "")


def _idioma_do_nome(nome: str) -> str | None:
    """Idioma de um comando/opção que só existe em uma língua ('plan' -> en); senão None."""
    for tabela in (NOMES, VISTAS):
        for traducoes in tabela.values():
            idiomas = {i for i, n in traducoes.items() if n == nome}
            if len(idiomas) == 1:
                return idiomas.pop()
    return None


def _normalizar(valor: str) -> str:
    valor = valor.strip().lower()
    if valor.startswith(("pt", "portug")):
        return "pt"
    if valor.startswith(("es", "spanish", "españ", "espan")):
        return "es"
    return "en"


def nomes(chave: str, idioma: str, tabela: dict = NOMES) -> list[str]:
    """Nome no idioma escolhido primeiro, depois os outros, sem repetir."""
    lista = [tabela[chave][idioma]] + [tabela[chave][i] for i in IDIOMAS]
    return list(dict.fromkeys(lista))


def texto(chave: str, idioma: str, **valores) -> str:
    return TEXTOS[chave][idioma].format(**valores)


def vista_interna(valor: str) -> str | None:
    """'top', 'arriba', 'cima' -> 'cima'; None se não existir."""
    valor = valor.strip().lower().replace("á", "a")  # "trás", "atrás"
    for interna, traducoes in VISTAS.items():
        if valor in {v.lower() for v in traducoes.values()} | {interna}:
            return interna
    return None
