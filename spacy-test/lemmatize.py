from codecs import open
from spacy.lemmatizer import Lemmatizer
from spacy.lookups import Lookups, Table
from time import time


def to_bin():
    with open(f'data/noun-lemmas.json', 'r', encoding="utf-8") as f:
        dexonline_lemmas = eval(f.read())

    lookups = Lookups()
    lookups.add_table("noun-lemmas", dexonline_lemmas)
    lookups.to_disk(".")


def load_lemmas():
    start_time = time()

    lookups = Lookups()
    lookups.from_disk('.')
    lemmas = lookups.get_table("noun-lemmas")

    pronouns = {'meu': 'eu', 'mea': 'eu', 'mei': 'eu', 'mele': 'eu'}
    pron_lemmas = Table.from_dict(pronouns)

    print(f'Loaded in {time() - start_time} s')
    return pron_lemmas


lemmas = load_lemmas()
print('meu' in lemmas)

while True:
    word = input("> ")
    print(lemmas.get(word, " = " + word))

# lemmatizer = Lemmatizer(lookups)
# lemmas = lemmatizer.lookup("mâncând")
