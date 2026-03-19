from mosaicolabs import Message, Image
from packs.manipulation.adapters.base import BaseAdapter
from packs.manipulation.utils.extract_reassemble_event_image import extract_reassemble_event_image


class EventsAdapter(BaseAdapter):
    adapter_id = "reassemble.events"
    ontology_type = Image

    @classmethod
    def translate(cls, payload: dict) -> Message:
        return Message(
            timestamp_ns=int(payload["timestamp"] * 1e9),
            data=extract_reassemble_event_image(
                payload["event"],
            )
        )
