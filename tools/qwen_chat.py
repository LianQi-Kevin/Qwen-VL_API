import logging
from typing import Tuple, Literal, List, Optional

from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation import GenerationConfig

from tools.openai_types import ChatMessage, ChatCompletionResponse
from tools.tools import download_img_from_url


def load_model(_model_path: str, device_map: Literal["cuda", "cpu", "auto"] = "auto", trust_remote_code: bool = True
               ) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """Load model and tokenizer from Hugging Face model hub."""
    _model = AutoModelForCausalLM.from_pretrained(_model_path,
                                                  trust_remote_code=trust_remote_code, device_map=device_map)
    _tokenizer = AutoTokenizer.from_pretrained(_model_path, trust_remote_code=trust_remote_code)
    _model.generation_config = GenerationConfig.from_pretrained(_model_path, trust_remote_code=trust_remote_code)
    return _model, _tokenizer


def _create_query(_query: ChatMessage, **kwargs):
    """Create the query for the model.chat function."""
    if isinstance(_query.content, str):
        return [{"text": _query.content}]
    else:
        _query_list = []
        for index, content in enumerate(_query.content):
            if content.type == "text":
                _query_list.append({"text": content.text})
            elif content.type == "image_url":
                _img_path = download_img_from_url(content.image_url.url, **kwargs)
                logging.debug(f"Save Image, path: {_img_path}")
                _query_list.append({"image": _img_path})
        return _query_list


def format_history(_messages: List[ChatMessage], _tokenizer: AutoTokenizer, **kwargs) -> tuple[
    str, Optional[List[Tuple[str, str]]], str]:
    """
    Format the OpenAI API style chat messages to Qwen-VL model.chat style.

    :returns: query, history, system
    """
    _system: str = "You are a helpful assistant."
    _query: str
    _history: Optional[List[Tuple[str, str]]] = None

    # system
    if _messages[0].role == "system":
        _system = _messages.pop(0).content

    # query
    assert _messages[-1].role == "user", ValueError("The last message should be from the user.")
    _query = _tokenizer.from_list_format(_create_query(_messages.pop(-1), **kwargs))

    # history
    if len(_messages) > 0:
        _history = []
        it = iter(_messages)
        for prompt, response in zip(it, it):
            _history.append((_tokenizer.from_list_format(_create_query(prompt, **kwargs)), response.content))

    return _query, _history, _system


async def stream_chat(query: str, history: List[Tuple[str, str]], model: AutoModelForCausalLM,
                      tokenizer: AutoTokenizer, model_name: str = "", **kwargs):
    """
    Stream chat with the model.

    todo: unSupported Stream Chat
    """
    answer = ""
    for index, chunk in enumerate(model.chat_stream(tokenizer, query=query, history=history, **kwargs)):
        yield bytes(ChatCompletionResponse(**{
            "object": "chat.completion.chunk",
            "model": model_name,
            "choices": [{
                "index": index,
                "delta": {"role": "assistant", "content": chunk.replace(answer, "")},
            }]}).model_dump_json(), "utf-8")
        answer = chunk


if __name__ == '__main__':
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "使用中文回复我图里有啥?"},
                {"type": "image_url", "image_url": {"url": "assets/Shanghai.jpg"}}
            ]
        }
    ]
    # messages = [ChatMessage(**message) for message in messages]
    # _, tokenizer = load_model("Qwen/Qwen-VL-Chat-Int4")
    # query, history, system = format_history(messages, tokenizer)
