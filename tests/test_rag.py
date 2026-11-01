from unittest.mock import Mock

from langchain_core.runnables import RunnableLambda

from app.multi_query import deduplicate, retrieve
from app.rag import FALLBACK, answer_question, generate_answer
from app.schemas import ChatRequest, GroundedAnswer, QueryVariants, Turn


def structured_model(result):
    model = Mock()
    model.with_structured_output.return_value = RunnableLambda(lambda _: result)
    return model


def test_multi_query_dedup(populated):
    model = structured_model(QueryVariants(queries=['remote policy', 'work from home', 'remote policy']))
    docs, queries, warning, comparison = retrieve(populated, 'remote days', model, True)
    assert len(queries) == 3
    assert len(docs) == 1 and warning is None
    assert comparison['standard'] == comparison['multi_query']
    assert len(deduplicate(docs + docs)) == 1


def test_expansion_failure_falls_back(populated):
    model = Mock()
    model.with_structured_output.side_effect = RuntimeError('offline')
    docs, queries, warning, _ = retrieve(populated, 'remote days', model, True)
    assert docs and queries == ['remote days'] and warning


def test_answer_sources(populated):
    docs = populated.search('remote days')
    model = structured_model(GroundedAnswer(answer='Two days per week.',
        chunk_ids=[docs[0].metadata['chunk_id']], insufficient_information=False))
    result = generate_answer('remote days', docs, model)
    assert result.answer == 'Two days per week.' and len(result.sources) == 1


def test_unknown_citation_rejected(populated):
    result = generate_answer('remote days', populated.search('remote'), structured_model(
        GroundedAnswer(answer='invented', chunk_ids=['fake'], insufficient_information=False)))
    assert result.answer == FALLBACK and not result.sources


def test_insufficient_information(populated):
    result = generate_answer('CEO home?', populated.search('CEO'), structured_model(
        GroundedAnswer(answer='unknown', chunk_ids=[], insufficient_information=True)))
    assert result.answer == FALLBACK


def test_failure_returns_passages(populated):
    model = Mock()
    model.with_structured_output.side_effect = RuntimeError('SECRET_KEY_MUST_NOT_LEAK')
    result = generate_answer('remote days', populated.search('remote'), model)
    assert result.answer == FALLBACK and result.warning and result.sources
    assert 'SECRET' not in result.model_dump_json()


def test_no_documents_does_not_call_provider(store):
    model = Mock()
    result = answer_question(ChatRequest(question='policy?'), store, model)
    assert result.answer == FALLBACK
    model.with_structured_output.assert_not_called()


def test_conversation_rewrite(populated):
    model = RunnableLambda(lambda prompt: __import__('langchain_core.messages', fromlist=['AIMessage']).AIMessage(
        content='How many days can employees work remotely?'))
    from app.rag import standalone_question
    question = standalone_question('How many days?', [Turn(role='user', content='Tell me about remote work')], model)
    assert 'remotely' in question
