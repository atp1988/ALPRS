from typing import Union
import numpy as np
from fastapi import Request
from settings import app, APP_ROOT, inference
import logging

# Configure the logger
logger = logging.getLogger("plate")
logger.setLevel(logging.DEBUG)
# You can configure a StreamHandler (or FileHandler if needed)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

def b64_to_img(image_byte: Union[bytes, str]) -> np.ndarray:
    """
    Converts the input bytes or string to an 3-channel image
    :param image_byte: base64 image string
    :return: numpy image
    """
    import base64
    import cv2
    if isinstance(image_byte, bytes):
        image_byte = image_byte.decode()
    if ";" in image_byte:
        image_byte = image_byte.split(";")[-1]

    image_byte = image_byte.encode()
    im_bytes = base64.b64decode(image_byte)
    im_arr = np.frombuffer(im_bytes, dtype=np.uint8)  # im_arr is one-dim Numpy array
    img = cv2.imdecode(im_arr, flags=cv2.IMREAD_COLOR)

    return img


# @app.post(APP_ROOT)
# async def plate_recognition(request: Request):
#     r = await request.json()
#     if next(iter(r)) == 'image':
#         image = r['image']
#         img = b64_to_img(image)  # You would need to implement or import this function
#         res = inference.infer(img, width=1920, height=1080)  # Assuming appropriate inference method
#         return res
#     elif next(iter(r)) == 'error':
#         error = r['error']
#         return {"status": "error received", "error": error}

@app.post(APP_ROOT)
async def plate_recognition(request: Request):
    r = await request.json()
    if 'image' in r:
        image = r['image']
        img = b64_to_img(image)  # You would need to implement or import this function
        try:
            res = inference.infer(img, width=1920, height=1080)
            logger.info("Inference result: %s", res)
            return res
        except Exception as e:
            logger.exception("Inference failed: %s", e)
            return {"error": "Inference failed."}
    elif 'error' in r:
        res = r['error']
        logger.info("error received: %s", res)
        return {"error": "Invalid payload, Expected 'error'."}

@app.get(APP_ROOT)
def get_plate():
    return {"Just": "Fine!"}
