from langchain_openai import ChatOpenAI

from app.config import Settings


def chat_model(settings: Settings):
    return ChatOpenAI(model=settings.openai_chat_model, api_key=settings.require_key(),
                      temperature=0, timeout=40, max_retries=1, max_tokens=1800)
