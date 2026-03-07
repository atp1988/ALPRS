# worker/receive.py
import os
import time
import pika
import json
import requests
from rabbitmq_settings import RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASS, QUEUE_NAME

# آدرس سرویس plate (به صورت پیش‌فرض به سرویس plate که روی پورت 660 اجرا می‌شود)
PLATE_SERVICE_URL = os.getenv("PLATE_SERVICE_URL", "http://plate:660/plate")

def connect_rabbitmq():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials
    )
    while True:
        try:
            connection = pika.BlockingConnection(parameters)
            return connection
        except Exception as e:
            print("Connection to RabbitMQ failed, retrying in 5 seconds...", e)
            time.sleep(5)

def callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        image = data.get("image")
        if image:
            payload = {"image": image}
            response = requests.post(PLATE_SERVICE_URL, json=payload)
            print(" [x] Sent image to plate service, response:", response.text)
        else:
            print(" [!] No image found in message")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(" [!] Error processing message:", e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def main():
    connection = connect_rabbitmq()
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    print(" [*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    main()
