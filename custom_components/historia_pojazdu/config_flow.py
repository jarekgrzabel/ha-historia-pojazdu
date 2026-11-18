"""Configuration from the Home Assistant UI."""
from __future__ import annotations

import hashlib
import re
from datetime import date, datetime

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util

from .const import CONF_FIRST_REGISTRATION, CONF_REGISTRATION, CONF_VIN, DOMAIN

_DATE_SELECTOR = (
    selector.ChooseSelector(
        selector.ChooseSelectorConfig(
            choices={
                'manual': {'selector': {'text': {}}},
                'calendar': {'selector': {'date': {}}},
            },
            translation_key='first_registration_mode',
        )
    )
    if hasattr(selector, 'ChooseSelector')
    else selector.TextSelector()
)

_USER_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): str,
    vol.Required(CONF_REGISTRATION): str,
    vol.Required(CONF_VIN): str,
    vol.Required(CONF_FIRST_REGISTRATION): _DATE_SELECTOR,
})


class HistoriaPojazduConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            name = user_input[CONF_NAME].strip()
            registration = re.sub(r'\s+', '', user_input[CONF_REGISTRATION]).upper()
            vin = user_input[CONF_VIN].strip().upper()
            raw_date = user_input[CONF_FIRST_REGISTRATION].strip()
            if not name:
                errors[CONF_NAME] = 'invalid_name'
            if not re.fullmatch(r'[A-Z0-9-]{2,12}', registration):
                errors[CONF_REGISTRATION] = 'invalid_registration'
            if not re.fullmatch(r'[A-HJ-NPR-Z0-9]{17}', vin):
                errors[CONF_VIN] = 'invalid_vin'
            try:
                first_date = (
                    datetime.strptime(raw_date, '%d.%m.%Y').date()
                    if '.' in raw_date
                    else date.fromisoformat(raw_date)
                )
            except ValueError:
                errors[CONF_FIRST_REGISTRATION] = 'invalid_date'
            else:
                if first_date > dt_util.now().date():
                    errors[CONF_FIRST_REGISTRATION] = 'future_date'
            if not errors:
                unique = hashlib.sha256((registration + ':' + vin).encode()).hexdigest()
                await self.async_set_unique_id(unique)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_NAME: name,
                        CONF_REGISTRATION: registration,
                        CONF_VIN: vin,
                        CONF_FIRST_REGISTRATION: first_date.isoformat(),
                    },
                )
        return self.async_show_form(
            step_id='user',
            data_schema=self.add_suggested_values_to_schema(_USER_SCHEMA, user_input),
            errors=errors,
        )
