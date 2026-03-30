import base64
import uuid
import os

UPLOAD_DIR = "static/prescriptions"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_image_to_disk(image_data: str) -> tuple[str, str]:
    """
    Takes base64 image string from canvas.toDataURL().
    Saves it as a PNG file to static/prescriptions/.
    Returns (filepath, prescription_id).
    """
    # canvas.toDataURL() adds a header like "data:image/png;base64,..."
    # we strip that header before decoding
    if "," in image_data:
        image_data = image_data.split(",")[1]

    image_bytes = base64.b64decode(image_data)

    prescription_id = str(uuid.uuid4())
    filepath = os.path.join(UPLOAD_DIR, f"{prescription_id}.png")

    with open(filepath, "wb") as f:
        f.write(image_bytes)

    return filepath, prescription_id


def overwrite_image_on_disk(filepath: str, image_data: str) -> None:
    """
    Overwrites an existing prescription image file.
    Called when doctor redraws and saves again.
    """
    if "," in image_data:
        image_data = image_data.split(",")[1]

    image_bytes = base64.b64decode(image_data)

    with open(filepath, "wb") as f:
        f.write(image_bytes)