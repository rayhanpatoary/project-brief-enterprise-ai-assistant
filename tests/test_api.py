import pytest
from fastapi.testclient import TestClient

from app.main import app, store_dependency


@pytest.fixture
def client(store):
    app.dependency_overrides[store_dependency] = lambda: store
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_api_inventory_upload_search(client):
    assert client.get('/health').status_code == 200
    assert client.get('/documents').json() == []
    response = client.post('/documents/upload', files={'file': ('policy.txt', b'Remote work policy two days.')})
    assert response.status_code == 201 and not response.json()['duplicate']
    assert client.post('/documents/upload', files={'file': ('policy.txt', b'Remote work policy two days.')}).json()['duplicate']
    assert len(client.get('/documents').json()) == 1
    result = client.post('/documents/search', json={'question': 'remote policy'})
    assert result.status_code == 200 and result.json()['sources'][0]['page'] == 1


def test_validation(client):
    assert client.post('/chat', json={'question': ' '}).status_code == 422
    assert client.post('/chat', json={'question': 'hello', 'mode': 'shell'}).status_code == 422
    assert client.post('/documents/upload', files={'file': ('bad.exe', b'123')}).status_code == 422
    assert client.post('/documents/upload', files={'file': ('empty.txt', b'')}).status_code == 422
    assert client.post('/documents/search', json={'question': ''}).status_code == 422


def test_chat_without_credentials(client, monkeypatch, settings):
    monkeypatch.setattr('app.main.get_settings', lambda: settings)
    response = client.post('/chat', json={'question': 'remote policy'})
    assert response.status_code == 503 and 'OPENAI_API_KEY' in response.json()['detail']


def test_chat_endpoint(client, monkeypatch):
    from app.schemas import GroundedAnswer
    from tests.test_rag import structured_model
    client.post('/documents/upload', files={'file': ('policy.md', b'Remote work two days.')})
    source = client.post('/documents/search', json={'question': 'remote'}).json()['sources'][0]
    model = structured_model(GroundedAnswer(answer='Two days.', chunk_ids=[source['chunk_id']], insufficient_information=False))
    monkeypatch.setattr('app.main.chat_model', lambda _: model)
    result = client.post('/chat', json={'question': 'remote days?'})
    assert result.status_code == 200 and result.json()['sources'][0]['document_name'] == 'policy.md'


def test_upload_size_status(client, monkeypatch, settings):
    settings.max_upload_bytes = 4
    monkeypatch.setattr('app.main.get_settings', lambda: settings)
    assert client.post('/documents/upload', files={'file': ('big.txt', b'12345')}).status_code == 413
