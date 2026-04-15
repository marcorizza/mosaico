from mosaicolabs import CompressedImage, ImageFormat, Message
from PIL import Image as PILImage

from mosaicopacks.manipulation.adapters.base import BaseAdapter


class FractalRT1VideoFrameAdapter(BaseAdapter):
    adapter_id = "fractal_rt1.video_frame"
    ontology_type = CompressedImage

    @classmethod
    def translate(cls, payload: dict) -> Message:
        return Message(
            timestamp_ns=int(payload["timestamp_ns"]),
            data=CompressedImage.from_image(
                PILImage.fromarray(payload["image"]),
                format=ImageFormat.JPEG,
                quality=90,
            ),
        )
