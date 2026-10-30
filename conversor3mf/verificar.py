"""Confere um 3MF convertido abrindo e regravando com o Anycubic Slicer Next."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from . import config
from .projeto import ler_projeto

__all__ = ["verificar"]


def verificar(arquivo: str | Path, tempo_limite: int = 300) -> dict:
    """Abre o arquivo no slicer (linha de comando), exporta de novo e compara.

    Confere se o slicer aceitou a impressora e as cores dos filamentos e se a
    pintura sobreviveu intacta (pintura inválida é apagada pelo slicer ao carregar).
    """
    arquivo = Path(arquivo)
    executavel = config.executavel_slicer()
    if executavel is None:
        return {"ok": False, "conferido_no_slicer": False,
                "problemas": ["não achei o Anycubic Slicer Next; defina CONVERSOR3MF_SLICER com a pasta dele"]}
    original = ler_projeto(arquivo)  # já falha se alguma pintura estiver corrompida
    if len(original.placas) > 1:
        # a linha de comando do Anycubic Slicer Next 2.0.0.3 trava com qualquer projeto
        # de várias placas, mesmo os salvos por ele; fica só a checagem interna
        return {
            "ok": True,
            "conferido_no_slicer": False,
            "motivo": "o slicer trava pela linha de comando em projetos com várias placas; "
                      "a pintura foi lida sem erros, mas abra no slicer para conferir",
            "impressora": original.impressora,
            "cores_dos_slots": [f.cor for f in original.filamentos],
            "triangulos_pintados_por_slot": {n: u.triangulos for n, u in original.uso.items() if u.triangulos},
            "pecas_por_slot": {n: u.pecas for n, u in original.uso.items() if u.pecas},
            "problemas": [],
        }
    with tempfile.TemporaryDirectory() as pasta:
        saida = Path(pasta) / "regravado.3mf"
        processo = subprocess.run(
            [str(executavel), "--export-3mf", str(saida), str(arquivo)],
            capture_output=True, text=True, timeout=tempo_limite, cwd=pasta,
        )
        if processo.returncode != 0 or not saida.exists():
            erros = [l for l in (processo.stdout + processo.stderr).splitlines() if "[error]" in l]
            return {"ok": False, "problemas": ["o slicer não conseguiu abrir o arquivo"] + erros[-5:]}
        regravado = ler_projeto(saida)

    problemas = []
    if regravado.impressora != original.impressora:
        problemas.append(f"impressora mudou: {original.impressora} -> {regravado.impressora}")
    cores_antes = [f.cor for f in original.filamentos]
    cores_depois = [f.cor for f in regravado.filamentos]
    if cores_antes != cores_depois:
        problemas.append(f"cores dos filamentos mudaram: {cores_antes} -> {cores_depois}")
    pintura_antes = {n: u.triangulos for n, u in original.uso.items() if u.triangulos}
    pintura_depois = {n: u.triangulos for n, u in regravado.uso.items() if u.triangulos}
    if pintura_antes != pintura_depois:
        problemas.append(f"pintura mudou: {pintura_antes} -> {pintura_depois}")
    pecas_antes = {n: u.pecas for n, u in original.uso.items() if u.pecas}
    pecas_depois = {n: u.pecas for n, u in regravado.uso.items() if u.pecas}
    if pecas_antes != pecas_depois:
        problemas.append(f"filamento das peças mudou: {pecas_antes} -> {pecas_depois}")
    return {
        "ok": not problemas,
        "conferido_no_slicer": True,
        "impressora": regravado.impressora,
        "cores_dos_slots": cores_depois,
        "triangulos_pintados_por_slot": pintura_depois,
        "pecas_por_slot": pecas_depois,
        "problemas": problemas,
    }
