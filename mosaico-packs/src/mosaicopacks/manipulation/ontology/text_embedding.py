from mosaicolabs import MosaicoField, MosaicoType, Serializable


class TextEmbedding(Serializable):
    __ontology_tag__ = "text_embedding"

    values: MosaicoType.list_(MosaicoType.float32) = MosaicoField(
        description="Values of the text embedding."
    )
