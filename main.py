import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

import torch
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
# from fastapi.responses import StreamingResponse
from transformers import AutoTokenizer, AutoModelForCausalLM

from routers import files_router
from routers.files import FileNotFound, clean_expired_files_cron
from tools.args import get_args
from tools.logging_utils import log_set
from tools.openai_types import ChatModelNotExists, ChatMessagesError, ChatFunctionCallNotAllow
from tools.openai_types import ModelList, ChatCompletionResponse, ChatCompletionRequest
from tools.qwen_chat import load_model, format_history

# from tools.qwen_chat import stream_chat

MODEL_NAME: Optional[str] = "Qwen/Qwen-VL-Chat-Int4"
MODEL: Optional[AutoModelForCausalLM] = None
TOKENIZER: Optional[AutoTokenizer] = None

path = os.path.dirname(__file__)

app = FastAPI()

# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routers
app.include_router(files_router)    # /v1/files


@app.on_event("startup")
async def startup_event():
    # init logging
    log_set(logging.DEBUG)

    # load model and tokenizer
    global MODEL, TOKENIZER
    MODEL, TOKENIZER = load_model(MODEL_NAME, trust_remote_code=True, device_map="cuda")

    # clean expired files
    clean_expired_files_cron.start()


@asynccontextmanager
@app.on_event("shutdown")
async def shutdown_event():
    yield
    # GPU allocation
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


@app.exception_handler(ChatModelNotExists)
async def chat_model_not_exists_exception_handler(request: Request, exc: ChatModelNotExists):
    """Handle the exception when the model does not exist."""
    logging.debug(request)
    return JSONResponse(status_code=404, content={
        "object": "error",
        "message": f"The model `{exc.model_name}` does not exist.",
        "type": "NotFoundError",
        "param": None,
        "code": 404
    })


@app.exception_handler(ChatMessagesError)
async def chat_messages_error_exception_handler(request: Request, exc: ChatMessagesError):
    """Handle the exception when the messages are not formatted correctly."""
    logging.debug(request)
    return JSONResponse(status_code=404, content={
        "object": "error",
        "message": f"The last message should be from the user.",
        "data": exc.messages,
        "type": "ValueError",
        "param": None,
        "code": 404
    })


@app.exception_handler(ChatFunctionCallNotAllow)
async def chat_function_call_not_allow_exception_handler(request: Request, exc: ChatFunctionCallNotAllow):
    """Handle the exception when the function call is not allowed."""
    logging.debug(request)
    return JSONResponse(status_code=404, content={
        "object": "error",
        "message": f"Function call `{exc.function_name}` is not allowed.",
        "type": "NotImplementedError",
        "param": None,
        "code": 404
    })


@app.exception_handler(FileNotFound)
async def file_not_found(request: Request, exc: FileNotFound):
    """Handle the exception when the model does not exist."""
    logging.debug(request)
    return JSONResponse(status_code=404, content={
        "object": "error",
        "message": f"The file '{exc.file_id}' is not found",
        "type": "FileNotFound",
        "param": None,
        "code": 404
    })


@app.get("/v1/models", response_model=ModelList, tags=["Models"])
async def list_models():
    global MODEL_NAME
    return ModelList(**{"data": [{"id": MODEL_NAME, "owned_by": os.path.split(MODEL_NAME)[-2]}]})


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse, tags=["Chat"])
async def chat_completions(request: ChatCompletionRequest):
    logging.debug(f"Get request: {request}")
    global MODEL, TOKENIZER
    # verify model_name
    if request.model != MODEL_NAME:
        raise ChatModelNotExists(model_name=request.model)

    try:
        query, history, system = format_history(request.messages, TOKENIZER)
        logging.debug(f"Get query: {query}, history: {history}, system: {system}")
    except ValueError as e:
        raise ChatMessagesError(messages=request.messages, exc=e.__str__())

    # functions and tools
    if request.functions is not None or request.tools is not None:
        raise ChatFunctionCallNotAllow(function_name="")

    # seed
    if request.seed:
        torch.manual_seed(request.seed)

    # chat
    if request.stream:
        # todo: unSupported stream
        raise HTTPException(status_code=501, detail="Stream chat is not implemented.")
        # return StreamingResponse(stream_chat(query, history, MODEL, TOKENIZER, MODEL_NAME, append_history=False,
        #                          top_p=request.top_p, temperature=request.temperature))
    else:
        response, _ = MODEL.chat(TOKENIZER, query=query, history=history, append_history=False,
                                 top_p=request.top_p, temperature=request.temperature)
        logging.debug(f"Return response: {response}")
        return ChatCompletionResponse(**{
            "object": "chat.completion",
            "model": MODEL_NAME,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": response},
                "finish_reason": "stop"
            }]})


if __name__ == '__main__':
    args = get_args()
    MODEL_NAME = args.checkpoint_path
    uvicorn.run(app, host=args.server_name, port=args.server_port, workers=1)
