from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str
    message: str
    user_id: str = Field(default="default", min_length=1)

class ChatResponse(BaseModel):
    response: str
