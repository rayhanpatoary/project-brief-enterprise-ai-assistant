import json

from langchain_core.tools import tool

from app.rag import evidence_json, generate_answer


def build_tools(store, model, evidence: dict):
    def remember(docs):
        for doc in docs:
            evidence[doc.metadata['chunk_id']] = doc

    @tool
    def search_documents(question: str) -> str:
        """Search company documents for passages relevant to a specific question."""
        try:
            docs = store.search(question[:2000])
            remember(docs)
            return evidence_json(docs)
        except Exception:
            return 'Document search unavailable. Do not guess an answer.'

    @tool
    def list_documents() -> list[dict]:
        """List available document names, document IDs and chunk counts. Use IDs for summaries."""
        try:
            return store.list_documents()
        except Exception:
            return [{'error': 'Document list unavailable.'}]

    @tool
    def summarize_document(document_id: str) -> str:
        """Summarize a company document by its exact ID obtained from list_documents."""
        try:
            docs = store.document_chunks(document_id)
            if not docs:
                return 'Document not found. Use list_documents to select an existing ID.'
            # Bounded context: disclose partial summaries, never silently truncate.
            selected, length = [], 0
            for doc in docs:
                if length + len(doc.page_content) > 24000:
                    break
                selected.append(doc)
                length += len(doc.page_content)
            remember(selected)
            result = generate_answer('Summarize this document, including any dates and qualifications.', selected, model)
            payload = result.model_dump()
            payload['partial'] = len(selected) < len(docs)
            return json.dumps(payload)
        except Exception:
            return 'Document summary unavailable. Do not invent a summary.'

    return [search_documents, summarize_document, list_documents]
