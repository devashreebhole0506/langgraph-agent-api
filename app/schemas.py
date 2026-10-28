from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    thread_id: str | None = Field(default=None, min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=5000)


class AgentResponse(BaseModel):
    thread_id: str
    reply: str
    message_count: int
    status: str = "success"


class HealthResponse(BaseModel):
    status: str
    service: str
    api_key_configured: bool
