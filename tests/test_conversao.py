import json
import os
import re
import tempfile
import unittest
import zipfile
from pathlib import Path

from conversor3mf import ace, ilhas, pintura
from conversor3mf.conversor import converter, planejar
from conversor3mf.projeto import ProjetoInvalido, ler_projeto
from conversor3mf.verificar import verificar

from fixtures import criar_molde_anycubic, criar_projeto_bambu


class Base(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp())
        self.ambiente = {k: os.environ.get(k) for k in ("CONVERSOR3MF_DADOS", "CONVERSOR3MF_SLICER")}
        os.environ["CONVERSOR3MF_DADOS"] = str(self.pasta / "dados")
        os.environ["CONVERSOR3MF_SLICER"] = "nenhum"
        ace.definir_molde(criar_molde_anycubic(self.pasta / "molde.3mf"))
        self.origem = criar_projeto_bambu(self.pasta / "modelo.3mf")

    def tearDown(self):
        for k, v in self.ambiente.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    @staticmethod
    def ler(caminho, nome):
        with zipfile.ZipFile(caminho) as z:
            return z.read(nome).decode("utf8")

    def estados_por_triangulo(self, caminho, arquivo="3D/Objects/object_1.model"):
        return [
            (pintura.decodificar(p.group(1)) if p and p.group(1) else None)
            for p in (re.search(r'paint_color="([0-9A-F]*)"', t)
                      for t in re.findall(r"<triangle ([^>]*)/>", self.ler(caminho, arquivo)))
        ]


class TestConversao(Base):
    def test_plano_automatico(self):
        plano = planejar(ler_projeto(self.origem), ace.carregar())
        self.assertEqual(plano.mapa, {1: 3, 2: 1, 3: 4})  # vermelho, branco, verde
        self.assertTrue(any("PETG" in aviso for aviso in plano.avisos))

    def test_converter(self):
        r = converter(self.origem)
        destino = Path(r.destino)
        self.assertEqual(destino.name, "modelo_KobraX.3mf")

        config = json.loads(self.ler(destino, "Metadata/project_settings.config"))
        self.assertEqual(config["printer_model"], "Anycubic Kobra X")
        self.assertEqual(config["filament_colour"], ["#EFF0F1", "#212721", "#E10600", "#009639"])
        self.assertEqual(config["layer_height"], "0.16")  # escolha do designer
        self.assertEqual(config["wall_loops"], "3")
        self.assertEqual(config["sparse_infill_speed"], "200")  # velocidade fica a da Kobra X

        estados = self.estados_por_triangulo(destino)
        self.assertEqual(estados[12:24], [[("folha", 3)]] * 12)  # caixinha A: vermelho -> slot 3
        self.assertEqual(estados[24:36], [[("folha", 4)]] * 12)  # caixinha B: verde -> slot 4
        self.assertEqual(estados[2], [("divisao", 1), ("folha", 3), ("folha", 0)])  # subdividido

        ms = self.ler(destino, "Metadata/model_settings.config")
        self.assertEqual(re.findall(r'key="extruder" value="(\d+)"', ms), ["1", "1", "4"])
        self.assertIn('key="filament_maps" value="1 1 1 1"', ms)

        trocas = self.ler(destino, "Metadata/custom_gcode_per_layer.xml")
        self.assertIn('extruder="3" color="#E10600"', trocas)

        principal = self.ler(destino, "3D/3dmodel.model")
        self.assertIn("BambuStudio-2.0.0.3", principal)
        xs = [float(t.split()[9]) for t in re.findall(r'<item[^>]*transform="([^"]+)"', principal)]
        self.assertAlmostEqual(xs[0], 130.0, places=3)  # placa 1: centro da mesa de 260
        self.assertAlmostEqual(xs[1], 444.4, places=3)  # placa 2: grade da Kobra X

        with zipfile.ZipFile(destino) as z:
            self.assertNotIn("Metadata/plate_1.json", z.namelist())
            self.assertIn("X-ACNext-Client-Version", z.read("Metadata/slice_info.config").decode())

    def test_mapa_manual_e_nao_sobrescreve(self):
        r = converter(self.origem, mapa_manual={1: 2})
        self.assertEqual(r.plano.mapa[1], 2)
        self.assertTrue(any("vermelho" in a and "slot 2" in a for a in r.avisos))
        with self.assertRaises(ValueError):
            converter(self.origem, destino=r.destino)

    def test_mais_cores_que_slots(self):
        ace.alterar_slot(4, cor="#FFFFFF")
        ace.alterar_slot(3, cor="#FFFFFE")
        plano = planejar(ler_projeto(self.origem), ace.carregar())
        self.assertTrue(any("ruim" in a.qualidade for a in plano.associacoes if a.usado))

    def test_so_malha_e_recusado(self):
        caminho = self.pasta / "malha.3mf"
        with zipfile.ZipFile(caminho, "w") as z:
            z.writestr("3D/3dmodel.model", "<model/>")
        with self.assertRaises(ProjetoInvalido):
            ler_projeto(caminho)

    def test_verificar_sem_slicer(self):
        r = verificar(converter(self.origem).destino)
        self.assertFalse(r["ok"])
        self.assertFalse(r["conferido_no_slicer"])


class TestIlhas(Base):
    def test_mapa_e_repintura(self):
        destino = Path(converter(self.origem).destino)
        png, info = ilhas.mapa_de_ilhas(destino, objeto="2")
        self.assertTrue(png.startswith(b"\x89PNG"))
        rotuladas = {i["ilha"]: i for i in info["ilhas_rotuladas"]}
        caixa_a = next(n for n, i in rotuladas.items() if i["centro_mm"][:2] == [-6.0, -6.0])
        self.assertEqual(rotuladas[caixa_a]["slot_atual"], 3)

        r = ilhas.repintar_ilhas(destino, {caixa_a: 2}, objeto="2")
        self.assertTrue(r["arquivo_repintado"].endswith("_repintado.3mf"))
        estados = self.estados_por_triangulo(r["arquivo_repintado"])
        self.assertEqual(estados[12:24], [[("folha", 2)]] * 12)
        self.assertEqual(estados[24:36], [[("folha", 4)]] * 12)  # caixinha B intacta
        # o triângulo meio vermelho da base não encosta na caixinha A, então não muda
        self.assertEqual(estados[2], [("divisao", 1), ("folha", 3), ("folha", 0)])

    def test_ilha_inexistente(self):
        destino = Path(converter(self.origem).destino)
        with self.assertRaises(ValueError):
            ilhas.repintar_ilhas(destino, {999: 1}, objeto="2")


if __name__ == "__main__":
    unittest.main()
