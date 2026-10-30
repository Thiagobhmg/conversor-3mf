"""Molde de configuração da impressora e slots do ACE.

O molde é tirado de um projeto salvo pelo próprio Anycubic Slicer Next depois de
sincronizar o ACE: ele já traz impressora, perfis de filamento e a ordem real
dos carretéis. O arquivo `dados/meu_ace.json` guarda os slots e pode ser
editado à mão (por exemplo, para trocar a cor de um slot sem salvar outro molde).
"""

from __future__ import annotations

import json
import re
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path

from . import cores
from .config import pasta_dados, pasta_perfis

__all__ = ["Slot", "Ace", "definir_molde", "carregar", "alterar_slot", "aplicar_slots"]

ARQUIVO_ACE = "meu_ace.json"
ARQUIVO_MOLDE = "molde_project_settings.json"

# Espaçamento entre placas medido em projetos salvos pelo Anycubic Slicer Next
ESPACAMENTO_PLACAS = {"Anycubic Kobra X": (314.4, 328.8)}


@dataclass
class Slot:
    slot: int
    cor: str
    tipo: str
    nome: str
    perfil: str


@dataclass
class Ace:
    slots: list[Slot]
    molde: dict
    origem: str

    @property
    def impressora(self) -> str:
        return self.molde.get("printer_model", "?")

    def resumo(self) -> dict:
        return {
            "impressora": self.impressora,
            "molde_tirado_de": self.origem,
            "slots": [asdict(s) for s in self.slots],
        }


def _chaves_de_filamento() -> set[str]:
    """Todas as chaves que aparecem em perfis de filamento do slicer."""
    chaves = {"filament_colour", "filament_colour_info", "filament_settings_id", "default_filament_colour"}
    perfis = pasta_perfis()
    for arquivo in (perfis / "filament").glob("*.json") if perfis else []:
        try:
            chaves |= set(json.loads(arquivo.read_text(encoding="utf8")))
        except (OSError, ValueError):
            continue
    return chaves - {"name", "inherits", "from", "type", "setting_id", "instantiation", "version",
                     "compatible_printers", "compatible_printers_condition", "is_custom_defined",
                     "filament_id"}


def perfil_de_processo(nome: str) -> dict | None:
    perfis = pasta_perfis()
    caminho = perfis / "process" / f"{nome}.json" if perfis else None
    if caminho is None or not caminho.exists():
        return None
    perfil = json.loads(caminho.read_text(encoding="utf8"))
    if perfil.get("inherits"):
        base = perfil_de_processo(perfil["inherits"]) or {}
        perfil = {**base, **perfil}
    return perfil


CHAVES_META = {"type", "from", "setting_id", "is_custom_defined", "instantiation", "version",
               "inherits", "name", "compatible_printers", "compatible_printers_condition"}


def definir_molde(projeto_3mf: str | Path) -> Ace:
    """Lê um projeto salvo pelo Anycubic Slicer Next e grava molde + slots em dados/."""
    projeto_3mf = Path(projeto_3mf)
    with zipfile.ZipFile(projeto_3mf) as arquivo:
        config = json.loads(arquivo.read("Metadata/project_settings.config"))
        principal = arquivo.read("3D/3dmodel.model").decode("utf8")
        embutidos = [n for n in arquivo.namelist()
                     if re.match(r"Metadata/(machine|filament|process)_settings_\d+\.config$", n)]
    if not str(config.get("printer_model", "")).startswith("Anycubic"):
        raise ValueError(f"o projeto é de {config.get('printer_model')}, preciso de um salvo para a impressora Anycubic")
    diferencas = config.get("different_settings_to_system") or []
    if diferencas and diferencas[-1]:
        raise ValueError(
            "o perfil de impressora desse projeto foi modificado "
            f"({diferencas[-1][:120]}). Salve um projeto usando o perfil de sistema da impressora."
        )
    if any("machine_settings" in n for n in embutidos):
        # projetos com perfil de impressora embutido podem carregar G-code de outra máquina
        raise ValueError("o projeto traz um perfil de impressora personalizado embutido; use outro projeto")

    # processo volta ao perfil de fábrica; as escolhas do modelo entram na conversão
    perfil = perfil_de_processo(config.get("print_settings_id", ""))
    if perfil:
        for chave, valor in perfil.items():
            if chave not in CHAVES_META and chave in config:
                config[chave] = valor
        if diferencas:
            diferencas[0] = ""
    app = re.search(r'<metadata name="Application">([^<]*)<', principal)
    config["_aplicativo"] = app.group(1) if app else f"BambuStudio-{config.get('version', '2.0.0.3')}"

    n = len(config.get("filament_colour") or [])
    slots = [
        Slot(
            slot=i + 1,
            cor=cores.normalizar(config["filament_colour"][i]),
            tipo=config["filament_type"][i],
            nome=cores.nome_da_cor(config["filament_colour"][i]),
            perfil=config["filament_settings_id"][i],
        )
        for i in range(n)
    ]
    pasta_dados().mkdir(parents=True, exist_ok=True)
    (pasta_dados() / ARQUIVO_MOLDE).write_text(json.dumps(config, indent=1, ensure_ascii=False), encoding="utf8")
    ace = Ace(slots=slots, molde=config, origem=str(projeto_3mf))
    salvar_slots(ace)
    return ace


def salvar_slots(ace: Ace) -> None:
    dados = {
        "_leia_me": "Slots do ACE na ordem da impressora. Pode editar cor e nome; "
        "para mudar o tipo use um tipo que já exista em algum slot do molde.",
        "molde_tirado_de": ace.origem,
        "slots": [asdict(s) for s in ace.slots],
    }
    pasta_dados().mkdir(parents=True, exist_ok=True)
    (pasta_dados() / ARQUIVO_ACE).write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf8")


def carregar() -> Ace:
    caminho_molde = pasta_dados() / ARQUIVO_MOLDE
    caminho_ace = pasta_dados() / ARQUIVO_ACE
    if not caminho_molde.exists() or not caminho_ace.exists():
        raise FileNotFoundError(
            "ainda não há molde do ACE. Salve um projeto no Anycubic Slicer Next com o ACE "
            "sincronizado e rode: python -m conversor3mf ace definir <projeto.3mf>"
        )
    molde = json.loads(caminho_molde.read_text(encoding="utf8"))
    dados = json.loads(caminho_ace.read_text(encoding="utf8"))
    slots = [Slot(**{**s, "cor": cores.normalizar(s["cor"])}) for s in dados["slots"]]
    tipos_no_molde = set(molde.get("filament_type") or [])
    for s in slots:
        if s.tipo not in tipos_no_molde:
            raise ValueError(
                f"slot {s.slot} está como {s.tipo}, mas o molde só tem {sorted(tipos_no_molde)}. "
                "Salve um projeto no slicer com esse filamento e defina o molde de novo."
            )
    return Ace(slots=slots, molde=molde, origem=dados.get("molde_tirado_de", "?"))


def alterar_slot(numero: int, cor: str | None = None, tipo: str | None = None, nome: str | None = None) -> Ace:
    """Atualiza um slot depois de trocar o carretel; o tipo precisa existir no molde."""
    ace = carregar()
    slot = next((s for s in ace.slots if s.slot == numero), None)
    if slot is None:
        raise ValueError(f"slot {numero} não existe")
    if tipo:
        tipos = sorted(set(ace.molde.get("filament_type") or []))
        if tipo not in tipos:
            raise ValueError(
                f"o molde só tem {tipos}. Para usar {tipo}, salve um projeto no slicer com esse "
                "filamento em algum slot e defina o molde de novo."
            )
        slot.tipo = tipo
    if cor:
        slot.cor = cores.normalizar(cor)
        slot.nome = cores.nome_da_cor(slot.cor)
    if nome:
        slot.nome = nome
    salvar_slots(ace)
    return ace


def aplicar_slots(config: dict, ace: Ace) -> None:
    """Ajusta as listas por filamento do config para refletir os slots (cor e tipo)."""
    chaves = _chaves_de_filamento()
    n = len(ace.slots)
    tipos_molde = list(config.get("filament_type") or [])
    original = {k: list(v) for k, v in config.items() if k in chaves and isinstance(v, list) and len(v) == n}
    for i, slot in enumerate(ace.slots):
        if i < len(tipos_molde) and tipos_molde[i] != slot.tipo:
            fonte = tipos_molde.index(slot.tipo)
            for chave, valores in original.items():
                config[chave][i] = valores[fonte]
        config["filament_colour"][i] = slot.cor
        if "filament_colour_info" in config and i < len(config["filament_colour_info"]):
            config["filament_colour_info"][i] = slot.cor
