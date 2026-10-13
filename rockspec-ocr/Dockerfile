FROM python:3.10-slim

WORKDIR /app

# ติดตั้งเฉพาะ dependency ของเว็บแอป (ไม่รวม torch/easyocr/opencv ที่ใช้แค่ใน batch pipeline)
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

# คัดลอกเฉพาะไฟล์ที่เว็บแอปต้องใช้จริง (.dockerignore กรองไฟล์ไม่จำเป็นออกแล้ว)
COPY app.py .
COPY src ./src
COPY templates ./templates
COPY static ./static

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
