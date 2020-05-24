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
            "heads": [1, 1, 3, 1, 1],
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
            "heads": [1, 1, 3, 1, 1, 4],
            "deps": ["-", "ROOT", "-", "unde", "când", "care"]}
    ),
    (
        "Maria stă la apartamentul 23 pe strada principală",
        {
            "heads": [1, 1, 3, 1, 3, 6, 1, 6],
            "deps": ['cine', 'ROOT', '-', 'unde', 'care', '-', 'unde', 'care'],
        }
    ),
    (
        "cărțile de matematică ale mariei sunt sub pat",
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
        "ziua de naștere a lui alex este pe 5 mai",
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
            "heads": [5, 2, 0, 5, 5, 5, 5, 9, 9, 5],
            "deps": ['când', 'cât', 'cât timp', '-', '-', 'ROOT', 'cine', '-', '-', 'unde'],
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
        "o să trebuiască să merg la serviciu începând de luna viitoare",
        {
            "heads": [2, 2, 2, 4, 2, 6, 4, 9, 9, 4, 9],
            "deps": ['-', '-', 'ROOT', '-', 'ce', '-', 'unde', '-', 'prep', 'când', 'care'],
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
        "telefonul alexandrei este 074123456",
        {
            "heads": [2, 0, 2, 2],
            "deps": ['cine', 'al cui', 'ROOT', 'care este'],
        }
    ),
    (
        "numărul de la interfon al lui iulian apare jos la intrarea în scară",
        {
            "heads": [7, 3, 3, 0, 6, 6, 0, 7, 7, 10, 7, 12, 10],
            "deps": ['cine', '-', '-', 'care', '-', '-', 'al cui', 'ROOT', 'unde', '-', 'unde', '-', 'care'],
        }
    ),
    (
        "mâine voi rezolva problema cu furtunul stricat",
        {
            "heads": [2, 2, 2, 2, 5, 3, 5],
            "deps": ['când', '-', 'ROOT', 'ce', '-', 'care', 'care'],
        }
    ),
    (
        "ultima zi de lucru a mea e peste două săptămâni",
        {
            "heads": [1, 6, 3, 1, 5, 1, 6, 6, 9, 7],
            "deps": ['care', 'cine', '-', 'care', '-', 'al cui', 'ROOT', 'când', 'cât', 'cât timp'],
        }
    ),
    (
        "am de făcut o temă grea până vineri",
        {
            "heads": [0, 2, 0, 4, 2, 4, 7, 2],
            "deps": ['ROOT', '-', 'ce', '-', 'ce', 'ce fel de', 'prep', 'când'],
        }
    ),
    (
        "în fiecare zi fac antrenament sportiv",
        {
            "heads": [2, 2, 3, 3, 3, 4],
            "deps": ['-', '-', 'când', 'ROOT', 'ce', 'ce fel de'],
        }
    ),
    (
        "am de terminat proiectul la programare până în mai",
        {
            "heads": [0, 2, 0, 2, 5, 3, 8, 8, 2],
            "deps": ['ROOT', '-', 'ce', 'ce', '-', 'care', 'prep', '-', 'când'],
        }
    ),
    (
        "voi avea de făcut rapoartele pentru ultima lună până pe 23 iunie 2021",
        {
            "heads": [1, 1, 3, 1, 3, 7, 7, 4, 10, 10, 3, 10, 10],
            "deps": ["-", "ROOT", "-", "ce", "ce", "-", "care", "care", "prep", "-", "când", "care", "care"]
        }
    ),
    (
        "numărul de la interfon al verișoarei mele Iulia este 24",
        {
            "heads": [8, 3, 3, 0, 5, 0, 5, 5, 8, 8],
            "deps": ["cine", "-", "-", "care", "-", "al cui", "al cui", "care", "ROOT", "care este"]
        }
    ),
    (
        "laborantul meu de la EIM e Dan Bina",
        {
            "heads": [5, 0, 4, 4, 0, 5, 5, 6],
            "deps": ["cine", "al cui", "-", "-", "care", "ROOT", "care este", "care"]
        }
    ),
    (
        "zilele ăstea am făcut câte 30 de flotări",
        {
            "heads": [3, 0, 3, 3, 5, 7, 7, 3],
            "deps": ["când", "care", "-", "ROOT", "-", "cât", "-", "ce"]}
    ),
    (
        "i-am dat 10 lei lui george",
        {
            "heads": [3, 0, 3, 3, 5, 3, 7, 3],
            "deps": ["cui", "-", "-", "ROOT", "cât", "ce", "-", "cui"]
        }
    ),
    (
        "eu mi-am schimbat telefonul în ianuarie anul trecut",
        {
            "heads": [4, 4, 1, 4, 4, 4, 7, 4, 7, 8],
            "deps": ["cine", "cui", "-", "-", "ROOT", "ce", "-", "când", "care", "care"]
        }
    ),
    (
        "acela și-a făcut tema acum 2 zile",
        {
            "heads": [4, 4, 1, 4, 4, 4, 5, 8, 6],
            "deps": ["cine", "cui", "-", "-", "ROOT", "ce", "când", "cât", "cât timp"]}
    ),
    (
        "am terminat de spălat vasele acum 30 de minute",
        {
            "heads": [1, 1, 3, 1, 3, 1, 8, 8, 5],
            "deps": ["-", "ROOT", "-", "ce", "ce", "când", "cât", "-", "cât timp"]}
    ),
    (
        "acum un an aveam 60 de kilograme",
        {
            "heads": [3, 2, 0, 3, 6, 6, 3],
            "deps": ["când", "-", "cât timp", "ROOT", "cât", "-", "ce"]}
    ),
    (
        "ultima dată m-am tuns acum 2 săptămâni",
        {
            "heads": [1, 5, 5, 2, 5, 5, 5, 8, 6],
            "deps": ["care", "când", "pe cine", "-", "-", "ROOT", "când", "cât", "cât timp"]}
    ),
    (
        "afară e foarte frig de azi de la prânz",
        {
            "heads": [1, 1, 3, 1, 5, 1, 8, 8, 1],
            "deps": ["unde", "ROOT", "-", "cum este", "prep", "când", "prep", "-", "când"]}
    ),
    (
        "documentarul va fi dat pe Discovery de sâmbăta viitoare",
        {
            "heads": [3, 3, 3, 3, 5, 3, 7, 3, 7],
            "deps": ["cine", "-", "-", "ROOT", "-", "unde", "prep", "când", "care"]}
    ),
    (
        "proiectul la franceză trebuie predat până la sfârșitul sesiunii",
        {
            "heads": [4, 2, 0, 4, 4, 7, 7, 4, 7],
            "deps": ["cine", "-", "care", "-", "ROOT", "prep", "-", "când", "al cui"]}
    ),
    (
        "după curs am ajutat-o pe profesoara de chimie la un experiment complicat",
        {
            "heads": [1, 3, 3, 3, 5, 3, 7, 3, 9, 7, 12, 12, 3, 12],
            "deps": ["-", "când", "-", "ROOT", "-", "pe cine", "-", "pe cine", "-", "care", "-", "-", "la ce",
                     "ce fel de"]}
    ),
    (
        "adresa de email a lui george ionescu e george@gmail.com",
        {
            "heads": [7, 2, 0, 5, 5, 0, 5, 7, 7],
            "deps": ["cine", "-", "care", "-", "-", "al cui", "care", "ROOT", "care este"]}
    ),
    (
        "trebuie să fac tema până mâine",
        {
            "heads": [0, 2, 0, 2, 5, 2],
            "deps": ["ROOT", "-", "ce", "ce", "prep", "când"]}
    ),
    (
        "în timpul prezentării s-a auzit un zgomot acolo",
        {
            "heads": [1, 6, 1, 6, 3, 6, 6, 8, 6, 6],
            "deps": ["-", "când", "al cui", "pe cine", "-", "-", "ROOT", "-", "ce", "unde"]}
    ),
    (
        "aici nu a mai venit un urs de mult timp",
        {
            "heads": [4, 4, 4, 4, 4, 6, 4, 9, 9, 4],
            "deps": ["unde", "-", "-", "-", "ROOT", "-", "ce", "prep", "-", "cât timp"]}
    ),
    (
        "după două săptămâni o să plec de aici",
        {
            "heads": [5, 2, 0, 5, 5, 5, 7, 5],
            "deps": ["când", "cât", "cât timp", "-", "-", "ROOT", "prep", "unde"]}
    ),
    (
        "acasă nu mai sunt pungi de 2 ore",
        {
            "heads": [3, 3, 3, 3, 3, 7, 7, 3],
            "deps": ["unde", "-", "-", "ROOT", "ce", "prep", "cât", "cât timp"]}
    ),
    (
        "la Slatina nu a mai plouat de 3 zile",
        {
            "heads": [1, 5, 5, 5, 5, 5, 8, 8, 5],
            "deps": ["-", "unde", "-", "-", "-", "ROOT", "prep", "cât", "cât timp"]}
    ),
    (
        "Dan Ion a ajuns la Craiova în 3 ore și 20 de minute",
        {
            "heads": [3, 0, 3, 3, 5, 3, 8, 8, 3, 12, 12, 12, 8],
            "deps": ["cine", "care", "-", "ROOT", "-", "unde", "prep", "cât", "cât timp", "-", "cât", "-", "cât timp"]}
    ),
    (
        "capsatorul cel mare se află pe masa din încăperea de lângă baie",
        {
            "heads": [4, 2, 0, 4, 4, 6, 4, 8, 6, 10, 11, 8],
            "deps": ["cine", "-", "care", "-", "ROOT", "-", "unde", "-", "care", "-", "-", "care"]}
    ),
    (
        "am vizitat - o pe Irina de ziua lui mihai",
        {
            "heads": [1, 1, 3, 1, 5, 1, 7, 1, 9, 7],
            "deps": ["-", "ROOT", "-", "pe cine", "-", "pe cine", "-", "când", "-", "al cui"]}
    ),
    (
        "de obicei merg la alergat în fiecare săptămână pe malul lacului morii",
        {
            "heads": [1, 2, 2, 4, 2, 7, 7, 2, 9, 2, 9, 10],
            "deps": ["-", "cât de des", "ROOT", "-", "unde", "-", "-", "cât de des", "-", "unde", "al cui", "care"]}
    ),
    (
        "trebuie să îmi pun picături în ochi de 3 ori pe zi",
        {
            "heads": [0, 3, 3, 0, 3, 6, 3, 9, 9, 3, 11, 9],
            "deps": ["ROOT", "-", "cui", "ce", "ce", "-", "unde", "-", "cât", "cât de des", "-", "la cât timp"]}
    ),
    (
        "ea iese afară de 10 ori pe lună",
        {
            "heads": [1, 1, 1, 5, 5, 1, 7, 5],
            "deps": ["cine", "ROOT", "unde", "-", "cât", "cât de des", "-", "la cât timp"]}
    ),
    (
        "în timpul anului universitar ajung acasă cam o dată la două săptămâni",
        {
            "heads": [1, 2, 4, 2, 4, 4, 8, 8, 4, 11, 11, 8],
            "deps": ["-", "-", "când", "care", "ROOT", "unde", "-", "cât", "cât de des", "-", "cât", "la cât timp"]}
    ),
    (
        "la mine s-a oprit apa caldă de câteva ore",
        {
            "heads": [1, 5, 5, 2, 5, 5, 5, 6, 10, 10, 5],
            "deps": ["-", "unde", "pe cine", "-", "-", "ROOT", "cine", "care", "prep", "cât", "cât timp"]}
    ),
    (
        "la facultate există multe calculatoare cu procesoare de generație nouă",
        {
            "heads": [1, 2, 2, 4, 2, 6, 4, 8, 6, 8],
            "deps": ["-", "unde", "ROOT", "cât", "ce", "-", "ce fel de", "-", "ce fel de", "ce fel de"]}
    ),
    (
        "o dată pe lună îi fac cartofi prăjiți alexandrei",
        {
            "heads": [1, 5, 3, 1, 5, 5, 5, 6, 5],
            "deps": ["cât", "cât de des", "-", "la cât timp", "cui", "ROOT", "ce", "ce fel de", "cui"]}
    ),
    (
        "el are o mașină audi de weekendul trecut",
        {
            "heads": [1, 1, 3, 1, 3, 6, 1, 6],
            "deps": ["cine", "ROOT", "-", "ce", "ce fel de", "prep", "când", "care"]}
    ),
    (
        "câinele meu a fost afară toată ziua de ieri",
        {
            "heads": [3, 0, 3, 3, 3, 6, 4, 8, 6],
            "deps": ["cine", "cui", "-", "ROOT", "unde", "-", "cât timp", "-", "care"]}
    ),
    (
        "sala laboratorului de ML este EG105",
        {
            "heads": [4, 0, 3, 1, 4, 4],
            "deps": ["cine", "al cui", "-", "care", "ROOT", "care este"]}
    ),

    # ------------------------------------ questions ------------------------------------
    (
        "unde se află biletul de avion",
        {
            "heads": [2, 2, 2, 2, 5, 3],
            "deps": ["unde", "-", "ROOT", "cine", "-", "care"]}
    ),
    (
        "de unde am cumpărat monitorul elenei",
        {
            "heads": [1, 3, 3, 3, 3, 4],
            "deps": ["prep", "unde", "-", "ROOT", "ce", "al cui"]}
    ),
    (
        "unde am lăsat husa de la telefon",
        {
            "heads": [2, 2, 2, 2, 6, 6, 3],
            "deps": ["unde", "-", "ROOT", "ce", "-", "-", "care"]}
    ),
    (
        "cât timp a durat examenul de inteligență artificială",
        {
            "heads": [1, 3, 3, 3, 3, 6, 4, 6],
            "deps": ["cât", "cât timp", "-", "ROOT", "cine", "-", "care", "ce fel de"]}
    ),
    (
        "când va începe colocviul de luni",
        {
            "heads": [2, 2, 2, 2, 5, 3],
            "deps": ["când", "-", "ROOT", "cine", "-", "care"]}
    ),
    (
        "până când o să țină înscrierea la facultatea de automatică",
        {
            "heads": [1, 4, 4, 4, 4, 4, 7, 5, 9, 7],
            "deps": ["prep", "când", "-", "-", "ROOT", "cine", "-", "care", "-", "care"]}
    ),
    (
        "de câți ani am geaca albastră",
        {
            "heads": [2, 2, 3, 3, 3, 4],
            "deps": ["prep", "cât", "cât timp", "ROOT", "ce", "care"]}
    ),
    (
        "care telefon are ecran mare",
        {
            "heads": [1, 2, 2, 2, 3],
            "deps": ["care", "cine", "ROOT", "ce", "ce fel de"]}
    ),
    (
        "care aparate sunt folosite la oftalmolog",
        {
            "heads": [1, 3, 3, 3, 5, 3],
            "deps": ["care", "cine", "-", "ROOT", "-", "unde"]}
    ),
    (
        "câți kilometri am alergat aseară pe afară",
        {
            "heads": [1, 3, 3, 3, 3, 6, 3],
            "deps": ["cât", "ce", "-", "ROOT", "când", "-", "unde"]}
    ),
    (
        "câte zile mai sunt până la weekend",
        {
            "heads": [1, 3, 3, 3, 6, 6, 3],
            "deps": ["cât", "cât timp", "-", "ROOT", "prep", "-", "când"]}
    ),
    (
        "șurubelnița dreaptă e în dulapul din camera mea",
        {
            "heads": [2, 0, 2, 4, 2, 6, 4, 6],
            "deps": ["cine", "care", "ROOT", "-", "unde", "-", "care", "al cui"]}
    ),
]


# TODO prepozitiile compuse ar trebui sa fie inlantuite?
# TODO exemple pentru intrebari

# când va fi sesiunea

def analyze_data(phrases):
    """
    Print statistics about the given phrases
    :param phrases: list of phrases to analyze
    """

    dep_freq = {}
    for phrase, relations in phrases:
        for dep in relations['deps']:
            dep_freq[dep] = dep_freq.get(dep, 0) + 1

    dep_freq = {k: v for k, v in sorted(dep_freq.items(), key=lambda item: item[1])}
    print('Depencencies frequencies:')
    print(dep_freq)


@plac.annotations(
    model=("Model name. Defaults to blank 'en' model.", "option", "m", str),
    n_iter=("Number of training iterations", "option", "n", int),
)
def train(model=None, n_iter=30):
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
    parser = [pipe for (name, pipe) in nlp.pipeline if name == "parser"][0]

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

    return nlp


def dep_span(doc, token, merge_attr=False):
    def dfs(node):
        first = last = node.i
        for child in node.children:
            if child.dep_ == '-' or (merge_attr and child.dep_ in ['care', 'ce fel de', 'cât', 'al cui']):
                child_first, child_last = dfs(child)
                first = min(first, child_first)
                last = max(last, child_last)
        return first, last

    first, last = dfs(token)  # compute bounds of the span
    span = Span(doc, first, last + 1)
    return span.text


def print_parse_result(doc):
    for token in doc:
        if token.dep_ != "-":
            print(TermColors.YELLOW, token.dep_, TermColors.ENDC, f'[{dep_span(doc, token.head)}] ->',
                  TermColors.PINK, dep_span(doc, token, True), TermColors.ENDC)


def store_model(nlp, output_dir=None):
    # save model to output directory
    if output_dir is not None:
        output_dir = Path(output_dir)
        if not output_dir.exists():
            output_dir.mkdir()
        nlp.to_disk(output_dir)
        print("Saved model to", output_dir)


def test_model(nlp, interactive=False):
    texts = [
        "peste 3 zile mergem la bunici",
        "ochelarii mei sunt în sertarul din sufragerie",
        "am pus mingea sub patul din dormitor acum o săptămână",
        "mâine începe un serial la televizor",
        "pălăria Adinei este frumoasă",
        "săptămâna mea de vacanță de vară este luna viitoare",
        "bunicul meu are de hrănit animalele în fiecare zi",
        "acum un an cineva și-a scris numele acolo",
        "de mâine va fi cald afară",
        "peste câteva săptămâni se va termina starea de urgență",
        "numele de utilizator al Irinei este irina",
        "ieri m-am jucat fifa 2 ore",
    ]

    if interactive:
        print("\nInteractive testing. Enter a phrase to parse it:")
        while True:
            phrase = input("\n>> ")
            doc = nlp(phrase)
            print_parse_result(doc)
    else:
        docs = nlp.pipe(texts)
        for doc in docs:
            print('\n', doc.text)
            print_parse_result(doc)


if __name__ == "__main__":
    analyze_data(TRAIN_DATA)

    model = None
    # model = train("spacy_ro", n_iter=40)
    # store_model(model, '../models/spacy-syntactic')

    if model is None:
        model = spacy.load('../models/spacy-syntactic')

    test_model(model, True)
