import typing
from typing import Any, Optional, Text, Dict, List, Type

from rasa.nlu.components import Component
from rasa.nlu.config import RasaNLUModelConfig
from rasa.nlu.training_data import Message, TrainingData

import spacy
from spacy.tokens import Span

if typing.TYPE_CHECKING:
    from rasa.nlu.model import Metadata


class SyntacticParser(Component):
    """Component that identifies syntactic entities of the phrase by their syntactic question"""

    @classmethod
    def required_components(cls) -> List[Type[Component]]:
        """Specify which components need to be present in the pipeline."""

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

    def __init__(self, component_config: Optional[Dict[Text, Any]] = None) -> None:
        super().__init__(component_config)

        self.nlp_spacy = spacy.load('../models/spacy-syntactic')

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

    def process(self, message: Message, **kwargs: Any) -> None:
        """Process an incoming message.

        This is the components chance to process an incoming message. The component can rely on any context
        attribute to be present, that gets created by a call to :meth:`components.Component.pipeline_init`
        of ANY component and on any context attributes created by a call to :meth:`components.Component.process`
        of components previous to this one."""

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

        # parse the phrase
        doc = self.nlp_spacy(message.text)

        # TODO integrate attributes into their determiners as sub-dicts
        semantic_roles = []
        for token in doc:
            if token.dep_ not in ['-']:
                entity = {
                    "question": token.dep_,
                    "determiner": dep_span(doc, token.head),
                    "value": dep_span(doc, token, True),
                    "extractor": self.name
                }
                semantic_roles.append(entity)

        # add extracted entities to the message
        message.set("semantic_roles", semantic_roles, add_to_output=True)

    def persist(self, file_name: Text, model_dir: Text) -> Optional[Dict[Text, Any]]:
        """Persist this component to disk for future loading."""

        pass
