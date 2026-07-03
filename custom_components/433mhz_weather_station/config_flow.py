"""Config flow for the 433MHz Weather Station integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import mqtt
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_MQTT_TOPIC,
    CONF_PROTOCOL,
    DEFAULT_MQTT_TOPIC,
    DEFAULT_PROTOCOL,
    DOMAIN,
    PROTOCOLS,
)


class WeatherStationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for 433MHz Weather Station."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if not await mqtt.async_wait_for_mqtt_client(self.hass):
            return self.async_abort(reason="mqtt_not_available")

        if user_input is not None:
            topic = user_input[CONF_MQTT_TOPIC].strip()
            if not topic:
                errors[CONF_MQTT_TOPIC] = "invalid_topic"
            else:
                await self.async_set_unique_id(topic)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"433MHz Station ({topic})",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_MQTT_TOPIC, default=DEFAULT_MQTT_TOPIC): str,
                vol.Required(CONF_PROTOCOL, default=DEFAULT_PROTOCOL): vol.In(PROTOCOLS),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> OptionsFlowHandler:
        """Return the options flow handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for the 433MHz Weather Station integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialise the options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Handle options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_MQTT_TOPIC,
                    default=self.config_entry.data.get(CONF_MQTT_TOPIC, DEFAULT_MQTT_TOPIC),
                ): str,
                vol.Required(
                    CONF_PROTOCOL,
                    default=self.config_entry.data.get(CONF_PROTOCOL, DEFAULT_PROTOCOL),
                ): vol.In(PROTOCOLS),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
