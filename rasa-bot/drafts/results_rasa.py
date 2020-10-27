import itertools

from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


def plot_confusion_matrix(y_true, y_pred, labels):
    print(labels)
    conf_mat = confusion_matrix(y_true, y_pred, labels=labels)

    sns.heatmap(conf_mat, annot=conf_mat, fmt='g', cmap='Blues',
                xticklabels=labels, yticklabels=labels, annot_kws={"size": 13})
    plt.xticks(fontsize=13, rotation=90, ha='right')
    plt.yticks(fontsize=13)
    plt.xlabel('Predicted label', fontsize=14)
    plt.ylabel('True label', fontsize=14)
    plt.title("Intent Confusion matrix", fontsize=14)
    plt.savefig("intent_confmat.svg", format="svg", bbox_inches='tight')
    plt.show()


intents = {
    'affirm': 3,
    'get_attr': 12,
    'get_location': 10,
    'get_specifier': 14,
    'get_subject': 5,
    'get_timestamp': 16,
    'goodbye': 2,
    'greet': 2,
    'store_attr': 11,
    'store_following_attr': 10,
    'store_location': 18,
    'store_request': 3,
    'store_timestamp': 22,
}


intents_true = list(itertools.chain.from_iterable([[label] * f for (label, f) in intents.items()]))
intents_pred = list(intents_true)
plot_confusion_matrix(intents_true, intents_pred, list(intents.keys()))

def count_examples_for_intent(file):
    freq = {}
    intent = None
    with open(file) as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('##'):
                intent = line.split(':')[1].strip()
                freq[intent] = 0
            elif line.startswith('-'):
                freq[intent] += 1
    return freq


def plot_datasets_distribution(train, test):
    y_pos = np.arange(len(intents))

    width = 0.4

    plt.barh(y_pos + width / 2, [train.get(intent) for intent in intents], width,
             color='mediumseagreen', label='Train')
    plt.barh(y_pos - width / 2, [test.get(intent) for intent in intents], width,
             color='tan', label='Test')

    plt.yticks(y_pos, intents, fontsize=13)
    plt.xticks(fontsize=13)
    plt.xlabel('Number of examples', fontsize=13)
    plt.ylabel('Intent', fontsize=13)
    plt.title('Distribution of the intent classification dataset', fontsize=13)
    plt.legend(fontsize=12)
    plt.savefig("distr_intent_classif_dataset.svg", format="svg", bbox_inches='tight')
    plt.show()


train = count_examples_for_intent('../data/nlu.md')
test = count_examples_for_intent('../data/nlu_test.md')
print(train)
print(test)

# plot_datasets_distribution(train, test)
