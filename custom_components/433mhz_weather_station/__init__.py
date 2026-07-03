"""The 433MHz Weather Station integration."""
from __future__ import annotations

import logging

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback

from .const import CONF_MQTT_TOPIC, CONF_PROTOCOL, DEFAULT_PROTOCOL, DOMAIN, EVENT_RF_DATA_RECEIVED
from .decoder import RFDecoder

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up 433MHz Weather Station from a config entry."""
    topic: str = entry.data[CONF_MQTT_TOPIC]
    protocol: str = entry.data.get(CONF_PROTOCOL, DEFAULT_PROTOCOL)
    decoder = RFDecoder(protocol=protocol)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "decoder": decoder,
        "latest": None,
    }

    @callback
    def _on_message(msg: mqtt.ReceiveMessage) -> None:
        raw_payload: str = msg.payload
        _LOGGER.debug("Received RF payload on %s: %s…", topic, raw_payload[:60])

        result = decoder.decode(raw_payload)
        if result is None:
            _LOGGER.debug("Could not decode RF payload")
            return

        _LOGGER.debug("Decoded: %s", result.as_dict())
        hass.data[DOMAIN][entry.entry_id]["latest"] = result

        hass.bus.fire(
            EVENT_RF_DATA_RECEIVED,
            {
                "entry_id": entry.entry_id,
                "topic": msg.topic,
                **result.as_dict(),
            },
        )

    entry.async_on_unload(
        await mqtt.async_subscribe(hass, topic, _on_message, qos=0)
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
