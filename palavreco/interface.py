"""Interface gráfica (tkinter). Toda a regra do jogo vive em jogo.py."""

from __future__ import annotations

import sys
import tempfile
import tkinter as tk
from pathlib import Path

from .estatisticas import Estatisticas
from .jogo import (
    CERTA,
    ERRADA,
    LUGAR,
    MAX_TENTATIVAS,
    PERDEU,
    TAMANHO,
    VENCEU,
    ChuteInvalido,
    Partida,
    compartilhar,
    normalizar,
)
from .palavras import PALAVRAS, numero_do_dia, palavra_aleatoria, palavra_do_dia

FONTE = "Segoe UI" if sys.platform == "win32" else "Helvetica"

PECA = 62
ESPACO = 6
MARGEM = 8
LARGURA_TABULEIRO = TAMANHO * PECA + (TAMANHO - 1) * ESPACO + 2 * MARGEM
ALTURA_TABULEIRO = MAX_TENTATIVAS * PECA + (MAX_TENTATIVAS - 1) * ESPACO + 2 * MARGEM

TECLA_L = 34
TECLA_L_LARGA = 56
TECLA_A = 48
TECLA_ESPACO = 5
LINHAS_TECLADO = ("QWERTYUIOP", "ASDFGHJKL", "#ZXCVBNM<")  # # = ENTER, < = apagar

PASSOS_VIRADA = 7          # quadros por metade da virada
INTERVALO_QUADRO = 18      # ms
ATRASO_ENTRE_PECAS = 230   # ms

TEMAS = {
    "escuro": {
        "fundo": "#121213", "texto": "#f2f2f2", "sutil": "#9a9aa0",
        "painel": "#1e1e20", "borda": "#3a3a3c", "borda_ativa": "#818384",
        "tecla": "#565758", "tecla_texto": "#ffffff", "errada": "#2c2c2e",
        "toast_fundo": "#f2f2f2", "toast_texto": "#121213",
    },
    "claro": {
        "fundo": "#fafafa", "texto": "#1a1a1b", "sutil": "#6b6b70",
        "painel": "#ffffff", "borda": "#d3d6da", "borda_ativa": "#878a8c",
        "tecla": "#c9ccd0", "tecla_texto": "#1a1a1b", "errada": "#787c7e",
        "toast_fundo": "#1a1a1b", "toast_texto": "#fafafa",
    },
}

# (cor da peça, cor do texto sobre ela)
CORES_STATUS = {
    False: {CERTA: ("#538d4e", "#ffffff"), LUGAR: ("#b59f3b", "#ffffff")},
    True: {CERTA: ("#f5793a", "#ffffff"), LUGAR: ("#85c0f9", "#101010")},
}

ELOGIOS = ("Genial!", "Magnífico!", "Impressionante!", "Muito bem!", "Boa!", "Ufa!")


def _rgb(cor: str) -> tuple[int, int, int]:
    return int(cor[1:3], 16), int(cor[3:5], 16), int(cor[5:7], 16)


def misturar(cor: str, outra: str, t: float) -> str:
    """Mistura `cor` com `outra` (t=0 só cor, t=1 só outra)."""
    a, b = _rgb(cor), _rgb(outra)
    r, g, bl = (round(x + (y - x) * t) for x, y in zip(a, b))
    return f"#{r:02x}{g:02x}{bl:02x}"


def _pontos_arredondados(x1: float, y1: float, x2: float, y2: float, r: float) -> list[float]:
    r = max(0.0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    return [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
        x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]


class App:
    def __init__(
        self,
        root: tk.Tk,
        livre: bool = False,
        estatisticas: Estatisticas | None = None,
    ) -> None:
        self.root = root
        self.est = estatisticas or Estatisticas()
        self.tema = self.est.preferencias.get("tema", "escuro")
        if self.tema not in TEMAS:
            self.tema = "escuro"
        self.alto_contraste = bool(self.est.preferencias.get("alto_contraste", False))
        self.erros: list[BaseException] = []

        self.ocupado = False
        self.toast_id: str | None = None
        self.toast: tk.Label | None = None
        self.janela_stats: tk.Toplevel | None = None
        self.tecla_hover: str | None = None
        self.digitado = ""
        self.livre = livre
        self.aviso_inicial: str | None = None
        if not livre and self.est.ultimo_dia == numero_do_dia():
            self.livre = True
            self.aviso_inicial = "Você já jogou a palavra de hoje. Modo livre!"

        root.title("Palavreco")
        root.resizable(False, False)
        self._montar_widgets()
        self._nova_partida()
        self._aplicar_tema()
        self._centralizar()

        root.bind("<Key>", self._ao_teclar)
        if self.aviso_inicial:
            root.after(300, lambda: self.mostrar_toast(self.aviso_inicial or "", 3000))

    # ------------------------------------------------------------------ UI
    def _montar_widgets(self) -> None:
        self.cabecalho = tk.Frame(self.root)
        self.cabecalho.pack(fill="x", padx=14, pady=(10, 0))
        self.titulo = tk.Label(self.cabecalho, text="PALAVRECO", font=(FONTE, 20, "bold"))
        self.titulo.pack(side="left")
        self.botoes: list[tk.Label] = []
        for texto, comando, dica in (
            ("▦", self.mostrar_estatisticas, "Estatísticas (F4)"),
            ("◐", self.alternar_contraste, "Alto contraste (F3)"),
            ("☀", self.alternar_tema, "Tema claro/escuro (F2)"),
        ):
            botao = tk.Label(self.cabecalho, text=texto, font=("Segoe UI Symbol", 16), padx=8)
            botao.pack(side="right")
            botao.bind("<Button-1>", lambda _e, c=comando: c())
            botao.bind("<Enter>", lambda _e, b=botao: b.config(cursor="hand2", fg=self._t("texto")))
            botao.bind("<Leave>", lambda _e, b=botao: b.config(cursor="", fg=self._t("sutil")))
            self.botoes.append(botao)
            _ = dica
        self.botao_tema = self.botoes[2]

        self.subtitulo = tk.Label(self.root, font=(FONTE, 10))
        self.subtitulo.pack(pady=(0, 2))

        self.tabuleiro = tk.Canvas(
            self.root, width=LARGURA_TABULEIRO, height=ALTURA_TABULEIRO, highlightthickness=0
        )
        self.tabuleiro.pack(padx=14)

        largura_teclado = 10 * TECLA_L + 9 * TECLA_ESPACO + 2 * MARGEM
        altura_teclado = 3 * TECLA_A + 2 * TECLA_ESPACO + 2 * MARGEM
        self.teclado = tk.Canvas(
            self.root, width=largura_teclado, height=altura_teclado, highlightthickness=0
        )
        self.teclado.pack(padx=14, pady=(6, 12))

        # peças: poly + texto por célula
        self.itens_peca: list[list[tuple[int, int]]] = []
        for r in range(MAX_TENTATIVAS):
            linha = []
            for c in range(TAMANHO):
                poly = self.tabuleiro.create_polygon(0, 0, 0, 0, smooth=True, width=2)
                texto = self.tabuleiro.create_text(0, 0, font=(FONTE, 26, "bold"))
                linha.append((poly, texto))
            self.itens_peca.append(linha)

        # teclas: guarda geometria
        self.geom_teclas: dict[str, tuple[float, float, float, float]] = {}
        self.itens_tecla: dict[str, tuple[int, int]] = {}
        y = MARGEM
        for linha in LINHAS_TECLADO:
            larguras = [TECLA_L_LARGA if k in "#<" else TECLA_L for k in linha]
            total = sum(larguras) + TECLA_ESPACO * (len(linha) - 1)
            x = (largura_teclado - total) / 2
            for k, w in zip(linha, larguras):
                nome = {"#": "ENTER", "<": "BACK"}.get(k, k)
                self.geom_teclas[nome] = (x, y, x + w, y + TECLA_A)
                tag = f"k_{nome}"
                poly = self.teclado.create_polygon(0, 0, 0, 0, smooth=True, tags=(tag,))
                rotulo = {"ENTER": "ENTER", "BACK": "⌫"}.get(nome, nome)
                tam = 10 if nome == "ENTER" else 14
                texto = self.teclado.create_text(
                    (x + x + w) / 2, y + TECLA_A / 2, text=rotulo,
                    font=(FONTE, tam, "bold"), tags=(tag,),
                )
                self.itens_tecla[nome] = (poly, texto)
                self.teclado.tag_bind(tag, "<Button-1>", lambda _e, n=nome: self._clicou_tecla(n))
                self.teclado.tag_bind(tag, "<Enter>", lambda _e, n=nome: self._hover(n))
                self.teclado.tag_bind(tag, "<Leave>", lambda _e: self._hover(None))
                x += w + TECLA_ESPACO
            y += TECLA_A + TECLA_ESPACO

    def _centralizar(self) -> None:
        self.root.update_idletasks()
        w, h = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = max(0, (self.root.winfo_screenheight() - h) // 3)
        self.root.geometry(f"+{x}+{y}")

    # ---------------------------------------------------------------- cores
    def _t(self, chave: str) -> str:
        return TEMAS[self.tema][chave]

    def _cor_status(self, status: str) -> tuple[str, str]:
        if status == ERRADA:
            return self._t("errada"), "#ffffff"
        return CORES_STATUS[self.alto_contraste][status]

    def _cores_peca(self, estado: str) -> tuple[str, str, str]:
        """(fundo, borda, texto) de uma peça no estado dado."""
        if estado == "vazio":
            return self._t("fundo"), self._t("borda"), self._t("texto")
        if estado == "digitando":
            return self._t("fundo"), self._t("borda_ativa"), self._t("texto")
        fundo, texto = self._cor_status(estado)
        return fundo, fundo, texto

    def _aplicar_tema(self) -> None:
        self.root.configure(bg=self._t("fundo"))
        for w in (self.cabecalho,):
            w.configure(bg=self._t("fundo"))
        self.titulo.configure(bg=self._t("fundo"), fg=self._t("texto"))
        for b in self.botoes:
            b.configure(bg=self._t("fundo"), fg=self._t("sutil"))
        self.botao_tema.configure(text="☀" if self.tema == "escuro" else "☾")
        self.subtitulo.configure(bg=self._t("fundo"), fg=self._t("sutil"))
        self.tabuleiro.configure(bg=self._t("fundo"))
        self.teclado.configure(bg=self._t("fundo"))
        self._redesenhar_tudo()

    def _redesenhar_tudo(self) -> None:
        for r in range(MAX_TENTATIVAS):
            for c in range(TAMANHO):
                self._desenhar_peca(r, c)
        for nome in self.itens_tecla:
            self._desenhar_tecla(nome)

    # --------------------------------------------------------------- peças
    def _centro(self, r: int, c: int) -> tuple[float, float]:
        return (
            MARGEM + c * (PECA + ESPACO) + PECA / 2,
            MARGEM + r * (PECA + ESPACO) + PECA / 2,
        )

    def _desenhar_peca(self, r: int, c: int, sx: float = 1.0, sy: float = 1.0) -> None:
        poly, texto = self.itens_peca[r][c]
        cx, cy = self._centro(r, c)
        meio_l, meio_a = PECA / 2 * sx, max(PECA / 2 * sy, 1.0)
        pontos = _pontos_arredondados(cx - meio_l, cy - meio_a, cx + meio_l, cy + meio_a, 9 * min(sx, sy))
        fundo, borda, cor_texto = self._cores_peca(self.estados[r][c])
        self.tabuleiro.coords(poly, *pontos)
        self.tabuleiro.itemconfigure(poly, fill=fundo, outline=borda)
        self.tabuleiro.coords(texto, cx, cy)
        visivel = sy > 0.3
        self.tabuleiro.itemconfigure(
            texto, text=self.letras[r][c], fill=cor_texto,
            state="normal" if visivel else "hidden",
            font=(FONTE, max(8, round(26 * min(sx, sy) ** 0.5)), "bold"),
        )

    def _pulsar(self, r: int, c: int, quadros: tuple[float, ...] = (1.08, 1.14, 1.08, 1.03, 1.0), i: int = 0) -> None:
        if self.estados[r][c] != "digitando" and i < len(quadros) - 1:
            i = len(quadros) - 1
        s = quadros[i]
        self._desenhar_peca(r, c, s, s)
        if i + 1 < len(quadros):
            self.root.after(28, lambda: self._pulsar(r, c, quadros, i + 1))

    def _virar(self, r: int, c: int, status: str, fim, i: int = 0) -> None:
        n = PASSOS_VIRADA
        if i == n:
            self.estados[r][c] = status
        self._desenhar_peca(r, c, 1.0, max(abs(n - i) / n, 0.04))
        if i < 2 * n:
            self.root.after(INTERVALO_QUADRO, lambda: self._virar(r, c, status, fim, i + 1))
        else:
            self._desenhar_peca(r, c)
            fim()

    def _tremer(self, r: int, linha_pronta, deslocamentos=(-9, 9, -7, 7, -4, 4, 0), i: int = 0, atual: float = 0.0) -> None:
        if i >= len(deslocamentos):
            linha_pronta()
            return
        alvo = deslocamentos[i]
        for c in range(TAMANHO):
            poly, texto = self.itens_peca[r][c]
            self.tabuleiro.move(poly, alvo - atual, 0)
            self.tabuleiro.move(texto, alvo - atual, 0)
        self.root.after(35, lambda: self._tremer(r, linha_pronta, deslocamentos, i + 1, alvo))

    # -------------------------------------------------------------- teclas
    def _desenhar_tecla(self, nome: str) -> None:
        x1, y1, x2, y2 = self.geom_teclas[nome]
        poly, texto = self.itens_tecla[nome]
        status = self.partida.teclado.get(nome) if len(nome) == 1 else None
        if status is None:
            fundo, cor_texto = self._t("tecla"), self._t("tecla_texto")
        else:
            fundo, cor_texto = self._cor_status(status)
        if self.tecla_hover == nome:
            fundo = misturar(fundo, "#ffffff", 0.22)
        self.teclado.coords(poly, *_pontos_arredondados(x1, y1, x2, y2, 8))
        self.teclado.itemconfigure(poly, fill=fundo, outline=fundo)
        self.teclado.itemconfigure(texto, fill=cor_texto)

    def _hover(self, nome: str | None) -> None:
        anterior, self.tecla_hover = self.tecla_hover, nome
        self.teclado.configure(cursor="hand2" if nome else "")
        for n in (anterior, nome):
            if n:
                self._desenhar_tecla(n)

    def _clicou_tecla(self, nome: str) -> None:
        if nome == "ENTER":
            self.confirmar()
        elif nome == "BACK":
            self.apagar()
        else:
            self.digitar(nome)

    def _ao_teclar(self, evento: tk.Event) -> None:
        if evento.state & 0x4:  # Ctrl
            return
        tecla = evento.keysym
        if tecla in ("Return", "KP_Enter"):
            self.confirmar()
        elif tecla == "BackSpace":
            self.apagar()
        elif tecla == "F2":
            self.alternar_tema()
        elif tecla == "F3":
            self.alternar_contraste()
        elif tecla == "F4":
            self.mostrar_estatisticas()
        elif evento.char and evento.char.isalpha():
            letra = normalizar(evento.char)
            if len(letra) == 1 and "A" <= letra <= "Z":
                self.digitar(letra)

    # ---------------------------------------------------------------- jogo
    def _nova_partida(self) -> None:
        segredo = palavra_aleatoria() if self.livre else palavra_do_dia()
        self.partida = Partida(segredo, PALAVRAS)
        self.digitado = ""
        self.estados = [["vazio"] * TAMANHO for _ in range(MAX_TENTATIVAS)]
        self.letras = [[""] * TAMANHO for _ in range(MAX_TENTATIVAS)]
        self.ocupado = False
        self.subtitulo.configure(
            text="Modo livre" if self.livre else f"Palavra do dia #{numero_do_dia()}"
        )
        if hasattr(self, "itens_tecla"):
            self._redesenhar_tudo()

    def novo_jogo_livre(self) -> None:
        self.livre = True
        self._fechar_stats()
        self._nova_partida()

    @property
    def _linha(self) -> int:
        return self.partida.tentativas_usadas

    def digitar(self, letra: str) -> None:
        if self.ocupado or self.partida.terminou or len(self.digitado) >= TAMANHO:
            return
        c = len(self.digitado)
        self.digitado += letra
        self.letras[self._linha][c] = letra
        self.estados[self._linha][c] = "digitando"
        self._desenhar_peca(self._linha, c)
        self._pulsar(self._linha, c)

    def apagar(self) -> None:
        if self.ocupado or self.partida.terminou or not self.digitado:
            return
        c = len(self.digitado) - 1
        self.digitado = self.digitado[:-1]
        self.letras[self._linha][c] = ""
        self.estados[self._linha][c] = "vazio"
        self._desenhar_peca(self._linha, c)

    def confirmar(self) -> None:
        if self.ocupado or self.partida.terminou:
            return
        r = self._linha
        try:
            resultado = self.partida.chutar(self.digitado)
        except ChuteInvalido as erro:
            self.ocupado = True
            self.mostrar_toast(str(erro))
            self._tremer(r, lambda: setattr(self, "ocupado", False))
            return
        self.ocupado = True
        self.digitado = ""
        for c, status in enumerate(resultado):
            ultimo = c == TAMANHO - 1
            fim = self._fim_da_linha if ultimo else (lambda: None)
            self.root.after(
                c * ATRASO_ENTRE_PECAS,
                lambda c=c, s=status, f=fim: self._virar(r, c, s, f),
            )

    def _fim_da_linha(self) -> None:
        for nome in self.itens_tecla:
            self._desenhar_tecla(nome)
        self.ocupado = False
        estado = self.partida.estado
        if estado == VENCEU:
            n = self.partida.tentativas_usadas
            self.mostrar_toast(ELOGIOS[n - 1], 2200)
        elif estado == PERDEU:
            self.mostrar_toast(f"A palavra era {self.partida.segredo.upper()}", 4000)
        else:
            return
        self.est.registrar(
            estado == VENCEU,
            self.partida.tentativas_usadas,
            dia=None if self.livre else numero_do_dia(),
        )
        self.root.after(1300, self.mostrar_estatisticas)

    # --------------------------------------------------------- preferências
    def alternar_tema(self) -> None:
        self.tema = "claro" if self.tema == "escuro" else "escuro"
        self.est.definir_preferencia("tema", self.tema)
        self._aplicar_tema()

    def alternar_contraste(self) -> None:
        self.alto_contraste = not self.alto_contraste
        self.est.definir_preferencia("alto_contraste", self.alto_contraste)
        self.mostrar_toast("Alto contraste " + ("ligado" if self.alto_contraste else "desligado"), 1500)
        self._redesenhar_tudo()
        if self.janela_stats is not None:
            self.mostrar_estatisticas()

    # ---------------------------------------------------------------- toast
    def mostrar_toast(self, mensagem: str, duracao: int = 1600) -> None:
        if self.toast_id is not None:
            self.root.after_cancel(self.toast_id)
        if self.toast is not None:
            self.toast.destroy()
        self.toast = tk.Label(
            self.root, text=mensagem, font=(FONTE, 12, "bold"), padx=16, pady=8,
            bg=self._t("toast_fundo"), fg=self._t("toast_texto"),
        )
        self.toast.place(relx=0.5, y=78, anchor="n")
        self.toast_id = self.root.after(duracao, self._esconder_toast)

    def _esconder_toast(self) -> None:
        if self.toast is not None:
            self.toast.destroy()
        self.toast = None
        self.toast_id = None

    # ----------------------------------------------------------- estatísticas
    def _titulo_compartilhar(self) -> str:
        return "Palavreco livre" if self.livre else f"Palavreco #{numero_do_dia()}"

    def copiar_resultado(self) -> None:
        texto = compartilhar(self.partida, self._titulo_compartilhar(), self.alto_contraste)
        self.root.clipboard_clear()
        self.root.clipboard_append(texto)
        self.root.update()  # mantém o clipboard após fechar o app
        self.mostrar_toast("Resultado copiado!", 1500)

    def _fechar_stats(self) -> None:
        if self.janela_stats is not None:
            self.janela_stats.destroy()
            self.janela_stats = None

    def mostrar_estatisticas(self) -> None:
        self._fechar_stats()
        bg, fg, sutil = self._t("painel"), self._t("texto"), self._t("sutil")
        janela = tk.Toplevel(self.root)
        self.janela_stats = janela
        janela.title("Estatísticas")
        janela.configure(bg=bg)
        janela.resizable(False, False)
        janela.transient(self.root)
        janela.protocol("WM_DELETE_WINDOW", self._fechar_stats)
        janela.bind("<Escape>", lambda _e: self._fechar_stats())

        tk.Label(janela, text="ESTATÍSTICAS", font=(FONTE, 14, "bold"), bg=bg, fg=fg).pack(pady=(16, 8))

        numeros = tk.Frame(janela, bg=bg)
        numeros.pack(padx=20)
        valores = (
            (self.est.jogos, "Jogos"),
            (f"{self.est.percentual_vitorias}%", "Vitórias"),
            (self.est.sequencia, "Sequência"),
            (self.est.melhor_sequencia, "Melhor"),
        )
        for i, (valor, rotulo) in enumerate(valores):
            caixa = tk.Frame(numeros, bg=bg)
            caixa.grid(row=0, column=i, padx=10)
            tk.Label(caixa, text=str(valor), font=(FONTE, 22, "bold"), bg=bg, fg=fg).pack()
            tk.Label(caixa, text=rotulo, font=(FONTE, 9), bg=bg, fg=sutil).pack()

        tk.Label(janela, text="DISTRIBUIÇÃO DE TENTATIVAS", font=(FONTE, 10, "bold"), bg=bg, fg=fg).pack(pady=(16, 4))
        altura_barra, largura_max = 24, 240
        grafico = tk.Canvas(janela, width=320, height=MAX_TENTATIVAS * (altura_barra + 4) + 4, bg=bg, highlightthickness=0)
        grafico.pack(padx=20)
        maximo = max(self.est.distribuicao.values(), default=0) or 1
        atual = self.partida.tentativas_usadas if self.partida.estado == VENCEU else None
        for i in range(1, MAX_TENTATIVAS + 1):
            valor = self.est.distribuicao[str(i)]
            y = 4 + (i - 1) * (altura_barra + 4)
            largura = max(26, largura_max * valor / maximo)
            if i == atual:
                cor, cor_txt = self._cor_status(CERTA)
            else:
                cor, cor_txt = self._t("errada"), "#ffffff"
            grafico.create_text(10, y + altura_barra / 2, text=str(i), fill=fg, font=(FONTE, 10, "bold"))
            grafico.create_polygon(
                _pontos_arredondados(26, y, 26 + largura, y + altura_barra, 6),
                smooth=True, fill=cor, outline=cor,
            )
            grafico.create_text(26 + largura - 8, y + altura_barra / 2, text=str(valor), fill=cor_txt, anchor="e", font=(FONTE, 10, "bold"))

        if self.partida.terminou:
            situacao = "Você acertou!" if self.partida.estado == VENCEU else "Não foi dessa vez."
            tk.Label(janela, text=f"{situacao} A palavra era {self.partida.segredo.upper()}.", font=(FONTE, 10), bg=bg, fg=sutil).pack(pady=(14, 0))

        botoes = tk.Frame(janela, bg=bg)
        botoes.pack(pady=16)
        acoes = []
        if self.partida.terminou:
            acoes.append(("Copiar resultado", self.copiar_resultado))
            acoes.append(("Jogar no modo livre", self.novo_jogo_livre))
        acoes.append(("Fechar", self._fechar_stats))
        for texto, comando in acoes:
            botao = tk.Label(botoes, text=texto, font=(FONTE, 10, "bold"), padx=14, pady=8,
                             bg=self._cor_status(CERTA)[0], fg=self._cor_status(CERTA)[1])
            botao.pack(side="left", padx=5)
            botao.bind("<Button-1>", lambda _e, c=comando: c())
            base = botao.cget("bg")
            botao.bind("<Enter>", lambda _e, b=botao, base=base: b.config(cursor="hand2", bg=misturar(base, "#ffffff", 0.2)))
            botao.bind("<Leave>", lambda _e, b=botao, base=base: b.config(cursor="", bg=base))

        janela.update_idletasks()
        w, h = janela.winfo_reqwidth(), janela.winfo_reqheight()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - w) // 2
        y = self.root.winfo_rooty() + 60
        janela.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        janela.focus_set()

    # ---------------------------------------------------------------- smoke
    def roteiro_smoke(self) -> None:
        """Joga uma partida de mentira para exercitar animações e janelas."""
        r = self.root
        for letra in "ZZZZZ":
            self.digitar(letra)
        r.after(100, self.confirmar)           # não existe: treme + toast
        r.after(900, lambda: [self.apagar() for _ in range(TAMANHO)])
        r.after(1000, self.alternar_contraste)
        r.after(1050, self.alternar_tema)

        def acertar() -> None:
            for letra in normalizar(self.partida.segredo):
                self.digitar(letra)
            self.confirmar()

        r.after(1100, acertar)
        r.after(4200, self.copiar_resultado)
        r.after(4600, r.destroy)


def iniciar(livre: bool = False, smoke: bool = False) -> None:
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    root = tk.Tk()
    pasta_temporaria = None
    estatisticas = None
    if smoke:  # nunca mexe nas estatísticas reais
        pasta_temporaria = tempfile.TemporaryDirectory()
        estatisticas = Estatisticas(Path(pasta_temporaria.name) / "estatisticas.json")
    app = App(root, livre=livre or smoke, estatisticas=estatisticas)

    def registrar_erro(tipo, valor, tb) -> None:
        app.erros.append(valor)
        sys.__excepthook__(tipo, valor, tb)

    root.report_callback_exception = registrar_erro
    if smoke:
        app.roteiro_smoke()
    root.mainloop()
    if pasta_temporaria is not None:
        pasta_temporaria.cleanup()
    if smoke and app.erros:
        raise SystemExit(1)
