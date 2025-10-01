from __future__ import annotations
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class MulticontrolConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Gestisce il primo step di configurazione."""
        errors = {}

        if user_input is not None:
            try:
                # Qui puoi aggiungere una validazione delle credenziali se necessario
                return self.async_create_entry(
                    title="Multicontrol",
                    data={
                        "username": user_input["username"],
                        "password": user_input["password"],
                    },
                )
            except Exception:
                errors["base"] = "cannot_connect"

        # Schema per il form di configurazione
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required("username"): str, vol.Required("password"): str}
            ),
            errors=errors,
        )
