# coding: utf-8
"""
Using the parser to recognise your own semantics
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
from spacy import displacy
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
from drafts.types import dependency_types
from drafts.print_utils import TermColors

# training data: texts, heads and dependency labels
# for no relation, we simply chose an arbitrary dependency label, e.g. '-'
TRAIN_DATA = [
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
            "deps": ['când', 'care', '-', '-', 'ROOT', 'ce', 'prep', 'care', 'prep', 'ce fel de', 'ce fel de'],
        }
    ),
    (
        "ceasul fetei de acolo e scump",
        {
            "heads": [4, 0, 3, 1, 4, 4],
            "deps": ['cine', 'al cui', 'prep', 'care', 'ROOT', 'cum este'],
        }
    ),
    (
        "de azi încep tema de la mate",
        {
            "heads": [1, 2, 2, 2, 5, 6, 3],
            "deps": ['prep', 'când', 'ROOT', 'ce', '-', 'prep', 'care'],
        }
    ),
    (
        "peste o săptămână o să vină Alina pe la mine",
        {
            "heads": [2, 2, 5, 5, 5, 5, 5, 8, 9, 5],
            "deps": ['prep', 'cât', 'cât timp', '-', '-', 'ROOT', 'cine', '-', 'prep', 'unde'],
        }
    ),
    (
        "anul trecut am luat un monitor de acasă",
        {
            "heads": [3, 0, 3, 3, 5, 3, 7, 3],
            "deps": ['când', 'care', '-', 'ROOT', '-', 'ce', 'prep', 'unde'],
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
            "deps": ['care', 'cine', 'care', 'prep', 'care', 'ROOT', 'ce'],
        }
    ),
    (
        "trebuie să iau pastila de hipertensiune seara și dimineața",
        {
            "heads": [0, 2, 2, 3, 5, 3, 2, 8, 2],
            "deps": ['ROOT', '-', 'ce', 'ce', 'prep', 'care', 'când', '-', 'când'],
        }
    ),
    (
        "o să trebuiască să merg la serviciu începând de luna viitoare",
        {
            "heads": [2, 2, 2, 4, 2, 6, 4, 9, 9, 4, 9],
            "deps": ['-', '-', 'ROOT', '-', 'ce', 'prep', 'unde', '-', 'prep', 'când', 'care'],
        }
    ),
    (
        "am pus joia trecută ochelarii mei de soare în sertarul meu din camera mea",
        {
            "heads": [1, 1, 1, 2, 1, 4, 7, 4, 9, 1, 9, 12, 9, 12],
            "deps": ['-', 'ROOT', 'când', 'care', 'ce', 'al cui', 'prep', 'care', 'prep', 'unde', 'al cui', 'prep',
                     'care', 'al cui'],
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
            "heads": [7, 2, 3, 0, 6, 6, 0, 7, 7, 10, 7, 12, 10],
            "deps": ['cine', '-', 'prep', 'care', '-', '-', 'al cui', 'ROOT', 'unde', 'prep', 'unde', 'prep', 'care'],
        }
    ),
    (
        "mâine voi rezolva problema cu furtunul stricat",
        {
            "heads": [2, 2, 2, 2, 5, 3, 5],
            "deps": ['când', '-', 'ROOT', 'ce', 'prep', 'care', 'care'],
        }
    ),
    (
        "ultima zi de lucru a mea e peste două săptămâni",
        {
            "heads": [1, 6, 3, 1, 5, 1, 6, 9, 9, 6],
            "deps": ['care', 'cine', 'prep', 'care', '-', 'al cui', 'ROOT', 'prep', 'cât', 'cât timp'],
        }
    ),
    (
        "am de făcut o temă grea până vineri",
        {
            "heads": [0, 2, 0, 4, 2, 4, 7, 2],
            "deps": ['ROOT', 'prep', 'ce', '-', 'ce', 'ce fel de', 'prep', 'când'],
        }
    ),
    (
        "în fiecare zi fac antrenament sportiv",
        {
            "heads": [2, 2, 3, 3, 3, 4],
            "deps": ['prep', 'care', 'cât de des', 'ROOT', 'ce', 'ce fel de'],
        }
    ),
    (
        "am de terminat proiectul la programare până în mai",
        {
            "heads": [0, 2, 0, 2, 5, 3, 8, 8, 2],
            "deps": ['ROOT', '-', 'ce', 'ce', 'prep', 'care', 'prep', 'prep', 'când'],
        }
    ),
    (
        "voi avea de făcut rapoartele pentru ultima lună până pe 23 iunie 2021",
        {
            "heads": [1, 1, 3, 1, 3, 7, 7, 4, 10, 10, 3, 10, 11],
            "deps": ["-", "ROOT", "prep", "ce", "ce", "-", "care", "care", "prep", "prep", "când", "care", "care"]
        }
    ),
    (
        "numărul de la interfon al verișoarei mele Iulia este 24",
        {
            "heads": [8, 2, 3, 0, 5, 0, 5, 5, 8, 8],
            "deps": ["cine", "-", "prep", "care", "-", "al cui", "al cui", "care", "ROOT", "care este"]
        }
    ),
    (
        "laborantul meu de la EIM e Dan Bina",
        {
            "heads": [5, 0, 3, 4, 0, 5, 5, 6],
            "deps": ["cine", "al cui", "-", "prep", "care", "ROOT", "care este", "care"]
        }
    ),
    (
        "zilele ăstea am făcut câte 30 de flotări",
        {
            "heads": [3, 0, 3, 3, 5, 7, 7, 3],
            "deps": ["când", "care", "-", "ROOT", "-", "cât", "prep", "ce"]}
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
            "deps": ["cine", "cui", "-", "-", "ROOT", "ce", "prep", "când", "care", "care"]
        }
    ),
    (
        "acela și-a făcut tema acum 2 zile",
        {
            "heads": [4, 4, 1, 4, 4, 4, 8, 8, 5],
            "deps": ["cine", "cui", "-", "-", "ROOT", "ce", "prep", "cât", "cât timp"]}
    ),
    (
        "am terminat de spălat vasele acum 30 de minute",
        {
            "heads": [1, 1, 3, 1, 3, 8, 8, 8, 1],
            "deps": ["-", "ROOT", "-", "ce", "ce", "prep", "cât", "prep", "cât timp"]}
    ),
    (
        "acum 3 ore aveam 60 de kilograme",
        {
            "heads": [2, 2, 3, 3, 6, 6, 3],
            "deps": ["prep", "cât", "cât timp", "ROOT", "cât", "prep", "ce"]}
    ),
    (
        "ultima dată m-am tuns acum 2 luni",
        {
            "heads": [1, 5, 5, 2, 5, 5, 8, 8, 5],
            "deps": ["care", "când", "pe cine", "-", "-", "ROOT", "prep", "cât", "cât timp"]}
    ),
    (
        "afară e foarte frig de azi de la prânz",
        {
            "heads": [1, 1, 3, 1, 5, 1, 7, 8, 1],
            "deps": ["unde", "ROOT", "-", "cum este", "prep", "când", "-", "prep", "când"]}
    ),
    (
        "documentarul va fi dat pe Discovery de sâmbăta viitoare",
        {
            "heads": [3, 3, 3, 3, 5, 3, 7, 3, 7],
            "deps": ["cine", "-", "-", "ROOT", "prep", "unde", "prep", "când", "care"]}
    ),
    (
        "proiectul la franceză trebuie predat până la sfârșitul sesiunii",
        {
            "heads": [4, 2, 0, 4, 4, 6, 7, 4, 7],
            "deps": ["cine", "prep", "care", "-", "ROOT", "-", "prep", "când", "al cui"]}
    ),
    (
        "după curs am ajutat-o pe profesoara de chimie la un experiment complicat",
        {
            "heads": [1, 3, 3, 3, 5, 3, 7, 3, 9, 7, 12, 12, 3, 12],
            "deps": ["prep", "când", "-", "ROOT", "-", "pe cine", "prep", "pe cine", "prep", "care", "prep", "-",
                     "la ce",
                     "ce fel de"]}
    ),
    (
        "adresa de email a lui george ionescu e george@gmail.com",
        {
            "heads": [7, 2, 0, 5, 5, 0, 5, 7, 7],
            "deps": ["cine", "prep", "care", "-", "-", "al cui", "care", "ROOT", "care este"]}
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
            "deps": ["prep", "când", "al cui", "pe cine", "-", "-", "ROOT", "-", "ce", "unde"]}
    ),
    (
        "aici nu a mai venit un urs de mult timp",
        {
            "heads": [4, 4, 4, 4, 4, 6, 4, 9, 9, 4],
            "deps": ["unde", "-", "-", "-", "ROOT", "-", "ce", "prep", "cât", "cât timp"]}
    ),
    (
        "după două săptămâni o să plec de aici",
        {
            "heads": [5, 2, 0, 5, 5, 5, 7, 5],
            "deps": ["prep", "cât", "cât timp", "-", "-", "ROOT", "prep", "unde"]}
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
            "deps": ["prep", "unde", "-", "-", "-", "ROOT", "prep", "cât", "cât timp"]}
    ),
    (
        "Dan Ion a ajuns la Craiova în 3 ore și 20 de minute",
        {
            "heads": [3, 0, 3, 3, 5, 3, 8, 8, 3, 12, 12, 12, 8],
            "deps": ["cine", "care", "-", "ROOT", "prep", "unde", "prep", "cât", "cât timp", "-", "cât", "prep",
                     "cât timp"]}
    ),
    (
        "capsatorul cel mare se află pe masa din încăperea de lângă baie",
        {
            "heads": [4, 2, 0, 4, 4, 6, 4, 8, 6, 10, 11, 8],
            "deps": ["cine", "-", "care", "-", "ROOT", "prep", "unde", "prep", "care", "-", "prep", "care"]}
    ),
    (
        "am vizitat-o pe Irina de ziua lui mihai",
        {
            "heads": [1, 1, 3, 1, 5, 1, 7, 1, 9, 7],
            "deps": ["-", "ROOT", "-", "pe cine", "prep", "pe cine", "prep", "când", "-", "al cui"]}
    ),
    (
        "de obicei merg la alergat în fiecare săptămână pe malul lacului morii",
        {
            "heads": [1, 2, 2, 4, 2, 7, 7, 2, 9, 2, 9, 10],
            "deps": ["prep", "cât de des", "ROOT", "prep", "unde", "prep", "care", "cât de des", "prep", "unde",
                     "al cui", "al cui"]}
    ),
    (
        "trebuie să îmi pun picături în ochi de 3 ori pe zi",
        {
            "heads": [0, 3, 3, 0, 3, 6, 3, 9, 9, 3, 11, 9],
            "deps": ["ROOT", "-", "cui", "ce", "ce", "prep", "unde", "prep", "cât", "cât de des", "prep",
                     "la cât timp"]}
    ),
    (
        "ea iese afară de 10 ori pe lună",
        {
            "heads": [1, 1, 1, 5, 5, 1, 7, 5],
            "deps": ["cine", "ROOT", "unde", "prep", "cât", "cât de des", "prep", "la cât timp"]}
    ),
    (
        "în timpul anului universitar ajung acasă cam o dată la două săptămâni",
        {
            "heads": [1, 2, 4, 2, 4, 4, 8, 8, 4, 11, 11, 8],
            "deps": ["prep", "când", "al cui", "care", "ROOT", "unde", "-", "cât", "cât de des", "prep", "cât",
                     "la cât timp"]}
    ),
    (
        "la mine s-a oprit apa caldă de câteva ore",
        {
            "heads": [1, 5, 5, 2, 5, 5, 5, 6, 10, 10, 5],
            "deps": ["prep", "unde", "pe cine", "-", "-", "ROOT", "cine", "care", "prep", "cât", "cât timp"]}
    ),
    (
        "la facultate există multe calculatoare cu procesoare de generație nouă",
        {
            "heads": [1, 2, 2, 4, 2, 6, 4, 8, 6, 8],
            "deps": ["prep", "unde", "ROOT", "cât", "ce", "prep", "ce fel de", "prep", "ce fel de", "ce fel de"]}
    ),
    (
        "o dată pe lună îi fac cartofi prăjiți alexandrei",
        {
            "heads": [1, 5, 3, 1, 5, 5, 5, 6, 5],
            "deps": ["cât", "cât de des", "prep", "la cât timp", "cui", "ROOT", "ce", "ce fel de", "cui"]}
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
            "deps": ["cine", "cui", "-", "ROOT", "unde", "-", "cât timp", "prep", "care"]}
    ),
    (
        "sala laboratorului de ML este EG105",
        {
            "heads": [4, 0, 3, 1, 4, 4],
            "deps": ["cine", "al cui", "prep", "care", "ROOT", "care este"]}
    ),
    (
        "dimensiunile portbagajului meu sunt acestea",
        {
            "heads": [3, 0, 1, 3, 3],
            "deps": ["cine", "al cui", "al cui", "ROOT", "care este"]}
    ),
    (
        "șurubelnița dreaptă e în dulapul din camera mea",
        {
            "heads": [2, 0, 2, 4, 2, 6, 4, 6],
            "deps": ["cine", "care", "ROOT", "prep", "unde", "prep", "care", "al cui"]}
    ),
    (
        "sezonul de pescuit se finalizează pe 2 iunie",
        {
            "heads": [4, 2, 0, 4, 4, 6, 4, 6],
            "deps": ["cine", "prep", "care", "-", "ROOT", "prep", "când", "care"]}
    ),
    (
        "mi-am făcut pașaportul acum 3 săptămâni",
        {
            "heads": [3, 0, 3, 3, 3, 7, 7, 3],
            "deps": ["cui", "-", "-", "ROOT", "ce", "prep", "cât", "cât timp"]}
    ),
    (
        "concursul va fi pe 12 ianuarie",
        {
            "heads": [2, 2, 2, 4, 2, 4],
            "deps": ["cine", "-", "ROOT", "prep", "când", "care"]}
    ),
    (
        "permisul meu de conducere e în torpedoul de la mașină",
        {
            "heads": [4, 0, 3, 0, 4, 6, 4, 8, 9, 6],
            "deps": ["cine", "al cui", "prep", "care", "ROOT", "prep", "unde", "-", "prep", "care"]}
    ),
    (
        "eu stau la adresa strada Ecaterina Teodoroiu numărul 17",
        {
            "heads": [1, 1, 3, 1, 3, 4, 5, 3, 7],
            "deps": ["cine", "ROOT", "prep", "unde", "care", "care", "care", "care", "care"]}
    ),
    (
        "adresa elenei este strada zorilor numărul 9",
        {
            "heads": [2, 0, 2, 2, 3, 3, 5],
            "deps": ["cine", "al cui", "ROOT", "care este", "care", "care", "care"]}
    ),
    (
        "Maria Popescu locuiește pe Bulevardul Timișoara numărul 5",
        {
            "heads": [2, 0, 2, 4, 2, 4, 4, 6],
            "deps": ["cine", "care", "ROOT", "prep", "unde", "care", "care", "care"]}
    ),
    (
        "cheile mele de la casă sunt ușoare",
        {
            "heads": [5, 0, 3, 4, 0, 5, 5],
            "deps": ["cine", "al cui", "-", "prep", "care", "ROOT", "cum este"]}
    ),
    (
        "Darius și-a schimbat domiciliul iarna trecută",
        {
            "heads": [4, 4, 1, 4, 4, 4, 4, 6],
            "deps": ["cine", "cui", "-", "-", "ROOT", "ce", "când", "care"]}
    ),
    (
        "prezentarea proiectului durează 45 de minute",
        {
            "heads": [2, 0, 2, 5, 5, 2],
            "deps": ["cine", "al cui", "ROOT", "cât", "prep", "cât timp"]}
    ),
    (
        "Jack a fost la biserică duminică",
        {
            "heads": [2, 2, 2, 4, 2, 2],
            "deps": ["cine", "-", "ROOT", "prep", "unde", "când"]}
    ),
    (
        "poimâine merg la mall",
        {
            "heads": [1, 1, 3, 1],
            "deps": ["când", "ROOT", "prep", "unde"]}
    ),
    (
        "peste 2 ani o să termin masterul",
        {
            "heads": [2, 2, 5, 5, 5, 5, 5],
            "deps": ["prep", "cât", "cât timp", "-", "-", "ROOT", "ce"]}
    ),
    (
        "mi-am făcut analize primăvara trecută",
        {
            "heads": [3, 0, 3, 3, 3, 3, 5],
            "deps": ["cui", "-", "-", "ROOT", "ce", "când", "care"]}
    ),
    (
        "restricțiile de circulație se încheie la vară",
        {
            "heads": [4, 2, 0, 4, 4, 6, 4],
            "deps": ["cine", "prep", "care", "-", "ROOT", "prep", "când"]}
    ),
    (
        "garanția de la frigider se termină marțea viitoare",
        {
            "heads": [5, 2, 3, 0, 5, 5, 5, 6],
            "deps": ["cine", "-", "prep", "care", "-", "ROOT", "când", "care"]}
    ),
    (
        "iarna trecută a nins afară",
        {
            "heads": [3, 0, 3, 3, 3],
            "deps": ["când", "care", "-", "ROOT", "unde"]}
    ),
    (
        "la iarnă o să învăț să schiez",
        {
            "heads": [1, 4, 4, 4, 4, 6, 4],
            "deps": ["prep", "când", "-", "-", "ROOT", "-", "ce"]}
    ),
    (
        "întâlnirea cu managerul este peste o jumătate de oră",
        {
            "heads": [3, 2, 0, 3, 6, 6, 3, 8, 6],
            "deps": ["cine", "prep", "care", "ROOT", "prep", "cât", "cât timp", "prep", "ce fel de"]}
    ),
    (
        "pălăria Adinei este frumoasă",
        {
            "heads": [2, 0, 2, 2],
            "deps": ["cine", "al cui", "ROOT", "cum este"]}
    ),
    (
        "săptămâna mea de vacanță de vară este luna viitoare",
        {
            "heads": [6, 0, 3, 0, 5, 3, 6, 6, 7],
            "deps": ["cine", "al cui", "prep", "care", "prep", "ce fel de", "ROOT", "când", "care"]}
    ),
    (
        "acum un an cineva a scris numele acolo",
        {
            "heads": [2, 2, 5, 5, 5, 5, 5, 5],
            "deps": ["prep", "cât", "cât timp", "cine", "-", "ROOT", "ce", "unde"]}
    ),
    (
        "am lăsat lădița cu cartofi în pivniță",
        {
            "heads": [1, 1, 1, 4, 2, 6, 1],
            "deps": ["-", "ROOT", "ce", "prep", "care", "prep", "unde"]}
    ),
    (
        "lămpile solare sunt de la bricostore",
        {
            "heads": [2, 0, 2, 4, 5, 2],
            "deps": ["cine", "care", "ROOT", "-", "prep", "unde"]}
    ),
    (
        "am lăsat suportul de brad la țară în garaj",
        {
            "heads": [1, 1, 1, 4, 2, 6, 1, 8, 1],
            "deps": ["-", "ROOT", "ce", "prep", "care", "prep", "unde", "prep", "unde"]}
    ),
    (
        "până unde a alergat aseară marius",
        {
            "heads": [1, 3, 3, 3, 3, 3],
            "deps": ["prep", "unde", "-", "ROOT", "când", "cine"]}
    ),
    (
        "anul nașterii lui Ștefan cel Mare a fost 1433",
        {
            "heads": [7, 0, 3, 1, 5, 3, 7, 7, 7],
            "deps": ["cine", "al cui", "-", "al cui", "-", "care", "-", "ROOT", "care este"]}
    ),
    (
        "suprafața apartamentului de la București este de 58mp",
        {
            "heads": [5, 0, 3, 4, 1, 5, 7, 5],
            "deps": ["cine", "al cui", "-", "prep", "care", "ROOT", "prep", "care este"]}
    ),
    (
        "Viorel e născut pe 16 mai 1998",
        {
            "heads": [1, 1, 1, 4, 2, 4, 5],
            "deps": ["cine", "ROOT", "ce", "prep", "când", "care", "care"]}
    ),
    (
        "pe 3 iulie se termină sesiunea de licență",
        {
            "heads": [1, 4, 1, 4, 4, 4, 7, 5],
            "deps": ["prep", "când", "care", "-", "ROOT", "cine", "prep", "care"]}
    ),
    (
        "ziua Daianei este în august",
        {
            "heads": [2, 0, 2, 4, 2],
            "deps": ["cine", "al cui", "ROOT", "prep", "când"]}
    ),
    (
        "din octombrie apare un nou film la cinema",
        {
            "heads": [1, 2, 2, 5, 5, 2, 7, 2],
            "deps": ["prep", "când", "ROOT", "-", "ce fel de", "ce", "prep", "unde"]}
    ),
    (
        "noile autobuze au apărut în decembrie",
        {
            "heads": [1, 3, 3, 3, 5, 3],
            "deps": ["care", "cine", "-", "ROOT", "prep", "când"]}
    ),
    (
        "coletul cu jacheta va ajunge miercuri",
        {
            "heads": [4, 2, 0, 4, 4, 4],
            "deps": ["cine", "prep", "care", "-", "ROOT", "când"]}
    ),
    (
        "testul de curs la rețele neurale a fost joi",
        {
            "heads": [7, 2, 0, 4, 0, 4, 7, 7, 7],
            "deps": ["cine", "prep", "care", "prep", "care", "ce fel de", "-", "ROOT", "când"]}
    ),
    (
        "vineri încep promoțiile de black friday",
        {
            "heads": [1, 1, 1, 4, 2, 4],
            "deps": ["când", "ROOT", "ce", "prep", "care", "care"]}
    ),
    (
        "am terminat proiecul la programare web alaltăieri",
        {
            "heads": [1, 1, 1, 4, 2, 4, 1],
            "deps": ["-", "ROOT", "ce", "prep", "care", "ce fel de", "când"]}
    ),
    (
        "sesiunea din browser a expirat acum 10 secunde",
        {
            "heads": [4, 2, 0, 4, 4, 7, 7, 4],
            "deps": ["cine", "prep", "care", "-", "ROOT", "prep", "cât", "cât timp"]}
    ),
    (
        "peste 2 ani termină Nicoleta masterul",
        {
            "heads": [2, 2, 3, 3, 3, 3],
            "deps": ["prep", "cât", "cât timp", "ROOT", "cine", "ce"]}
    ),
    (
        "prețul canapelei a fost de 1300 de lei",
        {
            "heads": [3, 0, 3, 3, 5, 3, 7, 5],
            "deps": ["cine", "al cui", "-", "ROOT", "prep", "care este", "prep", "ce fel de"]}
    ),
    (
        "vacanța de vară începe pe 30 iunie",
        {
            "heads": [3, 2, 0, 3, 5, 3, 5],
            "deps": ["cine", "prep", "care", "ROOT", "prep", "când", "care"]}
    ),
    (
        "victor stă pe aleea romancierilor numărul 12",
        {
            "heads": [1, 1, 3, 1, 3, 3, 5],
            "deps": ["cine", "ROOT", "prep", "unde", "care", "care", "care"]}
    ),
    (
        "pliculețele de praf de copt sunt în cutiuța din primul sertar",
        {
            "heads": [5, 2, 0, 4, 2, 5, 7, 5, 10, 10, 7],
            "deps": ["cine", "prep", "care", "prep", "ce fel de", "ROOT", "prep", "unde", "prep", "care", "care"]}
    ),
    (
        "am așezat etuiul de la ochelari peste teancul de reviste din hol",
        {
            "heads": [1, 1, 1, 4, 5, 2, 7, 1, 9, 7, 11, 7],
            "deps": ["-", "ROOT", "ce", "-", "prep", "care", "prep", "unde", "prep", "care", "prep", "care"]}
    ),
    (
        "prețul ceasului meu Atlantic a fost 500 de lei",
        {
            "heads": [5, 0, 1, 1, 5, 5, 5, 8, 6],
            "deps": ["cine", "al cui", "al cui", "care", "-", "ROOT", "care este", "prep", "ce fel de"]}
    ),
    (
        "numele profesoarei mele de biologie din liceu este Mariana Mihai",
        {
            "heads": [7, 0, 1, 4, 1, 6, 1, 7, 7, 8],
            "deps": ["cine", "al cui", "al cui", "prep", "care", "prep", "care", "ROOT", "care este", "care"]}
    ),
    (
        "modelul tastaturii mele este logitech mx keys",
        {
            "heads": [3, 0, 1, 3, 3, 4, 5],
            "deps": ["cine", "al cui", "al cui", "ROOT", "care este", "care", "care"]}
    ),
    (
        "peste 123 de secunde trecem în noul an",
        {
            "heads": [3, 3, 3, 4, 4, 7, 7, 4],
            "deps": ["prep", "cât", "prep", "cât timp", "ROOT", "prep", "care", "unde"]}
    ),
    (
        "la primăvară e gata blocul",
        {
            "heads": [1, 2, 2, 2, 2],
            "deps": ["prep", "când", "ROOT", "cum este", "cine"]}
    ),
    (
        "mâine ajunge Alex la întorsura Buzăului",
        {
            "heads": [1, 1, 1, 4, 1, 4],
            "deps": ["când", "ROOT", "cine", "prep", "unde", "al cui"]}
    ),
    (
        "ieri s-a terminat perioada de pregătire a elevilor",
        {
            "heads": [4, 4, 1, 4, 4, 4, 7, 5, 9, 5],
            "deps": ["când", "pe cine", "-", "-", "ROOT", "cine", "prep", "care", "-", "al cui"]}
    ),
    (
        "am găsit rezolvarea problemei",
        {
            "heads": [1, 1, 1, 2],
            "deps": ["-", "ROOT", "ce", "al cui"]}
    ),
    (
        "trebuie să mă tund până pe 1 iunie",
        {
            "heads": [0, 3, 3, 0, 5, 6, 3, 6],
            "deps": ["ROOT", "-", "pe cine", "ce", "-", "prep", "când", "care"]}
    ),
    (
        "miercurea viitoare începe concursul de programare",
        {
            "heads": [2, 0, 2, 2, 5, 3],
            "deps": ["când", "care", "ROOT", "cine", "prep", "care"]}
    ),
    (
        "săptămâna trecută am udat pomul meu de afară",
        {
            "heads": [3, 0, 3, 3, 3, 4, 7, 4],
            "deps": ["când", "care", "-", "ROOT", "ce", "al cui", "prep", "care"]}
    ),
    (
        "azi începe vacanța noastră",
        {
            "heads": [1, 1, 1, 2],
            "deps": ["când", "ROOT", "cine", "al cui"]}
    ),
    (
        "ziua de naștere a lui alex este pe 5 mai",
        {
            "heads": [6, 2, 0, 5, 5, 0, 6, 8, 6, 8],
            "deps": ["cine", "prep", "care", "-", "-", "al cui", "ROOT", "prep", "când", "care"]}
    ),
    (
        "eu locuiesc pe bulevardul Timișoara",
        {
            "heads": [1, 1, 3, 1, 3],
            "deps": ['cine', 'ROOT', 'prep', 'unde', 'care'],
        }
    ),
    (
        "eu merg spre casă azi",
        {
            "heads": [1, 1, 3, 1, 1],
            "deps": ["cine", "ROOT", "prep", "unde", "când"]}
    ),
    (
        "cărțile de matematică ale mariei sunt sub pat",
        {
            "heads": [5, 2, 0, 4, 0, 5, 7, 5],
            "deps": ["cine", "prep", "care", "-", "al cui", "ROOT", "prep", "unde"]}
    ),
    (
        "ieri am fost în București",
        {
            "heads": [2, 2, 2, 4, 2],
            "deps": ['când', '-', 'ROOT', 'prep', 'unde'],
        },
    ),
    (
        "am fost la sală ieri seara",
        {
            "heads": [1, 1, 3, 1, 1, 4],
            "deps": ["-", "ROOT", "prep", "unde", "când", "care"]}
    ),
    (
        "cursul se ține în sala EC105 de la parter din facultatea noastră",
        {
            "heads": [2, 2, 2, 4, 2, 4, 7, 8, 4, 10, 4, 10],
            "deps": ["cine", "-", "ROOT", "prep", "unde", "care", "-", "prep", "care", "prep", "care", "al cui"]}
    ),
    (
        "Maria stă la apartamentul 23 pe strada principală",
        {
            "heads": [1, 1, 3, 1, 3, 6, 1, 6],
            "deps": ["cine", "ROOT", "prep", "unde", "care", "prep", "unde", "care"]}
    ),
    (
        "floarea din bucătărie se află pe pervaz sub geam",
        {
            "heads": [4, 2, 0, 4, 4, 6, 4, 8, 4],
            "deps": ["cine", "prep", "care", "-", "ROOT", "prep", "unde", "prep", "unde"]}
    ),
    (
        "cardul de memorie al telefonului e în cutia albastră din sertarul lui Adrian Enache",
        {
            "heads": [5, 2, 0, 4, 0, 5, 7, 5, 7, 10, 7, 12, 10, 12],
            "deps": ["cine", "prep", "care", "-", "care", "ROOT", "prep", "unde", "care", "prep", "care", "-", "al cui",
                     "care"]}
    ),
    (
        "dioptriile mele de la ochelari erau ultima dată acestea",
        {
            "heads": [5, 0, 3, 4, 0, 5, 7, 5, 5],
            "deps": ["cine", "al cui", "-", "prep", "care", "ROOT", "care", "când", "care este"]}
    ),
    (
        "sala laboratorului de PP este EG321",
        {
            "heads": [4, 0, 3, 1, 4, 4],
            "deps": ["cine", "al cui", "prep", "care", "ROOT", "care este"]}
    ),
    (
        "până sâmbătă a fost interzis accesul",
        {
            "heads": [1, 3, 3, 3, 3, 3],
            "deps": ["prep", "când", "-", "ROOT", "cum este", "cine"]}
    ),
    (
        "numărul blocului fratelui Mihaelei este 10",
        {
            "heads": [4, 0, 1, 2, 4, 4],
            "deps": ["cine", "al cui", "al cui", "al cui", "ROOT", "care este"]}
    ),
    (
        "codul PIN de la cardul meu de sănătate este 0000",
        {
            "heads": [8, 0, 3, 4, 0, 4, 7, 4, 8, 8],
            "deps": ["cine", "care", "-", "prep", "care", "al cui", "prep", "care", "ROOT", "care este"]}
    ),
    (
        "viteza trenurilor din România este foarte mică",
        {
            "heads": [4, 0, 3, 1, 4, 6, 4],
            "deps": ["cine", "al cui", "prep", "care", "ROOT", "-", "cum este"]}
    ),
    (
        "numărul de telefon al lui Dan Miron este 4312321",
        {
            "heads": [7, 2, 0, 5, 5, 0, 5, 7, 7],
            "deps": ["cine", "prep", "care", "-", "-", "al cui", "care", "ROOT", "care este"]}
    ),
    (
        "seria mea de la buletin este GG2020",
        {
            "heads": [5, 0, 3, 4, 0, 5, 5],
            "deps": ["cine", "al cui", "-", "prep", "care", "ROOT", "care este"]}
    ),
    (
        "secvența de mutări pentru câștigarea jocului este ab43bdnfdsa90",
        {
            "heads": [6, 2, 0, 4, 0, 4, 6, 6],
            "deps": ["cine", "prep", "care", "prep", "care", "al cui", "ROOT", "care este"]}
    ),
    (
        "prețul canapelei a fost 1300 de lei",
        {
            "heads": [3, 0, 3, 3, 3, 6, 4],
            "deps": ["cine", "al cui", "-", "ROOT", "care este", "prep", "ce fel de"]}
    ),
    (
        "trebuie să deschid poarta casei în 30 de secunde",
        {
            "heads": [0, 2, 0, 2, 3, 8, 8, 8, 2],
            "deps": ["ROOT", "-", "ce", "ce", "al cui", "prep", "cât", "prep", "cât timp"]}
    ),
    (
        "suprafața apartamentului de la Ploiești este de 60mp",
        {
            "heads": [5, 0, 3, 4, 1, 5, 7, 5],
            "deps": ["cine", "al cui", "-", "prep", "care", "ROOT", "prep", "care este"]}
    ),
    (
        "lunea trecută a sosit mobilă pentru noua terasă",
        {
            "heads": [3, 0, 3, 3, 3, 7, 7, 4],
            "deps": ["când", "care", "-", "ROOT", "ce", "prep", "care", "ce fel de"]}
    ),
    (
        "în care săptămână e examenul de învățare automată",
        {
            "heads": [2, 2, 3, 3, 3, 6, 4, 6],
            "deps": ["prep", "care", "când", "ROOT", "cine", "prep", "care", "ce fel de"]}
    ),
    (
        "unde am lăsat șosetele norocoase de la colegul meu",
        {
            "heads": [2, 2, 2, 2, 3, 6, 7, 3, 7],
            "deps": ["unde", "-", "ROOT", "ce", "care", "-", "prep", "care", "al cui"]}
    ),
    (
        "Bianca Zăvelcă o să se ducă la facultate la anul",
        {
            "heads": [5, 0, 5, 5, 5, 5, 7, 5, 9, 5],
            "deps": ["cine", "care", "-", "-", "-", "ROOT", "prep", "unde", "prep", "când"]}
    ),
    (
        "Oana și-a luat geacă de iarnă marți",
        {
            "heads": [4, 4, 1, 4, 4, 4, 7, 5, 4],
            "deps": ["cine", "cui", "-", "-", "ROOT", "ce", "prep", "ce fel de", "când"]}
    ),
    (
        "am primit o scrisoare de recomandare de la un profesor din facultatea mea",
        {
            "heads": [1, 1, 3, 1, 5, 3, 7, 9, 9, 1, 11, 9, 11],
            "deps": ["-", "ROOT", "-", "ce", "-", "ce fel de", "-", "prep", "-", "unde", "prep", "ce fel de", "al cui"]}
    ),
    (
        "vinerea trecută s-a rupt un șurub de prindere de la gard",
        {
            "heads": [5, 0, 5, 2, 5, 5, 7, 5, 9, 7, 11, 12, 7],
            "deps": ["când", "care", "pe cine", "-", "-", "ROOT", "-", "cine", "prep", "ce fel de", "-", "prep",
                     "ce fel de"]}
    ),
    (
        "în vaza de la geam sunt 35 de trandafiri de la o florărie cunoscută",
        {
            "heads": [1, 5, 3, 4, 1, 5, 8, 8, 5, 10, 12, 12, 8, 12],
            "deps": ["prep", "unde", "-", "prep", "care", "ROOT", "cât", "prep", "ce", "-", "prep", "-", "ce fel de",
                     "ce fel de"]}
    ),
    (
        "primăvara viitoare încep lucrările de la noua autostradă",
        {
            "heads": [2, 0, 2, 2, 5, 7, 7, 3],
            "deps": ["când", "care", "ROOT", "cine", "-", "prep", "care", "care"]}
    ),
    (
        "peste 3 ani se va închide o fabrică de pâine",
        {
            "heads": [2, 2, 5, 5, 5, 5, 7, 5, 9, 7],
            "deps": ["prep", "cât", "cât timp", "-", "-", "ROOT", "-", "cine", "prep", "ce fel de"]}
    ),
    (
        "pe Maria am văzut-o la magazinul de articole de pescuit joia trecută",
        {
            "heads": [1, 3, 3, 3, 5, 3, 7, 3, 9, 7, 11, 9, 3, 12],
            "deps": ["prep", "pe cine", "-", "ROOT", "-", "pe cine", "prep", "unde", "prep", "care", "prep",
                     "ce fel de", "când", "care"]}
    ),
    (
        "cartea cu desene de colorat este plină",
        {
            "heads": [5, 2, 0, 4, 2, 5, 5],
            "deps": ["cine", "prep", "care", "prep", "ce fel de", "ROOT", "cum este"]}
    ),
    (
        "l-am pus pe Doru la cârma avionului",
        {
            "heads": [3, 0, 3, 3, 5, 3, 7, 3, 7],
            "deps": ["pe cine", "-", "-", "ROOT", "prep", "pe cine", "prep", "unde", "al cui"]}
    ),
    (
        "cărămida l-a lovit pe zidar la piciorul stâng",
        {
            "heads": [4, 4, 1, 4, 4, 6, 4, 8, 4, 8],
            "deps": ["cine", "pe cine", "-", "-", "ROOT", "prep", "pe cine", "prep", "unde", "care"]}
    ),
    (
        "pe mine m-a prins ploaia în parcare sâmbătă",
        {
            "heads": [1, 5, 5, 2, 5, 5, 5, 8, 5, 5],
            "deps": ["prep", "pe cine", "pe cine", "-", "-", "ROOT", "cine", "prep", "unde", "când"]}
    ),
    (
        "un purice l-a mușcat pe Grivei azi noapte",
        {
            "heads": [1, 5, 5, 2, 5, 5, 7, 5, 5, 8],
            "deps": ["-", "cine", "pe cine", "-", "-", "ROOT", "prep", "pe cine", "când", "care"]}
    ),
    (
        "l-am certat pe colegul meu de cămin alaltăseară",
        {
            "heads": [3, 0, 3, 3, 5, 3, 5, 8, 5, 3],
            "deps": ["pe cine", "-", "-", "ROOT", "prep", "pe cine", "al cui", "prep", "care", "când"]}
    ),
    (
        "i-am lăsat Elenei 500 de euro sub un dosar din raft",
        {
            "heads": [3, 0, 3, 3, 3, 7, 7, 3, 10, 10, 3, 12, 10],
            "deps": ["cui", "-", "-", "ROOT", "cui", "cât", "prep", "ce", "prep", "-", "unde", "prep", "ce fel de"]}
    ),
    (
        "andi i-a luat corinei o mașină scumpă din italia",
        {
            "heads": [4, 4, 1, 4, 4, 4, 7, 4, 7, 10, 7],
            "deps": ["cine", "cui", "-", "-", "ROOT", "cui", "-", "ce", "ce fel de", "prep", "ce fel de"]}
    ),
    (
        "banca i-a dat prietenului meu 20 de mii de lei",
        {
            "heads": [4, 4, 1, 4, 4, 4, 5, 9, 9, 4, 11, 9],
            "deps": ["cine", "cui", "-", "-", "ROOT", "cui", "al cui", "cât", "prep", "ce", "prep", "ce fel de"]}
    ),
    (
        "de miercurea viitoare se deschide un cinematograf din oraș",
        {
            "heads": [1, 4, 1, 4, 4, 6, 4, 8, 6],
            "deps": ["prep", "când", "care", "ROOT", "ROOT", "-", "cine", "prep", "ce fel de"]}
    ),
    (
        "am cunoscut-o pe Ileana la conferința de algoritmi de optimizare de la Toronto",
        {
            "heads": [1, 1, 3, 1, 5, 1, 7, 1, 9, 7, 11, 9, 13, 14, 7],
            "deps": ["-", "ROOT", "-", "pe cine", "prep", "pe cine", "prep", "unde", "prep", "care", "prep",
                     "ce fel de", "-", "prep", "care"]}
    ),
    (
        "de paște o să se întoarcă marin la un post de televiziune",
        {
            "heads": [1, 5, 5, 5, 5, 5, 5, 9, 9, 5, 11, 9],
            "deps": ["prep", "când", "-", "-", "-", "ROOT", "cine", "prep", "-", "unde", "prep", "ce fel de"]}
    ),

    # ------------------------------------ questions ------------------------------------
    (
        "unde se află biletul de avion",
        {
            "heads": [2, 2, 2, 2, 5, 3],
            "deps": ["unde", "-", "ROOT", "cine", "prep", "care"]}
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
            "heads": [2, 2, 2, 2, 5, 6, 3],
            "deps": ["unde", "-", "ROOT", "ce", "-", "prep", "care"]}
    ),
    (
        "cât timp a durat examenul de inteligență artificială",
        {
            "heads": [1, 3, 3, 3, 3, 6, 4, 6],
            "deps": ["cât", "cât timp", "-", "ROOT", "cine", "prep", "care", "ce fel de"]}
    ),
    (
        "când va începe colocviul de luni",
        {
            "heads": [2, 2, 2, 2, 5, 3],
            "deps": ["când", "-", "ROOT", "cine", "prep", "care"]}
    ),
    (
        "până când o să țină înscrierea la facultatea de automatică",
        {
            "heads": [1, 4, 4, 4, 4, 4, 7, 5, 9, 7],
            "deps": ["prep", "când", "-", "-", "ROOT", "cine", "prep", "care", "prep", "care"]}
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
            "deps": ["care", "cine", "-", "ROOT", "prep", "unde"]}
    ),
    (
        "câți kilometri am alergat aseară pe afară",
        {
            "heads": [1, 3, 3, 3, 3, 6, 3],
            "deps": ["cât", "ce", "-", "ROOT", "când", "prep", "unde"]}
    ),
    (
        "câte zile mai sunt până la weekend",
        {
            "heads": [1, 3, 3, 3, 5, 6, 3],
            "deps": ["cât", "cât timp", "-", "ROOT", "-", "prep", "când"]}
    ),
    (
        "când va fi sesiunea",
        {
            "heads": [2, 2, 2, 2],
            "deps": ["când", "-", "ROOT", "cine"]}
    ),
    (
        "când trebuie să merg la control oftalmologic",
        {
            "heads": [1, 1, 3, 1, 5, 3, 5],
            "deps": ["când", "ROOT", "-", "ce", "prep", "unde", "ce fel de"]}
    ),
    (
        "când vor fi alegerile locale din 2020",
        {
            "heads": [2, 2, 2, 2, 3, 6, 4],
            "deps": ["când", "-", "ROOT", "cine", "care", "prep", "care"]}
    ),
    (
        "cine a venit ieri la cursul de astronomie",
        {
            "heads": [2, 2, 2, 2, 5, 2, 7, 5],
            "deps": ["cine", "-", "ROOT", "când", "prep", "unde", "prep", "care"]}
    ),
    (
        "care e dobânda de la creditul pentru casă",
        {
            "heads": [1, 1, 1, 4, 5, 2, 7, 5],
            "deps": ["care este", "ROOT", "cine", "-", "prep", "care", "prep", "care"]}
    ),
    (
        "care e înălțimea jaluzelelor de la bucătărie",
        {
            "heads": [1, 1, 1, 2, 5, 6, 3],
            "deps": ["care este", "ROOT", "cine", "al cui", "-", "prep", "care"]}
    ),
    (
        "care este numele de utilizator de github al laborantului de EIM",
        {
            "heads": [1, 1, 1, 4, 2, 6, 4, 8, 2, 10, 8],
            "deps": ["care este", "ROOT", "cine", "prep", "care", "prep", "care", "-", "al cui", "prep", "care"]}
    ),
    (
        "care este telefonul de la frizerie",
        {
            "heads": [1, 1, 1, 4, 5, 2],
            "deps": ["care este", "ROOT", "cine", "-", "prep", "care"]}
    ),
    (
        "când am avut ultimul examen anul trecut",
        {
            "heads": [2, 2, 2, 4, 2, 2, 5],
            "deps": ["când", "-", "ROOT", "care", "ce", "când", "care"]}
    ),
    (
        "cine a câștigat locul 1 la olimpiada națională de matematică din 2016",
        {
            "heads": [2, 2, 2, 2, 3, 6, 2, 6, 9, 6, 11, 6],
            "deps": ["cine", "-", "ROOT", "ce", "care", "prep", "unde", "care", "prep", "care", "prep", "care"]}
    ),
    (
        "cine m-a tuns ultima dată",
        {
            "heads": [4, 4, 1, 4, 4, 6, 4],
            "deps": ["cine", "pe cine", "-", "-", "ROOT", "care", "când"]}
    ),
    (
        "de la cine a cumpărat mihaela cireșele",
        {
            "heads": [1, 2, 4, 4, 4, 4, 4],
            "deps": ["-", "prep", "unde", "-", "ROOT", "cine", "ce"]}
    ),
    (
        "cât timp durează sezonul de pescuit",
        {
            "heads": [1, 2, 2, 2, 5, 3],
            "deps": ["cât", "cât timp", "ROOT", "cine", "prep", "care"]}
    ),
    (
        "cât timp va ține ploaia diseară",
        {
            "heads": [1, 3, 3, 3, 3, 3],
            "deps": ["cât", "cât timp", "-", "ROOT", "cine", "când"]}
    ),
    (
        "când am fost plecat în Germania",
        {
            "heads": [2, 2, 2, 2, 5, 2],
            "deps": ["când", "-", "ROOT", "ce", "prep", "unde"]}
    ),
    (
        "de cât timp era însurat ghiță",
        {
            "heads": [2, 2, 3, 3, 3, 3],
            "deps": ["prep", "cât", "cât timp", "ROOT", "cum este", "cine"]}
    ),
    (
        "cine mi-a reparat bateria de la chiuveta de la baie",
        {
            "heads": [4, 4, 1, 4, 4, 4, 7, 8, 5, 10, 11, 8],
            "deps": ["cine", "cui", "-", "-", "ROOT", "ce", "-", "prep", "care", "-", "prep", "care"]}
    ),
    (
        "care era valoarea maximă a presiunii admise",
        {
            "heads": [1, 1, 1, 2, 5, 2, 5],
            "deps": ["care este", "ROOT", "cine", "care", "-", "al cui", "care"]}
    ),
    (
        "care sunt dimensiunile portbagajului de la mașina lui Alin",
        {
            "heads": [1, 1, 1, 2, 5, 6, 3, 8, 6],
            "deps": ["care este", "ROOT", "cine", "al cui", "-", "prep", "care", "-", "al cui"]}
    ),
    (
        "unde am pus ciocolata denisei",
        {
            "heads": [2, 2, 2, 2, 3],
            "deps": ["unde", "-", "ROOT", "ce", "al cui"]}
    ),
    (
        "care e temperatura de fierbere a apei",
        {
            "heads": [1, 1, 1, 4, 2, 6, 2],
            "deps": ["care este", "ROOT", "cine", "prep", "care", "-", "al cui"]}
    ),
    (
        "sandalele alexandrei sunt de la magazinul colegului lui Mircea",
        {
            "heads": [2, 0, 2, 4, 5, 2, 5, 8, 6],
            "deps": ["cine", "al cui", "ROOT", "-", "prep", "unde", "al cui", "-", "al cui"]}
    ),
    (
        "de unde am cumpărat capacele roților mașinii",
        {
            "heads": [1, 3, 3, 3, 3, 4, 5],
            "deps": ["prep", "unde", "-", "ROOT", "ce", "al cui", "al cui"]}
    ),
    (
        "care sunt cele mai bune întrerupătoare",
        {
            "heads": [1, 1, 4, 4, 5, 1],
            "deps": ["care este", "ROOT", "-", "-", "ce fel de", "cine"]}
    ),
    (
        "unde am pus caietul de matematică 1",
        {
            "heads": [2, 2, 2, 2, 5, 3, 5],
            "deps": ["unde", "-", "ROOT", "ce", "prep", "care", "ce fel de"]}
    ),
    (
        "de unde mi-am luat cravata cea grena",
        {
            "heads": [1, 5, 5, 2, 5, 5, 5, 8, 6],
            "deps": ["prep", "unde", "cui", "-", "-", "ROOT", "ce", "-", "care"]}
    ),
    (
        "pentru cât timp o să fie plecat Mihai",
        {
            "heads": [2, 2, 5, 5, 5, 5, 5, 5],
            "deps": ["prep", "cât", "cât timp", "-", "-", "ROOT", "cum este", "cine"]}
    ),
    (
        "care sunt ministerele cu probleme",
        {
            "heads": [1, 1, 1, 4, 2],
            "deps": ["care este", "ROOT", "cine", "prep", "care"]}
    ),
    (
        "cine a văzut un arici mic în curte aseară",
        {
            "heads": [2, 2, 2, 4, 2, 4, 7, 2, 2],
            "deps": ["cine", "-", "ROOT", "-", "ce", "ce fel de", "prep", "unde", "când"]}
    ),
    (
        "despre ce task au vorbit colegii ieri la ședință",
        {
            "heads": [2, 2, 4, 4, 4, 4, 4, 8, 4],
            "deps": ["prep", "care", "comp ind", "-", "ROOT", "cine", "când", "prep", "unde"]}
    ),
    (
        "unde și-a pus Evelina geamantanul cu haine",
        {
            "heads": [4, 4, 1, 4, 4, 4, 4, 8, 6],
            "deps": ["unde", "cui", "-", "-", "ROOT", "cine", "ce", "prep", "care"]}
    ),
    (
        "peste câte ore se termină programul de la mașina de spălat",
        {
            "heads": [2, 2, 4, 4, 4, 4, 7, 8, 5, 10, 8],
            "deps": ["prep", "cât", "cât timp", "-", "ROOT", "cine", "-", "prep", "care", "prep", "care"]}
    ),
    (
        "unde am lăsat pernuța maro de pe scaunul din colțul camerei",
        {
            "heads": [2, 2, 2, 2, 3, 6, 7, 3, 9, 7, 9],
            "deps": ["unde", "-", "ROOT", "ce", "care", "-", "prep", "care", "prep", "care", "al cui"]}
    ),
    (
        "de unde vine primarul comunei cu nume complicat",
        {
            "heads": [1, 2, 2, 2, 3, 6, 4, 6],
            "deps": ["prep", "unde", "ROOT", "cine", "al cui", "prep", "care", "ce fel de"]}
    ),
]

TEST_DATA = [
    (
        "săptămâna trecută s-au terminat lucrările la gura de metrou de la stația Romancierilor",
        {
            "heads": [5, 0, 5, 4, 5, 5, 5, 8, 6, 10, 8, 12, 13, 8, 13],
            "deps": ["când", "care", "pe cine", "-", "-", "ROOT", "ce", "prep", "care", "prep", "care", "-", "prep",
                     "care",
                     "al cui"]}
    ),
    (
        "marți vine Elon Musk în România",
        {
            "heads": [1, 1, 1, 2, 5, 1],
            "deps": ["când", "ROOT", "cine", "care", "prep", "unde"]}
    ),
    (
        "bateria de la ceasul meu de mână este descărcată",
        {
            "heads": [7, 2, 3, 0, 3, 6, 3, 7, 7],
            "deps": ["cine", "-", "prep", "care", "al cui", "prep", "care", "ROOT", "cum este"]}
    ),
    (
        "predicțiile lui Michael pentru evoluția crizei au fost corecte",
        {
            "heads": [7, 2, 0, 4, 0, 4, 7, 7, 7],
            "deps": ["cine", "-", "al cui", "prep", "care", "al cui", "-", "ROOT", "cum este"]}
    ),
    (
        "unde am pus pantalonii de pijama ai lui Radu",
        {
            "heads": [2, 2, 2, 2, 5, 3, 8, 8, 3],
            "deps": ["unde", "-", "ROOT", "ce", "prep", "care", "-", "-", "al cui"]}
    ),
    (
        "de unde am luat pliculețele de ceai negru",
        {
            "heads": [1, 3, 3, 3, 3, 6, 4, 6],
            "deps": ["prep", "unde", "-", "ROOT", "ce", "prep", "care", "ce fel de"]}
    ),
    (
        "ochelarii ionelei sunt pe noptiera lui ionuț din dormitor",
        {
            "heads": [2, 0, 2, 4, 2, 6, 4, 8, 4],
            "deps": ["cine", "al cui", "ROOT", "prep", "unde", "-", "al cui", "prep", "care"]}
    ),
    (
        "pe unde am lăsat pompa de bicicletă",
        {
            "heads": [1, 3, 3, 3, 3, 6, 4],
            "deps": ["prep", "unde", "-", "ROOT", "ce", "prep", "care"]}
    ),
    (
        "care a fost durata domniei lui Cezar",
        {
            "heads": [2, 2, 2, 2, 3, 6, 4],
            "deps": ["care este", "-", "ROOT", "cine", "al cui", "-", "al cui"]}
    ),
    (
        "mărimea la tricou a lui Teo este L",
        {
            "heads": [6, 2, 0, 5, 5, 0, 6, 6],
            "deps": ["cine", "prep", "care", "-", "-", "al cui", "ROOT", "care este"]}
    ),
    (
        "numele profesoarei mele de biologie din liceu este Mariana Mihai",
        {
            "heads": [7, 0, 1, 4, 1, 6, 1, 7, 7, 8],
            "deps": ["cine", "al cui", "al cui", "prep", "care", "prep", "care", "ROOT", "care este", "care"]}
    ),
    (
        "care este înălțimea vârfului Everest",
        {
            "heads": [1, 1, 1, 2, 3],
            "deps": ["care este", "ROOT", "cine", "al cui", "care"]}
    ),
    (
        "mâine se termină perioada de rodaj a mașinii",
        {
            "heads": [2, 2, 2, 2, 5, 3, 7, 3],
            "deps": ["când", "-", "ROOT", "cine", "prep", "care", "-", "al cui"]}
    ),
    (
        "Dan vine acasă din Germania în fiecare vară",
        {
            "heads": [1, 1, 1, 4, 2, 7, 7, 1],
            "deps": ["cine", "ROOT", "unde", "prep", "unde", "prep", "care", "cât de des"]}
    ),
    (
        "în cât timp am urcat pe vârful Omu",
        {
            "heads": [2, 2, 4, 4, 4, 6, 4, 6],
            "deps": ["prep", "cât", "cât timp", "-", "ROOT", "prep", "unde", "care"]}
    ),
    (
        "cine mi-a reparat bateria de la chiuveta de la baie",
        {
            "heads": [4, 4, 3, 4, 4, 4, 7, 8, 5, 10, 11, 8],
            "deps": ["cine", "cui", "-", "-", "ROOT", "ce", "-", "prep", "care", "-", "prep", "care"]}
    ),
    (
        "am pus bateria externă în rucsacul albastru",
        {
            "heads": [1, 1, 1, 2, 5, 1, 5],
            "deps": ["-", "ROOT", "ce", "care", "prep", "unde", "care"]}
    ),
    (
        "numele de utilizator al Irinei este irina",
        {
            "heads": [5, 2, 0, 4, 0, 5, 5],
            "deps": ["cine", "prep", "care", "-", "al cui", "ROOT", "care este"]}
    ),
    (
        "profesorul se află în camera vecină",
        {
            "heads": [2, 2, 2, 4, 2, 4],
            "deps": ["cine", "-", "ROOT", "prep", "unde", "care"]}
    ),
    (
        "lămpile solare sunt de la bricostore",
        {
            "heads": [2, 0, 2, 4, 5, 2],
            "deps": ["cine", "care", "ROOT", "-", "prep", "unde"]}
    ),
    (
        "până unde au ajuns radiațiile de la Cernobâl",
        {
            "heads": [1, 3, 3, 3, 3, 6, 7, 4],
            "deps": ["prep", "unde", "-", "ROOT", "cine", "-", "prep", "care"]}
    ),
    (
        "de unde am luat draperiile din sufragerie",
        {
            "heads": [1, 3, 3, 3, 3, 6, 4],
            "deps": ["prep", "unde", "-", "ROOT", "ce", "prep", "care"]}
    ),
    (
        "numele asistentului de programare paralelă e Paul Walker",
        {
            "heads": [5, 0, 3, 1, 3, 5, 5, 6],
            "deps": ["cine", "al cui", "prep", "care", "ce fel de", "ROOT", "care este", "care"]}
    ),
    (
        "când trebuie să merg la control oftalmologic",
        {
            "heads": [1, 1, 3, 1, 5, 3, 5],
            "deps": ["când", "ROOT", "-", "ce", "prep", "unde", "ce fel de"]}
    ),
    (
        "Cine stă în căminul P16",
        {
            "heads": [1, 1, 3, 1, 3],
            "deps": ["cine", "ROOT", "prep", "unde", "care"]}
    ),
    (
        "de mâine va fi cald afară",
        {
            "heads": [1, 3, 3, 3, 3, 3],
            "deps": ["prep", "când", "-", "ROOT", "cum este", "unde"]}
    ),
    (
        "codul de activare al sistemului de operare e APCHF6798HJ67GI90",
        {
            "heads": [7, 2, 0, 4, 0, 6, 4, 7, 7],
            "deps": ["cine", "prep", "care", "-", "al cui", "prep", "care", "ROOT", "care este"]}
    ),
    (
        "care e punctul de topire al aluminiului",
        {
            "heads": [1, 1, 1, 4, 2, 6, 2],
            "deps": ["care este", "ROOT", "cine", "prep", "care", "-", "al cui"]}
    ),
    (
        "i-am dat adrianei mașina mea săptămâna trecută",
        {
            "heads": [3, 0, 3, 3, 3, 3, 5, 3, 7],
            "deps": ["cui", "-", "-", "ROOT", "cui", "ce", "al cui", "când", "care"]}
    ),
    (
        "care este tipografia centrală din orașul lui Marian",
        {
            "heads": [1, 1, 1, 2, 5, 2, 7, 5],
            "deps": ["care este", "ROOT", "cine", "care", "prep", "care", "-", "al cui"]}
    ),
    (
        "de cât timp era însurat Ghiță",
        {
            "heads": [2, 2, 3, 3, 3, 3],
            "deps": ["prep", "cât", "cât timp", "ROOT", "cum este", "cine"]}
    ),
    (
        "acum 3 ore mi s-a stricat fermoarul rucsacului de laptop",
        {
            "heads": [2, 2, 7, 7, 7, 4, 7, 7, 7, 8, 12, 9],
            "deps": ["prep", "cât", "cât timp", "cui", "pe cine", "-", "-", "ROOT", "cine", "al cui", "prep", "care"]}
    ),
    (
        "de unde am cumpărat uscătorul de păr al Dianei",
        {
            "heads": [1, 3, 3, 3, 3, 6, 4, 8, 4],
            "deps": ["prep", "unde", "-", "ROOT", "ce", "prep", "care", "-", "al cui"]}
    ),
    (
        "cât timp am așteptat la coadă la pâine",
        {
            "heads": [1, 3, 3, 3, 5, 3, 7, 3],
            "deps": ["cât", "cât timp", "-", "ROOT", "prep", "unde", "prep", "unde"]}
    ),
    (
        "de unde a luat Mihaela revista cu benzi desenate",
        {
            "heads": [3, 3, 3, 3, 3, 3, 7, 5, 7],
            "deps": ["prep", "unde", "-", "ROOT", "cine", "ce", "prep", "care", "ce fel de"]}
    ),
    (
        "peste cât timp se finalizează selecția studenților pentru master",
        {
            "heads": [2, 2, 4, 4, 5, 4, 5, 8, 5],
            "deps": ["prep", "cât", "cât timp", "-", "cine", "cine", "al cui", "prep", "care"]}
    ),
    (
        "valoarea prețului se modifică o dată la 4 luni",
        {
            "heads": [3, 0, 3, 3, 5, 3, 8, 8, 3],
            "deps": ["cine", "al cui", "-", "ROOT", "cât", "cât de des", "prep", "cât", "la cât timp"]}
    ),
    (
        "trebuie să mă tund până pe 1 iunie",
        {
            "heads": [0, 3, 3, 0, 5, 6, 3, 6],
            "deps": ["ROOT", "-", "pe cine", "ce", "-", "prep", "când", "care"]}
    ),
    (
        "am cumpărat 2 kilograme de piersici de la un vânzător din piață",
        {
            "heads": [1, 1, 3, 1, 5, 3, 7, 9, 9, 1, 11, 9],
            "deps": ["-", "ROOT", "cât", "ce", "prep", "ce fel de", "-", "prep", "-", "unde", "prep", "ce fel de"]}
    ),
    (
        "calculatorul lui Andrei are 2 procesoare Intel",
        {
            "heads": [3, 2, 0, 3, 5, 3, 5],
            "deps": ["cine", "-", "al cui", "ROOT", "cât", "ce", "ce fel de"]}
    ),
    (
        "Anisia merge o dată pe săptămână la mallul de pe bulevardul Timișoara",
        {
            "heads": [1, 1, 3, 1, 5, 1, 7, 1, 9, 10, 7, 10],
            "deps": ["cine", "ROOT", "cât", "cât de des", "prep", "la cât timp", "prep", "unde", "-", "prep", "care",
                     "care"]}
    ),
    (
        "l-am pus pe darius la volanul mașinii mele",
        {
            "heads": [3, 0, 3, 3, 5, 3, 7, 3, 7, 8],
            "deps": ["pe cine", "-", "-", "ROOT", "prep", "pe cine", "prep", "unde", "al cui", "al cui"]}
    ),
    (
        "Mașina ambulanței a dus - o pe Tereza la un spital din București",
        {
            "heads": [3, 0, 3, 3, 5, 3, 7, 3, 10, 10, 3, 12, 10],
            "deps": ["cine", "al cui", "-", "ROOT", "-", "pe cine", "prep", "pe cine", "prep", "-", "unde", "prep",
                     "ce fel de"]}
    ),
    (
        "tura de la uzină se schimbă de 2 ori pe zi",
        {
            "heads": [5, 2, 3, 0, 5, 5, 8, 8, 5, 10, 5],
            "deps": ["cine", "-", "prep", "care", "-", "ROOT", "prep", "cât", "cât de des", "prep", "la cât timp"]}
    ),
    (
        "sesiunea de restanțe a durat de pe 3 iunie pe 10 iunie",
        {
            "heads": [4, 2, 0, 4, 4, 6, 7, 4, 7, 10, 4, 10],
            "deps": ["cine", "prep", "care", "-", "ROOT", "-", "prep", "când", "care", "prep", "când", "care"]}
    ),
    (
        "m-a durut capul ieri seara",
        {
            "heads": [3, 0, 3, 3, 3, 3, 5],
            "deps": ["pe cine", "-", "-", "ROOT", "cine", "când", "care"]}
    ),
    (
        "pe liviu l - au luat la țară pe 19 aprilie",
        {
            "heads": [1, 5, 5, 2, 5, 5, 7, 5, 9, 5, 9],
            "deps": ["prep", "pe cine", "pe cine", "-", "-", "ROOT", "prep", "unde", "prep", "când", "care"]}
    ),
    (
        "marți o să trimit cererea de înscriere la facultate",
        {
            "heads": [3, 3, 3, 3, 3, 6, 4, 8, 6],
            "deps": ["când", "-", "-", "ROOT", "ce", "prep", "care", "prep", "ce fel de"]}
    ),
    (
        "reparația unei turbine stricate a durat foarte mult timp",
        {
            "heads": [5, 2, 0, 2, 5, 5, 7, 8, 5],
            "deps": ["cine", "-", "al cui", "ce fel de", "-", "ROOT", "-", "cât", "cât timp"]}
    ),
    (
        "exemplele din manual sunt foarte complicate",
        {
            "heads": [3, 2, 0, 3, 5, 3],
            "deps": ["cine", "prep", "care", "ROOT", "-", "cum este"]}
    ),
    (
        "data de expirare de pe cutia de cereale integrale este 23 august",
        {
            "heads": [9, 2, 0, 4, 5, 0, 7, 5, 7, 9, 9, 10],
            "deps": ["cine", "prep", "care", "-", "prep", "care", "prep", "care", "ce fel de", "ROOT", "care este",
                     "care"]}
    ),
    (
        "am luat lecții de chitară 4 ani",
        {
            "heads": [1, 1, 1, 4, 2, 1, 1],
            "deps": ["-", "ROOT", "ce", "prep", "ce fel de", "cât", "cât timp"]}
    ),
    (
        "în februarie se vor achiziționa 5 autospeciale noi",
        {
            "heads": [1, 4, 4, 4, 4, 6, 4, 6],
            "deps": ["prep", "când", "-", "-", "ROOT", "cât", "ce", "ce fel de"]}
    ),
    (
        "în 3 minute încep știrile de la ora 7",
        {
            "heads": [2, 2, 3, 3, 3, 6, 7, 4, 7],
            "deps": ["prep", "cât", "cât timp", "ROOT", "cine", "-", "prep", "care", "care"]}
    ),
    (
        "codul de acces la laboratorul de biologie moleculară este 42132",
        {
            "heads": [8, 2, 0, 4, 2, 6, 4, 6, 8, 8],
            "deps": ["cine", "prep", "care", "prep", "ce fel de", "prep", "care", "ce fel de", "ROOT", "care este"]}
    ),
    (
        "i-am lăsat fratelui Dianei cheile de la motocicleta lui Damian",
        {
            "heads": [3, 0, 3, 3, 3, 4, 3, 8, 9, 6, 11, 9],
            "deps": ["cui", "-", "-", "ROOT", "cui", "al cui", "ce", "-", "prep", "care", "-", "al cui"]}
    ),
    (
        "primăria i-a oferit lui gigi premiul de onoare",
        {
            "heads": [4, 4, 1, 4, 4, 6, 4, 4, 9, 7],
            "deps": ["cine", "cui", "-", "-", "ROOT", "-", "cui", "ce", "prep", "care"]}
    ),
    (
        "voi ajunge la control peste un an",
        {
            "heads": [1, 1, 3, 1, 6, 6, 1],
            "deps": ["-", "ROOT", "prep", "unde", "prep", "cât", "cât timp"]}
    ),
    (
        "lui daniel i-au mărit salariul",
        {
            "heads": [1, 5, 5, 2, 5, 5, 5],
            "deps": ["-", "cui", "cui", "-", "-", "ROOT", "ce"]}
    ),
    (
        "acum 2 secunde era destul de întuneric afară",
        {
            "heads": [2, 2, 3, 3, 5, 6, 3, 3],
            "deps": ["prep", "cât", "cât timp", "ROOT", "-", "-", "cum este", "unde"]}
    ),
    (
        "în 1978 a fost prima ediție a festivalului simfonia lalelelor",
        {
            "heads": [1, 3, 3, 3, 5, 3, 7, 5, 7, 8],
            "deps": ["prep", "când", "-", "ROOT", "care", "cine", "-", "al cui", "care", "al cui"]}
    ),
    (
        "magazinul de echipamente electronice s-a deschis de 3 luni",
        {
            "heads": [7, 2, 0, 2, 7, 4, 7, 7, 10, 10, 7],
            "deps": ["cine", "prep", "care", "ce fel de", "pe cine", "-", "-", "ROOT", "prep", "cât", "cât timp"]}
    ),
    (
        "care e codul de la seiful din dormitor",
        {
            "heads": [1, 1, 1, 4, 5, 2, 7, 5],
            "deps": ["care este", "ROOT", "cine", "-", "prep", "care", "prep", "care"]}
    ),
    (
        "toamna viitoare se va deschide noul bazin de înot din oraș",
        {
            "heads": [4, 0, 4, 4, 4, 6, 4, 8, 6, 10, 6],
            "deps": ["când", "care", "-", "-", "ROOT", "care", "ce", "prep", "care", "prep", "care"]}
    ),
    (
        "numărul de identificare de pe laptop este AN490238jf",
        {
            "heads": [6, 2, 0, 4, 5, 0, 6, 6],
            "deps": ["cine", "prep", "care", "-", "prep", "care", "ROOT", "care este"]}
    ),
    (
        "trebuie să termin licența până miercuri",
        {
            "heads": [0, 2, 0, 2, 5, 2],
            "deps": ["ROOT", "-", "ce", "ce", "prep", "când"]}
    ),
    (
        "avionul i-a stropit pe oamenii aceia acum o jumătate de oră",
        {
            "heads": [4, 4, 1, 4, 4, 6, 4, 6, 10, 10, 4, 12, 10],
            "deps": ["cine", "pe cine", "-", "-", "ROOT", "prep", "pe cine", "care", "prep", "cât", "cât timp", "prep",
                     "ce fel de"]}
    ),
    (
        "săptămâna trecută s - au afișat notele de la arhitecturi de calculatoare",
        {
            "heads": [5, 0, 5, 2, 5, 5, 5, 8, 9, 6, 11, 9],
            "deps": ["când", "care", "pe cine", "-", "-", "ROOT", "cine", "-", "prep", "care", "prep", "ce fel de"]}
    ),
    (
        "azi emil a câștigat proba de înot de la olimpiadă",
        {
            "heads": [3, 3, 3, 3, 3, 6, 4, 8, 9, 4],
            "deps": ["când", "cine", "-", "ROOT", "ce", "prep", "care", "-", "prep", "care"]}
    ),
    (
        "cât timp a ținut prezentarea de specializări de master",
        {
            "heads": [1, 3, 3, 3, 3, 6, 4, 8, 6],
            "deps": ["cât", "cât timp", "-", "ROOT", "cine", "prep", "care", "prep", "ce fel de"]}
    ),
]


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

    print("TRAIN EXAMPLES: ", len(TRAIN_DATA))

    y_pos = np.arange(len(dependency_types))

    plt.barh(y_pos, [dep_freq[q] for q in dependency_types], align='center', alpha=0.5)
    plt.xticks(fontsize=12)
    plt.yticks(y_pos, dependency_types, fontsize=12)
    plt.xlabel('Number of occurrences', fontsize=13)
    plt.ylabel('Syntactic question (label)', fontsize=13)
    plt.title('Syntactic question frequencies in the train examples', fontsize=13)
    plt.savefig("synt_questions_freq.svg", format="svg", bbox_inches='tight')
    plt.show()


@plac.annotations(
    model=("Model name. Defaults to blank 'en' model.", "option", "m", str),
    n_iter=("Number of training iterations", "option", "n", int),
)
def train(model=None, n_iter=30):
    """ Load the model, set up the pipeline and train the parser. """

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
            print(itn, "Losses", losses)

    return nlp


def dep_span(doc, token, span_level=0):
    def dfs(node):
        first = last = node.i
        for child in node.children:
            if child.dep_ in ['-'] or \
                    (span_level >= 1 and child.dep_ == "prep") or \
                    (span_level >= 2 and child.dep_ in ['care', 'ce fel de', 'cât', 'al cui']):
                child_first, child_last = dfs(child)
                first = min(first, child_first)
                last = max(last, child_last)
        return first, last

    first, last = dfs(token)  # compute bounds of the span
    span = Span(doc, first, last + 1)
    return span.text


def print_parse_result(doc):
    for token in doc:
        if token.dep_ != "-" and token.dep_ != 'prep':
            print(TermColors.YELLOW, token.dep_, TermColors.ENDC,
                  f'[{dep_span(doc, token.head, 0)}] ->',
                  TermColors.RED, dep_span(doc, token, 2), TermColors.ENDC)


def store_model(nlp, output_dir=None):
    """ Save the model to the output directory. """

    if output_dir is not None:
        output_dir = Path(output_dir)
        if not output_dir.exists():
            output_dir.mkdir()
        nlp.to_disk(output_dir)
        print("Saved model to", output_dir)


def test_model(nlp, interactive=False):
    """
    Test the results of the model for a set of predefined sentences
    or by interactively introducing sentences to the prompt.
    """

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

        "cartea e pe masă",
        "Cardul de debit este în portofelul vechi",
        "buletinul meu se află în rucsac",
        "biblioteca se află la etajul 5",
        "service-ul gsm este pe strada Ecaterina Teodoroiu numărul 12",
        "Am pus foile cu tema la mate pe dulapul din sufragerie",
        "Alex stă în căminul P5",
        "Maria Popescu locuiește pe Bulevardul Timișoara numărul 5",
        "Daniela stă la blocul 23",
        "eu stau la adresa str. Ec. Teod. nr. 17",
        "Bonurile de transport sunt în plicul de pe raft",
        "cardul de memorie e sub cutia telefonului",
        "tastatura mea este în depozit",
        "profesorul se află în camera vecină",
        "am lăsat lădița cu cartofi în pivniță",
        "mi-am pus casca de înot în dulapul cu tricouri",
        "geaca de iarnă este în șifonierul de acasă",
        "lămpile solare sunt de la bricostore",
        "perechea de adidași albi este de la intersport din Afi",
        "Alin Dumitru stă în Militari Residence",
        "am lăsat suportul de brad la țară în garaj",
        "pachetul de creioane colorate este pe polița de pe perete",
        "mi-am așezat prosoapele pe suport",

        "Unde se află ochelarii",
        "Unde e buletinul",
        "știi unde am pus cheile",
        "poți să-mi zici unde este încârcătorul de telefon",
        "zi-mi unde am pus ochelarii de înot",
        "unde am lăsat ceasul",
        "pe unde e sticla de ulei",
        "pe unde mi-am pus pantofii negri",
        "de unde am cumpărat uscătorul de păr",
        "de unde au venit cartofii în Europa",
        "de unde pleacă trenul IR1892",
        "până unde a alergat aseară Marius",
        "până unde au ajuns radiațiile de la Cernobâl",
        "de unde am luat draperiile din sufragerie",

        "Mailul lui Alex Marin este alex@marin.com",
        "Adresa Elenei este strada Zorilor numărul 9",
        "Numărul de telefon al lui Dan e 123456789",
        "numărul blocului fratelui Mihaelei e 10",
        "anul nașterii lui Ștefan cel Mare a fost 1433",
        "numele meu este Gabriel",
        "cheile mele de la casă sunt ușoare",
        "adresa de la serviciu este Bulevardul Unirii nr. 0",
        "numele asistentului de programare paralelă e Paul Walker",
        "suprafața apartamentului de la București este de 58mp",
        "prețul canapelei a fost de 1300 de lei",
        "codul de activare al sistemului de operare e APCHF6798HJ67GI90",
        "sala laboratorului de PP este EG321",
        "username-ul meu de github este gabrielboroghina",
        "seria mea de la buletin este GG2020",
        "codul PIN de la cardul meu de sănătate este 0000",
        "placa mea video este NVidia GeForce GTX950m",
        "telefonul Karinei este 243243",

        "Care e mailul lui Mihai",
        "care este numele de utilizator de github al laborantului de EIM",
        "poți să-mi spui care era prețul abonamentului la sală",
        "zi-mi care a fost câștigătorul concursului Eestec Olympics de anul trecut",
        "care era denumirea bazei de date de la proiect",
        "care sunt tipurile de rețele neurale",
        "care este valoarea de adevăr a propoziției",
        "care e adresa colegului meu",
        "care e frecvența procesorului meu",
        "care e numărul lui Radu",
        "care e limita de viteză în localitate",
        "care e punctul de topire al aluminiului",
        "care e data de naștere a lui Mihai Popa",
        "care este mărimea mea la adidași",
        "care este temperatura medie în Monaco în iunie",
        "care este diferența de vârstă între mine și Vlad",
        "zi-mi și mie care era adresa de căsuță poștală a Karinei Preda",
        "care sunt datele cardului meu revolut",
        "care este telefonul de la frizerie",
        "care e dobânda de la creditul pentru casă",
        "care sunt ministerele cu probleme",
        "care este tipografia centrală",

        "ce floare s-a uscat",
        "ce hackathon va avea loc săptămâna viitoare",
        "ce windows am acum pe calculator",
        "ce examene vor fi date în iunie",
        "ce temperatură a fost în iulie anul trecut",
        "ce culoare au ochii Andreei",
        "ce mail am folosit la serviciu",
        "la ce apartament locuiește verișorul meu",
        "la ce sală se află microscopul electronic",
        "la ce număr de telefon se dau informații despre situația actuală",
        "la care salon este internat bunicul lui",
        "la care cod poștal a fost trimis pachetul",
        "la care hotel s-au cazat Mihai și Alex ieri",
        "ce fel de imprimantă  am acasă",
        "ce fel de baterie folosește ceasul de mână",
        "ce fel de procesor are telefonul meu",
        "în care dulap am pus dosarul",
        "în care cameră am lăsat încărcătorul de telefon",
        "în care săptămână e examenul de învățare automată",
        "de la care prieten e cadoul acesta",
        "de la care magazin mi-am luat cablul de date",
        "pentru ce test am învățat acum 2 zile",
        "pe care masă am pus ieri periuța de dinți",
        "pe care poziție este mașina în parcare",
        "de pe care cont am plătit factura de curent acum 3 zile",
        "pe ce viteză am setat aerul condiționat",
        "pe ce loc am ieșit la olimpiada de info din clasa a 12-a",
        "care aparat de făcut sandwichuri e la reducere",
        "ce fel de uscător de păr folosește Alice",
        "care clasificare e corectă",
        "care emisferă este",
        "care elicopter",
        "care autoturism este cel mai prietenos cu mediul",
        "la ce sprânceană e problema",
        "la ce fel de neurooftalmologie trebuie să meargă",
        "pentru care deversare au fost amedați",
        "ce fel de pocănit se auzea ieri",

        "concursul va fi pe 12 ianuarie",
        "îmi expiră permisul de conducere pe 25 februarie 2023",
        "plecarea în Franța este pe 5 martie",
        "abonamentul STB îmi expiră pe 23 aprilie",
        "Viorel e născut pe 16 mai 1998",
        "Vacanța de vară începe pe 30 iunie",
        "Pe 3 iulie se termină sesiunea de licență",
        "ziua Daianei este în august",
        "în septembrie începe școala",
        "din octombrie apare un nou film la cinema",
        "până în noiembrie trebuie să termin task-ul",
        "noile autobuze au apărut în decembrie",
        "luni am fost la alergat",
        "am mers la bazinul de înot marți",
        "coletul cu jacheta va ajunge miercuri",
        "testul de curs la rețele neurale a fost joi",
        "vineri încep promoțiile de black friday",
        "până sâmbătă e interzis accesul în mall",
        "Jack a fost la biserică duminică",
        "azi am fost în parcul Titan",
        "Mâine vine Mihai pe la mine",
        "poimâine merg la mall",
        "de ieri s-a făcut cald afară",
        "am terminat proiecul la programare web alaltăieri",
        "peste 2 zile începe examenul de bacalaureat",
        "sesiunea din browser a expirat acum 10 secunde",
        "am de prezentat temele peste o oră",
        "am mâncat acum 2 ore",
        "Maria pleacă în concediu peste 5 săptămâni",
        "conferința de bioinformatică a fost acum o lună",
        "peste 2 ani termină Nicoleta masterul",
        "buletinul îmi expiră peste 3 ani",
        "mi-am făcut pașaportul acum un an",
        "garanția de la frigider se termină marțea viitoare",
        "săptămâna viitoare încep cursurile de înot",
        "luna viitoare vine Florin din Spania",
        "prezentarea proiectului durează 45 de minute",
        "meciul dintre Franța și Spania va fi în weekend",
        "întâlnirea cu managerul este peste o jumătate de oră",
        "la anul se deschide mall-ul din Slatina",
        "mi-am făcut analize primăvara trecută",
        "restricțiile de circulație se încheie la vară",
        "toamna viitoare încep masterul",
        "Darius și-a schimbat domiciliul iarna trecută",

        "când vor avea loc alegerile locale din 2020",
        "Când am avut ultimul examen anul trecut",
        "zi-mi când am fost la sală",
        "De când începe vacanța",
        "Până când trebuie trimisă tema",
        "până când a durat al 2-lea război mondial",
        "până când trebuie rezolvată problema la vlsi",
        "cât timp a durat prezentarea temei",
        "peste cât timp se termină starea de urgență",
        "peste cât timp începe sesiunea de examene",
        "când trebuie să merg la control oftalmologic",
        "când trebuie să iau pastilele de stomac",
        "Cine stă în căminul P16",
        "Spune-mi te rog cine a inventat becul",
        "cine a câștigat locul 1 la olimpiada națională de matematică din 2016",
        "cine m-a tuns ultima dată",
        "de la cine a cumpărat mihaela cireșele",
        "de la cine a apărut problema",
        "cine a fost primul om pe lună",
        "cine a venit ieri la cursul de astronomie",
        "zi-mi cine a propus problemele de la concursul InfoOlt 2016",
    ]

    test_sentences = [
        "atlasul de geografie se află pe raftul cu dicționarul",
        "am pus bateria externă în rucsacul albastru",
        "cheia franceză e pe balcon",
        "cartela mea SIM veche este sub cutia telefonului",
        "am lăsat geanta în dulapul numărul 4",
        "Victor stă pe Aleea Romancierilor numărul 12",
        "eu stau la blocul nr. 8",
        "am lăsat mașina la service-ul auto din Crângași",
        "pliculețele de praf de copt sunt în cutiuța din primul sertar",
        "am așezat etuiul de la ochelari peste teancul de reviste din hol",

        "unde am pus caietul de matematică 1?",
        "știi unde sunt burghiele mici",
        "pe unde am lăsat pompa de bicicletă",
        "unde locuiește Claudia Ionescu",
        "de unde este brelocul meu de la chei?",
        "unde se află bazinul de înot Dinamo",
        "unde mi-am aruncat sculele de construcții",
        "de unde mi-am luat cravata cea grena",
        "zi-mi unde am lăsat certificatul meu de naștere",
        "unde este setul de baterii pentru mouse?",

        "telefonul Dianei este 0745789654",
        "prețul ceasului meu Atlantic a fost 500 de lei",
        "numărul de la mașină al Elenei este B 07 ELN",
        "codul de identificare al cardului meu de de acces la birou este 57627",
        "numele profesoarei mele de biologie din liceu este Mariana Mihai",
        "mărimea la tricou a lui Teo este L",
        "materiile la care am luat 9 sunt M1 și M2",
        "rank-ul universității Politehnica este 800",
        "tipul de baterii de la tastatură este AAA",
        "modelul tastaturii mele este logitech mx keys",
        "ziua de naștere a Grațielei este pe 12 mai 1995",

        "care este telefonul Dianei",
        "care este prețul ceasului meu Atlantic",
        "care este numărul de la mașină al Elenei",
        "zi-mi care e codul PIN de la cardul meu de sănătate",
        "care e numele profesoarei mele de biologie din liceu",
        "care sunt cele mai bune întrerupătoare",
        "care era emailul asistentului de la APP?",
        "care a fost durata domniei lui Cezar",
        "zi-mi care e codul de pe spatele telefonului",
        "care e vărsta de pensionare la bărbați",
        "care era modelul tastaturii mele?",
        "care este înălțimea vârfului Everest?",

        "la ce apartament stă Alex Marin?",
        "ce fel de bec am pus la bucătărie",
        "în care dulap am lăsat plasa?",
        "de la ce magazin am luat tortul de la ziua mea",
        "care colegi au luat 10 la chimie",
        "care copil a rupt scaunul de la școală",
        "ce profesor a prezentat la conferință",
        "în ce zi e născut unchiul meu?",
        "care dinamometru e afară",
        "ce floare este de la expo flora?",
        "care persoane suferă de diabet",
        "care bomboane sunt pentru ziua ei",
        "ce os a înghițit acel băiat",
        "care bomboane sunt de la auchan",

        "mâine se termină perioada de rodaj al mașinii",
        "examenul la ML este peste 4 zile",
        "testul practic de EIM o să fie săptămâna viitoare",
        "peste o zi expiră prăjiturile",
        "ieri m-am tuns",
        "aniversarea prieteniei cu Andreea e pe 30 aprilie",
        "am trimis rezolvările la gazeta matematică miercurea trecută",
        "vineri apare revista historia",
        "virusul a apărut acum 3 luni",
        "peste 123 de secunde trecem în noul an",
        "hackathonul s-a organizat weekend-ul trecut",
        "la primăvară e gata blocul",
        "voi pleca in Monaco peste 3 ore",

        "când începe vacanța de iarnă",
        "când am fost la mare anul trecut",
        "de când s-a deschis McDonalds din Slatina",
        "cât timp a durat bătălia de la Oituz",
        "când am fost plecat în Germania",
        "până când va dura festivalul de muzică folk?",
        "de cât timp s-a deschis fabrica de mașini din Pitești",
        "de cât timp era însurat Ghiță",
        "pentru cât timp o să fie plecat Mihai",
        "în cât timp am urcat pe vârful Omu?",
        "peste cât timp începe sesiunea de comunicări științifice?",

        "cine a inventat motorul cu reacție",
        "cine a fost la ziua mea acum 3 ani",
        "cine m-a ajutat la proiectul de la anatomie?",
        "cine mi-a reparat bateria de la chiuveta de la baie?",
        "spune-mi te rog cine a luat 10 la arhitectura sistemelor de calcul",
    ]

    if interactive:
        print("\nInteractive testing. Enter a phrase to parse it:")
        while True:
            phrase = input("\n>> ")
            doc = nlp(phrase)
            print_parse_result(doc)
    else:
        docs = nlp.pipe(test_sentences)
        for doc in docs:
            print('\n', doc.text)
            print_parse_result(doc)

        # show a visual result as a web page with the help of displacy
        docs = [nlp(phrase) for phrase in texts]
        options = {"add_lemma": False, "compact": True, "fine_grained": False}

        html_dep = displacy.render(docs, style="dep", page=True, options=options)
        with open("deps.html", "w", encoding='utf8') as f:
            f.write(html_dep)


def plot_confusion_matrix(y_true, y_pred, labels):
    conf_mat = confusion_matrix(y_true, y_pred, labels=labels)

    sns.heatmap(conf_mat, annot=conf_mat, fmt='g', cmap='Greens',
                xticklabels=labels, yticklabels=labels, annot_kws={"size": 11})
    plt.xticks(fontsize=13)
    plt.yticks(fontsize=13)
    plt.xlabel('Predicted', fontsize=14)
    plt.ylabel('True', fontsize=14)
    plt.title("Syntactic questions prediction", fontsize=14)
    plt.savefig("synt_quest_pred.svg", format="svg", bbox_inches='tight')
    plt.show()


def evaluate_model(nlp):
    """ Compute evaluation metrics (confusion matrix, classification report, accuracy) for the model. """

    deps_true = []
    deps_pred = []
    correct_heads = {dep: 0 for dep in dependency_types}
    num_deps = {dep: 0 for dep in dependency_types}

    # parse sentences
    docs = nlp.pipe(map(lambda s: s[0], TEST_DATA))

    # evaluate predictions
    for i, doc in enumerate(docs):
        true_sentence_deps = TEST_DATA[i][1]

        # evaluate dependencies (syntactic questions) prediction
        sentence_deps_true = true_sentence_deps['deps']
        sentence_deps_pred = [token.dep_ for token in doc]

        deps_true += sentence_deps_true
        deps_pred += sentence_deps_pred

        if any(true != pred for (true, pred) in zip(sentence_deps_true, sentence_deps_pred)):
            print()
            print(sentence_deps_true)
            print(sentence_deps_pred)

            for token in doc:
                if token.dep_ != "-":
                    print(TermColors.YELLOW, token.dep_, TermColors.ENDC, f'[{token.head.text}] ->',
                          TermColors.GREEN, token.text, TermColors.ENDC)

        # evaluate heads prediction
        for j, token in enumerate(doc):
            if token.head.i == true_sentence_deps['heads'][j]:
                correct_heads[true_sentence_deps['deps'][j]] += 1
            num_deps[true_sentence_deps['deps'][j]] += 1

    print("Number of test examples", len(TEST_DATA))

    # print syntactic questions evaluation scores
    print("Syntactic questions accuracy:")
    print(classification_report(deps_true, deps_pred, zero_division=0))
    plot_confusion_matrix(deps_true, deps_pred, dependency_types)

    # print heads prediction accuracies
    print("Heads accuracy: ", sum(correct_heads.values()) / sum(num_deps.values()), '\n')

    for dep in dependency_types:
        acc = round(correct_heads[dep] / num_deps[dep], 2) if num_deps[dep] > 0 else '-'
        print(f'- {dep}: {" " * (15 - len(dep))}{acc}')


if __name__ == "__main__":
    analyze_data(TRAIN_DATA)

    # uncomment this to train the model before the testing stage
    # model = train("spacy_ro", n_iter=40)
    # store_model(model, '../../models/spacy-syntactic')

    nlp = spacy.load('../../models/spacy-syntactic')

    # evaluate the model using a separate test set
    # evaluate_model(nlp)

    # test the model for debugging
    test_model(nlp, interactive=True)
