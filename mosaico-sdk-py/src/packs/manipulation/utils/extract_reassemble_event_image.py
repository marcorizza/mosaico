from functools import lru_cache

from mosaicolabs import Image, ImageFormat

EVENT_CAMERA_WIDTH = 346
EVENT_CAMERA_HEIGHT = 260
EVENT_IMAGE_ENCODING = "mono8"

EVENT_IMAGE_STRIDE = EVENT_CAMERA_WIDTH
EVENT_IMAGE_SIZE = EVENT_CAMERA_WIDTH * EVENT_CAMERA_HEIGHT
EVENT_PIXEL_ON = 255


@lru_cache(maxsize=None)
def _event_frame_png(x: int | None, y: int | None) -> bytes:
    pixels = bytearray(EVENT_IMAGE_SIZE)

    if x is not None and y is not None:
        pixels[(y * EVENT_CAMERA_WIDTH) + x] = EVENT_PIXEL_ON

    return Image.from_linear_pixels(
        data=list(pixels),
        format=ImageFormat.PNG,
        width=EVENT_CAMERA_WIDTH,
        height=EVENT_CAMERA_HEIGHT,
        stride=EVENT_IMAGE_STRIDE,
        encoding=EVENT_IMAGE_ENCODING,
    ).data


def extract_reassemble_event_image(event) -> Image:
    if len(event) != 3:
        raise ValueError(f"Expected an event shaped as [x, y, polarity], got {event}")

    x, y, polarity = (int(value) for value in event)

    if not (0 <= x < EVENT_CAMERA_WIDTH and 0 <= y < EVENT_CAMERA_HEIGHT):
        raise ValueError(
            f"Invalid event coordinates ({x}, {y}) for a {EVENT_CAMERA_WIDTH}x{EVENT_CAMERA_HEIGHT} frame"
        )

    if polarity not in (0, 1):
        raise ValueError(f"Invalid event polarity {polarity}, expected 0 or 1")

    png_data = _event_frame_png(x, y) if polarity == 1 else _event_frame_png(None, None)

    return Image(
        data=png_data,
        format=ImageFormat.PNG,
        width=EVENT_CAMERA_WIDTH,
        height=EVENT_CAMERA_HEIGHT,
        stride=EVENT_IMAGE_STRIDE,
        encoding=EVENT_IMAGE_ENCODING,
    )
