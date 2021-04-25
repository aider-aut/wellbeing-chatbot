# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType, ConversationPaused, UserUtteranceReverted


def _ReadLookUps(path):
    lookups = open(path, "r")
    temp = lookups.read().splitlines()
    lookups.close()
    return temp


ANGRY = _ReadLookUps("data/lookups/angry.txt")
SAD = _ReadLookUps("data/lookups/sad.txt")


class ActionSubmitDiagnosisForm(Action):
    def name(self) -> Text:
        return "action_submit_diagnosis_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[EventType]:
        area_of_life = tracker.get_slot("area_of_life")
        coping_strategy = tracker.get_slot("coping_strategy")
        unhealthy_thoughts = tracker.get_slot("unhealthy_thoughts")

        dispatcher.utter_message(text="area of life: {}".format(area_of_life))
        dispatcher.utter_message(
            text="coping strategy: {}".format(coping_strategy))
        dispatcher.utter_message(
            text="unhealthy thoughts: {}".format(unhealthy_thoughts))

        return []


class ActionClarifyEmotions(Action):
    def name(self) -> Text:
        return "action_clarify_emotions"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        emotion = tracker.get_slot("emotions")
        dispatcher.utter_message(
            text="Just confirming what you have said, am I correct that you are feeling '{}'?".format(emotion))
        dispatcher.utter_message(buttons=[
            {"payload": "/affirm", "title": "Yes"},
            {"payload": "/deny", "title": "No"},
        ])
        return []


class ActionWhyEmotions(Action):

    def name(self) -> Text:
        return "action_why_emotions"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        emotion = tracker.get_slot("emotions")

        dispatcher.utter_message(
            text="If you would like to share with me, what would be the reason that you are feeling '{}'?".format(emotion))

        return []


class ActionGreetingWithName(Action):
    def name(self) -> Text:
        return "action_greeting_with_name"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        name = tracker.get_slot("name")
        if name != "None":
            dispatcher.utter_message(text="Hi {}, How are you?".format(name))
        else:
            dispatcher.utter_message(template="utter_greet")
        return []


class ActionResponseToEmotions(Action):

    def name(self) -> Text:
        return "action_response_to_emotions"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        emotion = tracker.get_slot("emotions")
        dispatcher.utter_message(template="utter_sorry_to_hear")
        dispatcher.utter_message(template="utter_cheer_up")
        if (emotion in SAD):
            dispatcher.utter_message(template="utter_quote_about_sadness")
        elif (emotion in ANGRY):
            dispatcher.utter_message(template="utter_quote_about_anger")
        return []


class ActionSetEmotion(Action):
    def name(self) -> Text:
        return "action_set_emotion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        emotion = tracker.get_slot("emotions")
        return [SlotSet('emotions', emotion)]


class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        # # Fallback caused by TwoStageFallbackPolicy
        # if (
        #     len(tracker.events) >= 4
        #     and tracker.events[-4].get("name") == "action_default_ask_affirmation"
        # ):

        #     dispatcher.utter_message(template="utter_restart_with_button")

        #     return [SlotSet("feedback_value", "negative"), ConversationPaused()]

        # Fallback caused by Core
        # else:
        dispatcher.utter_message(template="utter_default")
        return [UserUtteranceReverted()]
