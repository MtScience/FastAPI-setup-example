import pytest_asyncio as pta
from httpx import ASGITransport, AsyncClient

from main import app


@pta.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://0.0.0.0:8000/departments",
    ) as client:
        yield client
