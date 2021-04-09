import typing
from typing import Any, Optional, Text, Dict, List, Type
import numpy as np
import scipy
from rich import print
from rich.markdown import Markdown
from rasa.nlu.components import Component
from rasa.nlu.config import RasaNLUModelConfig
from rasa.shared.nlu.training_data.training_data import TrainingData
from rasa.shared.nlu.training_data.message import Message
from rasa.nlu.tokenizers.tokenizer import Token
from rasa.shared.nlu.constants import TEXT

if typing.TYPE_CHECKING:
    from rasa.nlu.model import Metadata


def dense_message(dense_array: np.ndarray) -> Dict[Text, Any]:
    return {"shape": dense_array.shape, "dtype": dense_array.dtype}


def sparse_message(sparse_array: scipy.sparse.spmatrix) -> Dict[Text, Any]:
    return {
        "shape": sparse_array.shape,
        "dtype": sparse_array.dtype,
        "stored_elements": sparse_array.nnz,
    }


def print_message(message: Message) -> None:
    features = {**message.as_dict_nlu()}
    seq_vecs, sen_vecs = message.get_dense_features(TEXT)
    features["dense"] = {
        "sequence": None if not seq_vecs else dense_message(seq_vecs.features),
        "sentence": None if not sen_vecs else dense_message(sen_vecs.features),
    }
    seq_vecs, sen_vecs = message.get_sparse_features(TEXT)
    features["sparse"] = {
        "sequence": None if not seq_vecs else sparse_message(seq_vecs.features),
        "sentence": None if not sen_vecs else sparse_message(sen_vecs.features),
    }
    if "text_tokens" in features.keys():
        features["text_tokens"] = [t.text for t in features["text_tokens"]]
    if "intent" in features.keys():
        if features['intent'] == 'str':
            features["intent"] = {k: v for k,
                                  v in features["intent"] if "id" != k}
        else:
            features["intent"] = {k: v for k,
                                  v in features["intent"].items() if "id" != k}
    if "intent_ranking" in features.keys():
        features["intent_ranking"] = [
            {k: v for k, v in i.items() if "id" != k}
            for i in features["intent_ranking"]
        ]

    if "diagnostic_data" in features.keys():
        features["diagnostic_data"] = {
            name: {k: dense_message(v) for k, v in comp.items()}
            for name, comp in features["diagnostic_data"].items()
        }
    print(features)


def _is_list_tokens(v: Any) -> bool:
    if isinstance(v, List):
        if len(v) > 0:
            if isinstance(v[0], Token):
                return True
    return False


class Printer(Component):
    """
    A component that prints the message. Useful for debugging while running `rasa shell`.
    """

    @classmethod
    def required_components(cls) -> List[Type[Component]]:
        return []

    defaults = {"alias": None}
    language_list = None

    def __init__(self, component_config: Optional[Dict[Text, Any]] = None) -> None:
        super().__init__(component_config)

    def train(
        self,
        training_data: TrainingData,
        config: Optional[RasaNLUModelConfig] = None,
        **kwargs: Any,
    ) -> None:
        pass

    def process(self, message: Message, **kwargs: Any) -> None:
        if self.component_config["alias"]:
            print(Markdown(f'# {self.component_config["alias"]}'))
        for k, v in message.data.items():
            if _is_list_tokens(v):
                print(f"{k}: {[t.text for t in v]}")
            else:
                print(f"{k}: {v.__repr__()}")

    def persist(self, file_name: Text, model_dir: Text) -> Optional[Dict[Text, Any]]:
        pass

    @classmethod
    def load(
        cls,
        meta: Dict[Text, Any],
        model_dir: Optional[Text] = None,
        model_metadata: Optional["Metadata"] = None,
        cached_component: Optional["Component"] = None,
        **kwargs: Any,
    ) -> "Component":
        """Load this component from file."""

        if cached_component:
            return cached_component

        return cls(meta)
