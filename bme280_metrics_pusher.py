import logging
from smbus2 import SMBus
from bme280 import BME280
from prometheus_client import Gauge, Counter, CollectorRegistry, push_to_gateway
import subprocess
import sys
import time
import os

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Настраиваем реестр и метрики для Pushgateway
registry = CollectorRegistry()
TEMPERATURE_GAUGE = Gauge("meteo_temperature", "Current temperature in Celsius", registry=registry)
PRESSURE_GAUGE = Gauge("meteo_pressure", "Current atmospheric pressure in hPa", registry=registry)
HUMIDITY_GAUGE = Gauge("meteo_humidity", "Current humidity percentage", registry=registry)

# Добавляем метрики для отслеживания ошибок
SENSOR_INIT_ERRORS = Counter("bme280_sensor_init_errors", "Number of sensor initialization errors", registry=registry)
SENSOR_READ_ERRORS = Counter("bme280_sensor_read_errors", "Number of sensor read errors", registry=registry)
PUSH_METRICS_ERRORS = Counter("push_metrics_errors", "Number of errors when pushing metrics to Pushgateway", registry=registry)

# URL для Pushgateway, переданный в переменной окружения
PUSHGATEWAY_URL = os.getenv("PUSHGATEWAY_URL")

if not PUSHGATEWAY_URL:
    logging.error("URL Pushgateway не найден. Установите PUSHGATEWAY_URL в переменные окружения.")
    sys.exit(1)

# Функция для отправки метрик на Pushgateway
def push_metrics(job_name="meteo_server"):
    try:
        logging.debug("Подготовка к отправке метрик")
        push_to_gateway(PUSHGATEWAY_URL, job=job_name, registry=registry)
        logging.info("Метрики успешно отправлены на Pushgateway")
    except Exception as e:
        PUSH_METRICS_ERRORS.inc()  # Увеличиваем счетчик ошибок отправки метрик
        logging.error(f"Ошибка при отправке метрик на Pushgateway: {e}")
        sys.exit(1)

# Функция для проверки устройства по адресу 0x76
def check_device_address(address=0x76):
    try:
        logging.debug(f"Проверка устройства на адресе 0x{address:02x}")
        result = subprocess.run(["i2cdetect", "-y", "1"], capture_output=True, text=True)
        logging.debug(f"Результат i2cdetect: {result.stdout}")
        if f"{address:02x}" not in result.stdout:
            logging.error(f"Устройство по адресу 0x{address:02x} не найдено. Проверьте подключение.")
            return False
        logging.info(f"Устройство по адресу 0x{address:02x} найдено.")
        return True
    except Exception as e:
        logging.error(f"Ошибка при проверке устройства: {e}")
        return False

# Инициализация датчика
def initialize_sensor():
    try:
        bus = SMBus(1)
        bme280 = BME280(i2c_dev=bus)
        logging.info("Датчик BME280 успешно инициализирован.")
        return bme280
    except Exception as e:
        SENSOR_INIT_ERRORS.inc()  # Увеличиваем счетчик ошибок инициализации
        logging.error(f"Ошибка при инициализации датчика: {e}")
        return None

# Чтение данных с датчика и обновление метрик
def get_weather_data(bme280):
    try:
        logging.debug("Перед обновлением датчика")
        # Принудительная задержка для стабилизации показаний
        time.sleep(1)
        bme280.update_sensor()
        logging.debug("После первого обновления датчика")
        time.sleep(0.5)
        bme280.update_sensor()
        logging.debug("После второго обновления датчика")

        temperature = bme280.get_temperature()
        pressure = bme280.get_pressure()
        humidity = bme280.get_humidity()

        # Обновляем значения метрик перед отправкой на Pushgateway
        TEMPERATURE_GAUGE.set(temperature)
        PRESSURE_GAUGE.set(pressure)
        HUMIDITY_GAUGE.set(humidity)

        logging.info(f"Получены данные: Температура={temperature:.2f} °C, Давление={pressure:.2f} hPa, Влажность={humidity:.2f}%")
    except Exception as e:
        SENSOR_READ_ERRORS.inc()  # Увеличиваем счетчик ошибок чтения данных
        logging.error(f"Ошибка при чтении данных с датчика: {e}")
        sys.exit(1)

# Функция для периодической отправки метрик
def metric_push_loop(bme280, interval=60):
    while True:
        get_weather_data(bme280)  # Обновляем метрики
        push_metrics()  # Отправляем на Pushgateway
        time.sleep(interval)

# Основная программа
if __name__ == "__main__":
    # Шаг 1: Проверка устройства
    if not check_device_address():
        sys.exit(1)

    # Шаг 2: Инициализация датчика
    bme280 = initialize_sensor()
    if bme280 is None:
        logging.error("Не удалось инициализировать датчик. Программа будет завершена.")
        sys.exit(1)

    # Шаг 3: Запуск цикла отправки метрик
    logging.info("Начинаем отправку метрик на Pushgateway.")
    metric_push_loop(bme280)
