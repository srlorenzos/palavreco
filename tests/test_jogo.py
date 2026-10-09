import unittest

from palavreco.jogo import (
    CERTA,
    ERRADA,
    JOGANDO,
    LUGAR,
    PERDEU,
    VENCEU,
    ChuteInvalido,
    Partida,
    avaliar,
    compartilhar,
    normalizar,
)

C, L, E = CERTA, LUGAR, ERRADA


class TestAvaliar(unittest.TestCase):
    def test_tudo_certo(self):
        self.assertEqual(avaliar("TERMO", "TERMO"), [C] * 5)

    def test_tudo_errado(self):
        self.assertEqual(avaliar("MUITO", "FALAR"), [E] * 5)

    def test_letras_no_lugar_errado(self):
        self.assertEqual(avaliar("OTMRE", "TERMO"), [L] * 5)

    def test_repetida_so_uma_vale(self):
        # BALAO tem dois A: AALAA acerta o A da posição 2 (índice 1)? Não:
        # B A L A O / A A L A A -> A(1)=A certa, L certa, A(3) certa, A(0) e A(4) erradas
        self.assertEqual(avaliar("AALAA", "BALAO"), [E, C, C, C, E])

    def test_repetida_fora_do_lugar_usa_estoque(self):
        # segredo com um único A: só o primeiro A fora do lugar é amarelo
        self.assertEqual(avaliar("AAXXX", "XXXXA"), [L, E, C, C, L])

    def test_certa_tem_prioridade_sobre_lugar(self):
        # ARARA vs CARRO: só o R da posição 3 é certo; A e R(1) usam o estoque
        self.assertEqual(avaliar("ARARA", "CARRO"), [L, L, E, C, E])

    def test_duas_letras_repetidas_amarelas(self):
        # ABACO tem dois A: o A da posição 2 é certo, o da 1 vira lugar
        self.assertEqual(avaliar("CAAXX", "ABACO"), [L, L, C, E, E])

    def test_letra_extra_no_chute(self):
        self.assertEqual(avaliar("EEEXX", "TERMO"), [E, C, E, E, E])

    def test_ignora_acentos(self):
        self.assertEqual(avaliar("balao", "BALÃO"), [C] * 5)
        self.assertEqual(avaliar("BALÃO", "balao"), [C] * 5)

    def test_tamanhos_diferentes(self):
        with self.assertRaises(ValueError):
            avaliar("CASA", "BALAO")


class TestNormalizar(unittest.TestCase):
    def test_remove_acentos(self):
        self.assertEqual(normalizar("Ação"), "ACAO")
        self.assertEqual(normalizar("maçã"), "MACA")
        self.assertEqual(normalizar("herói"), "HEROI")

    def test_espacos(self):
        self.assertEqual(normalizar("  casa "), "CASA")


class TestPartida(unittest.TestCase):
    VALIDAS = ["BALÃO", "TERMO", "MUNDO", "FALAR", "CARRO", "HOTEL", "LIVRO"]

    def nova(self, segredo="BALÃO"):
        return Partida(segredo, self.VALIDAS)

    def test_vitoria(self):
        p = self.nova()
        self.assertEqual(p.estado, JOGANDO)
        p.chutar("termo")
        self.assertEqual(p.estado, JOGANDO)
        p.chutar("balao")  # sem acento
        self.assertEqual(p.estado, VENCEU)
        self.assertTrue(p.terminou)
        self.assertEqual(p.tentativas_usadas, 2)
        self.assertEqual(p.segredo, "BALÃO")  # revelada com acento

    def test_derrota_apos_seis(self):
        p = self.nova()
        for _ in range(6):
            self.assertEqual(p.estado, JOGANDO)
            p.chutar("TERMO")
        self.assertEqual(p.estado, PERDEU)

    def test_nao_aceita_chute_depois_do_fim(self):
        p = self.nova()
        p.chutar("balao")
        with self.assertRaises(ChuteInvalido):
            p.chutar("termo")
        self.assertEqual(p.tentativas_usadas, 1)

    def test_chute_invalido_nao_consome_tentativa(self):
        p = self.nova()
        for ruim in ("zzzzz", "casa", "termos", "12345", "te rm"):
            with self.assertRaises(ChuteInvalido):
                p.chutar(ruim)
        self.assertEqual(p.tentativas_usadas, 0)
        self.assertEqual(p.teclado, {})

    def test_mensagens(self):
        p = self.nova()
        with self.assertRaisesRegex(ChuteInvalido, "não existe"):
            p.chutar("zzzzz")
        with self.assertRaisesRegex(ChuteInvalido, "Faltam"):
            p.chutar("ab")

    def test_teclado_guarda_melhor_status(self):
        p = Partida("BALÃO", ["BALÃO", "CARRO", "OBRAS"])
        p.chutar("carro")  # A e O certas; C e R erradas
        self.assertEqual(p.teclado["C"], ERRADA)
        self.assertEqual(p.teclado["R"], ERRADA)
        self.assertEqual(p.teclado["A"], CERTA)
        self.assertEqual(p.teclado["O"], CERTA)
        p.chutar("obras")  # O vira "lugar" nesse chute, mas o teclado mantém CERTA
        self.assertEqual(p.teclado["O"], CERTA)
        self.assertEqual(p.teclado["B"], LUGAR)
        self.assertNotIn("Z", p.teclado)
        p.chutar("balao")
        self.assertEqual(p.teclado["B"], CERTA)

    def test_teclado_nunca_rebaixa(self):
        p = Partida("BALÃO", ["BALÃO", "OBRAS"])
        p.chutar("balao")  # só para ter certas; já termina
        self.assertEqual(p.teclado["B"], CERTA)

    def test_sem_lista_aceita_qualquer_cinco_letras(self):
        p = Partida("BALÃO")
        p.chutar("zzzzz")
        self.assertEqual(p.tentativas_usadas, 1)

    def test_segredo_tamanho_errado(self):
        with self.assertRaises(ValueError):
            Partida("casa")


class TestCompartilhar(unittest.TestCase):
    def test_vitoria(self):
        p = Partida("TERMO", ["TERMO", "MUNDO"])
        p.chutar("mundo")
        p.chutar("termo")
        texto = compartilhar(p, "Palavreco #123")
        linhas = texto.splitlines()
        self.assertEqual(linhas[0], "Palavreco #123 2/6")
        self.assertEqual(linhas[-1], "🟩🟩🟩🟩🟩")
        self.assertEqual(len(linhas), 4)

    def test_derrota(self):
        p = Partida("TERMO", ["TERMO", "MUNDO"])
        for _ in range(6):
            p.chutar("mundo")
        self.assertTrue(compartilhar(p, "Palavreco #7").startswith("Palavreco #7 X/6"))

    def test_alto_contraste(self):
        p = Partida("TERMO", ["TERMO", "OTMRE"])
        p.chutar("otmre")
        self.assertIn("🟦", compartilhar(p, "x", alto_contraste=True))
        self.assertNotIn("🟨", compartilhar(p, "x", alto_contraste=True))


if __name__ == "__main__":
    unittest.main()
