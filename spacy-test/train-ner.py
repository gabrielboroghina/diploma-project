# coding: utf8
"""Example of training spaCy's named entity recognizer, starting off with an
existing model or a blank model.
For more details, see the documentation:
* Training: https://spacy.io/usage/training
* NER: https://spacy.io/usage/linguistic-features#named-entities
Compatible with: spaCy v2.0.0+
Last tested with: v2.1.0
"""
from __future__ import unicode_literals, print_function

import time
import plac
import random
from pathlib import Path
import spacy
from spacy.util import minibatch, compounding

# training data

LOC = 'LOC'
TIME = 'TIME'
TRAIN_DATA = [
    ("cartea e pe birou", {"entities": [(9, 17, LOC)]}),
    ("cartea e in dulap la facultate", {"entities": [(9, 17, LOC), (18, 30, LOC)]}),
    ("am venit in casă", {"entities": [(9, 16, LOC)]}),
    ("mergem la mare", {"entities": [(7, 14, LOC)]}),
    ("mihai a pus floarea la geam", {"entities": [(20, 27, LOC)]}),
    ("am văzut-o la magazin", {"entities": [(11, 21, LOC)]}),
    ("mingea este sub pat", {"entities": [(12, 19, LOC)]}),

    ("o să merg la prânz acasă", {"entities": [(10, 18, TIME)]}),
    ("eu merg de la 2 ani", {"entities": [(8, 19, TIME)]}),
    ("tu cânți de trei zile", {"entities": [(8, 20, TIME)]}),
    ("tu cânți de 10 zile", {"entities": [(8, 20, TIME)]}),
    ("azi am fost la mare", {"entities": [(0, 3, TIME)]}),
    ("de mâine începe școala", {"entities": [(0, 8, TIME)]}),
    ("mâine începe școala", {"entities": [(0, 5, TIME)]}),
    ("mihai are teme de acum 2 zile", {"entities": [(15, 29, TIME)]}),
    ("cred că are treabă mâine", {"entities": [(19, 24, TIME)]}),
    ("eu am luat asta azi", {"entities": [(16, 19, TIME)]}),
    ("ieri a plouat mult", {"entities": [(0, 4, TIME)]}),

    ("pe 10 martie o să merg la teatru", {"entities": [(0, 12, TIME), (23, 32, LOC), ]}),
    ("în ianuarie a nins", {"entities": [(0, 12, TIME), ]}),
    ("în februarie a fost mai bine", {"entities": [(0, 13, TIME), ]}),
    ("în martie e cald și frumos afară", {"entities": [(27, 32, LOC), (3, 10, TIME), ]}),
    ("din aprilie se încălzește afară", {"entities": [(26, 31, LOC), (4, 12, TIME), ]}),
    ("cred că în mai o să am treabă la birou", {"entities": [(30, 38, LOC), (8, 14, TIME), ]}),
    ("în iunie e ziua mea", {"entities": [(0, 9, TIME), ]}),
    ("în general în iulie e foarte cald în București", {"entities": [(34, 46, LOC), (11, 19, TIME), ]}),
    ("pe 9 august e ziua Europei", {"entities": [(0, 12, TIME), ]}),
    ("de obicei în septembrie merg la bunici", {"entities": [(10, 23, TIME), (29, 38, LOC), ]}),
    ("tati e născut în octombrie", {"entities": [(14, 26, TIME), ]}),
    ("colegii mei au vacanță în noiembrie", {"entities": [(23, 35, TIME), ]}),
    ("în decembrie e destul de frig peste tot", {"entities": [(30, 39, LOC), (3, 13, TIME), ]}),
]

TEST_DATA = [
    ("ce e in birou", ''),
    ("cum a fost ieri la facultate?", ''),
    ("de mâine mă apuc de învățat", ''),
    ("în iulie o să am de prezentat licența la facultate", ''),
]


@plac.annotations(
    model=("Model name. Defaults to blank 'en' model.", "option", "m", str),
    output_dir=("Optional output directory", "option", "o", Path),
    n_iter=("Number of training iterations", "option", "n", int),
)
def main(model=None, output_dir=None, n_iter=100):
    """Load the model, set up the pipeline and train the entity recognizer."""
    start = time.time()

    if model is not None:
        nlp = spacy.load(model)  # load existing spaCy model
        print("Loaded model '%s'" % model)
    else:
        nlp = spacy.blank("ro")  # create blank Language class
        print("Created blank 'ro' model")

    # create the built-in pipeline components and add them to the pipeline
    # nlp.create_pipe works for built-ins that are registered with spaCy
    if "ner" not in nlp.pipe_names:
        ner = nlp.create_pipe("ner")
        nlp.add_pipe(ner, last=True)
    # otherwise, get it so we can add labels
    else:
        ner = nlp.get_pipe("ner")

    # add labels
    for _, annotations in TRAIN_DATA:
        for ent in annotations.get("entities"):
            ner.add_label(ent[2])

    # get names of other pipes to disable them during training
    pipe_exceptions = ["ner", "trf_wordpiecer", "trf_tok2vec"]
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]
    with nlp.disable_pipes(*other_pipes):  # only train NER
        # reset and initialize the weights randomly – but only if we're
        # training a new model
        if model is None:
            nlp.begin_training()
        for itn in range(n_iter):
            random.shuffle(TRAIN_DATA)
            losses = {}
            # batch up the examples using spaCy's minibatch
            batches = minibatch(TRAIN_DATA, size=compounding(4.0, 32.0, 1.001))
            for batch in batches:
                texts, annotations = zip(*batch)
                nlp.update(
                    texts,  # batch of texts
                    annotations,  # batch of annotations
                    drop=0.5,  # dropout - make it harder to memorise data
                    losses=losses,
                )
            print("Losses", losses)

    end = time.time()
    print('Training elapsed time:', round(end - start, 2), 's')
    print('-------------------------------------------------------', '\n')

    # test the trained model
    for text, _ in TEST_DATA:
        doc = nlp(text)
        print("Entities", [(ent.text, ent.label_) for ent in doc.ents])
        print("Tokens", [(t.text, t.ent_type_, t.ent_iob) for t in doc])

    # save model to output directory
    if output_dir is not None:
        output_dir = Path(output_dir)
        if not output_dir.exists():
            output_dir.mkdir()
        nlp.to_disk(output_dir)
        print("Saved model to", output_dir)

        # test the saved model
        print("Loading from", output_dir)
        nlp2 = spacy.load(output_dir)
        for text, _ in TEST_DATA:
            doc = nlp2(text)
            print("Entities", [(ent.text, ent.label_) for ent in doc.ents])
            print("Tokens", [(t.text, t.ent_type_, t.ent_iob) for t in doc])


if __name__ == "__main__":
    plac.call(main)
