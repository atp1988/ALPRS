# worker/camera_api.py
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
import cv2
import base64
import os
import pika
import json
import threading
import time
import tempfile
import platform
import requests


app = FastAPI()

# Default settings
DEFAULT_CAMERA_URL = os.getenv("CAMERA_URL", "rtsp://admin:$adraPASS@192.168.50.150:554/")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "camera_frames")
PLATE_SERVICE_URL = os.getenv("PLATE_SERVICE_URL", "http://plate:660/plate")

def connect_rabbitmq():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        return connection, channel
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to RabbitMQ: {str(e)}")

def send_to_rabbitmq(message_body: bytes):
    try:
        connection, channel = connect_rabbitmq()
        channel.basic_publish(
            exchange="",
            routing_key=RABBITMQ_QUEUE,
            body=message_body,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        connection.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message to RabbitMQ: {str(e)}")

def prepare_message(image_bytes: bytes) -> bytes:
    """
    تبدیل باینری تصویر به رشته Base64 داخل JSON
    (همانند camera_capture.py)
    """
    jpg_as_text = base64.b64encode(image_bytes).decode('utf-8')
    message = json.dumps({"image": jpg_as_text})
    return message.encode('utf-8')

def capture_frame_from_video_source(source: str) -> bytes:
    """
    دریافت یک فریم از منبع ویدیویی (چه از دوربین یا فایل)
    """
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise HTTPException(status_code=500, detail="Cannot open video stream.")
    
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise HTTPException(status_code=500, detail="Failed to capture frame.")
    
    # frame converting - bgr-to-rgb
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret:
        raise HTTPException(status_code=500, detail="Failed to encode frame.")
    return buffer.tobytes()

# ===============================
# state 1: Image Mode (Upload Image)
# ===============================
@app.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    """
    دریافت یک تصویر آپلود شده از لوکال و ارسال به RabbitMQ
    """
    try:
        contents = await file.read()
        # فرض بر این است که فایل ارسالی یک تصویر معتبر است.
        msg = prepare_message(contents)
        send_to_rabbitmq(msg)
        return {"message": "Image uploaded and sent to RabbitMQ successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===============================================================================================
# state 2: Offline Video Mode (Upload Video)
# ===============================================================================================
@app.post("/upload/video")
async def upload_video(file: UploadFile = File(...)):
    """
    دریافت یک فایل ویدیویی آپلود شده از لوکال، استخراج فریم‌ها و ارسال به RabbitMQ
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(await file.read())
            tmp_filename = tmp.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded video: {str(e)}")
    
    cap = cv2.VideoCapture(tmp_filename)
    if not cap.isOpened():
        os.unlink(tmp_filename)
        raise HTTPException(status_code=500, detail="Cannot open video file.")
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # frame converting - bgr-to-rgb
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        msg = prepare_message(buffer.tobytes())
        send_to_rabbitmq(msg)
        frame_count += 1
        time.sleep(0.1)  # control for framerate sending
    cap.release()
    os.unlink(tmp_filename)
    return {"message": f"Video processed and {frame_count} frames sent to RabbitMQ successfully."}

# ===============================================================================================
# state 3: Live Feed Mode (Input Camera URL)
# ===============================================================================================
# global variables for live stream control
live_capture_thread = None
live_capture_active = False

# Added for Alarm Handler - Begin
def ping_device(ip_address):
   
    if platform.system() == 'Linux':
        response = os.system(f"ping -c 1 {ip_address}")
    elif platform.system() == 'Windows':
        response = os.system(f"ping -n 1 {ip_address}")
    return response

def send_error_to_ai(message):
    requests.post(PLATE_SERVICE_URL, headers={"Content-Type": "application/json"}, data=json.dumps({"error": message}))
    # print(f"[⚠️] Alarm---: {message}")

def check_PING(rtsp_url):
    ip_address = rtsp_url.split("@")[-1].split(":")[0]
    response = ping_device(ip_address)
    if response == 256:
        send_error_to_ai(f"The IP address:{ip_address} has no PING")
        return
    if response != 0:
        send_error_to_ai(f"The IP address:{ip_address} has no PING")
        return
    else:
        return response
    
# Added for Alarm Handler - End  

def live_capture_worker(camera_url: str):
    global live_capture_active

    response = check_PING(camera_url)
    if response == 0:
        cap = cv2.VideoCapture(camera_url)
        if not cap.isOpened():
            # print("Live capture: Cannot open camera stream.")
            send_error_to_ai(f"Failed to connect to camera: Invalid credentials.")   # Added for Alarm Handler
            return
        while live_capture_active:
            check_PING(camera_url)
            ret, frame = cap.read()
            if not ret:
                # print("Live capture: Failed to capture frame.")
                send_error_to_ai("Failed to get frame from camera.")  # Added for Alarm Handler
                time.sleep(1)
                continue
            # تبدیل فریم از BGR به RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("Live capture: Failed to encode frame.")
                continue
            msg = prepare_message(buffer.tobytes())
            try:
                send_to_rabbitmq(msg)
                print("Live capture: Frame sent to RabbitMQ.")
            except Exception as e:
                print(f"Live capture: Failed to send frame: {str(e)}")
            time.sleep(0.5)  # franerate setting
        cap.release()
        print("Live capture stopped.")

@app.post("/live/start")
def start_live_feed(camera_url: str = Form(...)):
    """
    شروع استریم زنده: ورودی باید یک URL دوربین به صورت (مثلاً 
    rtsp://admin:$$adraPASS@192.168.50.150:554/) باشد.
    """
    global live_capture_active, live_capture_thread
    if live_capture_active:
        return {"message": "Live capture is already running."}
    live_capture_active = True
    live_capture_thread = threading.Thread(target=live_capture_worker, args=(camera_url,), daemon=True)
    live_capture_thread.start()
    return {"message": "Live capture started."}

@app.post("/live/stop")
def stop_live_feed():
    """
    توقف استریم زنده
    """
    global live_capture_active
    if not live_capture_active:
        return {"message": "Live capture is not running."}
    live_capture_active = False
    return {"message": "Live capture stopping. Please wait a few seconds."}
