"""Lógica pura do jogo (sem tkinter)."""

from __future__ import annotations

import unicodedata
from collections import Counter
from collections.abc import Iterable

TAMANHO = 5
MAX_TENTATIVAS = 6

CERTA = "certa"      # letra certa no lugar certo
LUGAR = "lugar"      # a letra existe, mas em outra posição
ERRADA = "errada"    # a letra não existe (ou já foi usada nas outras)

_PRIORIDADE = {ERRADA: 1, LUGAR: 2, CERTA: 3}

JOGANDO = "jogando"
VENCEU = "venceu"
PERDEU = "perdeu"

_EMOJIS = {
    False: {CERTA: "🟩", LUGAR: "🟨", ERRADA: "⬛"},
    True: {CERTA: "🟧", LUGAR: "🟦", ERRADA: "⬛"},  # alto contraste
}


class ChuteInvalido(ValueError):
    """Chute que não conta como tentativa (tamanho errado, não existe...)."""


def normalizar(texto: str) -> str:
    """Remove acentos e passa para maiúsculas: 'Balão' -> 'BALAO'."""
    decomposto = unicodedata.normalize("NFD", texto.strip())
    sem_marcas = "".join(c for c in decomposto if unicodedata.category(c) != "Mn")
    return sem_marcas.upper()


def avaliar(chute: str, segredo: str) -> list[str]:
    """Avalia o chute letra a letra, tratando letras repetidas.

    Primeiro marcam-se as certas; depois cada letra fora do lugar só vale
    enquanto ainda sobrar aquela letra no segredo.
    """
    chute, segredo = normalizar(chute), normalizar(segredo)
    if len(chute) != len(segredo):
        raise ValueError("chute e segredo precisam ter o mesmo tamanho")
    resultado = [ERRADA] * len(chute)
    restantes: Counter[str] = Counter()
    for i, (c, s) in enumerate(zip(chute, segredo)):
        if c == s:
            resultado[i] = CERTA
        else:
            restantes[s] += 1
    for i, c in enumerate(chute):
        if resultado[i] == CERTA:
            continue
        if restantes[c] > 0:
            resultado[i] = LUGAR
            restantes[c] -= 1
    return resultado


class Partida:
    """Uma partida: segredo, tentativas, estado e teclado."""

    def __init__(
        self,
        segredo: str,
        palavras_validas: Iterable[str] | None = None,
        max_tentativas: int = MAX_TENTATIVAS,
    ) -> None:
        self.segredo = segredo  # com acento, para revelar
        self._segredo_norm = normalizar(segredo)
        if len(self._segredo_norm) != TAMANHO:
            raise ValueError(f"o segredo precisa ter {TAMANHO} letras")
        self.max_tentativas = max_tentativas
        self._validas = (
            None if palavras_validas is None else {normalizar(p) for p in palavras_validas}
        )
        self.chutes: list[str] = []                 # normalizados
        self.resultados: list[list[str]] = []
        self.teclado: dict[str, str] = {}

    @property
    def tentativas_usadas(self) -> int:
        return len(self.chutes)

    @property
    def estado(self) -> str:
        if self.chutes and self.chutes[-1] == self._segredo_norm:
            return VENCEU
        if len(self.chutes) >= self.max_tentativas:
            return PERDEU
        return JOGANDO

    @property
    def terminou(self) -> bool:
        return self.estado != JOGANDO

    def validar(self, chute: str) -> str:
        """Devolve o chute normalizado ou levanta ChuteInvalido."""
        if self.terminou:
            raise ChuteInvalido("A partida já terminou")
        norm = normalizar(chute)
        if len(norm) < TAMANHO:
            raise ChuteInvalido("Faltam letras")
        if len(norm) > TAMANHO or not norm.isalpha() or not norm.isascii():
            raise ChuteInvalido("Palavra inválida")
        if self._validas is not None and norm not in self._validas:
            raise ChuteInvalido("Palavra não existe")
        return norm

    def chutar(self, chute: str) -> list[str]:
        """Registra o chute e devolve o resultado por letra.

        Chute inválido levanta ChuteInvalido e NÃO consome tentativa.
        """
        norm = self.validar(chute)
        resultado = avaliar(norm, self._segredo_norm)
        self.chutes.append(norm)
        self.resultados.append(resultado)
        for letra, status in zip(norm, resultado):
            if _PRIORIDADE[status] > _PRIORIDADE.get(self.teclado.get(letra, ""), 0):
                self.teclado[letra] = status
        return resultado


def compartilhar(partida: Partida, titulo: str, alto_contraste: bool = False) -> str:
    """Texto para copiar: 'Palavreco #123 4/6' + grade de emojis."""
    if partida.estado == VENCEU:
        placar = f"{partida.tentativas_usadas}/{partida.max_tentativas}"
    else:
        placar = f"X/{partida.max_tentativas}"
    emojis = _EMOJIS[alto_contraste]
    linhas = ["".join(emojis[s] for s in r) for r in partida.resultados]
    return "\n".join([f"{titulo} {placar}", "", *linhas])
