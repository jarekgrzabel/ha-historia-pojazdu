"""Date and status sensors."""
from __future__ import annotations
from datetime import date, datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import CONF_NAME

from .const import DOMAIN

DESCRIPTIONS = (
    SensorEntityDescription(key='insurance', translation_key='insurance', device_class=SensorDeviceClass.DATE),
    SensorEntityDescription(key='inspection', translation_key='inspection', device_class=SensorDeviceClass.DATE),
    SensorEntityDescription(key='odometer', translation_key='odometer', device_class=SensorDeviceClass.DISTANCE),
    SensorEntityDescription(key='last_success', translation_key='last_success', device_class=SensorDeviceClass.TIMESTAMP, entity_category=EntityCategory.DIAGNOSTIC),
    SensorEntityDescription(key='status', translation_key='status', entity_category=EntityCategory.DIAGNOSTIC),
)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(VehicleSensor(coordinator, entry, description) for description in DESCRIPTIONS)

class VehicleSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f'{entry.entry_id}_{description.key}'
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)}, name=entry.data[CONF_NAME], manufacturer='Historia Pojazdu')

    @property
    def native_value(self):
        key = self.entity_description.key
        if key == 'status':
            return self.coordinator.data['problem'] or 'Aktualne'
        if key == 'odometer':
            return self.coordinator.data.get('odometer')
        value = self.coordinator.data.get(key)
        if value is None:
            return None
        try:
            return datetime.fromisoformat(value) if key == 'last_success' else date.fromisoformat(value)
        except (TypeError, ValueError):
            return None

    @property
    def native_unit_of_measurement(self):
        if self.entity_description.key == 'odometer':
            return self.coordinator.data.get('odometer_unit')
        return super().native_unit_of_measurement

    @property
    def extra_state_attributes(self):
        key = self.entity_description.key
        if key == 'odometer':
            return {'data_odczytu': self.coordinator.data.get('odometer_date'),
                    'aktualnosc': 'aktualne' if self.coordinator.data.get('odometer_fresh') else 'zapisane lub nieaktualne',
                    'problem': self.coordinator.data.get('problem')}
        if key in ('insurance', 'inspection'):
            return {'aktualnosc': 'aktualne' if self.coordinator.data.get(f'{key}_fresh') else 'zapisane lub nieaktualne',
                    'problem': self.coordinator.data.get('problem')}
        return None
