import hashlib
from threading import RLock

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from app.config import Settings
from app.ingestion import prepare_document
from app.schemas import Source


def as_source(doc) -> Source:
    return Source(**{key: doc.metadata[key] for key in (
        'chunk_id', 'document_id', 'document_name', 'source', 'page'
    )}, text=doc.page_content)


class KnowledgeStore:
    def __init__(self, settings: Settings, embeddings=None):
        self.settings = settings
        if embeddings is None:
            embeddings = OpenAIEmbeddings(model=settings.openai_embedding_model,
                                          api_key=settings.require_key(), max_retries=1, request_timeout=30)
        # Separate incompatible embedding models and chunking settings automatically.
        signature = f'{settings.openai_embedding_model}:{settings.chunk_size}:{settings.chunk_overlap}'
        collection = 'ironstore-' + hashlib.sha256(signature.encode()).hexdigest()[:16]
        self.db = Chroma(collection_name=collection, embedding_function=embeddings,
                         persist_directory=str(settings.chroma_persist_directory))
        self.lock = RLock()

    def ingest(self, filename: str, content: bytes) -> dict:
        document_id, chunks = prepare_document(filename, content, self.settings)
        with self.lock:
            existing = self.db.get(where={'document_id': document_id}, include=['metadatas'])
            if existing['ids']:
                return {'document_id': document_id, 'chunks': len(existing['ids']), 'duplicate': True}
            ids = [doc.metadata['chunk_id'] for doc in chunks]
            try:
                # A failed batch must not leave a partially indexed document marked complete.
                for start in range(0, len(chunks), 100):
                    self.db.add_documents(chunks[start:start + 100], ids=ids[start:start + 100])
            except Exception:
                self.db.delete(ids=ids)
                raise
        return {'document_id': document_id, 'chunks': len(chunks), 'duplicate': False}

    def list_documents(self) -> list[dict]:
        rows = self.db.get(include=['metadatas'])
        documents = {}
        for meta in rows['metadatas'] or []:
            key = meta['document_id']
            row = documents.setdefault(key, {'document_id': key, 'name': meta['document_name'], 'chunks': 0})
            row['chunks'] += 1
        return sorted(documents.values(), key=lambda row: row['name'])

    def search(self, question: str):
        return self.db.similarity_search(question, k=self.settings.retrieval_k)

    def document_chunks(self, document_id: str):
        from langchain_core.documents import Document
        rows = self.db.get(where={'document_id': document_id}, include=['documents', 'metadatas'])
        return sorted([Document(page_content=text, metadata=meta)
                       for text, meta in zip(rows['documents'] or [], rows['metadatas'] or [])],
                      key=lambda doc: doc.metadata['chunk_index'])
