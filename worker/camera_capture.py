# worker/camera_capture.py
import cv2
import base64
import pika
import json
import os
import time
from rabbitmq_settings import RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASS, QUEUE_NAME

def connect_rabbitmq():
    """تلاش برای اتصال به RabbitMQ با retry هر ۵ ثانیه"""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
    )
    while True:
        try:
            connection = pika.BlockingConnection(parameters)
            print("Connected to RabbitMQ")
            return connection
        except Exception as e:
            print("Connection to RabbitMQ failed, retrying in 5 seconds...", e)
            time.sleep(5)

def capture_and_send():
    # دریافت آدرس دوربین از متغیر محیطی یا استفاده از مقدار پیش‌فرض
    camera_url = os.getenv("CAMERA_URL", "rtsp://admin:$adraPASS@192.168.50.150:554/")
    cap = cv2.VideoCapture(camera_url)
    
    if not cap.isOpened():
        print("Error: Could not open camera stream.")
        return

    # استفاده از تابع اتصال با مکانیزم retry
    connection = connect_rabbitmq()
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            time.sleep(1)
            continue

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            print("Error: Failed to encode frame.")
            continue

        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
        message = json.dumps({"image": jpg_as_text})
        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print(" [x] Sent frame to RabbitMQ")
        time.sleep(0.5)
    
    cap.release()
    connection.close()

if __name__ == '__main__':
    capture_and_send()
