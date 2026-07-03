"""Sensor platform for the 433MHz Weather Station integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, EVENT_RF_DATA_RECEIVED

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS: list[SensorEntityDescription] = [
    SensorEntityDescription(
        key="temperature_c",
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="humidity",
        name="Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    SensorEntityDescription(
        key="battery_ok",
        name="Battery",
        icon="mdi:battery",
    ),
    SensorEntityDescription(
        key="channel",
        name="Channel",
        icon="mdi:radiobox-marked",
    ),
    SensorEntityDescription(
        key="device_id",
        name="Device ID",
        icon="mdi:identifier",
    ),
    SensorEntityDescription(
        key="raw_bytes",
        name="Raw Data",
        icon="mdi:code-brackets",
        entity_registry_enabled_default=False,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities for this config entry."""
    entities = [
        WeatherStationSensor(hass, entry, desc)
        for desc in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class WeatherStationSensor(SensorEntity):
    """A sensor entity that reflects one field from the decoded RF data."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="433MHz Weather Station",
            manufacturer="Generic",
            model="433MHz RF Sensor",
        )
        self._attr_native_value: Any = None

    async def async_added_to_hass(self) -> None:
        """Register event listener when entity is added."""
        self.async_on_remove(
            self.hass.bus.async_listen(EVENT_RF_DATA_RECEIVED, self._handle_event)
        )
        # Restore last known value if available
        latest = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {}).get("latest")
        if latest is not None:
            self._update_from_data(latest.as_dict())

    @callback
    def _handle_event(self, event: Any) -> None:
        """Handle an incoming RF data event."""
        if event.data.get("entry_id") != self._entry.entry_id:
            return
        self._update_from_data(event.data)
        self.async_write_ha_state()

    def _update_from_data(self, data: dict[str, Any]) -> None:
        """Extract the relevant field from the decoded data."""
        key = self.entity_description.key
        value = data.get(key)
        if key == "battery_ok" and value is not None:
            self._attr_native_value = "OK" if value else "Low"
        elif key == "raw_bytes" and isinstance(value, list):
            self._attr_native_value = " ".join(value)
        else:
            self._attr_native_value = value
