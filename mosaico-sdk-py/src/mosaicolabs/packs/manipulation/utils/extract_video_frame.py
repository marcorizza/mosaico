import io

import av


def _resolve_timestamp(frame_idx, frame, timestamps):
    if frame_idx < len(timestamps):
        return timestamps[frame_idx]
    if frame.time is not None:
        return float(frame.time)
    return 0.0


def _encode_jpeg(frame):
    image = frame.to_image()
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()


def extract_video_frames(h5_handle, video_dataset_path, timestamps):
    video_bytes = bytes(h5_handle[video_dataset_path][()])
    timestamps = list(timestamps)

    with av.open(io.BytesIO(video_bytes), mode="r") as container:
        stream = container.streams.video[0]

        for frame_idx, frame in enumerate(container.decode(stream)):
            yield {
                "timestamp": _resolve_timestamp(frame_idx, frame, timestamps),
                "image": _encode_jpeg(frame),
            }
