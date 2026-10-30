"""Manual refresh button."""
from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([RefreshButton(hass.data[DOMAIN][entry.entry_id], entry)])

class RefreshButton(CoordinatorEntity, ButtonEntity):
    _attr_has_entity_name = True
    _attr_translation_key = 'refresh'
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f'{entry.entry_id}_refresh'
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)}, name=entry.data[CONF_NAME], manufacturer='Historia Pojazdu')

    async def async_press(self):
        await self.coordinator.async_request_refresh()
