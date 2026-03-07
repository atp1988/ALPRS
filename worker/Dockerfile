# worker/Dockerfile
FROM python:3.9-slim

# نصب بسته‌های سیستم مورد نیاز، از جمله libgl1 و libglib2.0-0
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# کپی کردن فایل requirements و نصب وابستگی‌ها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کردن کدهای پروژه
COPY . .

# CMD ["python", "receive.py"]
CMD ["uvicorn", "camera_api:app", "--host", "0.0.0.0", "--port", "5000"]

