import base64
import uuid
import os

UPLOAD_DIR = "static/prescriptions"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_image_to_disk(image_data: str):
    if "," in image_data:
        image_data = image_data.split(",")[1]
    image_bytes = base64.b64decode(image_data)
    prescription_id = str(uuid.uuid4())
    filepath = os.path.join(UPLOAD_DIR, f"{prescription_id}.png")
    with open(filepath, "wb") as f:
        f.write(image_bytes)
    return filepath, prescription_id


def overwrite_image_on_disk(filepath: str, image_data: str):
    if "," in image_data:
        image_data = image_data.split(",")[1]
    with open(filepath, "wb") as f:
        f.write(base64.b64decode(image_data))
