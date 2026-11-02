"""Exercise actual coordinator against a fake HA storage boundary."""
import importlib.util
import pathlib
import sys
import types
import unittest
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

BASE = pathlib.Path(__file__).parents[1] / 'custom_components/historia_pojazdu'

# Small HA boundary stubs allow testing coordinator behavior without installing HA.
for name in ('homeassistant', 'homeassistant.config_entries', 'homeassistant.core', 'homeassistant.helpers',
             'homeassistant.helpers.storage', 'homeassistant.helpers.update_coordinator', 'homeassistant.util', 'homeassistant.util.dt'):
    sys.modules.setdefault(name, types.ModuleType(name))
sys.modules['homeassistant.config_entries'].ConfigEntry = object
sys.modules['homeassistant.core'].HomeAssistant = object
sys.modules['homeassistant.util.dt'].utcnow = lambda: datetime(2026, 10, 30, tzinfo=timezone.utc)
class Coordinator:
    def __init__(self, *args, **kwargs): pass
sys.modules['homeassistant.helpers.update_coordinator'].DataUpdateCoordinator = Coordinator
class Store:
    contents = {}
    def __init__(self, hass, version, key): self.key = key
    async def async_load(self): return self.contents.get(self.key)
    async def async_save(self, value): self.contents[self.key] = dict(value)
sys.modules['homeassistant.helpers.storage'].Store = Store

name = 'custom_components.historia_pojazdu'
spec = importlib.util.spec_from_file_location(name, BASE / '__init__.py', submodule_search_locations=[str(BASE)])
integration = importlib.util.module_from_spec(spec)
sys.modules[name] = integration
spec.loader.exec_module(integration)

class CoordinatorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        Store.contents.clear()
        self.entry = types.SimpleNamespace(entry_id='test', data={'registration': 'AA11111', 'vin': 'X'*17, 'first_registration':'2022-04-05'})
        self.coord = integration.VehicleCoordinator(None, self.entry)

    async def update(self, return_value=None, side_effect=None):
        if isinstance(return_value, tuple) and len(return_value) == 2:
            return_value += (None,)
        with patch.object(integration, 'fetch_report', new=AsyncMock(return_value=return_value, side_effect=side_effect)):
            self.coord.data = await self.coord._async_update_data()
        return self.coord.data

    async def test_restore_and_failed_fetch_preserve_values(self):
        first = await self.update((date(2031,5,6), date(2031,5,7)))
        timestamp = first['last_success']
        self.assertTrue(first['insurance_fresh'])
        restored = integration.VehicleCoordinator(None, self.entry)
        await restored.restore()
        self.assertEqual(restored.data['insurance'], '2031-05-06')
        self.assertFalse(restored.data['insurance_fresh'])
        self.coord = restored
        failed = await self.update(side_effect=integration.FetchError('Pobieranie nieudane'))
        self.assertEqual((failed['insurance'], failed['inspection'], failed['last_success']), ('2031-05-06', '2031-05-07', timestamp))
        self.assertFalse(failed['inspection_fresh'])
        self.assertEqual(failed['problem'], 'Pobieranie nieudane')

    async def test_odometer_survives_restart_and_failure(self):
        await self.update((date(2031,5,6), date(2031,5,7), (12345, 'km', date(2025,1,2))))
        restored = integration.VehicleCoordinator(None, self.entry)
        await restored.restore()
        self.assertEqual(restored.data['odometer'], 12345)
        self.assertEqual(restored.data['odometer_date'], '2025-01-02')
        self.assertFalse(restored.data['odometer_fresh'])
        self.coord = restored
        result = await self.update(side_effect=integration.FetchError('błąd'))
        self.assertEqual(result['odometer'], 12345)

    async def test_partial_retains_missing_and_does_not_advance_full_success(self):
        before = await self.update((date(2031,5,6), date(2031,5,7)))
        timestamp = before['last_success']
        partial = await self.update((date(2028,3,3), None))
        self.assertEqual(partial['insurance'], '2028-03-03')
        self.assertEqual(partial['inspection'], '2031-05-07')
        self.assertEqual(partial['last_success'], timestamp)
        self.assertTrue(partial['insurance_fresh'])
        self.assertFalse(partial['inspection_fresh'])
        self.assertIn('badania technicznego', partial['problem'])
        restored = integration.VehicleCoordinator(None, self.entry)
        await restored.restore()
        self.assertEqual(restored.data['insurance'], '2028-03-03')
        self.assertEqual(restored.data['inspection'], '2031-05-07')
        self.assertFalse(restored.data['insurance_fresh'])

    async def test_storage_failure_is_visible_without_discarding_live_dates(self):
        with patch.object(self.coord.store, 'async_load', new=AsyncMock(side_effect=OSError('private path'))):
            await self.coord.restore()
        self.assertIn('odczytać', self.coord.data['problem'])
        with patch.object(self.coord.store, 'async_save', new=AsyncMock(side_effect=OSError('private path'))):
            result = await self.update((date(2031, 5, 6), date(2031, 5, 7)))
        self.assertEqual(result['insurance'], '2031-05-06')
        self.assertTrue(result['insurance_fresh'])
        self.assertIn('zapisać', result['problem'])
        self.assertNotIn('private path', result['problem'])

if __name__ == '__main__': unittest.main()
