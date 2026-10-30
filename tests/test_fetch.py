"""Bounded retries, verification defaults and sanitized failure tests."""
import asyncio
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('api_fetch', pathlib.Path(__file__).parents[1] / 'custom_components/historia_pojazdu/api.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)

class Response:
    def __init__(self, report=None):
        self.cookies = {'XSRF-TOKEN': types.SimpleNamespace(value='secret')}
        self.report = report
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
    def raise_for_status(self): pass
    async def json(self, **kwargs): return self.report
class Session:
    calls = []
    failures = 0
    def __init__(self, **kwargs): self.timeout = kwargs['timeout']
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
    def post(self, url, **kwargs):
        self.calls.append((url, kwargs, self.timeout))
        if self.failures:
            type(self).failures -= 1
            raise asyncio.TimeoutError('sensitive details')
        if len(self.calls) % 2:
            return Response()
        return Response({'timelineData': {'insuranceExpiryDate': '2031-05-06', 'events': []}})

class FetchTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        Session.calls = []
        Session.failures = 0

    async def test_verified_tls_and_bound(self):
        with patch.object(api.aiohttp, 'ClientSession', Session):
            result = await api.fetch_report('test', 'secret-vin', '2024-01-01')
        self.assertEqual(result[0].isoformat(), '2031-05-06')
        self.assertEqual(len(Session.calls), 2)
        for _, kwargs, timeout in Session.calls:
            self.assertNotIn('ssl', kwargs)  # aiohttp default verifies certificates
            self.assertEqual(timeout.total, 15)
            self.assertEqual(timeout.connect, 6)

    async def test_retries_sanitized_failure(self):
        Session.failures = 3
        sleeps = []
        async def fake_sleep(n): sleeps.append(n)
        with patch.object(api.aiohttp, 'ClientSession', Session), patch.object(api.asyncio, 'sleep', fake_sleep):
            with self.assertRaises(api.FetchError) as caught:
                await api.fetch_report('test', 'secret-vin', '2024-01-01')
        self.assertEqual(len(Session.calls), 3)
        self.assertEqual(sleeps, [1, 2])
        self.assertNotIn('secret', str(caught.exception))

if __name__ == '__main__': unittest.main()
