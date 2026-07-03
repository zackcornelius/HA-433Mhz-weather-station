"""Constants for the 433MHz Weather Station integration."""

DOMAIN = "433mhz_weather_station"

CONF_MQTT_TOPIC = "mqtt_topic"
CONF_PROTOCOL = "protocol"

DEFAULT_MQTT_TOPIC = "esphome/weather_station/raw"
DEFAULT_PROTOCOL = "auto"

PROTOCOL_AUTO = "auto"
PROTOCOL_FINEOFFSET = "fineoffset"
PROTOCOL_NEXUS = "nexus"
PROTOCOL_PWM_GENERIC = "pwm_generic"
PROTOCOL_PDM_GENERIC = "pdm_generic"

PROTOCOLS = {
    PROTOCOL_AUTO: "Auto-detect",
    PROTOCOL_FINEOFFSET: "Fine Offset / WH65B-compatible",
    PROTOCOL_NEXUS: "Nexus / Rubicson / Prologue",
    PROTOCOL_PWM_GENERIC: "Generic PWM (pulse-width)",
    PROTOCOL_PDM_GENERIC: "Generic PDM (pulse-distance)",
}

SENSOR_TEMPERATURE = "temperature"
SENSOR_HUMIDITY = "humidity"
SENSOR_BATTERY = "battery"
SENSOR_CHANNEL = "channel"
SENSOR_DEVICE_ID = "device_id"
SENSOR_RAIN_TOTAL = "rain_total"
SENSOR_WIND_SPEED = "wind_speed"
SENSOR_WIND_DIRECTION = "wind_direction"
SENSOR_RAW_DATA = "raw_data"

PULSE_THRESHOLD_US = 700

EVENT_RF_DATA_RECEIVED = f"{DOMAIN}_rf_data_received"
