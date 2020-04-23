import spacy
from spacy import displacy
from spacy.tokens import Span
# from dexBridge import DexBridge

nlp = spacy.load("spacy_ro")
# nlp = spacy.load("../../UD_Romanian-RRT/models/model-best")
if "ner" in nlp.pipe_names:
    nlp.disable_pipes("ner")

questionIntroductoryEnts = [
    # pronume interogative
    'cine',
    'ce',
    'care',  # 'cui', 'cărui', 'căruia', 'cărei', 'căreia', 'căror', 'cărora',
    'cât', 'câtă', 'câți', 'câte',  # câtor, câtora
    # 'a câta', 'al câtelea',
    # adverbe
    'unde',
    'când',
    'cum'
]

phrases = [
    'Adresa lui Dan este dan@mail',
    'Cartea mea e acolo',
    'FLorile lui Alex sunt pe pervaz',
    'Am pus ceasul la ușă',
    'Am scos televizorul din sufragerie din priză',
    'cartea de istorie de pe birou e plină cu poze cu război',
    'De fiecare dată când ies afară mă simt mai bine',
    'Azi eu mi-am cumpărat un nou ceas de la magazin',
    'Cartea de biologie se află pe raftul din sufragerie',
    'Părțile secundare de propoziție sunt subordonate altor părți de propoziție',
    'Care era adresa băiatului în 1996?',
    'Unde statea Gabi anul trecut?',
    'Unde este cartea de istorie',
    'Care este mailul lui?',
    # 'Eu și Alex am fost la concurs seara trecută',
    'Eu cânt de la 5 ani',
    'Când eu mergeam acasă l-am văzut pe Mihai la balcon',
    'Lui Winston îi displăcuse fata asta din primul moment când o văzuse.',
    'E făcut de o luna de cineva de la Elena',
    'Prezenta gramatică este normativă prin faptul că face ceva important',
    'Complementul circumstanţial de timp este partea secundară de propoziție care arată timpul în care se petrece o acțiune'
]

# dexBridge = DexBridge()


def findEntities(doc):
    ents = [(e.text, e.start_char, e.end_char, e.label_) for e in doc.ents]
    newEnts = []

    for i, token in enumerate(doc):
        word = token.text.lower()
        if token.tag_.startswith("V"):
            ent = Span(doc, i, i + 1, label='PREDICATE')  # create a Span for the new entity
            newEnts.append(ent)
        elif word in questionIntroductoryEnts:
            ent = Span(doc, i, i + 1, label='INTEROG')
            newEnts.append(ent)
        elif token.dep_.startswith('nsubj'):
            firstToken = i
            lastToken = i

            def dfs(node):
                nonlocal firstToken
                nonlocal lastToken
                firstToken = min(firstToken, node.i)
                lastToken = max(lastToken, node.i)
                for child in node.children:
                    dfs(child)

            dfs(token)
            ent = Span(doc, firstToken, lastToken + 1, label='SUBJ')
            newEnts.append(ent)

    doc.ents = list(doc.ents) + newEnts


def pos(tag):
    if tag[0] == 'N':
        return "substantiv"
    elif tag[0] == 'V':
        return "verb"
    elif tag[0] == 'P':
        return "pronume"
    elif tag[0] == 'A':
        return "adjectiv"
    return ""


class TermColors:
    PINK = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def parsePhrase(phrase):
    print('\n', phrase, '\n------------------------------')
    doc = nlp(phrase)
    findEntities(doc)
    for token in doc:
        lemma = ""  # dexBridge.lemmaForWord(token.text, pos(token.tag_))
        print(token.text, TermColors.YELLOW, lemma,
              TermColors.PINK, token.tag_, TermColors.ENDC)
    for chunk in doc.noun_chunks:
        print(chunk.text, chunk.root.text, chunk.root.dep_,
              chunk.root.head.text)

    return doc


docs = []
for phrase in phrases:
    parsedDoc = parsePhrase(phrase)
    docs.append(parsedDoc)

colors = {"INTEROG": "#6d629e", "SUBJ": "#db1f57"}
options = {"colors": colors, "add_lemma": True, "compact": False, "fine_grained": False}
# displacy.serve(docs, style="ent", host='localhost', options=options)

htmlDep = displacy.render(docs, style="dep", page=True, options=options)
htmlEnt = displacy.render(docs, style="ent", page=True, options=options)
with open("my.html", "w", encoding='utf8') as f:
    f.write(htmlEnt)
    f.write(htmlDep)
