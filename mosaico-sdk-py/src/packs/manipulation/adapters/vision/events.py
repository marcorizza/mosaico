from mosaicolabs import Message

from packs.manipulation.adapters.base import BaseAdapter
from packs.manipulation.ontology.event_camera import EventCamera, Event


class EventsAdapter(BaseAdapter):
    adapter_id = "reassemble.events"
    ontology_type = EventCamera

    @classmethod
    def translate(cls, payload: dict) -> Message:
        t_start_ns = int(payload["t_start_ns"])
        return Message(
            timestamp_ns=int(payload["timestamp_ns"]),
            data=EventCamera(
                width=346,
                height=260,
                events=[
                    Event(
                        x=int(event[0]),
                        y=int(event[1]),
                        polarity=int(event[2]),
                        dt_ns=int(event_timestamp_ns) - t_start_ns,
                    )
                    for event, event_timestamp_ns in zip(
                        payload["events"],
                        payload["event_timestamps_ns"],
                    )
                ],
                t_start_ns=t_start_ns,
                t_end_ns=int(payload["t_end_ns"]),
            ),
        )
