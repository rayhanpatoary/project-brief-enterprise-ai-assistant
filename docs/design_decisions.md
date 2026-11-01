# Design decisions and limits

- Preserve the original README assignment, project-intro.png and supplied ZIP. The
  application guide is appended. `--assignment` reads all 83 non-resource-fork PDFs
  directly from ZIP entries, without filesystem extraction.
- The assignment dataset contains department policies and product catalogs. Inspected
  policy headers include owners, policy IDs and review dates; the old catalog explicitly
  says December 2021. Keep this text in chunks and ask the model to identify historical
  or conflicting evidence. No automated policy precedence or reliable conflict detector
  is claimed. Similarity retrieval can miss the competing version; consult policy owners.
- The three added demo documents are intentionally small, separately named synthetic
  examples for repeatable evaluation. They are not authoritative additions to IronStore's
  supplied policies. Evaluate a clean collection with only these files; use a separate
  CHROMA_PERSIST_DIRECTORY for the assignment dataset to avoid conflicting demo policies.
- LangChain v1 `create_agent`, `@tool`, prompt/runnable composition and structured output
  replace legacy LLMChain/initialize_agent. API reference:
  https://reference.langchain.com/python/langchain/agents/factory/create_agent
- One configurable chat model supports query rewriting, expansion, answering and tools.
  A custom multi-query function makes expansion and deduplication explicit and avoids
  deprecated retrieval chains. Provider calls have bounded retries and timeouts.
- Local Chroma requires less setup than Elasticsearch or Pinecone for this small,
  single-machine dataset. Elasticsearch hybrid search and managed Pinecone scaling are
  useful future options. A single agent with three tools keeps cost and debugging
  manageable compared with multiple coordinating agents.
- Exact file hashes prevent repeated indexing, not semantic duplicates or PDFs whose
  binary metadata changed. Changed files are retained as separate versions; there is
  no document deletion UI. Retention, version lifecycle and content-level deduplication
  are future work.
- Missing credentials fail clearly. Chat completion failures expose retrieved passages
  for manual review with an explicit warning. Embedding failures return HTTP 503;
  the app does not pretend that lexical search is equivalent to semantic retrieval.
- No authentication, authorization, tenant isolation, rate limiting, malware scanning,
  OCR, audit logs, or production-grade PDF resource isolation. File and extracted-text
  limits reduce accidental load but do not sandbox adversarial PDFs. Run trusted demo
  files locally. Rendered text uses Streamlit's safe default; no unsafe HTML is enabled.
- Uploaded text/chunks and questions are processed by the configured OpenAI embedding
  and chat APIs. Local Chroma does not mean all processing stays local. The UI discloses
  this before upload. Do not use confidential company documents without authorization.

## Evaluation interpretation

`data/evaluation.json` has five answerable questions and two insufficient-information
questions. Hit rate is the fraction of answerable cases where at least one expected
document appears in the retrieved set. It does not measure answer accuracy, entailment,
precision, chunk-level relevance, or conflict resolution. Three tiny files and k=5
make this an easy retrieval test; do not interpret a high score as enterprise readiness.
Optional answer evaluation counts explicit abstention on unanswerable cases, excluding
provider failures. Human review of answers and sources is still required.

Live evaluation must use real API credentials and incurs usage charges. Offline tests
use deterministic non-semantic embeddings and fake chat models; they verify behavior
and persistence, not model quality. No live retrieval score is claimed unless recorded
with actual execution evidence in the verification report.
