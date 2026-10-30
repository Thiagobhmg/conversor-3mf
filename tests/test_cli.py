import contextlib
import io
import os
import unittest

from conversor3mf.__main__ import montar_parser
from conversor3mf.idiomas import detectar, vista_interna


class TestIdiomas(unittest.TestCase):
    def setUp(self):
        self.ambiente = os.environ.pop("CONVERSOR3MF_IDIOMA", None)

    def tearDown(self):
        if self.ambiente is not None:
            os.environ["CONVERSOR3MF_IDIOMA"] = self.ambiente

    def test_mesmo_comando_nas_tres_linguas(self):
        for argv in (
            ["converter", "a.3mf", "--mapa", "1=3", "--saida", "b.3mf", "--sem-verificar"],
            ["convert", "a.3mf", "--map", "1=3", "--output", "b.3mf", "--no-verify"],
            ["convertir", "a.3mf", "--mapa", "1=3", "--salida", "b.3mf", "--sin-verificar"],
        ):
            for idioma in ("pt", "en", "es"):
                a = montar_parser(idioma).parse_args(argv)
                self.assertEqual((a.comando, a.arquivo, a.mapa, a.saida, a.sem_verificar),
                                 ("converter", "a.3mf", "1=3", "b.3mf", True), (argv, idioma))

    def test_ace_e_vistas(self):
        p = montar_parser("pt")
        a = p.parse_args(["ace", "ranura", "4", "--color", "#FFD700", "--nombre", "oro"])
        self.assertEqual((a.comando, a.acao, a.numero, a.cor, a.nome), ("ace", "slot", 4, "#FFD700", "oro"))
        self.assertEqual(p.parse_args(["ace", "setup", "x.3mf"]).acao, "definir")
        for valor, interna in (("top", "cima"), ("arriba", "cima"), ("atrás", "tras"), ("right", "direita")):
            self.assertEqual(p.parse_args(["islands", "x.3mf", "--view", valor]).vista, interna)
        self.assertIsNone(vista_interna("diagonal"))

    def test_idioma_detectado(self):
        self.assertEqual(detectar(["--language", "es", "converter", "x"]), "es")
        self.assertEqual(detectar(["islands", "x"]), "en")
        self.assertEqual(detectar(["convertir", "x"]), "es")
        self.assertEqual(detectar(["converter", "x", "--sem-verificar"]), "pt")

    def test_ajuda_em_cada_lingua(self):
        esperado = {"pt": "mostra esta ajuda", "en": "show this help", "es": "muestra esta ayuda"}
        for idioma, trecho in esperado.items():
            saida = io.StringIO()
            with contextlib.redirect_stdout(saida), self.assertRaises(SystemExit):
                montar_parser(idioma).parse_args(["--help"])
            self.assertIn(trecho, saida.getvalue())


if __name__ == "__main__":
    unittest.main()
