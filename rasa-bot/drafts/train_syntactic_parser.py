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
            "heads": [5, 2, 0, 5, 5, 5, 5, 8, 9, 5],
            "deps": ['când', 'cât', 'cât timp', '-', '-', 'ROOT', 'cine', '-', 'prep', 'unde'],
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
                     'care',
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
            "heads": [1, 6, 3, 1, 5, 1, 6, 6, 9, 7],
            "deps": ['care', 'cine', 'prep', 'care', '-', 'al cui', 'ROOT', 'când', 'cât', 'cât timp'],
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
            "heads": [4, 4, 1, 4, 4, 4, 5, 8, 6],
            "deps": ["cine", "cui", "-", "-", "ROOT", "ce", "când", "cât", "cât timp"]}
    ),
    (
        "am terminat de spălat vasele acum 30 de minute",
        {
            "heads": [1, 1, 3, 1, 3, 1, 8, 8, 5],
            "deps": ["-", "ROOT", "-", "ce", "ce", "când", "cât", "prep", "cât timp"]}
    ),
    (
        "acum un an aveam 60 de kilograme",
        {
            "heads": [3, 2, 0, 3, 6, 6, 3],
            "deps": ["când", "-", "cât timp", "ROOT", "cât", "prep", "ce"]}
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
        "mi-am făcut pașaportul acum un an",
        {
            "heads": [3, 0, 3, 3, 3, 3, 7, 5],
            "deps": ["cui", "-", "-", "ROOT", "ce", "când", "cât", "cât timp"]}
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
            "heads": [5, 2, 0, 5, 5, 5, 5],
            "deps": ["când", "cât", "cât timp", "-", "-", "ROOT", "ce"]}
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
            "heads": [3, 2, 0, 3, 3, 6, 4, 8, 6],
            "deps": ["cine", "prep", "care", "ROOT", "când", "cât", "cât timp", "prep", "ce fel de"]}
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
            "heads": [5, 2, 0, 5, 5, 5, 5, 5],
            "deps": ["când", "cât", "cât timp", "cine", "-", "ROOT", "ce", "unde"]}
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
            "heads": [4, 2, 0, 4, 4, 4, 7, 5],
            "deps": ["cine", "prep", "care", "-", "ROOT", "când", "cât", "cât timp"]}
    ),
    (
        "peste 2 ani termină Nicoleta masterul",
        {
            "heads": [3, 2, 0, 3, 3, 3],
            "deps": ["când", "cât", "cât timp", "ROOT", "cine", "ce"]}
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
            "heads": [4, 3, 3, 0, 4, 7, 7, 4],
            "deps": ["când", "cât", "prep", "cât timp", "ROOT", "prep", "care", "unde"]}
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
]


# TODO prepozitiile compuse ar trebui sa fie inlantuite?

# trebuie să mă tund până pe 1 iunie

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
            print(itn, "Losses", losses)

    return nlp


def dep_span(doc, token, merge_attr=False):
    def dfs(node):
        first = last = node.i
        for child in node.children:
            if child.dep_ in ['-', 'prep'] or (merge_attr and child.dep_ in ['care', 'ce fel de', 'cât', 'al cui']):
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
    """ Save the model to the output directory. """

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


if __name__ == "__main__":
    analyze_data(TRAIN_DATA)

    # uncomment this to train the model before the testing step
    model = train("spacy_ro", n_iter=30)
    store_model(model, '../../models/spacy-syntactic')

    # test the model
    model = spacy.load('../../models/spacy-syntactic')
    test_model(model, True)
