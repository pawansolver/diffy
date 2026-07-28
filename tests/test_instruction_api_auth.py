import os
import unittest
from unittest.mock import patch

import httpx

from instruction_api import app


class InstructionApiAuthTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        )

    async def asyncTearDown(self):
        await self.client.aclose()

    @patch.dict(os.environ, {"MCP_API_KEY": "test-secret"}, clear=False)
    async def test_health_remains_public(self):
        response = await self.client.get("/health")
        self.assertEqual(response.status_code, 200)

    @patch.dict(os.environ, {"MCP_API_KEY": "test-secret"}, clear=False)
    async def test_protected_route_rejects_missing_token(self):
        response = await self.client.get("/get-base-instruction")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["www-authenticate"], "Bearer")

    @patch.dict(os.environ, {"MCP_API_KEY": "test-secret"}, clear=False)
    async def test_protected_route_accepts_valid_token(self):
        response = await self.client.get(
            "/get-base-instruction",
            headers={"Authorization": "Bearer test-secret"},
        )
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
