from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Turn(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    mode: Literal['standard', 'multi_query', 'agent'] = 'standard'
    history: list[Turn] = Field(default_factory=list, max_length=20)

    @field_validator('question')
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('Question must not be blank.')
        return value.strip()


class SearchRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    mode: Literal['standard', 'multi_query'] = 'standard'


class Source(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    source: str
    page: int
    text: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source] = Field(default_factory=list)
    retrieved_sources: list[Source] = Field(default_factory=list)
    queries: list[str] = Field(default_factory=list)
    warning: str | None = None
    comparison: dict[str, list[str]] = Field(default_factory=dict)


class GroundedAnswer(BaseModel):
    answer: str = Field(description='Answer using only supplied evidence; reference sources by chunk ID.')
    chunk_ids: list[str] = Field(description='Only IDs that directly support the answer.')
    insufficient_information: bool


class QueryVariants(BaseModel):
    queries: list[str] = Field(max_length=3)
