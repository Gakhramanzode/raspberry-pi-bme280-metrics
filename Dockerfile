# Используем Python 3
FROM python:3.11-slim

# Устанавливаем необходимые пакеты
RUN apt-get update && \
    apt-get install -y i2c-tools python3-smbus2 && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код в контейнер
COPY . /app
WORKDIR /app

# Запускаем скрипт
CMD ["python", "bme280_metrics_pusher.py"]
