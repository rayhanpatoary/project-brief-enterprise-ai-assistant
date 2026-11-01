import json

from langchain.agents import create_agent

from app.rag import FALLBACK, RULES, generate_answer
from app.schemas import ChatResponse
from app.tools import build_tools


def run_agent(request, store, model):
    evidence = {}
    tools = build_tools(store, model, evidence)
    try:
        agent = create_agent(model=model, tools=tools, system_prompt=RULES +
                             '\nUse tools to find evidence before answering. For document inventory use list_documents.')
        result = agent.invoke({'messages': [t.model_dump() for t in request.history] +
                              [{'role': 'user', 'content': request.question}]}, config={'recursion_limit': 12})
        # Ground the final answer independently in the actual passages tools returned.
        if evidence:
            response = generate_answer(request.question, list(evidence.values()), model, request.history)
            for message in result['messages']:
                if getattr(message, 'name', None) == 'summarize_document':
                    try:
                        partial = json.loads(message.content).get('partial', False)
                    except (ValueError, TypeError, AttributeError):
                        partial = False
                    if partial:
                        response.warning = ' '.join(filter(None, [response.warning,
                            'Partial summary: only the first 24,000 characters of the document were considered.']))
                        break
            return response
        # Inventory responses are deterministic; never return unverified agent prose.
        used_list = any(getattr(m, 'name', None) == 'list_documents' for m in result['messages'])
        if used_list:
            rows = store.list_documents()
            return ChatResponse(answer='Available documents:\n' + '\n'.join(
                f"- {row['name']} ({row['document_id']})" for row in rows) if rows else 'No documents indexed yet.')
        return ChatResponse(answer=FALLBACK)
    except Exception:
        return ChatResponse(answer=FALLBACK, warning='Agent provider unavailable or tool-step limit reached.')
