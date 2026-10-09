"""Ponto de entrada: python -m palavreco [--livre]."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(
        prog="palavreco", description="Adivinhe a palavra de 5 letras."
    )
    analisador.add_argument(
        "--livre", action="store_true", help="palavra aleatória em vez da palavra do dia"
    )
    analisador.add_argument("--smoke", action="store_true", help=argparse.SUPPRESS)
    args = analisador.parse_args(argv)

    try:
        from .interface import iniciar
    except ImportError as erro:  # tkinter ausente (alguns Linux)
        print(f"Não foi possível carregar o tkinter: {erro}", file=sys.stderr)
        return 1
    iniciar(livre=args.livre, smoke=args.smoke)
    return 0


if __name__ == "__main__":
    sys.exit(main())
