"""Estatísticas salvas em ~/.palavreco/estatisticas.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CAMINHO_PADRAO = Path.home() / ".palavreco" / "estatisticas.json"
MAX_TENTATIVAS = 6


def _inteiro(valor: Any, padrao: int = 0) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
        return padrao
    return valor


class Estatisticas:
    def __init__(self, caminho: Path | str | None = None) -> None:
        self.caminho = Path(caminho) if caminho is not None else CAMINHO_PADRAO
        self.jogos = 0
        self.vitorias = 0
        self.sequencia = 0
        self.melhor_sequencia = 0
        self.distribuicao = {str(i): 0 for i in range(1, MAX_TENTATIVAS + 1)}
        self.ultimo_dia: int | None = None  # última palavra do dia jogada
        self.preferencias: dict[str, Any] = {}
        self.carregar()

    @property
    def percentual_vitorias(self) -> int:
        return round(100 * self.vitorias / self.jogos) if self.jogos else 0

    def carregar(self) -> None:
        """Lê o arquivo; ausente ou corrompido vira estatística zerada."""
        try:
            dados = json.loads(self.caminho.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if not isinstance(dados, dict):
            return
        self.jogos = _inteiro(dados.get("jogos"))
        self.vitorias = min(_inteiro(dados.get("vitorias")), self.jogos)
        self.sequencia = _inteiro(dados.get("sequencia"))
        self.melhor_sequencia = max(_inteiro(dados.get("melhor_sequencia")), self.sequencia)
        dist = dados.get("distribuicao")
        if isinstance(dist, dict):
            for chave in self.distribuicao:
                self.distribuicao[chave] = _inteiro(dist.get(chave))
        ultimo = dados.get("ultimo_dia")
        valido = isinstance(ultimo, int) and not isinstance(ultimo, bool)
        self.ultimo_dia = ultimo if valido else None
        prefs = dados.get("preferencias")
        self.preferencias = prefs if isinstance(prefs, dict) else {}

    def salvar(self) -> bool:
        """Grava o JSON. Devolve False se não conseguiu (o jogo segue)."""
        dados = {
            "jogos": self.jogos,
            "vitorias": self.vitorias,
            "sequencia": self.sequencia,
            "melhor_sequencia": self.melhor_sequencia,
            "distribuicao": self.distribuicao,
            "ultimo_dia": self.ultimo_dia,
            "preferencias": self.preferencias,
        }
        try:
            self.caminho.parent.mkdir(parents=True, exist_ok=True)
            temporario = self.caminho.with_suffix(".tmp")
            temporario.write_text(
                json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            temporario.replace(self.caminho)
        except OSError:
            return False
        return True

    def registrar(self, venceu: bool, tentativas: int, dia: int | None = None) -> None:
        """Soma uma partida. `dia` marca a palavra do dia como já jogada."""
        self.jogos += 1
        if venceu:
            self.vitorias += 1
            self.sequencia += 1
            self.melhor_sequencia = max(self.melhor_sequencia, self.sequencia)
            chave = str(tentativas)
            if chave in self.distribuicao:
                self.distribuicao[chave] += 1
        else:
            self.sequencia = 0
        if dia is not None:
            self.ultimo_dia = dia
        self.salvar()

    def definir_preferencia(self, chave: str, valor: Any) -> None:
        self.preferencias[chave] = valor
        self.salvar()
