import pytest
from fastapi import status


@pytest.mark.asyncio(loop_scope="session")
async def test_create_department(client):
    response = await client.post("/", json={"name": "IT", "parent_id": None})
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["name"] == "IT"
    assert data["parent_id"] is None


@pytest.mark.asyncio(loop_scope="session")
async def test_get_department(client):
    response = await client.get("/1?depth=1&include_employees=false")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["department"]["name"] == "IT"
    assert data["department"]["parent_id"] is None
    assert data["employees"] is None
