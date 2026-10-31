"""Conversão de projetos 3MF para a impressora e a ordem de slots do ACE."""

from __future__ import annotations

import copy
import itertools
import json
import math
import re
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import ace as modulo_ace
from . import cores, pintura, purga
from .projeto import CHAVES_FUNCAO, RE_PINTURA, Projeto, ler_projeto

__all__ = ["Associacao", "Plano", "planejar", "converter", "Resultado"]

# Escolhas do designer que fazem sentido em qualquer impressora. Velocidades,
# acelerações e temperaturas ficam com o perfil de fábrica da Kobra X.
CHAVES_DO_MODELO = [
    "layer_height", "initial_layer_print_height", "wall_loops", "top_shell_layers",
    "bottom_shell_layers", "top_shell_thickness", "bottom_shell_thickness",
    "sparse_infill_density", "sparse_infill_pattern", "top_surface_pattern",
    "bottom_surface_pattern", "internal_solid_infill_pattern", "infill_direction",
    "enable_support", "support_type", "support_style", "support_threshold_angle",
    "support_on_build_plate_only", "support_critical_regions_only",
    "support_remove_small_overhang", "support_top_z_distance", "support_bottom_z_distance",
    "support_interface_top_layers", "support_interface_bottom_layers",
    "support_interface_spacing", "support_base_pattern", "support_base_pattern_spacing",
    "support_object_xy_distance", "support_interface_pattern", "tree_support_branch_angle",
    "tree_support_branch_diameter", "tree_support_wall_count", "independent_support_layer_height",
    "raft_layers", "brim_type", "brim_width", "brim_object_gap", "skirt_loops",
    "seam_position", "ironing_type", "ironing_flow", "ironing_spacing", "ironing_pattern",
    "fuzzy_skin", "fuzzy_skin_thickness", "fuzzy_skin_point_distance", "only_one_wall_top",
    "only_one_wall_first_layer", "wall_generator", "wall_sequence", "detect_thin_wall",
    "print_sequence", "spiral_mode", "xy_hole_compensation", "xy_contour_compensation",
    "elefant_foot_compensation", "interface_shells", "flush_into_infill",
    "flush_into_objects", "flush_into_support", "reduce_crossing_wall",
]
DESCARTAR = re.compile(
    r"Metadata/(plate_\d+\.json|plate_\d+\.gcode(\.md5)?|filament_sequence\.json|"
    r"(machine|filament|process)_settings_\d+\.config|slice_info\.config)$"
)
SEMELHANTES = 3.0  # ΔE abaixo disso: mesma cor, usa o mesmo slot


@dataclass
class Associacao:
    filamento: int
    cor: str
    nome_da_cor: str
    tipo: str
    usado: bool
    slot: int
    cor_do_slot: str
    nome_do_slot: str
    tipo_do_slot: str
    diferenca: float
    qualidade: str
    escolhido_por: str  # "automatico", "manual", "mesma cor de N" ou "sem uso"


@dataclass
class Plano:
    associacoes: list[Associacao]
    avisos: list[str] = field(default_factory=list)
    cores_por_placa: dict[int, list[str]] = field(default_factory=dict)

    @property
    def mapa(self) -> dict[int, int]:
        return {a.filamento: a.slot for a in self.associacoes}

    def resumo(self) -> dict:
        return {
            "associacoes": [asdict(a) for a in self.associacoes],
            "cores_por_placa": self.cores_por_placa,
            "avisos": self.avisos,
        }


def _familia(tipo: str) -> str:
    return re.split(r"[-+ ]", tipo.strip().upper() or "PLA")[0]


def _custo(cor: str, tipo: str, slot: modulo_ace.Slot) -> float:
    return cores.delta_e(cor, slot.cor) + (8 if _familia(tipo) != _familia(slot.tipo) else 0)


def planejar(projeto: Projeto, ace: modulo_ace.Ace, manual: dict[int, int] | None = None) -> Plano:
    """Decide em qual slot do ACE cada filamento do projeto vai sair."""
    manual = {int(k): int(v) for k, v in (manual or {}).items()}
    slots = {s.slot: s for s in ace.slots}
    for origem, destino in manual.items():
        if destino not in slots:
            raise ValueError(f"slot {destino} não existe (slots: {sorted(slots)})")
        if origem not in {f.numero for f in projeto.filamentos}:
            raise ValueError(f"o projeto não tem filamento {origem}")

    filamentos = {f.numero: f for f in projeto.filamentos}
    usados = [n for n in projeto.usados if n not in manual]

    # filamentos de mesma cor e tipo vão juntos
    grupos: list[list[int]] = []
    for n in usados:
        for grupo in grupos:
            lider = filamentos[grupo[0]]
            if (cores.delta_e(lider.cor, filamentos[n].cor) < SEMELHANTES
                    and _familia(lider.tipo) == _familia(filamentos[n].tipo)):
                grupo.append(n)
                break
        else:
            grupos.append([n])

    escolha: dict[int, int] = {}
    livres = [s for s in slots if s not in manual.values()]
    if grupos and len(grupos) <= len(livres):
        melhor, menor = None, math.inf
        for combinacao in itertools.permutations(livres, len(grupos)):
            custo = sum(_custo(filamentos[g[0]].cor, filamentos[g[0]].tipo, slots[s])
                        for g, s in zip(grupos, combinacao))
            if custo < menor:
                melhor, menor = combinacao, custo
        for grupo, slot in zip(grupos, melhor):
            escolha[grupo[0]] = slot
    else:
        for grupo in grupos:
            lider = filamentos[grupo[0]]
            escolha[grupo[0]] = min(slots, key=lambda s: _custo(lider.cor, lider.tipo, slots[s]))

    associacoes = []
    for f in projeto.filamentos:
        usado = projeto.uso[f.numero].usado
        if f.numero in manual:
            slot, motivo = manual[f.numero], "manual"
        elif not usado:
            slot = min(slots, key=lambda s: _custo(f.cor, f.tipo, slots[s]))
            motivo = "sem uso"
        else:
            grupo = next(g for g in grupos if f.numero in g)
            slot = escolha[grupo[0]]
            motivo = "automatico" if grupo[0] == f.numero else f"mesma cor do filamento {grupo[0]}"
        destino = slots[slot]
        diferenca = cores.delta_e(f.cor, destino.cor)
        associacoes.append(Associacao(
            filamento=f.numero, cor=f.cor, nome_da_cor=cores.nome_da_cor(f.cor), tipo=f.tipo,
            usado=usado, slot=slot, cor_do_slot=destino.cor, nome_do_slot=destino.nome,
            tipo_do_slot=destino.tipo, diferenca=round(diferenca, 1),
            qualidade=cores.qualidade(diferenca), escolhido_por=motivo,
        ))

    plano = Plano(associacoes)
    usadas = [a for a in associacoes if a.usado]
    for a in usadas:
        for placa in sorted(projeto.uso[a.filamento].placas):
            plano.cores_por_placa.setdefault(placa, []).append(
                f"filamento {a.filamento} ({a.nome_da_cor}) -> slot {a.slot} ({a.nome_do_slot})"
            )
    plano.cores_por_placa = dict(sorted(plano.cores_por_placa.items()))
    cores_na_placa: dict[int, set[str]] = {}
    for a in usadas:
        for placa in projeto.uso[a.filamento].placas:
            cores_na_placa.setdefault(placa, set()).add(a.cor)
    if len({a.cor for a in usadas}) > len(ace.slots) and cores_na_placa and all(
        len(c) <= len(ace.slots) for c in cores_na_placa.values()
    ):
        plano.avisos.append(
            "O projeto tem mais cores que o ACE, mas cada placa sozinha cabe. Para não juntar cores, "
            "imprima placa a placa trocando os carretéis e informe o slot de cada cor com o mapa manual."
        )
    for a in usadas:
        if a.qualidade == "ruim":
            plano.avisos.append(
                f"Nenhum slot tem cor parecida com o filamento {a.filamento} ({a.nome_da_cor} {a.cor}). "
                f"Ele vai sair no slot {a.slot} ({a.nome_do_slot} {a.cor_do_slot}). "
                f"Troque o carretel do slot {a.slot} ou escolha outro slot."
            )
        if _familia(a.tipo) != _familia(a.tipo_do_slot):
            plano.avisos.append(
                f"O filamento {a.filamento} é {a.tipo} no modelo e vai sair em {a.tipo_do_slot} (slot {a.slot})."
            )
    por_slot: dict[int, list[Associacao]] = {}
    for a in usadas:
        por_slot.setdefault(a.slot, []).append(a)
    for slot, lista in sorted(por_slot.items()):
        nomes = {a.cor for a in lista}
        if len(nomes) > 1:
            plano.avisos.append(
                f"As cores {', '.join(f'{a.nome_da_cor} ({a.filamento})' for a in lista)} "
                f"vão sair todas no slot {slot}: o modelo tem mais cores que o ACE."
            )
    familias = {_familia(a.tipo_do_slot) for a in usadas}
    if len(familias) > 1:
        plano.avisos.append(
            f"A impressão mistura {' e '.join(sorted(familias))}. Esses materiais grudam mal "
            "entre si; prefira slots do mesmo tipo quando as cores ficarem na mesma peça."
        )
    trocas = sum(projeto.uso[a.filamento].trocas_de_camada for a in usadas)
    if trocas:
        so_altura = [a for a in usadas if projeto.uso[a.filamento].trocas_de_camada
                     and not projeto.uso[a.filamento].pecas and not projeto.uso[a.filamento].triangulos]
        plano.avisos.append(
            f"Este modelo muda de cor por altura ({trocas} troca{'s' if trocas != 1 else ''} em alturas fixas). "
            "Na tela Preparar do "
            "slicer ele aparece com menos cores (às vezes uma só); as cores por altura só aparecem na "
            "Pré-visualização depois de fatiar. Não é preciso recolorir as peças à mão."
            + ((" A cor " if len(so_altura) == 1 else " As cores ")
               + ", ".join(f"{a.nome_da_cor} (slot {a.slot})" for a in so_altura)
               + (" só existe" if len(so_altura) == 1 else " só existem") + " nessas trocas por altura."
               if so_altura else "")
        )
    return plano


@dataclass
class Resultado:
    destino: str
    plano: Plano
    processo: str
    configuracoes_do_modelo: dict
    avisos: list[str]

    def resumo(self) -> dict:
        return {
            "arquivo_convertido": self.destino,
            "perfil_de_processo": self.processo,
            "configuracoes_mantidas_do_modelo": self.configuracoes_do_modelo,
            **self.plano.resumo(),
            "avisos": self.avisos,
        }


def _area(config: dict) -> tuple[float, float, float, float]:
    pontos = [tuple(map(float, p.split("x"))) for p in config.get("printable_area") or ["0x0", "256x256"]]
    xs, ys = [p[0] for p in pontos], [p[1] for p in pontos]
    return min(xs), min(ys), max(xs), max(ys)


def _espacamento(config: dict) -> tuple[float, float]:
    medido = modulo_ace.ESPACAMENTO_PLACAS.get(config.get("printer_model", ""))
    if medido:
        return medido
    x0, y0, x1, y1 = _area(config)
    return (x1 - x0) * 1.2, (y1 - y0) * 1.2


def _colunas(quantidade: int) -> int:
    raiz = math.sqrt(quantidade)
    arredondado = round(raiz)
    return arredondado + 1 if raiz > arredondado else max(arredondado, 1)


def _estilo_original(fonte: dict) -> str:
    """Na Bambu só "High Quality" muda velocidades e acelerações; "Fine", "Optimal", "Draft"
    e afins são só o nome da altura de camada, com as velocidades do Standard."""
    return "High Quality" if "high quality" in str(fonte.get("print_settings_id", "")).lower() else "Standard"


def _escolher_processo(config: dict, fonte: dict) -> tuple[dict | None, str, str | None]:
    """Perfil de fábrica da Kobra X na altura do original, no mesmo estilo quando existir."""
    impressora = config.get("printer_settings_id", "")
    try:
        altura = float(fonte.get("layer_height", config.get("layer_height", 0.2)))
    except ValueError:
        altura = 0.2
    preferido = _estilo_original(fonte)
    estilos = [preferido] + [e for e in ("Standard", "High Quality", "Draft", "Extra Draft") if e != preferido]
    for estilo in estilos:
        nome = f"{altura:.2f}mm {estilo} @{impressora}"
        perfil = modulo_ace.perfil_de_processo(nome)
        if perfil:
            aviso = None if estilo == preferido else (
                f"O processo original é {fonte.get('print_settings_id')}, mas a {impressora} não tem perfil "
                f"{preferido} em {altura:.2f} mm; usei {nome}.")
            return perfil, nome, aviso
    return None, config.get("print_settings_id", ""), None


def _montar_config(
    projeto: Projeto, ace: modulo_ace.Ace, mapa: dict[int, int]
) -> tuple[dict, str, dict, str | None]:
    config = copy.deepcopy(ace.molde)
    config.pop("_aplicativo", None)
    modulo_ace.aplicar_slots(config, ace)
    purga.aplicar_no_config(config)  # tabela de purga para as cores reais dos slots
    fonte = projeto.config

    perfil, nome, aviso_processo = _escolher_processo(config, fonte)
    if perfil:
        for chave, valor in perfil.items():
            if chave not in modulo_ace.CHAVES_META and chave in config:
                config[chave] = valor
        config["print_settings_id"] = nome
    alteradas: dict = {}
    for chave in CHAVES_DO_MODELO:
        if chave in fonte and chave in config and type(fonte[chave]) is type(config[chave]):
            if fonte[chave] != config[chave]:
                alteradas[chave] = fonte[chave]
                config[chave] = fonte[chave]
    for chave in CHAVES_FUNCAO:
        valor = str(fonte.get(chave, "0"))
        if chave in config and valor.isdigit():
            novo = str(mapa.get(int(valor), 0)) if int(valor) else "0"
            if novo != str(config[chave]):
                alteradas[chave] = novo
            config[chave] = novo
    diferencas = config.get("different_settings_to_system")
    if isinstance(diferencas, list) and diferencas:
        diferencas[0] = ";".join(sorted(alteradas))
    return config, nome, alteradas, aviso_processo


def _remapear_model_settings(texto: str, mapa: dict[int, int], n_slots: int) -> str:
    chaves = "|".join(("extruder",) + CHAVES_FUNCAO)

    def troca(m: re.Match) -> str:
        valor = m.group(2)
        if valor.isdigit() and int(valor) > 0:
            valor = str(mapa.get(int(valor), 1))
        return f'{m.group(1)}"{valor}"'

    texto = re.sub(rf'(<metadata key="(?:{chaves})" value=)"([^"]*)"', troca, texto)
    texto = re.sub(r'(<metadata key="filament_maps" value=)"[^"]*"',
                   lambda m: f'{m.group(1)}"{" ".join(["1"] * n_slots)}"', texto)
    texto = re.sub(r'\s*<metadata key="(?:filament_volume_maps|gcode_file)" value="[^"]*"\s*/>', "", texto)
    return texto


def _posicoes_por_placa(model_settings: str) -> dict[tuple[str, int], int]:
    placa_de: dict[tuple[str, int], int] = {}
    for bloco in re.findall(r"<plate>.*?</plate>", model_settings, re.S):
        numero = int(re.search(r'plater_id" value="(\d+)"', bloco).group(1))
        for instancia in re.findall(r"<model_instance>.*?</model_instance>", bloco, re.S):
            obj = re.search(r'object_id" value="(\d+)"', instancia).group(1)
            inst = int(re.search(r'instance_id" value="(\d+)"', instancia).group(1))
            placa_de[(obj, inst)] = numero
    return placa_de


def _ajustar_principal(texto: str, projeto: Projeto, config: dict, aplicativo: str) -> str:
    texto = re.sub(r'(<metadata name="Application">)[^<]*(<)', rf"\g<1>{aplicativo}\g<2>", texto)
    if projeto.impressora == config.get("printer_model"):
        return texto
    placa_de = _posicoes_por_placa(projeto.model_settings)
    quantidade = max(len(projeto.placas), 1)
    colunas = _colunas(quantidade)
    ax0, ay0, ax1, ay1 = _area(projeto.config)
    bx0, by0, bx1, by1 = _area(config)
    sx_antigo, sy_antigo = _espacamento(projeto.config)
    sx_novo, sy_novo = _espacamento(config)
    deslocamento_centro = ((bx0 + bx1) / 2 - (ax0 + ax1) / 2, (by0 + by1) / 2 - (ay0 + ay1) / 2)
    instancias: dict[str, int] = {}

    def mover(m: re.Match) -> str:
        obj = m.group(2)
        inst = instancias.get(obj, 0)
        instancias[obj] = inst + 1
        indice = placa_de.get((obj, inst), 1) - 1
        linha, coluna = divmod(indice, colunas)
        numeros = m.group(4).split()
        if len(numeros) != 12:
            return m.group(0)
        x, y = float(numeros[9]), float(numeros[10])
        x += coluna * (sx_novo - sx_antigo) + deslocamento_centro[0]
        y += -linha * (sy_novo - sy_antigo) + deslocamento_centro[1]
        numeros[9], numeros[10] = f"{x:.6f}", f"{y:.6f}"
        return f'{m.group(1)}{obj}{m.group(3)}transform="{" ".join(numeros)}"'

    return re.sub(r'(<item\b[^>]*?objectid=")(\d+)("[^>]*?)transform="([^"]+)"', mover, texto)


def _remapear_trocas(xml: str, mapa: dict[int, int], config: dict) -> str:
    cores_slot = config.get("filament_colour") or []
    pausa = config.get("machine_pause_gcode", "M600")

    def troca(m: re.Match) -> str:
        tag = m.group(0)
        tipo = re.search(r'type="(\d+)"', tag)
        extrusor = re.search(r'extruder="(\d+)"', tag)
        if extrusor and int(extrusor.group(1)) > 0:
            novo = mapa.get(int(extrusor.group(1)), 1)
            tag = tag.replace(extrusor.group(0), f'extruder="{novo}"')
            if tipo and tipo.group(1) in ("0", "2") and novo <= len(cores_slot):
                tag = re.sub(r'color="[^"]*"', f'color="{cores_slot[novo - 1]}"', tag)
        if tipo and tipo.group(1) == "1":
            tag = re.sub(r'gcode="[^"]*"', f'gcode="{pausa}"', tag)
        return tag

    return re.sub(r"<layer\b[^>]*/>", troca, xml)


def _destino_livre(origem: Path) -> Path:
    candidato = origem.with_name(f"{origem.stem}_KobraX.3mf")
    contador = 2
    while candidato.exists():
        candidato = origem.with_name(f"{origem.stem}_KobraX_{contador}.3mf")
        contador += 1
    return candidato


def converter(
    origem: str | Path,
    destino: str | Path | None = None,
    mapa_manual: dict[int, int] | None = None,
    ace: modulo_ace.Ace | None = None,
) -> Resultado:
    origem = Path(origem)
    ace = ace or modulo_ace.carregar()
    projeto = ler_projeto(origem)
    plano = planejar(projeto, ace, mapa_manual)
    mapa = plano.mapa
    destino = Path(destino) if destino else _destino_livre(origem)
    if destino.exists():
        raise ValueError(f"{destino} já existe; escolha outro nome")

    config, processo, alteradas, aviso_processo = _montar_config(projeto, ace, mapa)
    aplicativo = ace.molde.get("_aplicativo", f"BambuStudio-{config.get('version', '2.0.0.3')}")
    avisos = list(plano.avisos) + ([aviso_processo] if aviso_processo else [])
    if projeto.fatiado:
        avisos.append("O arquivo original estava fatiado; o G-code dele foi descartado. Fatie de novo no slicer.")
    ax0, ay0, ax1, ay1 = _area(projeto.config)
    bx0, by0, bx1, by1 = _area(config)
    if ax1 - ax0 > bx1 - bx0 + 1 or ay1 - ay0 > by1 - by0 + 1:
        avisos.append(
            f"A mesa original ({ax1 - ax0:.0f}x{ay1 - ay0:.0f} mm) é maior que a da Kobra X "
            f"({bx1 - bx0:.0f}x{by1 - by0:.0f} mm). Confira se as peças cabem em cada placa."
        )

    cache: dict[str, str] = {}

    def nova_pintura(m: re.Match) -> str:
        valor = m.group(2)
        if valor not in cache:
            cache[valor] = pintura.remapear(valor, mapa) if valor else valor
        return f'{m.group(1)}="{cache[valor]}"'

    temporario = destino.with_suffix(".tmp")
    with zipfile.ZipFile(origem) as entrada, zipfile.ZipFile(temporario, "w", zipfile.ZIP_DEFLATED) as saida:
        for info in entrada.infolist():
            nome = info.filename
            if DESCARTAR.match(nome):
                continue
            dados = entrada.read(nome)
            if nome == "Metadata/project_settings.config":
                dados = json.dumps(config, indent=4, ensure_ascii=False).encode("utf8")
            elif nome == "Metadata/model_settings.config":
                dados = _remapear_model_settings(dados.decode("utf8"), mapa, len(ace.slots)).encode("utf8")
            elif nome == "Metadata/custom_gcode_per_layer.xml":
                dados = _remapear_trocas(dados.decode("utf8"), mapa, config).encode("utf8")
            elif nome.startswith("3D/") and nome.endswith(".model"):
                texto = dados.decode("utf8")
                if nome == "3D/3dmodel.model":
                    texto = _ajustar_principal(texto, projeto, config, aplicativo)
                texto = RE_PINTURA.sub(nova_pintura, texto)
                dados = texto.encode("utf8")
            saida.writestr(info, dados, compress_type=zipfile.ZIP_DEFLATED)
        versao = config.get("version", "2.0.0.3")
        saida.writestr(
            "Metadata/slice_info.config",
            '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n  <header>\n'
            '    <header_item key="X-ACNext-Client-Type" value="slicer"/>\n'
            f'    <header_item key="X-ACNext-Client-Version" value="{versao}"/>\n'
            # marca o arquivo como gerado aqui (purga.aprender ignora esses arquivos)
            '    <header_item key="X-Conversor3mf" value="1"/>\n'
            "  </header>\n</config>\n",
        )
    temporario.replace(destino)
    return Resultado(str(destino), plano, processo, alteradas, avisos)
