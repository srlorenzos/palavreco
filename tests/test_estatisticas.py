import json
import tempfile
import unittest
from pathlib import Path

from palavreco.estatisticas import Estatisticas


class TestEstatisticas(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.caminho = Path(self._tmp.name) / "sub" / "estatisticas.json"

    def test_arquivo_ausente_comeca_zerado(self):
        e = Estatisticas(self.caminho)
        self.assertEqual((e.jogos, e.vitorias, e.sequencia, e.melhor_sequencia), (0, 0, 0, 0))
        self.assertEqual(e.percentual_vitorias, 0)
        self.assertEqual(sum(e.distribuicao.values()), 0)

    def test_registrar_vitorias_e_derrota(self):
        e = Estatisticas(self.caminho)
        e.registrar(True, 3)
        e.registrar(True, 4)
        e.registrar(True, 3)
        self.assertEqual(e.sequencia, 3)
        e.registrar(False, 6)
        self.assertEqual(e.sequencia, 0)
        self.assertEqual(e.melhor_sequencia, 3)
        self.assertEqual((e.jogos, e.vitorias), (4, 3))
        self.assertEqual(e.percentual_vitorias, 75)
        self.assertEqual(e.distribuicao["3"], 2)
        self.assertEqual(e.distribuicao["4"], 1)

    def test_persistencia(self):
        e = Estatisticas(self.caminho)
        e.registrar(True, 2, dia=10)
        e.definir_preferencia("tema", "claro")
        outra = Estatisticas(self.caminho)
        self.assertEqual(outra.jogos, 1)
        self.assertEqual(outra.distribuicao["2"], 1)
        self.assertEqual(outra.ultimo_dia, 10)
        self.assertEqual(outra.preferencias["tema"], "claro")

    def test_arquivo_corrompido(self):
        self.caminho.parent.mkdir(parents=True)
        self.caminho.write_text("{isto não é json", encoding="utf-8")
        e = Estatisticas(self.caminho)
        self.assertEqual(e.jogos, 0)
        e.registrar(True, 1)  # sobrescreve com dados válidos
        self.assertEqual(Estatisticas(self.caminho).jogos, 1)

    def test_json_com_tipos_errados(self):
        self.caminho.parent.mkdir(parents=True)
        self.caminho.write_text(
            json.dumps({"jogos": "x", "vitorias": -3, "sequencia": 2.5,
                        "distribuicao": {"1": "a", "2": 4}, "ultimo_dia": "hoje"}),
            encoding="utf-8",
        )
        e = Estatisticas(self.caminho)
        self.assertEqual((e.jogos, e.vitorias, e.sequencia), (0, 0, 0))
        self.assertEqual(e.distribuicao["1"], 0)
        self.assertEqual(e.distribuicao["2"], 4)
        self.assertIsNone(e.ultimo_dia)

    def test_json_que_nao_e_objeto(self):
        self.caminho.parent.mkdir(parents=True)
        self.caminho.write_text("[1, 2, 3]", encoding="utf-8")
        self.assertEqual(Estatisticas(self.caminho).jogos, 0)

    def test_nao_toca_no_home_real(self):
        e = Estatisticas(self.caminho)
        e.registrar(False, 6)
        self.assertTrue(self.caminho.exists())
        self.assertEqual(e.caminho, self.caminho)


if __name__ == "__main__":
    unittest.main()
