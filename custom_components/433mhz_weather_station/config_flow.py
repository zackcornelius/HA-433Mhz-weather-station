"""Config flow for the 433MHz Weather Station integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

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
)

_HUB_UNIQUE_ID = "rtl433_hub"


class WeatherStationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for 433MHz Weather Station."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the flow."""
        self._discovery_data: dict = {}

    # ------------------------------------------------------------------
    # Manual setup – creates the hub entry that keeps the domain loaded
    # ------------------------------------------------------------------

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle initial setup by the user."""
        await self.async_set_unique_id(_HUB_UNIQUE_ID)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(
                title="RTL_433 RF Listener",
                data={CONF_ENTRY_TYPE: ENTRY_TYPE_HUB},
            )

        return self.async_show_form(step_id="user")

    # ------------------------------------------------------------------
    # Discovery – fired by __init__.py when a new (model, id) is seen
    # ------------------------------------------------------------------

    async def async_step_integration_discovery(
        self, discovery_info: dict
    ) -> FlowResult:
        """Handle a newly discovered RF sensor."""
        model: str = discovery_info[CONF_MODEL]
        sensor_id = discovery_info[CONF_SENSOR_ID]

        unique_id = f"{model}_{sensor_id}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        self._discovery_data = discovery_info
        self.context["title_placeholders"] = {
            "model": model,
            "sensor_id": str(sensor_id),
        }

        return await self.async_step_confirm_discovery()

    async def async_step_confirm_discovery(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Ask the user to confirm (and optionally rename) a discovered sensor."""
        model: str = self._discovery_data[CONF_MODEL]
        sensor_id = self._discovery_data[CONF_SENSOR_ID]
        default_name = f"{model} #{sensor_id}"

        if user_input is not None:
            name: str = user_input.get("name", default_name).strip() or default_name
            return self.async_create_entry(
                title=name,
                data={
                    CONF_ENTRY_TYPE: ENTRY_TYPE_SENSOR,
                    CONF_MODEL: model,
                    CONF_SENSOR_ID: sensor_id,
                    CONF_ESPHOME_DEVICE_ID: self._discovery_data.get(
                        CONF_ESPHOME_DEVICE_ID, ""
                    ),
                    CONF_PROTOCOL_DESC: self._discovery_data.get(
                        CONF_PROTOCOL_DESC, ""
                    ),
                    CONF_AVAILABLE_FIELDS: self._discovery_data.get(
                        CONF_AVAILABLE_FIELDS, []
                    ),
                },
            )

        schema = vol.Schema(
            {vol.Optional("name", default=default_name): str}
        )

        return self.async_show_form(
            step_id="confirm_discovery",
            data_schema=schema,
            description_placeholders={
                "model": model,
                "sensor_id": str(sensor_id),
                "protocol": self._discovery_data.get(CONF_PROTOCOL_DESC, ""),
            },
        )
