# Requirements and implementation plan

The existing README is the authoritative assignment and is preserved verbatim above
the appended application guide. The existing documents/documents.zip contains synthetic
department policies and product catalog PDFs, including an explicitly old 2021 catalog.
The brief explicitly warns of duplicates, inconsistencies and outdated information.

1. Establish Python 3.12 dependencies, configuration and a validated FastAPI interface.
2. Validate and split PDF/TXT/Markdown, index persistent Chroma embeddings, detect exact duplicates.
3. Add evidence-only RAG, structured source IDs, abstention and provider failure handling.
4. Compare standard similarity retrieval with deduplicated multi-query retrieval.
5. Add a modern create_agent tool loop with three restricted, typed tools.
6. Add a Streamlit API client with session history, uploads, sources and modes.
7. Verify each layer with offline provider mocks, real local Chroma persistence and API tests.
8. Add repeatable live evaluation, synthetic demo policies and reproducible documentation.

Do not replace supplied data, commit, push or open a PR. No enterprise authorization
claims. Inspect assignment PDFs locally; never send them to a provider during automated tests.
