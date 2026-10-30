"""Leitura de projetos 3MF (Bambu Studio, OrcaSlicer, Anycubic Slicer Next)."""

from __future__ import annotations

import json
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from . import cores, pintura

__all__ = ["Filamento", "Uso", "Projeto", "ler_projeto", "ProjetoInvalido"]

ATRIBUTOS_PINTURA = ("paint_color", "slic3rpe:mmu_segmentation")
CHAVES_FUNCAO = (
    "wall_filament",
    "sparse_infill_filament",
    "solid_infill_filament",
    "support_filament",
    "support_interface_filament",
)
RE_PINTURA = re.compile(r'(paint_color|slic3rpe:mmu_segmentation)="([0-9A-Fa-f]*)"')
RE_COMPONENTE = re.compile(r'<component\b[^>]*?p:path="([^"]+)"')
RE_OBJETO = re.compile(r'<object\b[^>]*?\bid="(\d+)"(.*?)</object>', re.S)


class ProjetoInvalido(ValueError):
    pass


@dataclass
class Filamento:
    numero: int
    cor: str
    tipo: str
    perfil: str


@dataclass
class Uso:
    pecas: int = 0
    triangulos: int = 0
    trocas_de_camada: int = 0
    funcoes: list[str] = field(default_factory=list)
    placas: set[int] = field(default_factory=set)

    @property
    def usado(self) -> bool:
        return bool(self.pecas or self.triangulos or self.trocas_de_camada or self.funcoes)


@dataclass
class Projeto:
    caminho: Path
    aplicativo: str
    config: dict
    model_settings: str
    filamentos: list[Filamento]
    uso: dict[int, Uso]
    placas: dict[int, list[str]]  # placa -> ids de objeto
    fatiado: bool

    @property
    def impressora(self) -> str:
        return self.config.get("printer_model") or self.config.get("printer_settings_id", "?")

    @property
    def usados(self) -> list[int]:
        return [f.numero for f in self.filamentos if self.uso[f.numero].usado]

    def resumo(self) -> dict:
        return {
            "arquivo": str(self.caminho),
            "feito_em": self.aplicativo,
            "impressora_original": self.impressora,
            "placas": len(self.placas),
            "arquivo_fatiado": self.fatiado,
            "filamentos": [
                {
                    "numero": f.numero,
                    "cor": f.cor,
                    "nome_da_cor": cores.nome_da_cor(f.cor),
                    "tipo": f.tipo,
                    "usado": self.uso[f.numero].usado,
                    "pecas": self.uso[f.numero].pecas,
                    "triangulos_pintados": self.uso[f.numero].triangulos,
                    "trocas_por_camada": self.uso[f.numero].trocas_de_camada,
                    "funcoes": self.uso[f.numero].funcoes,
                    "placas": sorted(self.uso[f.numero].placas),
                }
                for f in self.filamentos
            ],
        }


def _lista(config: dict, chave: str, n: int, padrao: str) -> list[str]:
    valor = config.get(chave) or []
    if isinstance(valor, str):
        valor = [valor]
    return [valor[i] if i < len(valor) else padrao for i in range(n)]


def _blocos(texto: str, tag: str) -> list[str]:
    return re.findall(rf"<{tag}\b.*?</{tag}>", texto, re.S)


def _meta(bloco: str, chave: str) -> list[str]:
    return re.findall(rf'<metadata key="{chave}" value="([^"]*)"', bloco)


def ler_projeto(caminho: str | Path) -> Projeto:
    caminho = Path(caminho)
    try:
        arquivo = zipfile.ZipFile(caminho)
    except (zipfile.BadZipFile, FileNotFoundError) as erro:
        raise ProjetoInvalido(f"não consegui abrir {caminho}: {erro}") from erro
    with arquivo:
        nomes = arquivo.namelist()
        if "Metadata/project_settings.config" not in nomes:
            raise ProjetoInvalido(
                "o 3MF não tem configurações de projeto (é só a malha). "
                "Abra no slicer, dê as cores e salve como projeto antes de converter."
            )
        config = json.loads(arquivo.read("Metadata/project_settings.config"))
        model_settings = (
            arquivo.read("Metadata/model_settings.config").decode("utf8")
            if "Metadata/model_settings.config" in nomes
            else ""
        )
        principal = arquivo.read("3D/3dmodel.model").decode("utf8")
        app = re.search(r'<metadata name="Application">([^<]*)<', principal)

        cores_hex = _lista(config, "filament_colour", len(config.get("filament_colour") or [1]), "#FFFFFF")
        n = len(cores_hex)
        tipos = _lista(config, "filament_type", n, "PLA")
        perfis = _lista(config, "filament_settings_id", n, "")
        filamentos = [
            Filamento(i + 1, cores.normalizar(cores_hex[i] or "#FFFFFF"), tipos[i], perfis[i])
            for i in range(n)
        ]
        uso: dict[int, Uso] = defaultdict(Uso)

        # placas e objetos
        placas: dict[int, list[str]] = {}
        placa_do_objeto: dict[str, set[int]] = defaultdict(set)
        for bloco in _blocos(model_settings, "plate"):
            numero = int((_meta(bloco, "plater_id") or ["1"])[0])
            objetos = _meta(bloco, "object_id")
            placas[numero] = objetos
            for obj in objetos:
                placa_do_objeto[obj].add(numero)

        # filamento de cada objeto/peça
        for bloco in _blocos(model_settings, "object"):
            obj = re.search(r'<object id="(\d+)"', bloco).group(1)
            for valor in _meta(bloco, "extruder"):
                if valor.isdigit() and int(valor) > 0:
                    uso[int(valor)].pecas += 1
                    uso[int(valor)].placas |= placa_do_objeto[obj]
            for chave in CHAVES_FUNCAO:
                for valor in _meta(bloco, chave):
                    if valor.isdigit() and int(valor) > 0:
                        uso[int(valor)].funcoes.append(f"{chave} (objeto)")

        # pintura: arquivo de malha -> objetos que o usam
        objetos_do_arquivo: dict[str, set[str]] = defaultdict(set)
        for obj, corpo in RE_OBJETO.findall(principal):
            for caminho_malha in RE_COMPONENTE.findall(corpo):
                objetos_do_arquivo[caminho_malha.lstrip("/")].add(obj)
        for nome in nomes:
            if not (nome.startswith("3D/") and nome.endswith(".model")):
                continue
            texto = principal if nome == "3D/3dmodel.model" else arquivo.read(nome).decode("utf8")
            contagem: Counter = Counter()
            for _, valor in RE_PINTURA.findall(texto):
                if valor:
                    contagem.update(pintura.estados(valor))
            placas_do_arquivo = set().union(
                *(placa_do_objeto[o] for o in objetos_do_arquivo.get(nome, ()))
            ) if objetos_do_arquivo.get(nome) else set()
            for estado, quantidade in contagem.items():
                if estado:
                    uso[estado].triangulos += quantidade
                    uso[estado].placas |= placas_do_arquivo

        # trocas de filamento por camada
        if "Metadata/custom_gcode_per_layer.xml" in nomes:
            xml = arquivo.read("Metadata/custom_gcode_per_layer.xml").decode("utf8")
            for bloco in _blocos(xml, "plate"):
                placa = re.search(r'<plate_info id="(\d+)"', bloco)
                for tipo, extrusor in re.findall(r'<layer\b[^>]*?type="(\d+)"[^>]*?extruder="(\d+)"', bloco):
                    if tipo in ("0", "2") and int(extrusor) > 0:
                        uso[int(extrusor)].trocas_de_camada += 1
                        if placa:
                            uso[int(extrusor)].placas.add(int(placa.group(1)))

        for chave in CHAVES_FUNCAO:
            valor = str(config.get(chave, "0"))
            if valor.isdigit() and int(valor) > 0:
                uso[int(valor)].funcoes.append(chave)

        fatiado = any(re.match(r"Metadata/plate_\d+\.gcode$", n) for n in nomes)

    for numero in list(uso):
        if numero > n:
            # projeto aponta para filamento que não existe na lista; cria entrada cinza
            filamentos.append(Filamento(numero, "#808080", "PLA", ""))
    filamentos.sort(key=lambda f: f.numero)
    return Projeto(
        caminho=caminho,
        aplicativo=app.group(1) if app else "?",
        config=config,
        model_settings=model_settings,
        filamentos=filamentos,
        uso={f.numero: uso[f.numero] for f in filamentos},
        placas=placas,
        fatiado=fatiado,
    )
