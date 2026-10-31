"""Onde ficam os dados do usuário e o Anycubic Slicer Next.

Variáveis de ambiente (opcionais):
- CONVERSOR3MF_DADOS: pasta do molde e dos slots do ACE
- CONVERSOR3MF_SLICER: pasta de instalação do Anycubic Slicer Next (ou o executável)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

__all__ = ["pasta_dados", "pasta_slicer", "executavel_slicer", "ambiente_slicer", "pasta_perfis"]

NOME_APP = "conversor3mf"
# Linux: pasta do pacote do AUR (anycubicslicernext-bin), com bin/, lib/ e resources/
PASTAS_LINUX = (Path("/opt/AnycubicSlicerNext"),)


def pasta_dados() -> Path:
    if os.environ.get("CONVERSOR3MF_DADOS"):
        return Path(os.environ["CONVERSOR3MF_DADOS"])
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / NOME_APP
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / NOME_APP
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / NOME_APP


def _do_registro() -> list[Path]:
    if sys.platform != "win32":
        return []
    import winreg

    achados = []
    chaves = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for raiz, caminho in chaves:
        try:
            pai = winreg.OpenKey(raiz, caminho)
        except OSError:
            continue
        with pai:
            for i in range(winreg.QueryInfoKey(pai)[0]):
                try:
                    with winreg.OpenKey(pai, winreg.EnumKey(pai, i)) as filho:
                        nome = str(winreg.QueryValueEx(filho, "DisplayName")[0])
                        if "anycubicslicernext" not in nome.replace(" ", "").lower():
                            continue
                        for valor in ("DisplayIcon", "UninstallString", "InstallLocation"):
                            try:
                                texto = str(winreg.QueryValueEx(filho, valor)[0]).strip('" ').split(",")[0]
                            except OSError:
                                continue
                            if texto:
                                p = Path(texto)
                                achados.append(p.parent if p.suffix.lower() == ".exe" else p)
                except OSError:
                    continue
    return achados


def pasta_slicer() -> Path | None:
    """Pasta de instalação do Anycubic Slicer Next, ou None se não encontrar."""
    candidatos: list[Path] = []
    escolhido = os.environ.get("CONVERSOR3MF_SLICER")
    if escolhido is not None and escolhido.strip().lower() in ("", "nenhum", "none"):
        return None  # usado nos testes: finge que o slicer não está instalado
    if escolhido:
        p = Path(escolhido)
        # o executável fica na pasta de instalação (Windows) ou em bin/ dentro dela (Linux)
        candidatos += [p.parent, p.parent.parent] if p.is_file() else [p]
    candidatos += _do_registro()
    if sys.platform == "win32":
        for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"), os.environ.get("LOCALAPPDATA")):
            if base:
                candidatos += [Path(base) / "AnycubicSlicerNext", Path(base) / "Programs" / "AnycubicSlicerNext"]
    elif sys.platform == "darwin":
        candidatos.append(Path("/Applications/AnycubicSlicerNext.app"))
    else:
        candidatos += PASTAS_LINUX
    for c in candidatos:
        if executavel_slicer(c) is not None:
            return c
    return None


def executavel_slicer(pasta: Path | None = None) -> Path | None:
    pasta = pasta if pasta is not None else pasta_slicer()
    if pasta is None:
        return None
    for p in (pasta / "AnycubicSlicerNext.exe", pasta / "Contents" / "MacOS" / "AnycubicSlicerNext",
              pasta / "bin" / "AnycubicSlicerNext"):
        if p.is_file():
            return p
    return None


def ambiente_slicer(executavel: Path) -> dict[str, str] | None:
    """Variáveis para rodar o slicer; None = herda o ambiente atual.

    No Linux o binário de bin/ precisa das bibliotecas de lib/ (o lançador do pacote faz o
    mesmo) e de ponto decimal: com LC_NUMERIC em pt_BR ele lê "0,5" e quebra.
    """
    if sys.platform in ("win32", "darwin"):
        return None
    ambiente = dict(os.environ, LC_NUMERIC="C")
    bibliotecas = executavel.parent.parent / "lib"
    if bibliotecas.is_dir():
        ambiente["LD_LIBRARY_PATH"] = os.pathsep.join(
            filter(None, [str(bibliotecas), os.environ.get("LD_LIBRARY_PATH")]))
    return ambiente


def pasta_perfis() -> Path | None:
    """Pasta com os perfis de sistema da Anycubic (processo, filamento, impressora)."""
    pasta = pasta_slicer()
    if pasta is None:
        return None
    for p in (pasta / "resources" / "profiles" / "Anycubic",
              pasta / "Contents" / "Resources" / "profiles" / "Anycubic"):
        if p.is_dir():
            return p
    return None
