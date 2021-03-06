from rasa.nlu.components import Component
from rasa.nlu import utils
from rasa.nlu.model import Metadata
import time
import typing
from typing import Any, Optional, Text, Dict, List, Type

from tensorflow import keras
from tensorflow.keras.models import load_model
from rasa.nlu.config import RasaNLUModelConfig

from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.training_data.training_data import TrainingData
import platform
import pickle
import os

# myMacPath = "/Users/daniel/Projects/rasa/wellbeingchatbot/custom_component/"
# myWindowsPath = "C:\\Users\Daniel\\Projects\wellbeing-chatbot\\custom_component\\"
# path = ''
# if(platform.system() == "Darwin"):
#     path = myMacPath
# elif (platform.system() == "Windows"):
#     path = myWindowsPath

model = load_model(os.path.abspath(os.getcwd()) + "/custom_component/model.h5")
with open(os.path.abspath(os.getcwd()) + '/custom_component/tokenizer.pkl','rb') as f:
    tokenizer = pickle.load(f)

POSITIVE = "POSITIVE"
NEGATIVE = "NEGATIVE"
NEUTRAL = "NEUTRAL"
SENTIMENT_THRESHOLDS = (0.4, 0.7)
SEQUENCE_LENGTH = 300


class SentimentAnalyzer(Component):
    """A pre-trained sentiment component"""

    name = "sentiment"
    provides = ["entities"]
    requires = []
    defaults = {}
    language_list = ["en"]

    def __init__(self, component_config=None):
        super(SentimentAnalyzer, self).__init__(component_config)

    def train(
        self,
        training_data: TrainingData,
        config: Optional[RasaNLUModelConfig] = None,
        **kwargs: Any,
    ) -> None:
        """Train this component.

        This is the components chance to train itself provided
        with the training data. The component can rely on
        any context attribute to be present, that gets created
        by a call to :meth:`components.Component.pipeline_init`
        of ANY component and
        on any context attributes created by a call to
        :meth:`components.Component.train`
        of components previous to this one."""
        pass

    def convert_to_rasa(self, value, confidence):
        """Convert model output into the Rasa NLU compatible output format."""

        entity = {"value": value,
                  "confidence": confidence,
                  "entity": "sentiment",
                  "extractor": "sentiment_extractor"}

        return entity

    def decode_sentiment(self, score):
        label = NEUTRAL
        if score <= SENTIMENT_THRESHOLDS[0]:
            label = NEGATIVE
        elif score >= SENTIMENT_THRESHOLDS[1]:
            label = POSITIVE
        return label

    def predict(self, text):
        score = 0
        label = NEUTRAL

        # Predict
        pred = model.predict([text])[0]
        score = pred
        print("predict: ", score)
        # Decode sentiment
        label = self.decode_sentiment(score)

        return {"label": label, "score": float(score)}

    def process(self, message: Message, **kwargs: Any) -> None:
        """Process an incoming message.

        This is the components chance to process an incoming
        message. The component can rely on
        any context attribute to be present, that gets created
        by a call to :meth:`components.Component.pipeline_init`
        of ANY component and
        on any context attributes created by a call to
        :meth:`components.Component.process`
        of components previous to this one. """
        features = {**message.as_dict_nlu()}
        if "text_tokens" in features.keys():
            text = [t.text for t in features["text_tokens"]]
            print('text: ', text)
            processed_text = pad_sequences(
                tokenizer.texts_to_sequences(text), maxlen=SEQUENCE_LENGTH)
            sentiment = self.predict(text=processed_text)
            print("sentiment: ", sentiment)
            entity = self.convert_to_rasa(
                sentiment['label'], sentiment['score'])
            message.set("entities", [entity], add_to_output=True)

    def persist(self, file_name: Text, model_dir: Text) -> Optional[Dict[Text, Any]]:
        """Persist this component to disk for future loading."""

        pass

    @classmethod
    def load(
        cls,
        meta: Dict[Text, Any],
        model_dir: Text,
        model_metadata: Optional["Metadata"] = None,
        cached_component: Optional["Component"] = None,
        **kwargs: Any,
    ) -> "Component":
        """Load this component from file."""

        if cached_component:
            return cached_component
        else:
            return cls(meta)
