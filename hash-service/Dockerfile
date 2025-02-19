FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt && apt update && apt install curl -y
COPY hash_service.py .
CMD ["python", "hash_service.py"]