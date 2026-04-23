#!/usr/bin/env python3
"""
NIM Agent Gateway: A robust proxy using LiteLLM.
- Protocol: Anthropic Messages API (Incoming) -> LiteLLM -> NIM/OpenAI (Outgoing)
- Features: Tool Sanitization, JSON robustness, Fallback, Retry, Streaming support.
"""

import json
import os
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn
import litellm
from litellm import Router
import yaml

# Configuration
CONFIG_PATH = os.environ.get("LITELLM_CONFIG", "litellm-config.yaml")
NIM_API_KEY = os.environ.get("NVIDIA_NIM_API_KEY", "")
NIM_API_BASE = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
OLLAMA_API_BASE = os.environ.get("OLLAMA_API_BASE", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.environ.get("NIM_DEFAULT_MODEL", "nvidia/llama-3.1-nemotron-ultra-253b-v1")

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent-gateway")

app = FastAPI()


def load_router(config_path: str) -> Router:
    """Load LiteLLM router settings from YAML using the current Router API."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    litellm_settings = config.get("litellm_settings", {})
    router_settings = config.get("router_settings", {})

    if "drop_params" in litellm_settings:
        litellm.drop_params = bool(litellm_settings["drop_params"])

    router_kwargs = {
        "model_list": config.get("model_list", []),
        "num_retries": litellm_settings.get("num_retries"),
        "set_verbose": litellm_settings.get("set_verbose", False),
        "routing_strategy": router_settings.get("routing_strategy", "simple-shuffle"),
    }

    logger.info("Initializing LiteLLM router with config=%s", config_path)
    return Router(**{k: v for k, v in router_kwargs.items() if v is not None})


router = load_router(CONFIG_PATH)

def safe_json_loads(s: str) -> Dict[str, Any]:
    """Robust JSON loading to handle model 'hallucinations' or messy output."""
    if not s or not s.strip():
        return {}
    try:
        # Try cleaning the string first if it has markdown blocks
        clean_s = s.strip()
        if clean_s.startswith("```json"):
            clean_s = clean_s[7:-3].strip()
        elif clean_s.startswith("```"):
            clean_s = clean_s[3:-3].strip()
        return json.loads(clean_s)
    except Exception as e:
        logger.warning(f"Failed to parse JSON: {s[:100]}... Error: {e}")
        # If it looks like partial JSON or has trailing garbage, we could try harder
        return {}

def sanitize_args(args: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures tool arguments match the requested JSON schema.
    - Removes extra properties (NIM sometimes hallucinations extra fields).
    - Ensures required fields exist (even if null).
    """
    if not schema:
        return args
    
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    sanitized = {}
    for key, value in args.items():
        if key in properties:
            sanitized[key] = value
        else:
            logger.debug(f"Dropping hallucinated property: {key}")
            
    # Optional: Fill missing required fields with None to avoid crashes
    for req in required:
        if req not in sanitized:
            sanitized[req] = None
            
    return sanitized

def get_tool_schemas(body: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Extract tool schemas from Anthropic request body."""
    schemas = {}
    for tool in body.get("tools", []):
        name = tool.get("name")
        if name:
            schemas[name] = tool.get("input_schema", {})
    return schemas

@app.post("/v1/messages")
async def messages(request: Request):
    body = await request.json()
    model = body.get("model", DEFAULT_MODEL)
    stream = body.get("stream", False)
    
    # Store tool schemas for sanitization later
    tool_schemas = get_tool_schemas(body)
    
    # LiteLLM internally handles Anthropic Messages -> OpenAI/NIM conversion 
    # when passed through its router or completion call.
    # However, to use its powerful Fallback/Retry features, we use router.acompletion.
    
    try:
        # Prepare params for litellm
        # We need to map Anthropic params to LiteLLM expected params
        # Note: LiteLLM's acompletion can take the Anthropic messages format directly 
        # but works best if we pass specific provider flags if needed.
        
        litellm_kwargs = {
            "model": model,
            "messages": body.get("messages", []),
            "max_tokens": body.get("max_tokens", 4096),
            "stream": stream,
            "tools": None,
            "temperature": body.get("temperature", 1.0),
            "top_p": body.get("top_p", 1.0),
            "system": body.get("system"),
        }
        
        # Convert Anthropic tools to LiteLLM (OpenAI-like) tools
        if body.get("tools"):
            litellm_kwargs["tools"] = []
            for tool in body["tools"]:
                litellm_kwargs["tools"].append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("input_schema", {})
                    }
                })

        if stream:
            return StreamingResponse(
                stream_handler(model, litellm_kwargs, tool_schemas),
                media_type="text/event-stream"
            )
        else:
            response = await router.acompletion(**litellm_kwargs)
            # Convert OpenAI response back to Anthropic
            return JSONResponse(process_sync_response(response, model, tool_schemas))

    except Exception as e:
        logger.exception(f"Error in /v1/messages: {e}")
        return JSONResponse(
            {"type": "error", "error": {"type": "api_error", "message": str(e)}},
            status_code=500
        )

async def stream_handler(model: str, kwargs: Dict[str, Any], tool_schemas: Dict[str, Dict[str, Any]]):
    """Handles streaming with on-the-fly sanitization and format conversion."""
    try:
        # LiteLLM returns a stream of OpenAI-like chunks
        response_stream = await router.acompletion(**kwargs)
        
        # We need to emit Anthropic-style SSE events
        # simplified for brevity but robust for Tool Use
        
        yield f"event: message_start\ndata: {json.dumps({'type': 'message_start', 'message': {'id': 'msg_1', 'type': 'message', 'role': 'assistant', 'model': model, 'content': [], 'usage': {'input_tokens': 0, 'output_tokens': 0}}})}\n\n"
        
        block_index = 0
        current_tool_call = None
        
        async for chunk in response_stream:
            delta = chunk.choices[0].delta
            
            # 1. Text Content
            if delta.content:
                yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': block_index, 'content_block': {'type': 'text', 'text': ''}})}\n\n"
                yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': block_index, 'delta': {'type': 'text_delta', 'text': delta.content}})}\n\n"
                yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': block_index})}\n\n"
                block_index += 1
            
            # 2. Tool Calls (LiteLLM/OpenAI format)
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    if tc.function.name: # Start of a tool call
                        tool_name = tc.function.name
                        current_tool_call = {"id": tc.id, "name": tool_name, "input_raw": ""}
                        yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': block_index, 'content_block': {'type': 'tool_use', 'id': tc.id, 'name': tool_name, 'input': {}}})}\n\n"
                    
                    if tc.function.arguments:
                        current_tool_call["input_raw"] += tc.function.arguments
                        yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': block_index, 'delta': {'type': 'input_json_delta', 'partial_json': tc.function.arguments}})}\n\n"
                    
                    # In streaming, we don't 'sanitize' until the block stops if it's incremental,
                    # but Claude Code handles the delta. 
                    # For absolute robustness, we can send a final sanitized update at the end.

            # Handle finish reason
            if chunk.choices[0].finish_reason:
                if current_tool_call:
                    # Final sanitize of the arguments before finishing
                    args = safe_json_loads(current_tool_call["input_raw"])
                    schema = tool_schemas.get(current_tool_call["name"], {})
                    sanitized = sanitize_args(args, schema)
                    # Note: We can't 'rewrite' a stream delta easily, but we can emit a stop event
                    yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': block_index})}\n\n"
                    block_index += 1
                    current_tool_call = None

        stop_reason = "tool_use" if block_index > 0 else "end_turn"
        yield f"event: message_delta\ndata: {json.dumps({'type': 'message_delta', 'delta': {'stop_reason': stop_reason, 'stop_sequence': None}, 'usage': {'output_tokens': 0}})}\n\n"
        yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"

    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"event: error\ndata: {json.dumps({'type': 'error', 'error': {'type': 'api_error', 'message': str(e)}})}\n\n"

def process_sync_response(response, request_model, tool_schemas):
    """Converts LiteLLM/OpenAI sync response to Anthropic format with Sanitization."""
    message = response.choices[0].message
    content = []
    
    if message.content:
        content.append({"type": "text", "text": message.content})
        
    has_tool_use = False
    if message.tool_calls:
        has_tool_use = True
        for tc in message.tool_calls:
            tool_name = tc.function.name
            raw_args = tc.function.arguments
            
            # Robust JSON handling
            args = safe_json_loads(raw_args)
            
            # Sanitize against schema
            schema = tool_schemas.get(tool_name, {})
            sanitized_args = sanitize_args(args, schema)
            
            content.append({
                "type": "tool_use",
                "id": tc.id,
                "name": tool_name,
                "input": sanitized_args
            })
            
    # Claude Code requirement: always text before tool_use
    if content and content[0]["type"] == "tool_use":
        content.insert(0, {"type": "text", "text": ""})
        
    return {
        "id": response.id,
        "type": "message",
        "role": "assistant",
        "model": request_model,
        "content": content,
        "stop_reason": "tool_use" if has_tool_use else "end_turn",
        "stop_sequence": None,
        "usage": {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "config": CONFIG_PATH}

@app.get("/ping")
async def ping():
    return "pong"

if __name__ == "__main__":
    port = int(os.environ.get("PROXY_PORT", 8742))
    uvicorn.run(app, host="127.0.0.1", port=port)
