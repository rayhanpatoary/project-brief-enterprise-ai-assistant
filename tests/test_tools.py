import json
from unittest.mock import Mock

from app.agent import run_agent
from app.schemas import ChatRequest
from app.tools import build_tools
from tests.test_rag import structured_model
from app.schemas import GroundedAnswer


def test_tools_inventory_search_and_missing_document(populated):
    evidence = {}
    tools = {t.name: t for t in build_tools(populated, Mock(), evidence)}
    assert set(tools) == {'search_documents', 'summarize_document', 'list_documents'}
    listing = tools['list_documents'].invoke({})
    assert listing[0]['name'] == 'policy.md'
    passages = json.loads(tools['search_documents'].invoke({'question': 'remote'}))
    assert passages[0]['chunk_id'] in evidence
    assert 'not found' in tools['summarize_document'].invoke({'document_id': '../../.env'})


def test_summary_tool(populated):
    doc = populated.search('remote')[0]
    model = structured_model(GroundedAnswer(answer='Remote work policy.',
        chunk_ids=[doc.metadata['chunk_id']], insufficient_information=False))
    tool = build_tools(populated, model, {})[1]
    result = json.loads(tool.invoke({'document_id': doc.metadata['document_id']}))
    assert result['answer'] == 'Remote work policy.' and result['partial'] is False


def test_agent_provider_failure(populated):
    model = Mock()
    result = run_agent(ChatRequest(question='remote?', mode='agent'), populated, model)
    assert result.warning and not result.sources


def test_actual_agent_tool_loop(populated):
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.messages import AIMessage

    class ToolModel(FakeMessagesListChatModel):
        def bind_tools(self, tools, **kwargs):
            return self

    model = ToolModel(responses=[
        AIMessage(content='', tool_calls=[{'name': 'list_documents', 'args': {}, 'id': 'call-1', 'type': 'tool_call'}]),
        AIMessage(content='Inventory found.'),
    ])
    result = run_agent(ChatRequest(question='List available documents', mode='agent'), populated, model)
    assert 'policy.md' in result.answer and result.warning is None
