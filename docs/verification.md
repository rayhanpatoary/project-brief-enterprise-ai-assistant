# Verification report

Verified on 2026-11-01 with Windows PowerShell and Python 3.12.10.

## Executed successfully

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.in
.\.venv\Scripts\python.exe -m pip freeze | Set-Content -Encoding utf8 requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app ui scripts tests
.\.venv\Scripts\python.exe -m scripts.evaluate --help
.\.venv\Scripts\python.exe -m scripts.ingest_sample_data --help
git diff --check
```

- Clean Python 3.12 virtual environment installed the compatible dependencies; the
  complete resolved set of 126 packages is pinned in requirements.txt.
- `pip check`: **No broken requirements found.**
- Final `pytest -q`: **34 passed in 18.34s**.
- Compilation and whitespace checks passed.
- Local Chroma ingestion, retrieval, duplicate detection, rollback and reopening were
  verified with deterministic test embeddings. No OpenAI request was used in these tests.
- Tests extracted a real supplied PDF and checked metadata. ZIP inspection identified
  83 usable PDFs. Full assignment ingestion with OpenAI was not run.
- Citation rejection, insufficient-information responses, provider failure fallbacks,
  multi-query deduplication, conversation rewrite and tools were tested with fake models.
- One actual `create_agent` loop called the inventory tool with a fake tool-calling model.
  Search and summary tools were separately exercised, including missing document handling.
- Streamlit AppTest verified rendering, conversation history, forwarding follow-up
  history, clearing chat and visible API connection failures.
- Evaluation-script test measured hit-rate calculation against controlled local data;
  its score is a test assertion, not a live semantic retrieval benchmark.
- Original README content is preserved as an unchanged prefix. Original ZIP and image
  are untouched. Source scan found no OpenAI API-key literals. No key was configured.

## Startup checks

Executed:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
.\.venv\Scripts\python.exe -m streamlit run ui/streamlit_app.py --server.headless true --server.address 127.0.0.1 --server.port 8501
```

HTTP requests verified:

- `http://127.0.0.1:8000/health` → 200, `{"status":"ok","configured":false}`.
- `http://127.0.0.1:8501/_stcore/health` → 200, `ok`.
- `http://127.0.0.1:8501/` → 200, Streamlit HTML.

The first sandboxed installation attempt failed DNS resolution. After approved network
access, installation succeeded. Sandboxed Windows asyncio/socket initialization stalled
API tests and startup; approved execution outside the sandbox resolved this. An initial
Streamlit test entrypoint path failed under the installed version's relative-path rules;
using an absolute path corrected it. The final suite passed after these corrections.

## Not fully verified

- Real OpenAI embeddings, answer quality, semantic multi-query improvement and live agent
  tool selection: **not run because OPENAI_API_KEY is absent**.
- Live evaluation hit rate/abstention score: **not measured**. Run the README evaluation
  commands after indexing the demo documents with your own credentials.
- Full supplied dataset indexing, retrieval at its full size, policy conflict handling
  quality and historical-policy interpretation need live testing and human review.
- Visual browser review and interactive browser upload were not performed; UI behavior
  was checked using Streamlit's in-process AppTest and server health responses.
- Requirements are frozen from the successful clean Windows install. Other operating
  systems and Python versions were not tested. Reinstalling the generated lock file in
  a second independent environment was not performed.

## Review and interview notes

Suggested commit message: `feat: implement IronStore enterprise knowledge assistant with RAG and tool agent`

Interview explanation: “I built a modular document assistant with a FastAPI backend
and a Streamlit client. Documents are validated, split by page, embedded and persisted
in Chroma. I compare standard retrieval with deduplicated multi-query retrieval and use
structured model responses to validate citations against real source chunks. A LangChain
agent selects among three restricted tools. Tests mock providers while exercising real
local persistence, HTTP validation, failures and chat state. The main remaining production
work is access control, document lifecycle management and stronger groundedness evaluation.”

No commits, pushes or pull requests were created.
