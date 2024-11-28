# BME280 Metrics Pusher

Этот проект представляет собой Python-скрипт для Raspberry Pi, который считывает данные с датчика BME280 и отправляет метрики температуры, давления и влажности на Prometheus Pushgateway. Скрипт упакован в Docker-контейнер для удобства развертывания и работы.

## Схема
![image](https://github.com/user-attachments/assets/56bd5792-04dd-48db-b623-e2fee9c1a9b6)

## Описание

- **Считывание данных**: Температура, давление и влажность считываются с датчика BME280 по интерфейсу I2C.
- **Отправка метрик**: Метрики отправляются на Prometheus Pushgateway, откуда их можно собирать с помощью Prometheus и визуализировать в Grafana.
- **Мониторинг состояния датчика**: Скрипт также отправляет метрики состояния датчика, позволяющие отслеживать проблемы в работе.

## Требования

- **Raspberry Pi** с поддержкой I2C и установленным датчиком BME280.
- **Docker** и **Docker Compose** (опционально) для развертывания контейнера.
- **Prometheus Pushgateway**, доступный по сети для приема метрик.
- **Prometheus** и **Grafana** для сбора и визуализации метрик (опционально).

## Установка и настройка

### Настройка Raspberry Pi

1. **Включите интерфейс I2C** на Raspberry Pi:

```bash
sudo raspi-config
# Перейдите в "Interface Options" и включите I2C
```
2. **Проверьте** подключение датчика:

```bash
sudo i2cdetect -y 1
# Вы должны увидеть устройство по адресу 0x76 или 0x77
```
### Сборка Docker-образа

```bash
sudo docker build -t bme280-metrics-pusher:v0.0.1 .
```
### Запуск контейнера

```bash
sudo docker run -d --name bme280-metrics-pusher --device /dev/i2c-1 -e PUSHGATEWAY_URL=http://<IP>:<порт> --restart always bme280-metrics-pusher:v0.0.1
```
- Замените `<ip-адрес>:<порт>` на адрес вашего Prometheus Pushgateway.
- Флаг `--device /dev/i2c-1` позволяет контейнеру получить доступ к I2C интерфейсу Raspberry Pi.
- Флаг `--restart unless-stopped` обеспечивает автоматический перезапуск контейнера в случае сбоя.
## Метрики

Скрипт отправляет следующие метрики на Pushgateway:

- **Температура**: `meteo_temperature` (в градусах Цельсия)
- **Давление**: `meteo_pressure` (в hPa)
- **Влажность**: `meteo_humidity` (в процентах)
- **Ошибки инициализации датчика**: `bme280_sensor_init_errors`
- **Ошибки чтения данных с датчика**: `bme280_sensor_read_errors`
- **Ошибки отправки метрик**: `push_metrics_errors` (количество ошибок при отправке метрик на Pushgateway)
