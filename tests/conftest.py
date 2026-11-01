import hashlib

import pytest
from langchain_core.embeddings import Embeddings

from app.config import Settings
from app.vector_store import KnowledgeStore


class OfflineEmbeddings(Embeddings):
    """Deterministic local vectors exercise Chroma; not a semantic quality benchmark."""
    def embed_documents(self, texts):
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text):
        vector = [0.0] * 64
        for word in text.lower().split():
            vector[int(hashlib.sha256(word.encode()).hexdigest()[:8], 16) % 64] += 1
        return vector


@pytest.fixture
def settings(tmp_path):
    return Settings(_env_file=None, openai_api_key='', chroma_persist_directory=tmp_path / 'chroma',
                    chunk_size=200, chunk_overlap=30)


@pytest.fixture
def store(settings):
    return KnowledgeStore(settings, embeddings=OfflineEmbeddings())


@pytest.fixture
def populated(store):
    store.ingest('policy.md', b'Employees may work remotely two days each week with manager approval.')
    return store
