# coding: utf-8
"""Using the parser to recognise your own semantics
spaCy's parser component can be used to trained to predict any type of tree
structure over your input text. You can also predict trees over whole documents
or chat logs, with connections between the sentence-roots used to annotate
discourse structure. In this example, we'll build a message parser for a common
"chat intent": finding local businesses. Our message semantics will have the
following types of relations: ROOT, PLACE, QUALITY, ATTRIBUTE, TIME, LOCATION.
"show me the best hotel in berlin"
('show', 'ROOT', 'show')
('best', 'QUALITY', 'hotel') --> hotel with QUALITY best
('hotel', 'PLACE', 'show') --> show PLACE hotel
('berlin', 'LOCATION', 'hotel') --> hotel with LOCATION berlin
Compatible with: spaCy v2.0.0+
"""
from __future__ import unicode_literals, print_function

import plac
import random
from pathlib import Path
import spacy
from spacy.tokens import Span
from spacy.util import minibatch, compounding

from print_utils import TermColors

# training data: texts, heads and dependency labels
# for no relation, we simply chose an arbitrary dependency label, e.g. '-'
TRAIN_DATA = [
    (
        "eu merg spre casă azi",
        {
            "heads": [1, 1, 3, 1, 1],  # index of token head
            "deps": ['cine', 'ROOT', '-', 'unde', 'când'],
        },
    ),
    (
        "ieri am fost în București",
        {
            "heads": [2, 2, 2, 4, 2],
            "deps": ['când', '-', 'ROOT', '-', 'unde'],
        },
    ),
    (
        "am fost la sală ieri seara",
        {
            "heads": [1, 1, 3, 3, 1, 4],
            "deps": ['-', 'ROOT', '-', 'unde', 'când', 'care'],
        }
    ),
    (
        "Maria stă la apartamentul 23 pe strada principală",
        {
            "heads": [1, 1, 3, 1, 3, 6, 1, 6],
            "deps": ['cine', 'ROOT', '-', 'unde', 'care', '-', 'unde', 'care'],
        }
    ),
    (
        "cărțile de matematică ale Mariei sunt sub pat",
        {
            "heads": [5, 2, 0, 4, 0, 5, 7, 5],
            "deps": ['cine', '-', 'care', '-', 'al cui', 'ROOT', '-', 'unde'],
        }
    ),
    (
        "floarea din bucătărie se află pe pervaz sub geam",
        {
            "heads": [4, 2, 0, 4, 4, 6, 4, 8, 4],
            "deps": ['cine', '-', 'care', '-', 'ROOT', '-', 'unde', '-', 'unde'],
        }
    ),
    (
        "azi începe vacanța noastră",
        {
            "heads": [1, 1, 1, 2],
            "deps": ['când', 'ROOT', 'cine', 'al cui'],
        }
    ),
    (
        "săptămâna trecută am udat pomul meu de afară",
        {
            "heads": [3, 1, 3, 3, 3, 4, 7, 4],
            "deps": ['când', 'care', '-', 'ROOT', 'ce', 'al cui', '-', 'care'],
        }
    ),
    (
        "ziua de naștere a lui Alex este pe 5 mai",
        {
            "heads": [6, 2, 0, 5, 5, 0, 6, 9, 9, 6],
            "deps": ['cine', '-', 'care', '-', '-', 'al cui', 'ROOT', '-', '-', 'când'],
        }
    ),
    (
        "eu locuiesc pe bulevardul Timișoara",
        {
            "heads": [1, 1, 3, 1, 3],
            "deps": ['cine', 'ROOT', '-', 'unde', 'care'],
        }
    ),
    (
        "cursul se ține în sala EC105 de la parter din facultatea noastră",
        {
            "heads": [2, 2, 2, 4, 2, 4, 8, 8, 4, 10, 4, 10],
            "deps": ['cine', '-', 'ROOT', '-', 'unde', 'care', '-', '-', 'care', '-', 'care', 'al cui'],
        }
    ),
    (
        "Mihai este foarte înalt",
        {
            "heads": [1, 1, 3, 1],
            "deps": ['cine', 'ROOT', '-', 'cum este'],
        }
    ),
    (
        "lunea viitoare o să dăm testul la elemente de informatică mobilă",
        {
            "heads": [4, 0, 4, 4, 4, 4, 7, 5, 9, 7, 9],
            "deps": ['când', 'care', '-', '-', 'ROOT', 'ce', '-', 'care', '-', 'ce fel de', 'ce fel de'],
        }
    ),
    (
        "ceasul fetei de acolo e scump",
        {
            "heads": [4, 0, 3, 1, 4, 4],
            "deps": ['cine', 'al cui', '-', 'care', 'ROOT', 'cum este'],
        }
    ),
    (
        "de azi încep tema de la mate",
        {
            "heads": [1, 2, 2, 2, 6, 6, 3],
            "deps": ['-', 'când', 'ROOT', 'ce', '-', '-', 'care'],
        }
    ),
    (
        "peste o săptămână o să vină Alina pe la mine",
        {
            "heads": [2, 2, 5, 5, 5, 5, 5, 9, 9, 5],
            "deps": ['-', '-', 'când', '-', '-', 'ROOT', 'cine', '-', '-', 'unde'],
        }
    ),
    (
        "anul trecut am luat un monitor de acasă",
        {
            "heads": [3, 0, 3, 3, 5, 3, 7, 3],
            "deps": ['când', 'care', '-', 'ROOT', '-', 'ce', '-', 'unde'],
        }
    ),
    (
        "de dimineață am mâncat salată de ton",
        {
            "heads": [1, 3, 3, 3, 3, 6, 3],
            "deps": ['-', 'când', '-', 'ROOT', 'ce', '-', 'ce fel de'],
        }
    ),
    (
        "această parte principală de propoziție arată acțiunea",
        {
            "heads": [1, 5, 1, 4, 1, 5, 5],
            "deps": ['care', 'cine', 'care', '-', 'care', 'ROOT', 'ce'],
        }
    ),
    (
        "trebuie să iau pastila de hipertensiune seara și dimineața",
        {
            "heads": [0, 2, 2, 3, 5, 3, 2, 8, 2],
            "deps": ['ROOT', '-', 'ce', 'ce', '-', 'care', 'când', '-', 'când'],
        }
    ),
    (
        "O să trebuiască să merg la serviciu începând de luna viitoare",
        {
            "heads": [2, 2, 2, 4, 2, 6, 4, 9, 9, 4, 9],
            "deps": ['-', '-', 'ROOT', '-', 'ce', '-', 'unde', '-', '-', 'când', 'care'],
        }
    ),
    (
        "am pus joia trecută ochelarii mei de soare în sertarul meu din camera mea",
        {
            "heads": [1, 1, 1, 2, 1, 4, 7, 4, 9, 1, 9, 12, 9, 12],
            "deps": ['-', 'ROOT', 'când', 'care', 'ce', 'al cui', '-', 'care', '-', 'unde', 'al cui', '-', 'care',
                     'al cui'],
        }
    ),
    (
        "Telefonul Alexandrei este 074123456",
        {
            "heads": [2, 0, 2, 2],
            "deps": ['cine', 'al cui', 'ROOT', 'care este'],
        }
    ),
    (
        "Numărul de la interfon al lui Iulian apare jos la intrarea în scară",
        {
            "heads": [7, 3, 3, 0, 6, 6, 0, 7, 7, 10, 7, 12, 10],
            "deps": ['cine', '-', '-', 'care', '-', '-', 'al cui', 'ROOT', 'unde', '-', 'unde', '-', 'care'],
        }
    ),
]


def analyze_data(phrases):
    dep_freq = {}
    for phrase, relations in phrases:
        for dep in relations['deps']:
            dep_freq[dep] = dep_freq.get(dep, 0) + 1

    dep_freq = {k: v for k, v in sorted(dep_freq.items(), key=lambda item: item[1])}
    print('Depencencies frequencies:')
    print(dep_freq)


@plac.annotations(
    model=("Model name. Defaults to blank 'en' model.", "option", "m", str),
    output_dir=("Optional output directory", "option", "o", Path),
    n_iter=("Number of training iterations", "option", "n", int),
)
def main(model=None, output_dir=None, n_iter=30):
    """Load the model, set up the pipeline and train the parser."""
    if model is not None:
        nlp = spacy.load(model)  # load existing spaCy model
        print("Loaded model '%s'" % model)
    else:
        nlp = spacy.blank("ro")  # create blank Language class
        print("Created blank 'ro' model")

    # We'll use the built-in dependency parser class, but we want to create a fresh instance – just in case.
    # if "parser" in nlp.pipe_names:
    #     nlp.remove_pipe("parser")
    # parser = nlp.create_pipe("parser")
    # nlp.add_pipe(parser, first=True)
    parser = None
    for (name, pipe) in nlp.pipeline:
        if name == "parser":
            parser = pipe

    print("TRAIN EXAMPLES: ", len(TRAIN_DATA))
    for text, annotations in TRAIN_DATA:
        for dep in annotations.get("deps", []):
            parser.add_label(dep)

    pipe_exceptions = ["parser", "trf_wordpiecer", "trf_tok2vec"]
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]
    with nlp.disable_pipes(*other_pipes):  # only train parser
        optimizer = nlp.begin_training()
        for itn in range(n_iter):
            random.shuffle(TRAIN_DATA)
            losses = {}
            # batch up the examples using spaCy's minibatch
            batches = minibatch(TRAIN_DATA, size=compounding(4.0, 32.0, 1.001))
            for batch in batches:
                texts, annotations = zip(*batch)
                nlp.update(texts, annotations, sgd=optimizer, losses=losses)
            print("Losses", losses)

    # test the trained model
    test_model(nlp)

    # save model to output directory
    if output_dir is not None:
        output_dir = Path(output_dir)
        if not output_dir.exists():
            output_dir.mkdir()
        nlp.to_disk(output_dir)
        print("Saved model to", output_dir)


def dep_span(doc, node):
    def dfs(node):
        first = last = node.i
        for child in node.children:
            if child.dep_ == '-':
                child_first, child_last = dfs(child)
                first = min(first, child_first)
                last = max(last, child_last)
        return first, last

    first, last = dfs(node)
    span = Span(doc, first, last + 1)
    return span.text


def test_model(nlp):
    texts = [
        "peste 3 zile mergem la bunici",
        "ieri am fost pe bancă",
        "ochelarii mei sunt în sertarul din sufragerie",
        "am pus mingea sub patul din dormitor",
        "mâine începe un serial la televizor",
        "pălăria Adinei este frumoasă",
        "bunicul meu trebuie să hrănească animalele zilnic",
    ]

    docs = nlp.pipe(texts)
    for doc in docs:
        print('\n', doc.text)
        for token in doc:
            if token.dep_ != "-":
                print(TermColors.YELLOW, token.dep_, TermColors.ENDC, f'[{dep_span(doc, token.head)}] ->',
                      TermColors.PINK, dep_span(doc, token), TermColors.ENDC)


if __name__ == "__main__":
    analyze_data(TRAIN_DATA)
    main("rasa_spacy_ro", n_iter=80)
