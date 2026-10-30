"""Configuration from the Home Assistant UI."""
from __future__ import annotations

import hashlib
import re
from datetime import date

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from .const import CONF_FIRST_REGISTRATION, CONF_REGISTRATION, CONF_VIN, DOMAIN


class HistoriaPojazduConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            name = user_input[CONF_NAME].strip()
            registration = re.sub(r'\s+', '', user_input[CONF_REGISTRATION]).upper()
            vin = user_input[CONF_VIN].strip().upper()
            raw_date = user_input[CONF_FIRST_REGISTRATION].strip()
            try:
                first_date = date.fromisoformat(raw_date)
                if first_date > date.today():
                    raise ValueError
            except ValueError:
                errors['base'] = 'invalid_date'
            if not name or not re.fullmatch(r'[A-Z0-9-]{2,12}', registration) or not re.fullmatch(r'[A-HJ-NPR-Z0-9]{17}', vin):
                errors['base'] = 'invalid_data'
            if not errors:
                unique = hashlib.sha256((registration + ':' + vin).encode()).hexdigest()
                await self.async_set_unique_id(unique)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=name, data={CONF_NAME: name, CONF_REGISTRATION: registration,
                        CONF_VIN: vin, CONF_FIRST_REGISTRATION: first_date.isoformat()})
        schema = vol.Schema({vol.Required(CONF_NAME): str, vol.Required(CONF_REGISTRATION): str,
                             vol.Required(CONF_VIN): str, vol.Required(CONF_FIRST_REGISTRATION): str})
        return self.async_show_form(step_id='user', data_schema=schema, errors=errors)
