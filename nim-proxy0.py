#!/usr/bin/env python3
"""
Anthropic-to-OpenAI proxy for NVIDIA NIM API.
Translates Claude Code's Anthropic Messages API calls to NVIDIA's OpenAI-compatible format.
"""

import json
import sys
import os
import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn
import httpx

NIM_BASE_URL = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY = os.environ.get("NVIDIA_NIM_API_KEY", "")
DEFAULT_MODEL = os.environ.get("NIM_DEFAULT_MODEL", "nvidia/llama-3.1-nemotron-ultra-253b-v1")

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nim-proxy0")


def anthropic_to_openai(body: dict) -> dict:
    messages = []

    system = body.get("system")
    if system:
        if isinstance(system, str):
            messages.append({"role": "system", "content": system})
        elif isinstance(system, list):
            text_parts = []
            for block in system:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block["text"])
                elif isinstance(block, str):
                    text_parts.append(block)
            if text_parts:
                messages.append({"role": "system", "content": "\n".join(text_parts)})

    for msg in body.get("messages", []):
        role = msg["role"]
        content = msg.get("content", "")

        if isinstance(content, list):
            text_parts = []
            tool_calls_data = []
            tool_results = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_use":
                        tool_calls_data.append({
                            "id": block.get("id", ""),
                            "type": "function",
                            "function": {
                                "name": block.get("name", ""),
                                "arguments": json.dumps(block.get("input", {}))
                            }
                        })
                    elif block.get("type") == "tool_result":
                        tool_id = block.get("tool_use_id", "")
                        result_content = block.get("content", "")
                        if isinstance(result_content, list):
                            result_parts = []
                            for rb in result_content:
                                if isinstance(rb, dict) and rb.get("type") == "text":
                                    result_parts.append(rb.get("text", ""))
                                elif isinstance(rb, str):
                                    result_parts.append(rb)
                            result_content = "\n".join(result_parts)
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "content": str(result_content) if result_content else ""
                        })

            if tool_results:
                if text_parts or tool_calls_data:
                    assistant_msg = {"role": "assistant", "content": "\n".join(text_parts) if text_parts else None}
                    if tool_calls_data:
                        assistant_msg["tool_calls"] = tool_calls_data
                    messages.append(assistant_msg)
                for tr in tool_results:
                    messages.append(tr)
                continue

            if tool_calls_data:
                messages.append({
                    "role": "assistant",
                    "content": "\n".join(text_parts) if text_parts else None,
                    "tool_calls": tool_calls_data
                })
                continue
            content = "\n".join(text_parts) if text_parts else ""

        if content is not None:
            messages.append({"role": role, "content": content})

    tools = None
    if body.get("tools"):
        tools = []
        for tool in body["tools"]:
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {})
                }
            })

    result = {
        "model": body.get("model", DEFAULT_MODEL),
        "messages": messages,
        "max_tokens": body.get("max_tokens", 32768),
        "stream": body.get("stream", False),
    }

    if tools:
        result["tools"] = tools

    if body.get("temperature") is not None:
        result["temperature"] = body["temperature"]
    if body.get("top_p") is not None:
        result["top_p"] = body["top_p"]
    if body.get("stop_sequences"):
        result["stop"] = body["stop_sequences"]

    return result


def openai_to_anthropic(response_data: dict, request_model: str) -> dict:
    content = []
    has_tool_use = False

    for choice in response_data.get("choices", []):
        msg = choice.get("message", {})
        text = msg.get("content")
        if text:
            content.append({"type": "text", "text": text})

        for tc in msg.get("tool_calls", []):
            has_tool_use = True
            func = tc.get("function", {})
            try:
                inp = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                inp = {}
            content.append({
                "type": "tool_use",
                "id": tc.get("id", ""),
                "name": func.get("name", ""),
                "input": inp
            })

    if content and content[0]["type"] == "tool_use":
        content.insert(0, {"type": "text", "text": ""})

    if not content:
        content = [{"type": "text", "text": ""}]

    usage = response_data.get("usage", {})
    return {
        "id": response_data.get("id", ""),
        "type": "message",
        "role": "assistant",
        "model": request_model,
        "content": content,
        "stop_reason": "tool_use" if has_tool_use else "end_turn",
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        }
    }


async def stream_openai_as_anthropic(body: dict, request_model: str):
    headers = {
        "Authorization": f"Bearer {NIM_API_KEY}",
        "Content-Type": "application/json",
    }

    msg_id = f"msg_{os.getpid()}_{id(body)}"
    max_retries = 10
    base_delay = 2.0

    msg_started = False
    block_index = 0
    current_block_type = None
    current_tool_calls = {}
    has_tool_use = False
    output_tokens = 0

    async def do_stream():
        nonlocal msg_started, block_index, current_block_type, current_tool_calls, has_tool_use, output_tokens

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=600) as client:
                    async with client.stream("POST", f"{NIM_BASE_URL}/chat/completions", json=body, headers=headers) as resp:
                        if resp.status_code == 429:
                            delay = base_delay * (2 ** attempt)
                            logger.warning("Rate limited (429). Retrying in %ss... (Attempt %s/%s)", delay, attempt + 1, max_retries)
                            await asyncio.sleep(delay)
                            continue

                        if resp.status_code != 200:
                            error_text = await resp.aread()
                            logger.error("NIM API error %s: %s", resp.status_code, error_text)
                            if not msg_started:
                                yield f"event: message_start\ndata: {json.dumps({'type': 'message_start', 'message': {'id': msg_id, 'type': 'message', 'role': 'assistant', 'model': request_model, 'content': [], 'stop_reason': None, 'stop_sequence': None, 'usage': {'input_tokens': 0, 'output_tokens': 0}}})}\n\n"
                                msg_started = True

                            yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': block_index, 'content_block': {'type': 'text', 'text': ''}})}\n\n"
                            yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': block_index, 'delta': {'type': 'text_delta', 'text': f'API Error: {resp.status_code} - {error_text.decode()}'}})}\n\n"
                            yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': block_index})}\n\n"
                            return

                        if not msg_started:
                            yield f"event: message_start\ndata: {json.dumps({'type': 'message_start', 'message': {'id': msg_id, 'type': 'message', 'role': 'assistant', 'model': request_model, 'content': [], 'stop_reason': None, 'stop_sequence': None, 'usage': {'input_tokens': 0, 'output_tokens': 0}}})}\n\n"
                            msg_started = True

                        async for line in resp.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                            except json.JSONDecodeError:
                                continue

                            if chunk.get("usage"):
                                usage = chunk["usage"]
                                output_tokens = usage.get("completion_tokens", output_tokens)

                            for choice in chunk.get("choices", []):
                                delta = choice.get("delta", {})

                                reasoning = delta.get("reasoning_content") or delta.get("reasoning")
                                if reasoning:
                                    if current_block_type != "thinking":
                                        if current_block_type is not None:
                                            yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': block_index})}\n\n"
                                            block_index += 1

                                        current_block_type = "thinking"
                                        yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': block_index, 'content_block': {'type': 'thinking', 'thinking': ''}})}\n\n"

                                    yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': block_index, 'delta': {'type': 'thinking_delta', 'thinking': reasoning}})}\n\n"
                                    continue

                                tool_calls_delta = delta.get("tool_calls")
                                if tool_calls_delta:
                                    for tc in tool_calls_delta:
                                        tc_index = tc.get("index", 0)
                                        if tc_index not in current_tool_calls:
                                            has_tool_use = True
                                            if current_block_type in ["thinking", "text"]:
                                                yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': block_index})}\n\n"
                                                block_index += 1

                                            current_block_type = "tool_use"
                                            func = tc.get("function", {})
                                            tc_id = tc.get("id", f"call_{tc_index}")
                                            tc_name = func.get("name", "")
                                            current_tool_calls[tc_index] = {"id": tc_id, "name": tc_name, "arguments": ""}
                                            yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': block_index, 'content_block': {'type': 'tool_use', 'id': tc_id, 'name': tc_name, 'input': {}}})}\n\n"

                                        if "function" in tc and tc["function"].get("arguments"):
                                            current_tool_calls[tc_index]["arguments"] += tc["function"]["arguments"]
                                            yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': block_index, 'delta': {'type': 'input_json_delta', 'partial_json': tc['function']['arguments']}})}\n\n"
                                    continue

                                text = delta.get("content")
                                if text:
                                    if current_block_type != "text":
                                        if current_block_type in ["thinking", "tool_use"]:
                                            yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': block_index})}\n\n"
                                            block_index += 1

                                        current_block_type = "text"
                                        yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': block_index, 'content_block': {'type': 'text', 'text': ''}})}\n\n"

                                    yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': block_index, 'delta': {'type': 'text_delta', 'text': text}})}\n\n"

                        return

            except Exception as e:
                logger.exception("Stream error attempt %s: %s", attempt + 1, e)
                if attempt == max_retries - 1:
                    if not msg_started:
                        yield f"event: message_start\ndata: {json.dumps({'type': 'message_start', 'message': {'id': msg_id, 'type': 'message', 'role': 'assistant', 'model': request_model, 'content': [], 'usage': {'input_tokens': 0, 'output_tokens': 0}}})}\n\n"

                    if current_block_type != "text":
                        if current_block_type is not None:
                            yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': block_index})}\n\n"
                            block_index += 1
                        yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': block_index, 'content_block': {'type': 'text', 'text': ''}})}\n\n"
                    yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': block_index, 'delta': {'type': 'text_delta', 'text': f'\\nProxy error after {max_retries} attempts: {str(e)}'}})}\n\n"
                else:
                    await asyncio.sleep(base_delay * (2 ** attempt))

    async for event in do_stream():
        yield event

    if current_block_type is not None:
        yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': block_index})}\n\n"

    yield f"event: message_delta\ndata: {json.dumps({'type': 'message_delta', 'delta': {'stop_reason': 'tool_use' if has_tool_use else 'end_turn', 'stop_sequence': None}, 'usage': {'output_tokens': output_tokens}})}\n\n"
    yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"


@app.post("/v1/messages")
async def messages(request: Request):
    body = await request.json()
    request_model = body.get("model", DEFAULT_MODEL)

    openai_body = anthropic_to_openai(body)

    headers = {
        "Authorization": f"Bearer {NIM_API_KEY}",
        "Content-Type": "application/json",
    }

    if body.get("stream"):
        return StreamingResponse(
            stream_openai_as_anthropic(openai_body, request_model),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    max_retries = 5
    base_delay = 1.0
    async with httpx.AsyncClient(timeout=180) as client:
        for attempt in range(max_retries):
            resp = await client.post(f"{NIM_BASE_URL}/chat/completions", json=openai_body, headers=headers)

            if resp.status_code == 429:
                delay = base_delay * (2 ** attempt)
                logger.warning("Rate limited (429). Retrying in %ss... (Attempt %s/%s)", delay, attempt + 1, max_retries)
                await asyncio.sleep(delay)
                continue

            if resp.status_code != 200:
                logger.error("NIM API error %s: %s", resp.status_code, resp.text)
                if attempt == max_retries - 1:
                    return JSONResponse(
                        {"type": "error", "error": {"type": "api_error", "message": f"NIM API returned {resp.status_code}: {resp.text}"}},
                        status_code=resp.status_code
                    )
                await asyncio.sleep(base_delay * (2 ** attempt))
                continue

            return JSONResponse(openai_to_anthropic(resp.json(), request_model))


@app.get("/v1/models")
async def list_models():
    headers = {"Authorization": f"Bearer {NIM_API_KEY}"}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{NIM_BASE_URL}/models", headers=headers)
        return JSONResponse(resp.json())


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8742
    uvicorn.run(app, host="127.0.0.1", port=port)
