import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

from conversor3mf import ace, purga
from conversor3mf.conversor import converter

from fixtures import SLOTS_KOBRA, criar_molde_anycubic, criar_projeto_bambu

BRANCO, PRETO, VERMELHO, VERDE = (c for c, _ in SLOTS_KOBRA)


def projeto_anycubic(caminho: Path, cores: list[str], matriz: list[int], do_conversor=False) -> Path:
    """Projeto como o Anycubic Slicer Next grava (ou como o conversor grava, se do_conversor)."""
    marca = '<header_item key="X-Conversor3mf" value="1"/>' if do_conversor else ""
    with zipfile.ZipFile(caminho, "w") as z:
        z.writestr("Metadata/project_settings.config", json.dumps({
            "printer_model": "Anycubic Kobra X", "filament_colour": cores,
            "flush_volumes_matrix": [str(v) for v in matriz]}))
        z.writestr("Metadata/slice_info.config",
                   f'<config><header><header_item key="X-ACNext-Client-Type" value="slicer"/>{marca}</header></config>')
    return caminho


class TestPurga(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp())
        self.ambiente = {k: os.environ.get(k) for k in ("CONVERSOR3MF_DADOS", "CONVERSOR3MF_SLICER")}
        os.environ["CONVERSOR3MF_DADOS"] = str(self.pasta / "dados")
        os.environ["CONVERSOR3MF_SLICER"] = "nenhum"
        ace.definir_molde(criar_molde_anycubic(self.pasta / "molde.3mf"))

    def tearDown(self):
        for k, v in self.ambiente.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_formula_escuro_para_claro_purga_mais(self):
        self.assertGreater(purga.formula_orca(PRETO, BRANCO), 3 * purga.formula_orca(BRANCO, PRETO))
        self.assertGreaterEqual(purga.formula_orca(BRANCO, "#F0F0F0"), 60)  # mínimo do Orca

    def test_aprende_o_valor_mais_frequente_e_ignora_o_conversor(self):
        pasta = self.pasta / "projetos"
        pasta.mkdir()
        for i, valor in enumerate((785, 785, 587)):
            projeto_anycubic(pasta / f"p{i}.3mf", [PRETO, BRANCO], [0, valor, 142, 0])
        projeto_anycubic(pasta / "convertido.3mf", [PRETO, BRANCO], [0, 999, 999, 0], do_conversor=True)
        self.assertEqual(purga.aprender([pasta]), 2)
        self.assertEqual(purga.calcular_matriz([PRETO, BRANCO]), ["0", "785", "142", "0"])

    def test_ajuste_por_par_e_nivel_geral(self):
        projeto_anycubic(self.pasta / "p.3mf", [PRETO, BRANCO], [0, 785, 142, 0])
        purga.aprender([self.pasta / "p.3mf"])
        slots = [BRANCO, PRETO]
        purga.ajustar_par(2, 1, "mais", slots)  # preto -> branco +20%
        purga.ajustar_par(PRETO, BRANCO, "más", slots)  # espanhol também vale
        purga.ajustar_par(1, 2, "0.5", slots)
        self.assertEqual(purga.calcular_matriz([PRETO, BRANCO]), ["0", str(round(785 * 1.44)), "71", "0"])
        purga.definir_nivel("economy")
        self.assertEqual(purga.calcular_matriz([PRETO, BRANCO])[1], str(round(785 * 1.44 * 0.85)))
        with self.assertRaises(ValueError):
            purga.ajustar_par(1, 1, "mais", slots)

    def test_conversao_usa_as_cores_reais_dos_slots(self):
        ace.alterar_slot(4, cor="#FFD700")  # trocou o verde por amarelo
        destino = converter(criar_projeto_bambu(self.pasta / "modelo.3mf")).destino
        with zipfile.ZipFile(destino) as z:
            config = json.loads(z.read("Metadata/project_settings.config"))
            self.assertIn("X-Conversor3mf", z.read("Metadata/slice_info.config").decode())
        esperado = purga.calcular_matriz(config["filament_colour"])
        self.assertEqual(config["flush_volumes_matrix"], esperado)
        # preto (2) -> amarelo (4) pela fórmula + volume do bico (79 mm³ no padrão)
        self.assertEqual(esperado[1 * 4 + 3], str(round(purga.formula_orca(PRETO, "#FFD700") + 79)))

    def test_aplicar_em_arquivo_pronto(self):
        destino = Path(converter(criar_projeto_bambu(self.pasta / "modelo.3mf")).destino)
        purga.ajustar_par(PRETO, BRANCO, "mais", [BRANCO, PRETO])
        r = purga.aplicar_em_arquivo(destino)
        self.assertTrue(r["arquivo"].endswith("_KobraX_purga.3mf"))
        self.assertNotEqual(r["tabela_antes"][4], r["tabela_agora"][4])  # linha preto, coluna branco
        with self.assertRaises(ValueError):
            purga.aplicar_em_arquivo(destino, r["arquivo"])


if __name__ == "__main__":
    unittest.main()
