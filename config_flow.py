from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class SolarVideosConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Solar Videos."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                # Validate user input (e.g., download directory)
                download_dir = user_input["download_dir"]
                video_urls = user_input["video_urls"]

                return self.async_create_entry(title="Solar Videos", data=user_input)

            except Exception as ex:
                _LOGGER.exception(ex)
                errors["base"] = "invalid_input"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("download_dir", default="/config/www/solar_videos"): str,
                    vol.Required("video_urls"): vol.All(cv.ensure_list, [cv.string]),
                }
            ),
            errors=errors,
        )
