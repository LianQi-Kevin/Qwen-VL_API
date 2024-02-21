import time
from typing import List, Optional, Literal, Union, Dict
from uuid import uuid4

from pydantic import BaseModel, Field


class ModelCard(BaseModel):
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "owner"


class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelCard] = []


# class ChatToolCallsFunction(BaseModel):
#     name: str
#     arguments: str

# class ChatToolCalls(BaseModel):
#     id: str
#     type: str
#     function: ChatToolCallsFunction


class ChatContentImageImageUrl(BaseModel):
    url: str


class ChatContentImage(BaseModel):
    type: Literal["text", "image_url"]
    text: Optional[str] = None
    image_url: Optional[ChatContentImageImageUrl] = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: Optional[Union[str, List[ChatContentImage]]] = None
    # name: Optional[str] = None
    # tool_call_id: Optional[str] = None
    # tool_calls: Optional[List[ChatToolCalls]] = None


class DeltaMessage(BaseModel):
    role: Optional[Literal["user", "assistant", "system"]] = None
    content: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = Field(default=1, ge=0, le=2)
    top_p: Optional[float] = Field(default=1, ge=0, le=1)
    seed: Optional[int] = None
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None
    functions: Optional[list] = None
    tools: Optional[list] = None


class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Literal["stop", "length"]


class ChatCompletionResponseStreamChoice(BaseModel):
    index: int
    delta: DeltaMessage
    finish_reason: Optional[Literal["stop"]] = None


class ChatCompletionResponse(BaseModel):
    model: str
    choices: List[Union[ChatCompletionResponseChoice, ChatCompletionResponseStreamChoice]]

    id: str = Field(default_factory=lambda: str(uuid4()))
    created: Optional[int] = Field(default_factory=lambda: int(time.time()))
    usage: Optional[Dict[str, int]] = Field(default=None)
    object: Literal["chat.completion", "chat.completion.chunk"] = Field(default="chat.completion")


class ChatModelNotExists(Exception):
    def __init__(self, model_name: str):
        self.model_name = model_name


class ChatMessagesError(Exception):
    def __init__(self, messages: List[ChatMessage], exc: str = None):
        self.messages = messages
        self.exc = exc


class ChatFunctionCallNotAllow(Exception):
    def __init__(self, function_name: str = None):
        self.function_name = function_name
