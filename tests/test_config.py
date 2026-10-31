import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from conversor3mf import config


def instalacao_linux(pasta: Path, executavel: str = "AnycubicSlicerNext") -> Path:
    """Instalação falsa no layout do pacote do AUR (ou da AppImage extraída do OrcaSlicer):
    bin/, lib/ e resources/profiles/Anycubic."""
    (pasta / "bin").mkdir(parents=True)
    (pasta / "bin" / executavel).write_text("#!/bin/sh\n")
    (pasta / "lib").mkdir()
    (pasta / "resources" / "profiles" / "Anycubic" / "filament").mkdir(parents=True)
    return pasta


class TestOrcaSlicer(unittest.TestCase):
    def setUp(self):
        self.pasta = instalacao_linux(Path(tempfile.mkdtemp()) / "orcaslicer", "orca-slicer")
        self.ambiente = os.environ.get("CONVERSOR3MF_SLICER")
        os.environ["CONVERSOR3MF_SLICER"] = str(self.pasta)

    def tearDown(self):
        if self.ambiente is None:
            os.environ.pop("CONVERSOR3MF_SLICER", None)
        else:
            os.environ["CONVERSOR3MF_SLICER"] = self.ambiente

    def test_acha_a_instalacao_e_os_perfis(self):
        executavel = config.executavel_slicer()
        self.assertEqual(executavel, self.pasta / "bin" / "orca-slicer")
        self.assertTrue(config.eh_orca(executavel))
        self.assertEqual(config.pasta_perfis(), self.pasta / "resources" / "profiles" / "Anycubic")

    def test_verificar_usa_pasta_de_dados_temporaria(self):
        from conversor3mf import verificar as modulo
        from conversor3mf.projeto import Projeto

        uma_placa = Projeto(Path("x.3mf"), "?", {}, "", [], {}, {1: ["2"]}, False)
        falhou = subprocess.CompletedProcess([], 1, "", "")
        with mock.patch.object(modulo, "ler_projeto", return_value=uma_placa), \
                mock.patch.object(modulo.subprocess, "run", return_value=falhou) as rodar:
            modulo.verificar("x.3mf")
        argumentos = rodar.call_args.args[0]
        self.assertEqual(argumentos[0], str(self.pasta / "bin" / "orca-slicer"))
        datadir = argumentos[argumentos.index("--datadir") + 1]
        self.assertEqual(Path(datadir).parent, Path(rodar.call_args.kwargs["cwd"]))
        self.assertIn("--allow-newer-file", argumentos)

    def test_anycubic_nao_e_orca(self):
        self.assertFalse(config.eh_orca(Path("/opt/AnycubicSlicerNext/bin/AnycubicSlicerNext")))
        self.assertFalse(config.eh_orca(Path("C:/Program Files/AnycubicSlicerNext/AnycubicSlicerNext.exe")))


class TestSlicerNoLinux(unittest.TestCase):
    def setUp(self):
        self.pasta = instalacao_linux(Path(tempfile.mkdtemp()) / "AnycubicSlicerNext")
        self.ambiente = os.environ.get("CONVERSOR3MF_SLICER")

    def tearDown(self):
        if self.ambiente is None:
            os.environ.pop("CONVERSOR3MF_SLICER", None)
        else:
            os.environ["CONVERSOR3MF_SLICER"] = self.ambiente

    def conferir(self):
        self.assertEqual(config.pasta_slicer(), self.pasta)
        self.assertEqual(config.executavel_slicer(), self.pasta / "bin" / "AnycubicSlicerNext")
        self.assertEqual(config.pasta_perfis(), self.pasta / "resources" / "profiles" / "Anycubic")

    def test_pasta_indicada(self):
        os.environ["CONVERSOR3MF_SLICER"] = str(self.pasta)
        self.conferir()

    def test_executavel_indicado(self):
        os.environ["CONVERSOR3MF_SLICER"] = str(self.pasta / "bin" / "AnycubicSlicerNext")
        self.conferir()

    def test_pasta_padrao_do_linux(self):
        os.environ.pop("CONVERSOR3MF_SLICER", None)
        with mock.patch.object(config.sys, "platform", "linux"), \
                mock.patch.object(config, "PASTAS_LINUX", (self.pasta,)):
            self.conferir()

    def test_nenhum_desliga_o_slicer(self):
        os.environ["CONVERSOR3MF_SLICER"] = "nenhum"
        self.assertIsNone(config.pasta_slicer())
        self.assertIsNone(config.pasta_perfis())

    def test_ambiente_para_rodar_no_linux(self):
        executavel = self.pasta / "bin" / "AnycubicSlicerNext"
        with mock.patch.object(config.sys, "platform", "linux"), \
                mock.patch.dict(os.environ, {"LD_LIBRARY_PATH": "/outra", "LC_NUMERIC": "pt_BR.UTF-8"}):
            ambiente = config.ambiente_slicer(executavel)
        self.assertEqual(ambiente["LD_LIBRARY_PATH"], f"{self.pasta / 'lib'}{os.pathsep}/outra")
        self.assertEqual(ambiente["LC_NUMERIC"], "C")
        for sistema in ("win32", "darwin"):
            with mock.patch.object(config.sys, "platform", sistema):
                self.assertIsNone(config.ambiente_slicer(executavel))

    def test_verificar_roda_o_slicer_com_esse_ambiente(self):
        from conversor3mf import verificar as modulo
        from conversor3mf.projeto import Projeto

        executavel = self.pasta / "bin" / "AnycubicSlicerNext"
        uma_placa = Projeto(Path("x.3mf"), "?", {}, "", [], {}, {1: ["2"]}, False)
        falhou = subprocess.CompletedProcess([], 1, "", "")
        with mock.patch.object(modulo.config, "executavel_slicer", return_value=executavel), \
                mock.patch.object(modulo, "ler_projeto", return_value=uma_placa), \
                mock.patch.object(modulo.config, "ambiente_slicer", return_value={"LC_NUMERIC": "C"}), \
                mock.patch.object(modulo.subprocess, "run", return_value=falhou) as rodar:
            r = modulo.verificar("x.3mf")
        self.assertFalse(r["ok"])
        self.assertEqual(rodar.call_args.args[0][0], str(executavel))
        self.assertEqual(rodar.call_args.kwargs["env"], {"LC_NUMERIC": "C"})


if __name__ == "__main__":
    unittest.main()
