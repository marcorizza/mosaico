from mosaicolabs import Message

from mosaicopacks.manipulation.adapters.base import BaseAdapter
from mosaicopacks.manipulation.ontology.text_embedding import TextEmbedding


class FractalRT1TextEmbeddingAdapter(BaseAdapter):
    adapter_id = "fractal_rt1.text_embedding"
    ontology_type = TextEmbedding

    @classmethod
    def translate(cls, payload: dict) -> Message:
        return Message(
            timestamp_ns=int(payload["timestamp_ns"]),
            data=TextEmbedding(values=payload["values"]),
        )
