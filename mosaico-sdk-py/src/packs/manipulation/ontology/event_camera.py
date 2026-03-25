from typing import List

import numpy as np
import pyarrow as pa
from PIL import Image as PILImage

from mosaicolabs import HeaderMixin, Serializable


class Event(Serializable):
    __ontology_tag__ = "event"

    __msco_pyarrow_struct__ = pa.struct(
        [
            pa.field(
                "x",
                pa.uint16(),
                nullable=False,
                metadata={"description": "Horizontal pixel coordinate of the event."},
            ),
            pa.field(
                "y",
                pa.uint16(),
                nullable=False,
                metadata={"description": "Vertical pixel coordinate of the event."},
            ),
            pa.field(
                "polarity",
                pa.uint8(),
                nullable=False,
                metadata={"description": "Polarity of the brightness change."},
            ),
            pa.field(
                "dt_ns",
                pa.int64(),
                nullable=False,
                metadata={
                    "description": "Time offset, in nanoseconds, from the start of the enclosing event window."
                },
            ),
        ],
    )

    x: int
    y: int
    polarity: int
    dt_ns: int


class EventCamera(Serializable, HeaderMixin):
    __ontology_tag__ = "event_camera"

    __msco_pyarrow_struct__ = pa.struct(
        [
            pa.field(
                "width",
                pa.uint32(),
                nullable=False,
                metadata={"description": "Sensor width in pixels."},
            ),
            pa.field(
                "height",
                pa.uint32(),
                nullable=False,
                metadata={"description": "Sensor height in pixels."},
            ),
            pa.field(
                "events",
                pa.list_(Event.__msco_pyarrow_struct__),
                nullable=False,
                metadata={"description": "Raw events collected in the event window."},
            ),
            pa.field(
                "t_start_ns",
                pa.int64(),
                nullable=False,
                metadata={"description": "Inclusive start timestamp of the event window."},
            ),
            pa.field(
                "t_end_ns",
                pa.int64(),
                nullable=False,
                metadata={"description": "Exclusive end timestamp of the event window."},
            ),
        ],
    )

    width: int
    height: int
    events: List[Event]
    t_start_ns: int
    t_end_ns: int

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
