from mosaicolabs import MosaicoField, MosaicoType, Serializable


class TerminateEpisode(Serializable):
    __ontology_tag__ = "terminate_episode"

    terminate_episode: MosaicoType.list_(MosaicoType.int32, list_size=3) = MosaicoField(
        description=(
            "RT-1 terminate signal encoded as a 3-element int32 vector in the order "
            "[terminate, continue, undocumented]."
        )
    )
