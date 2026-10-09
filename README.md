# palavreco

Jogo de adivinhar a **palavra de 5 letras em português**, no estilo Termo/Wordle, com interface gráfica em tkinter.

- Uma palavra do dia (a mesma para todo mundo) e um modo livre com palavras aleatórias.
- Animações de virar as peças, tremida quando a palavra não existe, teclado virtual e tema claro/escuro.
- Modo de alto contraste para daltonismo.
- Zero dependências: só a biblioteca padrão do Python 3.10+ (com tkinter).

## Como jogar

Você tem **6 tentativas** para descobrir a palavra. Digite sem acento; a palavra revelada aparece com acento.

| Cor | Significado |
| --- | --- |
| Verde | A letra está na palavra e no lugar certo |
| Amarelo | A letra está na palavra, mas em outra posição |
| Cinza | A letra não está na palavra (ou já foi usada nas outras posições) |

Letras repetidas são tratadas com cuidado: se o chute tem dois `A` e a palavra só um, só um deles ganha cor.

Ao terminar, o painel de estatísticas mostra a distribuição de tentativas e o botão **Copiar resultado** gera a grade de emojis para compartilhar:

```
Palavreco #123 4/6

⬛🟨⬛⬛⬛
🟨⬛🟩⬛⬛
🟩🟩🟩⬛🟩
🟩🟩🟩🟩🟩
```

## Executar

```
python -m palavreco
```

Ou instalando como comando:

```
pip install .
palavreco
```

Em Linux, se faltar o tkinter: `sudo apt install python3-tk`.

### Modo livre

```
python -m palavreco --livre
```

Sorteia uma palavra qualquer a cada partida. Se você já jogou a palavra de hoje, o jogo abre direto no modo livre. Também dá para trocar pelo botão do painel de estatísticas.

## Atalhos

| Tecla | Ação |
| --- | --- |
| Letras | Digitar (acentos são ignorados) |
| Enter | Enviar o chute |
| Backspace | Apagar a última letra |
| F2 | Alternar tema claro/escuro |
| F3 | Alternar alto contraste (laranja/azul no lugar de verde/amarelo) |
| F4 | Abrir as estatísticas |
| Esc | Fechar a janela de estatísticas |

O teclado virtual também é clicável, e os botões do topo fazem o mesmo que F4, F3 e F2. O tema e o alto contraste ficam salvos.

## Estatísticas

Ficam em `~/.palavreco/estatisticas.json` (jogos, vitórias, sequência atual, melhor sequência e distribuição de tentativas). Se o arquivo não existir ou estiver corrompido, o jogo recomeça do zero sem erro. Apagar o arquivo reinicia tudo.

## Estrutura

```
palavreco/
  jogo.py          # regras: avaliar(), Partida, compartilhar() (sem tkinter)
  palavras.py      # lista embutida e palavra do dia (determinística pela data)
  estatisticas.py  # leitura e gravação do JSON
  interface.py     # tkinter: Canvas, animações, teclado, estatísticas
  __main__.py      # python -m palavreco [--livre]
tests/             # unittest, sem importar a interface
```

A palavra do dia sai de uma ordem fixa da lista (embaralhada por hash) a partir de `DATA_BASE` em `palavras.py`: mesmo dia, mesma palavra, sem repetir até a lista acabar.

## Testes

```
python -m unittest discover -s tests -v
```

Os testes não precisam de tkinter nem tocam na sua pasta pessoal: as estatísticas usam arquivos temporários.

## Licença

MIT © Eduardo Lorenzo
