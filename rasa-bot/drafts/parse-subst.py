from codecs import open
from random import shuffle, choice, choices

specifiers = ['care', 'ce', 'ce fel de']

with open('data/art_nouns.txt', 'r', encoding="utf-8") as f:
    lines = f.readlines()
    lines = list(filter(lambda word: '-' not in word and word.islower(), lines))
    shuffle(lines)

    for noun in lines[:100]:
        tokens = noun.split(' ')
        to_be = choices(['e', 'este', 'era', 'a fost'], weights=[8, 8, 1, 1])[0] if tokens[0] == "e" else \
            choices(['sunt', 'erau', 'au fost'], weights=[8, 1, 1])[0]

        print(f'- care {to_be} {tokens[1]}', end='')
