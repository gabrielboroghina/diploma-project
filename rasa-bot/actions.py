"""
Custom actions to be performed in response to specific intents.
"""

from typing import Any, Text, Dict, List, Union
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.forms import FormAction

from knowledge_base.db_bridge import DbBridge
from knowledge_base.types import InfoType

db_bridge = DbBridge()
entity_extraction_failure_msg = "Nu am putut extrage entitățile"


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
            dispatcher.utter_message(entity_extraction_failure_msg)

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
            dispatcher.utter_message(entity_extraction_failure_msg)
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
            db_bridge.set_value(entity, location, type=InfoType.LOC)
        else:
            dispatcher.utter_message(entity_extraction_failure_msg)
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
            result = db_bridge.get_value(entity, type=InfoType.LOC)
            dispatcher.utter_message(result)
        else:
            dispatcher.utter_message(entity_extraction_failure_msg)
        return []


class ActionGetTime(Action):
    def __init__(self):
        super().__init__()

    def name(self) -> Text:
        return "action_get_time"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        message = tracker.latest_message

        # extract relevant entities from the phrase
        entity = None
        action = None
        times = []
        is_simple_event = True  # simple event (noun phrase) or a complex one (containing subject/other details)

        semantic_roles = message['semantic_roles']
        print(semantic_roles)
        for ent in semantic_roles:
            if ent['question'] in ['ce', 'cine']:
                entity = ent
            elif ent['question'] in ['când', 'cât timp']:
                times.append(ent)
            elif ent['question'] == 'ROOT':
                action = ent['lemma']
            else:
                is_simple_event = False

        # determine the type of timestamp requested
        question_phrase = times[0]['ext_value']
        question_type = times[0]['question']

        info_type = InfoType.TIME_POINT
        if question_type == "cât timp" or action in ["dura", "ține"]:
            info_type = InfoType.TIME_DURATION
        elif question_phrase in ["de când"] or action in ["începe", "porni", "apărea", "veni"]:
            info_type = InfoType.TIME_START
        elif question_phrase in ["până când"] or action in ["termina", "sfârși", "încheia", "finaliza"]:
            info_type = InfoType.TIME_END

        if entity:
            if is_simple_event:
                result = db_bridge.get_value(entity, type=info_type)
            else:
                result = "Not implemented"
            dispatcher.utter_message(result)
        else:
            dispatcher.utter_message(entity_extraction_failure_msg)
        return []


class ActionStoreTime(Action):
    def __init__(self):
        super().__init__()

    def name(self) -> Text:
        return "action_store_time"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        message = tracker.latest_message

        # extract relevant entities from the phrase
        entity = None
        action = None
        time = None
        is_simple_event = True

        semantic_roles = message['semantic_roles']
        print(semantic_roles)

        for ent in semantic_roles:
            if ent['question'] in ['ce', 'cine']:
                if entity:
                    is_simple_event = False
                entity = ent
            elif ent['question'] in ['când', 'cât timp']:
                time = ent
            elif ent['question'] == "ROOT":
                pass
            else:
                is_simple_event = False

        info_type = InfoType.TIME_POINT
        if time['ext_value'] in ['de când'] or action in ["începe", "porni", "apărea", "veni"]:
            info_type = InfoType.TIME_START
        elif time['ext_value'] in ['până când'] or action in ["termina", "sfârși", "încheia", "finaliza"]:
            info_type = InfoType.TIME_END
        elif time['question'] == "cât timp":
            info_type = InfoType.TIME_DURATION

        print(time, time['question'], info_type)

        if entity:
            if is_simple_event:
                db_bridge.set_value(entity, time['ext_value'], type=info_type)
        else:
            dispatcher.utter_message(entity_extraction_failure_msg)
        return []


class ActionKeepRawAttrEntity(Action):
    def __init__(self):
        super().__init__()

    def name(self) -> Text:
        return "action_keep_raw_attr_entity"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        message = tracker.latest_message

        entity = None
        semantic_roles = message['semantic_roles']
        for ent in semantic_roles:
            if ent['question'] == 'cine':
                entity = ent

        return [SlotSet("raw_attr_entity", entity)]


class RawDataStoreForm(FormAction):
    """Example of a custom form action"""

    def name(self):
        """Unique identifier of the form"""
        return "raw_data_store_form"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill"""

        return ["raw_attr_val"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""

        return {
            "raw_attr_val": self.from_text(),  # the raw value is actually the whole text entered by the user
        }

    def submit(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Define what the form has to do after all required slots are filled"""

        raw_attr_entity = tracker.get_slot("raw_attr_entity")
        raw_attr_val = tracker.get_slot("raw_attr_val")
        db_bridge.set_value(raw_attr_entity, raw_attr_val, type=InfoType.VAL)
        return []
