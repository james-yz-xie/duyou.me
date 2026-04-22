#!/usr/bin/env python3
"""
Anthropic-to-OpenAI proxy for NVIDIA NIM API.
Translates Claude Code's Anthropic Messages API calls to NVIDIA's OpenAI-compatible format.
"""

import json
import sys
import os
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn
import httpx

NIM_BASE_URL = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY = os.environ.get("NVIDIA_NIM_API_KEY", "")
DEFAULT_MODEL = os.environ.get("NIM_DEFAULT_MODEL", "qwen/qwen3-coder-480b-a35b-instruct")

app = FastAPI()


def anthropic_to_openai(body: dict) -> dict:
    """Convert Anthropic Messages API request to OpenAI Chat Completions format."""
    messages = []

    # Handle system prompt
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

    # Handle messages
    for msg in body.get("messages", []):
        role = msg["role"]
        content = msg.get("content", "")

        # Convert content blocks to text
        if isinstance(content, list):
            text_parts = []
            tool_calls_data = []
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
                        # tool_result comes as a user message with tool role content
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
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "content": result_content
                        })
                        continue
            if tool_calls_data:
                messages.append({"role": "assistant", "content": "\n".join(text_parts) if text_parts else None, "tool_calls": tool_calls_data})
                continue
            content = "\n".join(text_parts) if text_parts else ""

        if content or role == "assistant":
            messages.append({"role": role, "content": content})

    # Convert tools
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
        "max_tokens": body.get("max_tokens", 8192),
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
    """Convert OpenAI Chat Completions response to Anthropic Messages API format."""
    content = []
    tool_uses = []

    for choice in response_data.get("choices", []):
        msg = choice.get("message", {})
        text = msg.get("content")
        if text:
            content.append({"type": "text", "text": text})

        # Handle tool calls
        for tc in msg.get("tool_calls", []):
            func = tc.get("function", {})
            try:
                inp = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                inp = {}
            tool_uses.append({
                "type": "tool_use",
                "id": tc.get("id", ""),
                "name": func.get("name", ""),
                "input": inp
            })

    content.extend(tool_uses)

    usage = response_data.get("usage", {})

    return {
        "id": response_data.get("id", ""),
        "type": "message",
        "role": "assistant",
        "model": request_model,
        "content": content if content else [{"type": "text", "text": ""}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        }
    }


async def stream_openai_as_anthropic(body: dict, request_model: str):
    """Stream OpenAI SSE events, converting to Anthropic SSE format."""
    headers = {
        "Authorization": f"Bearer {NIM_API_KEY}",
        "Content-Type": "application/json",
    }

    msg_id = f"msg_{id(body)}"
    input_tokens = 0

    # Send message_start
    yield f"event: message_start\ndata: {json.dumps({'type': 'message_start', 'message': {'id': msg_id, 'type': 'message', 'role': 'assistant', 'model': request_model, 'content': [], 'stop_reason': None, 'stop_sequence': None, 'usage': {'input_tokens': 0, 'output_tokens': 0}}})}\n\n"

    # Send content_block_start for text
    block_index = 0
    yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': block_index, 'content_block': {'type': 'text', 'text': ''}})}\n\n"

    current_tool_calls = {}
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", f"{NIM_BASE_URL}/chat/completions", json=body, headers=headers) as resp:
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

                # Track usage
                if chunk.get("usage"):
                    input_tokens = chunk["usage"].get("prompt_tokens", 0)

                for choice in chunk.get("choices", []):
                    delta = choice.get("delta", {})

                    # Handle tool calls in stream
                    for tc in delta.get("tool_calls", []):
                        tc_index = tc.get("index", 0)
                        if tc_index not in current_tool_calls:
                            # Close text block if still open
                            yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': block_index})}\n\n"
                            block_index += 1

                            # Start tool_use block
                            func = tc.get("function", {})
                            current_tool_calls[tc_index] = {
                                "id": tc.get("id", ""),
                                "name": func.get("name", ""),
                                "arguments": ""
                            }
                            yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': block_index, 'content_block': {'type': 'tool_use', 'id': tc.get('id', ''), 'name': func.get('name', ''), 'input': {}}})}\n\n"

                        # Append tool call arguments
                        if "function" in tc and tc["function"].get("arguments"):
                            current_tool_calls[tc_index]["arguments"] += tc["function"]["arguments"]
                            yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': block_index, 'delta': {'type': 'input_json_delta', 'partial_json': tc['function']['arguments']}})}\n\n"

                    # Handle text content
                    text = delta.get("content")
                    if text:
                        yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': block_index, 'delta': {'type': 'text_delta', 'text': text}})}\n\n"

    # Close last content block
    yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': block_index})}\n\n"

    # Send message_delta with stop
    msg_delta = {'type': 'message_delta', 'delta': {'stop_reason': 'end_turn', 'stop_sequence': None}, 'usage': {'output_tokens': 0}}
    yield f"event: message_delta\ndata: {json.dumps(msg_delta)}\n\n"
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
    else:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{NIM_BASE_URL}/chat/completions", json=openai_body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return JSONResponse(openai_to_anthropic(data, request_model))


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
    print(f"NVIDIA NIM Proxy starting on port {port}")
    print(f"  NIM Base URL: {NIM_BASE_URL}")
    print(f"  Default Model: {DEFAULT_MODEL}")
    print(f"  API Key: {'*' * 8}{NIM_API_KEY[-4:]}" if len(NIM_API_KEY) > 4 else "  API Key: not set")
    uvicorn.run(app, host="127.0.0.1", port=port)
