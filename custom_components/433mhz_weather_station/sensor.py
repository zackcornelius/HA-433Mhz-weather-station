"""Sensor platform for the 433MHz Weather Station integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_AVAILABLE_FIELDS,
    CONF_ENTRY_TYPE,
    CONF_ESPHOME_DEVICE_ID,
    CONF_MODEL,
    CONF_PROTOCOL_DESC,
    CONF_SENSOR_ID,
    DOMAIN,
    ENTRY_TYPE_SENSOR,
    EVENT_RF_DATA_RECEIVED,
    RTL433_FIELD_MAP,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities for a discovered RF sensor config entry."""
    if entry.data.get(CONF_ENTRY_TYPE) != ENTRY_TYPE_SENSOR:
        return

    model: str = entry.data[CONF_MODEL]
    sensor_id = entry.data[CONF_SENSOR_ID]
    available_fields: list[str] = entry.data.get(CONF_AVAILABLE_FIELDS, [])

    entities: list[RTL433SensorEntity] = []
    for field in available_fields:
        field_def = RTL433_FIELD_MAP.get(field)
        if field_def is None:
            # Unknown field – create a generic sensor for it.
            field_def = {"name": field.replace("_", " ").title()}
        elif field_def.get("skip_meta"):
            continue

        description = SensorEntityDescription(
            key=field,
            name=field_def.get("name", field),
            device_class=field_def.get("device_class"),
            state_class=field_def.get("state_class"),
            native_unit_of_measurement=field_def.get("native_unit_of_measurement"),
            suggested_display_precision=field_def.get("suggested_display_precision"),
            icon=field_def.get("icon"),
        )
        entities.append(
            RTL433SensorEntity(
                entry=entry,
                description=description,
                model=model,
                sensor_id=sensor_id,
                value_fn=field_def.get("value_fn"),
            )
        )

    if entities:
        async_add_entities(entities)


class RTL433SensorEntity(SensorEntity):
    """A sensor entity representing one field from an RTL_433 decoded message."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        entry: ConfigEntry,
        description: SensorEntityDescription,
        model: str,
        sensor_id: Any,
        value_fn: Any | None,
    ) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self._entry = entry
        self._model = model
        self._sensor_id = sensor_id
        self._value_fn = value_fn
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_native_value: Any = None

        protocol_desc: str = entry.data.get(CONF_PROTOCOL_DESC, "")
        esphome_device_id: str = entry.data.get(CONF_ESPHOME_DEVICE_ID, "")

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=_manufacturer_from_protocol(protocol_desc),
            model=model,
            serial_number=str(sensor_id),
            via_device=(DOMAIN, esphome_device_id) if esphome_device_id else None,
        )

    async def async_added_to_hass(self) -> None:
        """Register event listener once the entity is in the HA entity registry."""
        self.async_on_remove(
            self.hass.bus.async_listen(EVENT_RF_DATA_RECEIVED, self._handle_event)
        )

    @callback
    def _handle_event(self, event: Any) -> None:
        """Handle an incoming decoded RF data event for this entry."""
        if event.data.get("entry_id") != self._entry.entry_id:
            return

        raw = event.data.get(self.entity_description.key)
        if raw is None:
            return

        if self._value_fn is not None:
            try:
                self._attr_native_value = self._value_fn(raw)
            except Exception:  # noqa: BLE001
                self._attr_native_value = raw
        else:
            self._attr_native_value = raw

        self.async_write_ha_state()


def _manufacturer_from_protocol(protocol_desc: str) -> str:
    """Extract a short manufacturer name from an RTL_433 protocol string."""
    if not protocol_desc:
        return "Generic"
    # The protocol string is often "{brand} {model}, {full description}".
    # Return the first comma-separated segment, limited to 40 characters.
    short = protocol_desc.split(",")[0].strip()
    return short[:40] if short else "Generic"
