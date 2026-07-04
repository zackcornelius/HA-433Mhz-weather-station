"""The 433MHz Weather Station integration."""
from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.config_entries import SOURCE_INTEGRATION_DISCOVERY, ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_AVAILABLE_FIELDS,
    CONF_ENTRY_TYPE,
    CONF_ESPHOME_DEVICE_ID,
    CONF_MODEL,
    CONF_PROTOCOL_DESC,
    CONF_SENSOR_ID,
    DOMAIN,
    ENTRY_TYPE_HUB,
    ENTRY_TYPE_SENSOR,
    EVENT_RF_DATA_RECEIVED,
    HA_EVENT_TYPE,
    KNOWN_SENSORS_KEY,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the global ESPHome RF-message listener and discovery handler."""
    hass.data.setdefault(DOMAIN, {KNOWN_SENSORS_KEY: set()})

    @callback
    def _handle_rf_event(event: Event) -> None:
        raw_message: str = event.data.get("message", "")
        esphome_device_id: str = event.data.get("device_id", "")
        if not raw_message:
            return

        try:
            msg: dict[str, Any] = json.loads(raw_message)
        except (json.JSONDecodeError, TypeError):
            _LOGGER.debug("Could not parse RF message: %.100s", raw_message)
            return

        model: str = msg.get("model", "")
        sensor_id = msg.get("id")
        if not model or sensor_id is None:
            _LOGGER.debug("RF message missing model/id: %s", msg)
            return

        # Route data to an existing sensor config entry if one matches.
        for entry in hass.config_entries.async_entries(DOMAIN):
            if (
                entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_SENSOR
                and entry.data.get(CONF_MODEL) == model
                and entry.data.get(CONF_SENSOR_ID) == sensor_id
            ):
                hass.bus.async_fire(
                    EVENT_RF_DATA_RECEIVED,
                    {"entry_id": entry.entry_id, **msg},
                )
                return

        # Unknown sensor – fire a discovery flow if not already pending.
        sensor_key = (model, sensor_id)
        known: set = hass.data[DOMAIN][KNOWN_SENSORS_KEY]
        if sensor_key not in known:
            known.add(sensor_key)
            _LOGGER.debug(
                "Discovered new RF sensor: model=%s id=%s (ESPHome device %s)",
                model,
                sensor_id,
                esphome_device_id,
            )
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": SOURCE_INTEGRATION_DISCOVERY},
                    data={
                        CONF_MODEL: model,
                        CONF_SENSOR_ID: sensor_id,
                        CONF_ESPHOME_DEVICE_ID: esphome_device_id,
                        CONF_PROTOCOL_DESC: msg.get("protocol", ""),
                        CONF_AVAILABLE_FIELDS: list(msg.keys()),
                    },
                )
            )

    hass.bus.async_listen(HA_EVENT_TYPE, _handle_rf_event)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry (hub or sensor)."""
    hass.data.setdefault(DOMAIN, {KNOWN_SENSORS_KEY: set()})

    entry_type = entry.data.get(CONF_ENTRY_TYPE, ENTRY_TYPE_HUB)

    if entry_type == ENTRY_TYPE_SENSOR:
        # Mark as known so the listener never re-fires discovery for this sensor.
        sensor_key = (entry.data[CONF_MODEL], entry.data[CONF_SENSOR_ID])
        hass.data[DOMAIN][KNOWN_SENSORS_KEY].add(sensor_key)

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Hub entries have no platforms – they exist only to keep the domain loaded.
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if entry.data.get(CONF_ENTRY_TYPE, ENTRY_TYPE_HUB) == ENTRY_TYPE_SENSOR:
        return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return True
