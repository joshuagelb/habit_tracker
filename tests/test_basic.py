import pytest
from httpx import AsyncClient
from app.main import app
from app.db.session import engine
from app.models import SQLModel

@pytest.fixture(autouse=True)
def create_db():
    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)
    yield
    SQLModel.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(app=app, base_url='http://test') as ac:
        r = await ac.post('/auth/register', json={'email': 'a@b.com', 'password': 'pass'})
        assert r.status_code == 200
        r = await ac.post('/auth/login', json={'email': 'a@b.com', 'password': 'pass'})
        assert r.status_code == 200
        token = r.json()['access_token']
        assert token

@pytest.mark.asyncio
async def test_habit_crud_and_checkin():
    async with AsyncClient(app=app, base_url='http://test') as ac:
        await ac.post('/auth/register', json={'email': 'u@u.com', 'password': 'pwd'})
        r = await ac.post('/auth/login', json={'email': 'u@u.com', 'password': 'pwd'})
        token = r.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        r = await ac.post('/habits/', json={'name': 'Run', 'description': 'Run 5k'}, headers=headers)
        assert r.status_code == 200
        hid = r.json()['id']
        r = await ac.post(f'/habits/{hid}/checkin', json={}, headers=headers)
        assert r.status_code == 200
        r = await ac.get(f'/habits/{hid}/streak', headers=headers)
        assert r.status_code == 200
        assert r.json()['streak'] >= 1
