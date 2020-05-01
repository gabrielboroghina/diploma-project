"""
Custom actions.
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from knowledge_base.db_bridge import DbBridge

db_bridge = DbBridge()


class ActionStoreAttribute(Action):
    def __init__(self):
        super().__init__()
        # self.spacy_nlp = spacy.load("ro")

    def name(self) -> Text:
        return "action_store_attr"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # get user's utterance (request)
        message = tracker.latest_message

        # extract relevant entities from the phrase
        owner = None
        attr_name = None
        value = None

        semantic_roles = message['semantic_roles']
        print(semantic_roles)
        for ent in semantic_roles:
            if ent['question'] == 'cine':
                attr_name = ent['value']
                for specifier in ent['specifiers']:
                    if specifier['question'] == 'al cui':
                        owner = specifier['value']
                        break
            elif ent['question'] == 'care este':
                value = ent['value']

        # insert data into the database
        if owner and attr_name and value:
            db_bridge.set_attr(owner, (attr_name, value))
        else:
            dispatcher.utter_message("Nu am putut extrage entitățile")

        # doc = self.spacy_nlp(phrase)
        # dispatcher.utter_message(' '.join([token.tag_ for token in doc]))
        #
        # object = list(tracker.get_latest_entity_values('obj'))
        # attribute = list(tracker.get_latest_entity_values('location'))
        # dispatcher.utter_message(f"{object} -> {attribute}")

        return []


class ActionGetAttribute(Action):
    def __init__(self):
        super().__init__()

    def name(self) -> Text:
        return "action_get_attr"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # get user's utterance (request)
        message = tracker.latest_message

        # extract relevant entities from the phrase
        owner = None
        attr_name = None

        semantic_roles = message['semantic_roles']
        print(semantic_roles)
        for ent in semantic_roles:
            if ent['question'] in ['ce', 'cine'] and ent['value'] != "care":
                attr_name = ent['value']
                for specifier in ent['specifiers']:
                    if specifier['question'] == 'al cui':
                        owner = specifier['value']

        # query the database
        result = db_bridge.get_attr(owner, attr_name)
        dispatcher.utter_message(result)
        return []
