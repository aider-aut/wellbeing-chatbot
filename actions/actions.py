# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"
import datetime
from typing import Any, Text, Dict, List
import os
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import \
    SlotSet, \
    EventType, \
    ConversationPaused, \
    UserUtteranceReverted, \
    AllSlotsReset, \
    FollowupAction
from rasa_sdk.types import DomainDict
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate(os.path.abspath(os.getcwd()) + '/actions/serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
WELLBEING_COLLECTION = 'wellbeing'
USERS_COLLECTION = 'users'


def _ReadLookUps(path):
    lookups = open(path, "r")
    temp = lookups.read().splitlines()
    lookups.close()
    return temp


ANGRY = _ReadLookUps("data/lookups/angry.txt")
SAD = _ReadLookUps("data/lookups/sad.txt")
HAPPY = _ReadLookUps('data/lookups/happy.txt')


# class ValidateDiagnosisForm(FormValidationAction):
#     def name(self) -> Text:
#         return "validate_diagnosis_form"
#
#     def validate_unhealthy_thoughts(
#         self,
#         value: Text,
#         dispatcher: CollectingDispatcher,
#         tracker: Tracker,
#         domain: DomainDict,
#     ) -> Dict[Text, Any]:
#         intent = tracker.latest_message["intent"].get("name")
#         if intent == 'affirm':
#             return [FollowupAction('')]


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
        wellbeing_ref = db.collection(WELLBEING_COLLECTION).document(tracker.sender_id)
        wellbeing_ref.set({'area_of_life': area_of_life}, merge=True)
        wellbeing_ref.set({'coping_strategy': coping_strategy}, merge=True)
        if unhealthy_thoughts != 'None':
            dispatcher.utter_message(
                text="Everyone has thoughts such as '{}' from time to time..".format(unhealthy_thoughts))
            dispatcher.utter_message(
                text='Share your feelings with someone close to you if you can and socialize more often.')
            dispatcher.utter_message('It will help you to navigate away from having these thoughts.')
            wellbeing_ref.set({'unhealthy_thoughts': unhealthy_thoughts}, merge=True)
        dispatcher.utter_message(text="area of life: {}".format(area_of_life))
        dispatcher.utter_message(
            text="coping strategy: {}".format(coping_strategy))
        dispatcher.utter_message(
            text="unhealthy thoughts: {}".format(unhealthy_thoughts))

        return [AllSlotsReset()]


class ActionClarifyToUser(Action):
    def name(self) -> Text:
        return "action_clarify_to_user"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        emotion = tracker.get_slot("emotions")
        if emotion is not None:
            dispatcher.utter_message(
                text="Just confirming what you have said, am I correct that you are feeling '{}'?".format(emotion))
        else:
            dispatcher.utter_message(template="utter_sorry_to_hear")
            dispatcher.utter_message(
                text="Would you like to talk to me about the issue you are having?")
        dispatcher.utter_message(buttons=[
            {"payload": "/affirm", "title": "Yes"},
            {"payload": "/deny", "title": "No"},
        ])
        return []


class ActionAskWhyFeelingNegative(Action):
    def name(self) -> Text:
        return "action_why_feeling_negative"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        emotion = tracker.get_slot("emotions")
        if emotion is not None:
            wellbeing_ref = db.collection(WELLBEING_COLLECTION).document(tracker.sender_id)
            user_ref = db.collection(USERS_COLLECTION).document(tracker.sender_id)
            user_ref.set({'emotion': emotion.capitalize()}, merge=True)
            wellbeing_ref.update({'emotion': firestore.ArrayUnion([{str(datetime.datetime.now()): emotion.capitalize()}])})
            dispatcher.utter_message(
                text="If you would like to share with me, what would be the reason that you are feeling '{}'?".format(
                    emotion))
        else:
            dispatcher.utter_message(
                text="If you would like to share with me, what would be the reason that you are feeling this way?")

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


class ActionResponseToFeelingNegative(Action):

    def name(self) -> Text:
        return "action_response_to_feeling_negative"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        emotion = tracker.get_slot("emotions")
        dispatcher.utter_message(template="utter_sorry_to_hear")
        dispatcher.utter_message(template="utter_cheer_up")
        if emotion is not None:
            if emotion in SAD:
                dispatcher.utter_message(template="utter_quote_about_sadness")
            elif emotion in ANGRY:
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
        if emotion in HAPPY:
            return [SlotSet('emotions', emotion)]
        else:
            return [SlotSet('emotions', emotion), FollowupAction('action_why_feeling_negative')]


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
        #
        #     dispatcher.utter_message(template="utter_restart_with_button")
        #
        #     return [SlotSet("feedback_value", "negative"), ConversationPaused()]

        # Fallback caused by Core
        # else:
        dispatcher.utter_message(template="utter_default")
        return [UserUtteranceReverted()]
