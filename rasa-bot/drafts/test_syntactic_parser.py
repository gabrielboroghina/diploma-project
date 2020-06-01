import spacy
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

test_sentences = [
    (
        "săptămâna trecută s-au terminat lucrările la gura de metrou de la stația Romancierilor",
        {
            "heads": [5, 0, 5, 4, 5, 5, 5, 8, 6, 10, 8, 12, 13, 8, 13],
            "deps": ["când", "care", "pe cine", "-", "-", "ROOT", "ce", "-", "care", "-", "care", "-", "-", "care",
                     "al cui"]}
    ),
    (
        "marți vine Elon Musk în România",
        {
            "heads": [1, 1, 1, 2, 5, 1],
            "deps": ["când", "ROOT", "cine", "care", "-", "unde"]}
    ),
    (
        "bateria de la ceasul meu de mână este descărcată",
        {
            "heads": [7, 2, 3, 0, 3, 6, 3, 7, 7],
            "deps": ["cine", "-", "-", "care", "al cui", "-", "care", "ROOT", "cum este"]}
    ),
    (
        "predicțiile lui Michael pentru evoluția crizei au fost corecte",
        {
            "heads": [7, 2, 0, 4, 0, 4, 7, 7, 7],
            "deps": ["cine", "-", "al cui", "-", "care", "al cui", "-", "ROOT", "cum este"]}
    ),
    (
        "unde am pus pantalonii de pijama ai lui Radu",
        {
            "heads": [2, 2, 2, 2, 5, 3, 8, 8, 3],
            "deps": ["unde", "-", "ROOT", "ce", "-", "care", "-", "-", "al cui"]}
    ),
    (
        "de unde am luat pliculețele de ceai negru",
        {
            "heads": [1, 3, 3, 3, 3, 6, 4, 6],
            "deps": ["prep", "unde", "-", "ROOT", "ce", "-", "care", "ce fel de"]}
    ),
    (
        "ochelarii ionelei sunt pe noptiera lui ionuț din dormitor",
        {
            "heads": [2, 0, 2, 4, 2, 6, 4, 8, 4],
            "deps": ["cine", "al cui", "ROOT", "-", "unde", "-", "al cui", "-", "care"]}
    ),
    (
        "pe unde am lăsat pompa de bicicletă",
        {
            "heads": [1, 3, 3, 3, 3, 6, 4],
            "deps": ["-", "unde", "-", "ROOT", "ce", "-", "care"]}
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
            "deps": ["cine", "-", "care", "-", "-", "al cui", "ROOT", "care este"]}
    ),
    (
        "numele profesoarei mele de biologie din liceu este Mariana Mihai",
        {
            "heads": [7, 0, 1, 4, 1, 6, 1, 7, 7, 8],
            "deps": ["cine", "al cui", "al cui", "-", "care", "-", "care", "ROOT", "care este", "care"]}
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
            "deps": ["când", "-", "ROOT", "cine", "-", "care", "-", "al cui"]}
    ),
    (
        "Dan vine acasă din Germania în fiecare vară",
        {
            "heads": [1, 1, 1, 4, 2, 7, 7, 1],
            "deps": ["cine", "ROOT", "unde", "prep", "unde", "-", "care", "cât de des"]}
    ),
]

dependency_types = [
    "-",
    "prep",
    "ROOT",
    "cine",
    "care",
    "ce fel de",
    "ce",
    "pe cine",
    "unde",
    "când",
    "cât timp",
    "cât de des",
    "cum este",
    "ce este",
    "care este",
    "al cui",
    "cât",
    "cui",
]


def plot_confusion_matrix(y_true, y_pred, labels):
    conf_mat = confusion_matrix(y_true, y_pred, labels=labels)

    sns.heatmap(conf_mat, annot=conf_mat, fmt='g', cmap='Greens',
                xticklabels=labels, yticklabels=labels)
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title("Syntactic questions prediction")
    plt.show()


if __name__ == "__main__":
    nlp = spacy.load('../../models/spacy-syntactic')

    deps_true = []
    deps_pred = []
    correct_heads = {dep: 0 for dep in dependency_types}
    num_deps = {dep: 0 for dep in dependency_types}

    # parse sentences
    docs = nlp.pipe(map(lambda s: s[0], test_sentences))

    # evaluate predictions
    for i, doc in enumerate(docs):
        true_sentence_deps = test_sentences[i][1]

        # evaluate dependencies (syntactic questions) prediction
        deps_true += true_sentence_deps['deps']
        deps_pred += [token.dep_ for token in doc]

        # evaluate heads prediction
        for j, token in enumerate(doc):
            if token.head.i == true_sentence_deps['heads'][j]:
                correct_heads[true_sentence_deps['deps'][j]] += 1
            num_deps[true_sentence_deps['deps'][j]] += 1

    print("Number of test examples", len(test_sentences))
    print("Syntactic questions accuracy:")
    print(classification_report(deps_true, deps_pred, zero_division=0))
    plot_confusion_matrix(deps_true, deps_pred, dependency_types)

    print("Heads accuracy: ", sum(correct_heads.values()) / sum(num_deps.values()), '\n')

    for dep in dependency_types:
        acc = round(correct_heads[dep] / num_deps[dep], 2) if num_deps[dep] > 0 else '-'
        print(f'- {dep}: {" " * (15 - len(dep))}{acc}')
