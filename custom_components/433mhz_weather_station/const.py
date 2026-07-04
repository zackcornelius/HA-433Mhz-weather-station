"""Constants for the 433MHz Weather Station integration."""

DOMAIN = "433mhz_weather_station"

# HA event fired by ESPHome when an RTL_433 decoder produces a decoded message
HA_EVENT_TYPE = "esphome.rf_message_received"

# Internal event used to distribute decoded data to sensor entities
EVENT_RF_DATA_RECEIVED = f"{DOMAIN}_rf_data_received"

# Config-entry data keys
CONF_MODEL = "model"
CONF_SENSOR_ID = "sensor_id"
CONF_ESPHOME_DEVICE_ID = "esphome_device_id"
CONF_PROTOCOL_DESC = "protocol_desc"
CONF_AVAILABLE_FIELDS = "available_fields"

# Distinguishes the one-time listener/hub entry from per-sensor entries
ENTRY_TYPE_HUB = "hub"
ENTRY_TYPE_SENSOR = "sensor"
CONF_ENTRY_TYPE = "entry_type"

# Key under hass.data[DOMAIN] that tracks already-seen (model, id) pairs
KNOWN_SENSORS_KEY = "known_sensors"

# ---------------------------------------------------------------------------
# RTL_433 field → sensor descriptor parameters
#
# Each value is a dict that mirrors the keyword args of SensorEntityDescription
# plus two extras used only by sensor.py:
#   "value_fn"  – optional callable(raw_value) → displayed value
#   "skip_meta" – if True, this field is NOT turned into a sensor entity
# ---------------------------------------------------------------------------
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass  # noqa: E402
from homeassistant.const import (  # noqa: E402
    DEGREE,
    PERCENTAGE,
    UnitOfIrradiance,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)

RTL433_FIELD_MAP: dict[str, dict] = {
    # Temperature
    "temperature_C": {
        "name": "Temperature",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
        "suggested_display_precision": 1,
    },
    "temperature_F": {
        "name": "Temperature",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfTemperature.FAHRENHEIT,
        "suggested_display_precision": 1,
    },
    # Humidity
    "humidity": {
        "name": "Humidity",
        "device_class": SensorDeviceClass.HUMIDITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": PERCENTAGE,
    },
    # Battery
    "battery_ok": {
        "name": "Battery",
        "icon": "mdi:battery",
        "value_fn": lambda v: "OK" if int(v) else "Low",
    },
    # Precipitation
    "rain_mm": {
        "name": "Rain Total",
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "native_unit_of_measurement": UnitOfLength.MILLIMETERS,
        "suggested_display_precision": 1,
    },
    "rain_rate_mm_h": {
        "name": "Rain Rate",
        "device_class": SensorDeviceClass.PRECIPITATION_INTENSITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": "mm/h",
        "suggested_display_precision": 1,
    },
    # Wind
    "wind_avg_m_s": {
        "name": "Wind Speed",
        "device_class": SensorDeviceClass.WIND_SPEED,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfSpeed.METERS_PER_SECOND,
        "suggested_display_precision": 1,
    },
    "wind_max_m_s": {
        "name": "Wind Gust",
        "device_class": SensorDeviceClass.WIND_SPEED,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfSpeed.METERS_PER_SECOND,
        "suggested_display_precision": 1,
    },
    "wind_dir_deg": {
        "name": "Wind Direction",
        "icon": "mdi:compass",
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": DEGREE,
    },
    # Atmospheric pressure
    "pressure_hPa": {
        "name": "Pressure",
        "device_class": SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfPressure.HPA,
        "suggested_display_precision": 1,
    },
    # UV / light
    "uv": {
        "name": "UV Index",
        "icon": "mdi:sun-wireless",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "lux": {
        "name": "Illuminance",
        "device_class": SensorDeviceClass.ILLUMINANCE,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": "lx",
    },
    "light_lux": {
        "name": "Illuminance",
        "device_class": SensorDeviceClass.ILLUMINANCE,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": "lx",
    },
    # Fields that are metadata, not sensor values
    "model":    {"skip_meta": True},
    "id":       {"skip_meta": True},
    "mic":      {"skip_meta": True},
    "protocol": {"skip_meta": True},
    "status":   {"skip_meta": True},
    "type":     {"skip_meta": True},
    "subtype":  {"skip_meta": True},
    "channel":  {"skip_meta": True},
    "message_type": {"skip_meta": True},
}
