import unittest

from conversor3mf import pintura


class TestPintura(unittest.TestCase):
    def test_folha_simples(self):
        # estados 1 e 2 cabem em um nibble; 0 = "usa a cor da peça"
        for estado in (0, 1, 2):
            texto = pintura.codificar([("folha", estado)])
            self.assertEqual(pintura.decodificar(texto), [("folha", estado)])

    def test_estados_estendidos(self):
        for estado in (3, 4, 10, 17, 18, 20, 32):
            texto = pintura.codificar([("folha", estado)])
            self.assertEqual(pintura.decodificar(texto), [("folha", estado)])

    def test_arvore_e_remapeamento(self):
        nos = [("divisao", 0b0111), ("folha", 1), ("folha", 0), ("folha", 4), ("folha", 2)]
        texto = pintura.codificar(nos)
        self.assertEqual(pintura.decodificar(texto), nos)
        trocado = pintura.remapear(texto, {1: 3, 4: 1, 2: 20})
        self.assertEqual(
            pintura.decodificar(trocado),
            [("divisao", 0b0111), ("folha", 3), ("folha", 0), ("folha", 1), ("folha", 20)],
        )

    def test_exemplos_reais(self):
        # strings tiradas de projetos do Bambu Studio baixados do MakerWorld
        exemplos = {
            "4": {1: 1},
            "8": {2: 1},
            "0C": {3: 1},
            "4C": {7: 1},
            "00C0C2": {3: 2, 0: 1},
            "0C00C102": {0: 2, 3: 2},
        }
        for texto, esperado in exemplos.items():
            self.assertEqual(dict(pintura.estados(texto)), esperado, texto)
            self.assertEqual(pintura.codificar(pintura.decodificar(texto)), texto)

    def test_string_invalida(self):
        with self.assertRaises(pintura.PinturaInvalida):
            pintura.decodificar("3")  # nó dividido sem filhos


if __name__ == "__main__":
    unittest.main()
