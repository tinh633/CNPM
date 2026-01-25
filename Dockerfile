FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3-tk \
    tk \
    libx11-6 \
    x11-apps \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir ttkbootstrap

COPY . .

CMD ["python", "main.py"]