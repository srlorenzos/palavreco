"""Lista de palavras e escolha da palavra do dia.

Todas as palavras têm 5 letras (depois de remover acentos) e aparecem com a
acentuação correta, porque é assim que são reveladas ao jogador.
"""

from __future__ import annotations

import hashlib
import random
import unicodedata
from datetime import date

# Dia #1 do jogo. Mudar isto muda a palavra de todos os dias.
DATA_BASE = date(2024, 1, 1)

PALAVRAS: tuple[str, ...] = (
    "acaso", "achar", "ácido", "açude", "adeus", "aéreo", "afago", "afeto",
    "agito", "agora", "aguda", "águia", "ainda", "ajuda", "alado", "álbum",
    "algum", "aliar", "almas", "altar", "altos", "aluno", "amado", "amago",
    "ambos", "amiga", "amigo", "amora", "ampla", "andar", "anexo", "ânimo",
    "anjos", "ânsia", "antes", "anual", "aonde", "apelo", "áreas", "aroma",
    "arroz", "artes", "asilo", "aspas", "astro", "átomo", "atriz", "atual",
    "aulas", "avião", "avisa", "azeda", "azedo", "bacia", "baixo", "balão",
    "balde", "banco", "banho", "barba", "barco", "barro", "bases", "beber",
    "beijo", "beira", "bemol", "bicho", "bispo", "blusa", "bolos", "bolsa",
    "bonde", "bônus", "borda", "braço", "brado", "brasa", "bravo", "breve",
    "briga", "brisa", "bruma", "bruxa", "bulir", "burro", "busca", "cabra",
    "caçar", "cacau", "cacho", "cacto", "caixa", "calça", "calma", "calor",
    "campo", "canal", "canto", "capaz", "capim", "carga", "carne", "carro",
    "carta", "casal", "casco", "causa", "cedro", "cenas", "censo", "certo",
    "chama", "chave", "chefe", "cheio", "chuva", "cinco", "circo", "civil",
    "claro", "clima", "cobra", "coisa", "colar", "comer", "conta", "corpo",
    "corte", "couve", "crise", "cruel", "culto", "curso", "curva", "custo",
    "dados", "damas", "dança", "datas", "dedos", "deixa", "dente", "desde",
    "dever", "dizer", "doces", "dores", "drama", "ducha", "dueto", "duplo",
    "durar", "ecoar", "elite", "então", "entre", "época", "errar", "erros",
    "essas", "estar", "etapa", "exame", "exata", "êxito", "extra", "fácil",
    "falar", "falso", "falta", "farol", "farta", "fatia", "fazer", "feira",
    "feliz", "ferro", "festa", "fibra", "ficar", "filho", "final", "firma",
    "fisco", "flora", "focos", "folha", "fonte", "força", "forma", "forno",
    "forte", "fotos", "frase", "freio", "fruta", "fugir", "fundo", "fúria",
    "gaita", "galho", "ganho", "garfo", "gasto", "gatos", "gemer", "gênio",
    "genro", "gente", "gesto", "girar", "globo", "golpe", "gosto", "graça",
    "grama", "grato", "grave", "grupo", "guiar", "haste", "herói", "hotel",
    "humor", "ideal", "ideia", "idoso", "igual", "ilhas", "ímpar", "índio",
    "irmão", "jeito", "jogar", "jogos", "joias", "jovem", "juízo", "junto",
    "justo", "laços", "lagoa", "lápis", "largo", "lavar", "lazer", "leite",
    "lenda", "lento", "letra", "levar", "lição", "lidar", "ligar", "limão",
    "limpo", "linda", "lindo", "linha", "litro", "livro", "local", "longe",
    "lotes", "lucro", "lugar", "lunar", "luzes", "macio", "magia", "mágoa",
    "magro", "maior", "mamãe", "mamão", "manga", "manhã", "mapas", "marca",
    "marco", "massa", "matar", "medir", "meios", "melão", "menor", "mente",
    "mesas", "metal", "metro", "mexer", "mídia", "milho", "mimos", "minha",
    "misto", "moças", "moeda", "molho", "monte", "morar", "morro", "mosca",
    "motor", "móvel", "mover", "mudar", "muito", "mundo", "museu", "nação",
    "nadar", "naves", "nervo", "neste", "ninho", "nível", "nobre", "noção",
    "noite", "norte", "nossa", "notas", "novas", "novos", "nuvem", "obras",
    "olhar", "ombro", "ontem", "ópera", "ordem", "ótimo", "outro", "ouvir",
    "pacto", "padre", "pagar", "palco", "panos", "pares", "parte", "passo",
    "pasta", "pátio", "pausa", "pegar", "peito", "peixe", "pente", "perda",
    "perto", "pesar", "pesca", "piano", "pilha", "pinta", "pista", "plano",
    "plena", "pobre", "poder", "pólen", "polvo", "ponta", "ponte", "porão",
    "porta", "posse", "pouco", "prado", "praia", "prata", "prazo", "preço",
    "prima", "prosa", "prova", "pular", "punho", "quase", "queda", "quero",
    "raiva", "ramos", "rapaz", "raros", "razão", "reais", "regra", "reino",
    "relva", "renda", "resto", "ricos", "rimas", "risco", "ritmo", "rodas",
    "rogar", "rolar", "rosto", "rotas", "roupa", "rumor", "sabão", "sabor",
    "sacos", "safra", "saída", "salão", "salas", "saldo", "salto", "samba",
    "santo", "saúde", "selva", "senão", "senha", "sente", "série", "servo",
    "sexta", "sigla", "signo", "sinal", "sinto", "sobre", "sogra", "solar",
    "solto", "somar", "sonho", "sorte", "sótão", "suave", "subir", "super",
    "tábua", "talão", "tampa", "tanto", "tarde", "taxas", "tecla", "tédio",
    "tempo", "tenda", "tênis", "tenso", "tênue", "terça", "terno", "terra",
    "tigre", "tinta", "tocar", "todos", "tomar", "torre", "total", "touro",
    "trama", "trapo", "treze", "trigo", "troca", "trono", "tropa", "tubos",
    "turma", "turno", "ultra", "unhas", "união", "único", "unido", "usina",
    "vagas", "valer", "valor", "vapor", "vasos", "vazio", "veado", "velho",
    "vento", "verão", "verbo", "verde", "verso", "vezes", "vidas", "vidro",
    "vigor", "vinho", "vinte", "vírus", "visão", "viver", "volta", "votar",
    "vozes", "zebra", "zelar", "zerar",
)


def _sem_acento(texto: str) -> str:
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn").upper()


def _chave_ordem(palavra: str) -> str:
    # Ordem fixa e "embaralhada" que não depende da versão do Python.
    return hashlib.sha256(_sem_acento(palavra).encode("utf-8")).hexdigest()


_ORDEM_DIARIA: tuple[str, ...] = tuple(sorted(PALAVRAS, key=_chave_ordem))


def numero_do_dia(dia: date | None = None) -> int:
    """Número do jogo do dia (1 na data base)."""
    dia = dia or date.today()
    return (dia - DATA_BASE).days + 1


def palavra_do_dia(dia: date | None = None) -> str:
    """Mesma data, mesma palavra. Percorre a lista inteira antes de repetir."""
    indice = (numero_do_dia(dia) - 1) % len(_ORDEM_DIARIA)
    return _ORDEM_DIARIA[indice]


def palavra_aleatoria(rng: random.Random | None = None) -> str:
    """Palavra qualquer para o modo livre."""
    return (rng or random).choice(PALAVRAS)
