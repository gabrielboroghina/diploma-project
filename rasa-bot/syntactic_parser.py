import typing
from typing import Any, Optional, Text, Dict, List, Type

from rasa.nlu.components import Component
from rasa.nlu.config import RasaNLUModelConfig
from rasa.nlu.training_data import Message, TrainingData

import spacy
from spacy.tokens import Span
from spacy.lookups import Lookups
from spacy.lang.ro import tag_map

if typing.TYPE_CHECKING:
    from rasa.nlu.model import Metadata


class SyntacticParser(Component):
    """ Component that identifies syntactic entities of the phrase by their syntactic question. """

    @classmethod
    def required_components(cls) -> List[Type[Component]]:
        """ Specify which components need to be present in the pipeline. """

        return []

    name = "SyntacticParser"

    # Defines the default configuration parameters of a component
    # these values can be overwritten in the pipeline configuration
    # of the model. The component should choose sensible defaults
    # and should be able to create reasonable results with the defaults.
    defaults = {}

    # Defines what language(s) this component can handle.
    # This attribute is designed for instance method: `can_handle_language`.
    # Default value is None which means it can handle all languages.
    # This is an important feature for backwards compatibility of components.
    language_list = ['ro']

    @staticmethod
    def __load_lemmas():
        # extract lemma lookup tables from the compressed binary file (.bin)
        lookups = spacy.lookups.Lookups()
        lookups.from_disk('./data/lookups')
        noun_lemmas = lookups.get_table("noun-lemmas")
        prop_noun_lemmas = lookups.get_table("prop-noun-lemmas")
        verb_lemmas = lookups.get_table("verb-lemmas")

        # manually create a pronoun lemma lookup table
        pronouns = {'meu': 'eu', 'mea': 'eu', 'mei': 'eu', 'mele': 'eu',
                    'lui': 'el', 'lor': 'ei'}
        pron_lemmas = spacy.lookups.Table.from_dict(pronouns)

        return {
            tag_map.NOUN: noun_lemmas,
            tag_map.PROPN: prop_noun_lemmas,
            tag_map.VERB: verb_lemmas,
            tag_map.PRON: pron_lemmas,
        }

    def __init__(self, component_config: Optional[Dict[Text, Any]] = None) -> None:
        super().__init__(component_config)

        # initialize spaCy model used for syntactic-semantic parsing
        self.nlp_spacy = spacy.load('../models/spacy-syntactic')

        # initialize the lemmatizer
        self.lemmas = SyntacticParser.__load_lemmas()

    def train(
            self,
            training_data: TrainingData,
            config: Optional[RasaNLUModelConfig] = None,
            **kwargs: Any,
    ) -> None:
        """Train this component.

        This is the components chance to train itself provided with the training data. The component can rely on
        any context attribute to be present, that gets created by a call to :meth:`components.Component.pipeline_init`
        of ANY component and on any context attributes created by a call to :meth:`components.Component.train`
        of components previous to this one."""
        pass

    @staticmethod
    def __part_of_speech_from_tag(tag):
        """ Return the part of speech code for a given POS detailed tag. """

        pos_tag_map = {
            "A": tag_map.ADJ,
            "D": tag_map.DET,
            "C": tag_map.CCONJ,
            "I": tag_map.INTJ,
            "M": tag_map.NUM,
            "N": tag_map.NOUN,
            "P": tag_map.PRON,
            "R": tag_map.ADV,
            "T": tag_map.DET,
            "V": tag_map.VERB,
        }

        if tag in tag_map.TAG_MAP:
            return tag_map.TAG_MAP[tag][tag_map.POS]
        return pos_tag_map.get(tag[0])

    def __lemmatize(self, token):
        """
        Get the lemma for the given inflected word.

        :return the word's lemma ot the same word if the lemma is not available in the lookup tables
        """

        tag = token.tag_.split('__')[0]  # extract the compact tag
        pos = SyntacticParser.__part_of_speech_from_tag(tag)
        word = token.text

        # proper noun
        if word in self.lemmas[tag_map.PROPN]:
            return self.lemmas[tag_map.PROPN][word]

        # POS = pronoun
        if word in self.lemmas[tag_map.PRON]:
            return self.lemmas[tag_map.PRON][word]

        # POS = noun
        if pos == tag_map.NOUN:
            return self.lemmas[tag_map.NOUN].get(word, word)

        # POS = verb
        if pos == tag_map.VERB:
            return self.lemmas[tag_map.VERB].get(word, word)

        # TODO numeral - doi/două -> 2

        return word

    def __get_dependency_span(self, doc, token, include_all_deps=False):
        """
        Build the span of words connected to a given token
        (representing attributes/prepositions/conjunctions etc).
        """

        def dfs(node):
            first = last = node.i
            for child in node.children:
                if child.dep_ in ['-', 'prep', 'cât', 'cât timp'] or \
                        (include_all_deps and child.dep_ in ['care', 'ce fel de', 'al cui']):
                    child_first, child_last = dfs(child)
                    first = min(first, child_first)
                    last = max(last, child_last)
            return first, last

        first, last = dfs(token)  # compute bounds of the span
        span = Span(doc, first, last + 1)
        return span.text

    def __get_specifiers(self, doc, parent):
        """ Extract attributes (that identifies a specific instance of an entity) of a given token. """

        specifiers = []
        for token in doc:
            if token.head == parent:
                if token.dep_ in ['care', 'ce fel de', 'cât'] or \
                        token.dep_ == 'cât timp' and token.head.dep_ != "ROOT":
                    specifiers.append({
                        "question": token.dep_,
                        "determiner": self.__get_dependency_span(doc, token.head),
                        "value": self.__get_dependency_span(doc, token, True),
                        "lemma": self.__get_dependency_span(doc, token, True),
                        "specifiers": []
                    })
                elif token.dep_ in ['al cui']:
                    specifiers.append({
                        "question": token.dep_,
                        "determiner": self.__get_dependency_span(doc, token.head),
                        "value": token.text,
                        "lemma": self.__lemmatize(token),
                        "specifiers": self.__get_specifiers(doc, token)
                    })

        return specifiers

    def process(self, message: Message, **kwargs: Any) -> None:
        """Process an incoming message.

        This is the components chance to process an incoming message. The component can rely on any context
        attribute to be present, that gets created by a call to :meth:`components.Component.pipeline_init`
        of ANY component and on any context attributes created by a call to :meth:`components.Component.process`
        of components previous to this one."""

        # parse the phrase
        doc = self.nlp_spacy(message.text.lower())

        semantic_roles = []
        for token in doc:
            if token.dep_ not in ['-'] and token.head.dep_ == 'ROOT':
                entity = {
                    "question": token.dep_,
                    "determiner": self.__get_dependency_span(doc, token.head),
                    "value": token.text,
                    "lemma": self.__lemmatize(token),
                    "ext_value": self.__get_dependency_span(doc, token, True),
                    "specifiers": self.__get_specifiers(doc, token)
                }
                semantic_roles.append(entity)

        # add extracted entities to the message
        message.set("semantic_roles", semantic_roles, add_to_output=True)

    def persist(self, file_name: Text, model_dir: Text) -> Optional[Dict[Text, Any]]:
        """Persist this component to disk for future loading."""

        pass
