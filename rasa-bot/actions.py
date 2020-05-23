"""
Custom actions to be performed in response to specific intents.
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

    def name(self) -> Text:
        return "action_store_attr"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # get user's utterance (request)
        message = tracker.latest_message

        # extract relevant entities from the phrase
        entity = None
        value = None

        semantic_roles = message['semantic_roles']
        print(semantic_roles)
        for ent in semantic_roles:
            if ent['question'] == 'cine':
                entity = ent
            elif ent['question'] == 'care este':
                value = ent['value']

        # insert data into the database
        if entity and value:
            db_bridge.set_value(entity, value)
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
        entity = None

        semantic_roles = message['semantic_roles']
        print(semantic_roles)
        for ent in semantic_roles:
            if ent['question'] in ['ce', 'cine'] and ent['value'] != "care":
                entity = ent

        # query the database
        if entity:
            result = db_bridge.get_value(entity)
            dispatcher.utter_message(result)
        else:
            dispatcher.utter_message("Nu am putut extrage entitățile")
        return []


class ActionStoreLocation(Action):
    def __init__(self):
        super().__init__()

    def name(self) -> Text:
        return "action_store_location"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        message = tracker.latest_message

        # extract relevant entities from the phrase
        entity = None
        location = None

        semantic_roles = message['semantic_roles']
        print(semantic_roles)
        for ent in semantic_roles:
            if ent['question'] in ['ce', 'cine']:
                entity = ent
            elif ent['question'] == 'unde':
                location = ent

        # query the database
        if entity and location:
            db_bridge.set_value(entity, location, type="LOC")
        else:
            dispatcher.utter_message("Nu am putut extrage entitățile")
        return []


class ActionGetLocation(Action):
    def __init__(self):
        super().__init__()

    def name(self) -> Text:
        return "action_get_location"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        message = tracker.latest_message

        # extract relevant entities from the phrase
        entity = None

        semantic_roles = message['semantic_roles']
        print(semantic_roles)
        for ent in semantic_roles:
            if ent['question'] in ['ce', 'cine']:
                entity = ent

        if entity:
            result = db_bridge.get_value(entity, type="LOC")
            dispatcher.utter_message(result)
        else:
            dispatcher.utter_message("Nu am putut extrage entitățile")
        return []
