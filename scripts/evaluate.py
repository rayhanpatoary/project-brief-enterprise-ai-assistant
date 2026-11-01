"""Retrieval evaluation using real configured embeddings; no fabricated scores."""
import argparse
import json
from pathlib import Path

from app.config import get_settings
from app.models import chat_model
from app.rag import FALLBACK, answer_question
from app.schemas import ChatRequest
from app.vector_store import KnowledgeStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=Path('data/evaluation.json'))
    parser.add_argument('--mode', choices=['standard', 'multi_query'], default='standard')
    parser.add_argument('--answers', action='store_true', help='Also call chat API and measure insufficient-information abstention.')
    args = parser.parse_args()
    settings = get_settings()
    store = KnowledgeStore(settings)
    if not store.list_documents():
        raise SystemExit('No documents indexed. Run python -m scripts.ingest_sample_data first.')
    from app.multi_query import retrieve
    model = chat_model(settings) if args.answers or args.mode == 'multi_query' else None
    rows, hits, positive, abstained, negative = [], 0, 0, 0, 0
    for case in json.loads(args.dataset.read_text(encoding='utf-8')):
        docs, queries, warning, _ = retrieve(store, case['question'], model, args.mode == 'multi_query')
        names = sorted({doc.metadata['document_name'] for doc in docs})
        hit = bool(set(names) & set(case['expected_sources']))
        if not case['insufficient']:
            hits += int(hit)
            positive += 1
        row = {**case, 'retrieved_sources': names, 'hit': hit, 'queries': queries, 'warning': warning}
        if args.answers:
            response = answer_question(ChatRequest(question=case['question'], mode=args.mode), store, model)
            row['response'] = response.model_dump()
            if case['insufficient']:
                negative += 1
                abstained += int(response.answer == FALLBACK and response.warning is None)
        rows.append(row)
    print(json.dumps({'mode': args.mode, 'positive_cases': positive, 'retrieval_hit_rate': hits / positive if positive else None,
                      'insufficient_cases_scored': negative, 'abstention_rate': abstained / negative if negative else None,
                      'cases': rows}, indent=2))


if __name__ == '__main__':
    main()
