from functools import lru_cache

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.agent import run_agent
from app.config import ConfigurationError, get_settings
from app.ingestion import InvalidDocument
from app.models import chat_model
from app.multi_query import retrieve
from app.rag import answer_question
from app.schemas import ChatRequest, ChatResponse, SearchRequest
from app.vector_store import KnowledgeStore, as_source

app = FastAPI(title='IronStore Enterprise AI Assistant', version='1.0.0')


@lru_cache
def get_store():
    return KnowledgeStore(get_settings())


def store_dependency():
    try:
        return get_store()
    except ConfigurationError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(503, 'Knowledge store unavailable. Check local storage configuration.') from exc


@app.get('/health')
def health():
    return {'status': 'ok', 'configured': bool(get_settings().openai_api_key.get_secret_value().strip())}


@app.get('/documents')
def documents(store=Depends(store_dependency)):
    return store.list_documents()


@app.post('/documents/upload', status_code=201)
async def upload(file: UploadFile = File(...), store=Depends(store_dependency)):
    try:
        content = await file.read(get_settings().max_upload_bytes + 1)
        return await run_in_threadpool(store.ingest, file.filename or '', content)
    except InvalidDocument as exc:
        raise HTTPException(413 if 'limit' in str(exc) or 'too large' in str(exc) else 422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(503, 'Indexing unavailable. Check provider connectivity, quota and storage.') from exc
    finally:
        await file.close()


@app.post('/documents/search')
def search(request: SearchRequest, store=Depends(store_dependency)):
    try:
        model = chat_model(get_settings()) if request.mode == 'multi_query' else None
        docs, queries, warning, comparison = retrieve(store, request.question, model, request.mode == 'multi_query')
        return {'sources': [as_source(doc) for doc in docs], 'queries': queries,
                'warning': warning, 'comparison': comparison}
    except Exception as exc:
        raise HTTPException(503, 'Search provider unavailable. Check configuration and connectivity.') from exc


@app.post('/chat', response_model=ChatResponse)
def chat(request: ChatRequest, store=Depends(store_dependency)):
    try:
        model = chat_model(get_settings())
        return run_agent(request, store, model) if request.mode == 'agent' else answer_question(request, store, model)
    except ConfigurationError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(503, 'Chat or retrieval provider unavailable. Please retry later.') from exc
