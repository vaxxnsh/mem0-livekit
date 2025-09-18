import base64
from livekit.agents.utils.images import encode, EncodeOptions, ResizeOptions

def frame_to_base64(frame, width=1024, height=1024):
    image_bytes = encode(
        frame,
        EncodeOptions(
            format="JPEG",
            resize_options=ResizeOptions(width=width, height=height, strategy="scale_aspect_fit"),
        ),
    )
    return f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode('utf-8')}"

def bytes_to_base64_image(image_bytes, format="png"):
    return f"data:image/{format};base64,{base64.b64encode(image_bytes).decode('utf-8')}"
