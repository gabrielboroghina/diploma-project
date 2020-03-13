import spacy
from spacy.pipeline import EntityRuler
from spacy.tokens import Span
import json
import codecs
from enum import Enum
import datetime
import re

nlp = spacy.load("rasa_spacy_ro")
nlp.disable_pipes("ner")

entityRuler = EntityRuler(nlp).from_disk("./data/time-patterns.jsonl")

# entityRuler = EntityRuler(nlp, validate=True)
# with codecs.open('./data/time-patterns.jsonl', 'r', encoding='utf8') as f:
#     patternsStr = f.readlines()
#
# patterns = [json.loads(s.strip()) for s in patternsStr]
#
# other_pipes = [p for p in nlp.pipe_names if p != "tagger"]
# nlp.disable_pipes(*other_pipes)
#
# entityRuler.add_patterns(patterns)


nlp.add_pipe(entityRuler)


class TimeResolver:
    name = "datetime_resolver"

    class Grain(Enum):
        DAY = "%d-%m-%Y"

    class Timestamp:
        def __init__(self, value, grain, type='stamp'):
            self.value = value
            self.grain = grain.value
            self.type = type

        @staticmethod
        def buildOffseted(offset, grain):
            return TimeResolver.Timestamp(datetime.datetime.now() + datetime.timedelta(*offset), grain)

        @staticmethod
        def nextOf():
            pass

        def setType(self, type):
            self.type = type
            return self

        def getStamp(self):
            return {"type": self.type, "value": self.value, "grain": self.grain}

    @staticmethod
    def dayOffset(word):
        offset = {"azi": 0, "ieri": -1, "alaltăieri": -2, "mâine": 1, "poimâine": 2}
        return TimeResolver.Timestamp.buildOffseted([offset[word], 0, 0, 0, 0, 0, 0], TimeResolver.Grain.DAY)

    resolvers = {
        "": lambda ent: TimeResolver.Timestamp(datetime.datetime.now(), TimeResolver.Grain.DAY),
        "1": lambda ent: TimeResolver.dayOffset(ent[-1].text),
    }

    def __init__(self):
        Span.set_extension("datetime", default=False)

    def detectType(self, ent):
        if re.search('^(începând )?(de|din|de pe|de la)', ent.text):
            return "begin"
        elif ent.text.startswith("până") or ent.text.endswith('cel târziu') or ent.text.startswith('cel târziu'):
            return "end"
        return "point"

    def __call__(self, doc):
        for ent in doc.ents:
            if ent.label_ == "TIME":
                ent._.datetime = TimeResolver.resolvers[ent.ent_id_](ent).setType(self.detectType(ent)).getStamp()

        return doc


datetime_resolver = TimeResolver()
nlp.add_pipe(datetime_resolver, last=True)

# store the model to disk
nlp.to_disk("./time-model")

TEST_DATA = [
    "trebuie să fac tema până mâine",
    "începând de poimâine se scumpesc prețurile",
    "de miercurea viitoare se scumpesc prețurile peste 50 de ani",
    "mâine se scumpesc prețurile",
    "an examen peste câteva săptămâni",
    "o să merg pe la sfârșitul săptămânii viitoare pe 25 ianuarie",
    "Spectacolul e pe la începutul lui ianuarie anul viitor"
]
#############################################################################

for phrase in TEST_DATA:
    doc = nlp(phrase)
    for ent in doc.ents:
        print(ent.text, ent.label_, end=' ')
        if ent.label_ == "TIME":
            print(ent._.datetime['type'], ent._.datetime['value'].strftime(ent._.datetime['grain']))
        else:
            print()
