import numpy as np
from mosaicolabs import MosaicoField, MosaicoType, Serializable
from PIL import Image as PILImage


class Event(Serializable):
    __ontology_tag__ = "event"

    x: MosaicoType.uint16 = MosaicoField(
        description="Horizontal pixel coordinate of the event."
    )
    y: MosaicoType.uint16 = MosaicoField(
        description="Vertical pixel coordinate of the event."
    )
    polarity: MosaicoType.uint8 = MosaicoField(
        description="Polarity of the brightness change."
    )
    dt_ns: MosaicoType.int64 = MosaicoField(
        description="Time offset, in nanoseconds, from the start of the enclosing event window."
    )


class EventCamera(Serializable):
    __ontology_tag__ = "event_camera"

    width: MosaicoType.uint32 = MosaicoField(description="Sensor width in pixels.")
    height: MosaicoType.uint32 = MosaicoField(description="Sensor height in pixels.")
    events: MosaicoType.list_(Event) = MosaicoField(
        description="Raw events collected in the event window."
    )
    t_start_ns: MosaicoType.int64 = MosaicoField(
        description="Inclusive start timestamp of the event window."
    )
    t_end_ns: MosaicoType.int64 = MosaicoField(
        description="Exclusive end timestamp of the event window."
    )

    def to_pillow(self) -> PILImage.Image:
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        if not self.events:
            return PILImage.fromarray(frame, mode="RGB")

        # Extract coordinates and polarities into NumPy arrays
        xs = np.array([int(e.x) for e in self.events], dtype=np.int32)
        ys = np.array([int(e.y) for e in self.events], dtype=np.int32)
        pols = np.array([int(e.polarity) for e in self.events], dtype=np.uint8)

        # Vectorized validation
        if np.any((xs < 0) | (xs >= self.width) | (ys < 0) | (ys >= self.height)):
            raise ValueError("Invalid event coordinates")
        if np.any((pols != 0) & (pols != 1)):
            raise ValueError("Invalid polarity, expected 0 or 1")

        # Split by polarity and use np.maximum.at for max accumulation
        on_mask = pols == 1
        off_mask = ~on_mask

        # Polarity 1 → green (0, 255, 0)
        np.maximum.at(frame[:, :, 1], (ys[on_mask], xs[on_mask]), 255)

        # Polarity 0 → red (255, 0, 0)
        np.maximum.at(frame[:, :, 0], (ys[off_mask], xs[off_mask]), 255)

        return PILImage.fromarray(frame, mode="RGB")
