"""
Custom actions.
"""

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk import Action, Tracker

import spacy


class ActionGetLocation(Action):

    def __init__(self):
        super().__init__()
        self.spacy_nlp = spacy.load("ro")

    def name(self) -> Text:
        return "action_get_location"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        phrase = tracker.latest_message['text']
        doc = self.spacy_nlp(phrase)
        dispatcher.utter_message(' '.join([token.tag_ for token in doc]))

        object = list(tracker.get_latest_entity_values('obj'))
        attribute = list(tracker.get_latest_entity_values('location'))
        dispatcher.utter_message(f"{object} -> {attribute}")

        return []
