import random
import unittest
from datetime import date, timedelta

from palavreco.jogo import normalizar
from palavreco.palavras import (
    DATA_BASE,
    PALAVRAS,
    numero_do_dia,
    palavra_aleatoria,
    palavra_do_dia,
)


class TestLista(unittest.TestCase):
    def test_tamanho_minimo(self):
        self.assertGreaterEqual(len(PALAVRAS), 400)

    def test_todas_com_cinco_letras(self):
        for p in PALAVRAS:
            self.assertEqual(len(normalizar(p)), 5, p)
            self.assertTrue(normalizar(p).isalpha(), p)

    def test_sem_duplicatas(self):
        normalizadas = [normalizar(p) for p in PALAVRAS]
        self.assertEqual(len(normalizadas), len(set(normalizadas)))

    def test_em_minusculas_sem_espacos(self):
        for p in PALAVRAS:
            self.assertEqual(p, p.strip().lower(), p)


class TestPalavraDoDia(unittest.TestCase):
    def test_mesma_data_mesma_palavra(self):
        d = date(2025, 5, 17)
        self.assertEqual(palavra_do_dia(d), palavra_do_dia(date(2025, 5, 17)))

    def test_numero_do_dia(self):
        self.assertEqual(numero_do_dia(DATA_BASE), 1)
        self.assertEqual(numero_do_dia(DATA_BASE + timedelta(days=122)), 123)

    def test_dias_seguidos_diferem(self):
        palavras = {palavra_do_dia(DATA_BASE + timedelta(days=i)) for i in range(30)}
        self.assertEqual(len(palavras), 30)

    def test_percorre_a_lista_inteira_sem_repetir(self):
        n = len(PALAVRAS)
        vistas = {palavra_do_dia(DATA_BASE + timedelta(days=i)) for i in range(n)}
        self.assertEqual(len(vistas), n)
        self.assertEqual(
            palavra_do_dia(DATA_BASE), palavra_do_dia(DATA_BASE + timedelta(days=n))
        )

    def test_palavra_pertence_a_lista(self):
        self.assertIn(palavra_do_dia(date(2030, 1, 1)), PALAVRAS)

    def test_aleatoria_usa_rng(self):
        a = palavra_aleatoria(random.Random(1))
        b = palavra_aleatoria(random.Random(1))
        self.assertEqual(a, b)
        self.assertIn(a, PALAVRAS)


if __name__ == "__main__":
    unittest.main()
