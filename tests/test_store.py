import pytest

from app.vector_store import KnowledgeStore
from tests.conftest import OfflineEmbeddings


def test_duplicate_persistence_reload(populated, settings):
    result = populated.ingest('renamed.txt', b'Employees may work remotely two days each week with manager approval.')
    assert result['duplicate']
    reopened = KnowledgeStore(settings, OfflineEmbeddings())
    assert len(reopened.list_documents()) == 1
    docs = reopened.search('remote work')
    assert docs[0].metadata['document_name'] == 'policy.md'
    assert reopened.document_chunks(result['document_id'])
    assert reopened.document_chunks('missing') == []


def test_empty_store(store):
    assert store.list_documents() == []
    assert store.search('policy') == []


def test_failed_batch_rollback(store, monkeypatch):
    original = store.db.add_documents

    def fail(documents, ids):
        original(documents, ids=ids)
        raise RuntimeError('provider failure')

    monkeypatch.setattr(store.db, 'add_documents', fail)
    with pytest.raises(RuntimeError):
        store.ingest('test.txt', b'This document should be rolled back.')
    assert store.list_documents() == []
