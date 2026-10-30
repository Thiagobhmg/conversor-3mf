"""3MFs sintéticos para os testes, feitos do zero (sem modelos de terceiros).

Projeto "Bambu A1" com duas placas:
- placa 1, objeto 2: uma base 20x20x1 mm (filamento 2, branco) com duas caixinhas em
  relevo pintadas: A de vermelho (filamento 1) e B de verde (filamento 3). Um triângulo
  da base tem pintura subdividida (metade vermelha).
- placa 2, objeto 4: um cubo cuja peça usa o filamento 3 (verde), com troca de filamento
  por camada para o 1.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from conversor3mf import pintura

CORES_BAMBU = ["#FF0000", "#FFFFFF", "#00AE42"]  # vermelho, branco, verde
TIPOS_BAMBU = ["PLA", "PLA", "PLA"]
SLOTS_KOBRA = [("#EFF0F1", "PLA"), ("#212721", "PLA"), ("#E10600", "PETG"), ("#009639", "PETG")]


def caixa(x0, y0, z0, x1, y1, z1, deslocamento=0):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
         (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
    return v, [(a + deslocamento, b + deslocamento, c + deslocamento) for a, b, c in f]


def _malha(id_, partes):
    """partes: lista de (vértices, triângulos, pinturas)"""
    vs, ts = [], []
    for v, t, p in partes:
        base = len(vs)
        vs += v
        ts += [(a + base, b + base, c + base, p[i] if p else "") for i, (a, b, c) in enumerate(t)]
    vert = "".join(f'<vertex x="{x}" y="{y}" z="{z}"/>' for x, y, z in vs)
    tri = "".join(
        f'<triangle v1="{a}" v2="{b}" v3="{c}"' + (f' paint_color="{p}"' if p else "") + "/>"
        for a, b, c, p in ts
    )
    return f'<object id="{id_}" type="model"><mesh><vertices>{vert}</vertices><triangles>{tri}</triangles></mesh></object>'


def _modelo(objetos: str) -> str:
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" '
            'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
            'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06">'
            f"<resources>{objetos}</resources></model>")


def criar_projeto_bambu(caminho: Path) -> Path:
    vermelho = pintura.codificar([("folha", 1)])
    verde = pintura.codificar([("folha", 3)])
    metade = pintura.codificar([("divisao", 0b0001), ("folha", 1), ("folha", 0)])
    base_v, base_t = caixa(-10, -10, 0, 10, 10, 1)
    a_v, a_t = caixa(-8, -8, 1, -4, -4, 2)
    b_v, b_t = caixa(4, 4, 1, 8, 8, 2)
    pint_base = [""] * 12
    pint_base[2] = metade  # um triângulo do topo da base, metade vermelho
    objeto1 = _malha("1", [(base_v, base_t, pint_base), (a_v, a_t, [vermelho] * 12), (b_v, b_t, [verde] * 12)])
    c_v, c_t = caixa(-5, -5, 0, 5, 5, 10)
    objeto3 = _malha("3", [(c_v, c_t, None)])

    principal = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
        'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
        ' <metadata name="Application">BambuStudio-02.04.00.70</metadata>\n'
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        " <resources>\n"
        '  <object id="2" type="model"><components>'
        '<component p:path="/3D/Objects/object_1.model" objectid="1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>'
        "</components></object>\n"
        '  <object id="4" type="model"><components>'
        '<component p:path="/3D/Objects/object_3.model" objectid="3" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>'
        "</components></object>\n"
        " </resources>\n <build>\n"
        '  <item objectid="2" transform="1 0 0 0 1 0 0 0 1 128 128 0" printable="1"/>\n'
        '  <item objectid="4" transform="1 0 0 0 1 0 0 0 1 435.2 128 0" printable="1"/>\n'
        " </build>\n</model>\n"
    )
    model_settings = """<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="2">
    <metadata key="name" value="base com relevo"/>
    <metadata key="extruder" value="2"/>
    <part id="1" subtype="normal_part">
      <metadata key="name" value="base com relevo"/>
    </part>
  </object>
  <object id="4">
    <metadata key="name" value="cubo"/>
    <metadata key="extruder" value="2"/>
    <part id="3" subtype="normal_part">
      <metadata key="name" value="cubo"/>
      <metadata key="extruder" value="3"/>
    </part>
  </object>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="filament_maps" value="1 1 1"/>
    <model_instance>
      <metadata key="object_id" value="2"/>
      <metadata key="instance_id" value="0"/>
    </model_instance>
  </plate>
  <plate>
    <metadata key="plater_id" value="2"/>
    <metadata key="filament_maps" value="1 1 1"/>
    <model_instance>
      <metadata key="object_id" value="4"/>
      <metadata key="instance_id" value="0"/>
    </model_instance>
  </plate>
</config>
"""
    trocas = """<?xml version="1.0" encoding="utf-8"?>
<custom_gcodes_per_layer>
<plate>
<plate_info id="2"/>
<layer top_z="5" type="2" extruder="1" color="#FF0000" extra="" gcode="tool_change"/>
<mode value="MultiAsSingle"/>
</plate>
</custom_gcodes_per_layer>
"""
    config = {
        "printer_model": "Bambu Lab A1",
        "printer_settings_id": "Bambu Lab A1 0.4 nozzle",
        "printable_area": ["0x0", "256x0", "256x256", "0x256"],
        "filament_colour": CORES_BAMBU,
        "filament_type": TIPOS_BAMBU,
        "filament_settings_id": ["Generic PLA @BBL A1"] * 3,
        "layer_height": "0.16",
        "wall_loops": "3",
        "sparse_infill_speed": "999",
        "version": "02.04.00.70",
    }
    with zipfile.ZipFile(caminho, "w") as z:
        z.writestr("3D/3dmodel.model", principal)
        z.writestr("3D/Objects/object_1.model", _modelo(objeto1))
        z.writestr("3D/Objects/object_3.model", _modelo(objeto3))
        z.writestr("Metadata/model_settings.config", model_settings)
        z.writestr("Metadata/project_settings.config", json.dumps(config))
        z.writestr("Metadata/custom_gcode_per_layer.xml", trocas)
        z.writestr("Metadata/slice_info.config", "<config/>")
        z.writestr("Metadata/plate_1.json", "{}")
    return caminho


def criar_molde_anycubic(caminho: Path) -> Path:
    config = {
        "printer_model": "Anycubic Kobra X",
        "printer_settings_id": "Anycubic Kobra X 0.4 nozzle",
        "printable_area": ["0x0", "260x0", "260x260", "0x260"],
        "filament_colour": [c for c, _ in SLOTS_KOBRA],
        "filament_colour_info": [c for c, _ in SLOTS_KOBRA],
        "filament_type": [t for _, t in SLOTS_KOBRA],
        "filament_settings_id": [f"Anycubic {t} @Anycubic Kobra X 0.4 nozzle" for _, t in SLOTS_KOBRA],
        "nozzle_temperature": ["210", "210", "240", "240"],
        "print_settings_id": "0.20mm Standard @Anycubic Kobra X 0.4 nozzle",
        "layer_height": "0.2",
        "wall_loops": "2",
        "sparse_infill_speed": "200",
        "machine_pause_gcode": "M600",
        "different_settings_to_system": ["", "", "", "", "", ""],
        "version": "2.0.0.3",
    }
    principal = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter">'
                 '<metadata name="Application">BambuStudio-2.0.0.3</metadata><resources/><build/></model>')
    with zipfile.ZipFile(caminho, "w") as z:
        z.writestr("3D/3dmodel.model", principal)
        z.writestr("Metadata/project_settings.config", json.dumps(config))
    return caminho
