from codecs import open
from spacy.lemmatizer import Lemmatizer
from spacy.lookups import Lookups, Table
from time import time


def to_bin():
    with open(f'../data/lookups/noun-lemmas.json', 'r', encoding="utf-8") as f:
        noun_lemmas = eval(f.read())
    with open(f'../data/lookups/prop-noun-lemmas.json', 'r', encoding="utf-8") as f:
        prop_noun_lemmas = eval(f.read())
    with open(f'../data/lookups/verb-lemmas.json', 'r', encoding="utf-8") as f:
        verb_lemmas = eval(f.read())

    lookups = Lookups()
    lookups.add_table("noun-lemmas", noun_lemmas)
    lookups.add_table("prop-noun-lemmas", prop_noun_lemmas)
    lookups.add_table("verb-lemmas", verb_lemmas)
    lookups.to_disk(".")


def load_lemmas():
    start_time = time()

    lookups = Lookups()
    lookups.from_disk('../data/lookups')
    noun_lemmas = lookups.get_table("noun-lemmas")
    prop_noun_lemmas = lookups.get_table("prop-noun-lemmas")
    verb_lemmas = lookups.get_table("verb-lemmas")

    pronouns = {'meu': 'eu', 'mea': 'eu', 'mei': 'eu', 'mele': 'eu'}
    pron_lemmas = Table.from_dict(pronouns)

    print(f'Loaded in {time() - start_time} s')
    return prop_noun_lemmas


lemmas = load_lemmas()

while True:
    word = input("> ")
    print(lemmas.get(word, " = " + word))

# to_bin()

# lemmatizer = Lemmatizer(lookups)
# lemmas = lemmatizer.lookup("mâncând")
