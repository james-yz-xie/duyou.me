#!/usr/bin/env python3
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

def translate_anthropic_to_openai(messages):
    """
    Manually translates Anthropic Messages to OpenAI Chat Completion format.
    Ensures:
    1. tool_use -> tool_calls
    2. tool_result -> role: tool
    3. Merged consecutive same-role messages.
    """
    openai_msgs = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        
        if isinstance(content, str):
            openai_msgs.append({"role": role, "content": content})
            continue
            
        if isinstance(content, list):
            text_parts = []
            tool_calls = []
            
            for block in content:
                b_type = block.get("type")
                if b_type == "text":
                    if block.get("text", "").strip():
                        text_parts.append(block["text"])
                elif b_type == "tool_use":
                    tool_calls.append({
                        "id": block.get("id"),
                        "type": "function",
                        "function": {
                            "name": block.get("name"),
                            "arguments": json.dumps(block.get("input", {}))
                        }
                    })
                elif b_type == "tool_result":
                    # Flush preceding assistant content if any
                    if text_parts or tool_calls:
                        tmp_msg = {"role": role, "content": "\n".join(text_parts) if text_parts else None}
                        if tool_calls: tmp_msg["tool_calls"] = tool_calls
                        openai_msgs.append(tmp_msg)
                        text_parts, tool_calls = [], []
                    
                    openai_msgs.append({
                        "role": "tool",
                        "tool_call_id": block.get("tool_use_id"),
                        "content": str(block.get("content", ""))
                    })
            
            if text_parts or tool_calls:
                new_msg = {"role": role, "content": "\n".join(text_parts) if text_parts else ""}
                if tool_calls: new_msg["tool_calls"] = tool_calls
                openai_msgs.append(new_msg)

    # Final pass: merge consecutive same-role messages
    final = []
    for m in openai_msgs:
        if final and final[-1]["role"] == m["role"] and m["role"] != "tool":
            if m.get("content"):
                if final[-1].get("content"):
                    final[-1]["content"] += "\n\n" + m["content"]
                else:
                    final[-1]["content"] = m["content"]
            if m.get("tool_calls"):
                if "tool_calls" not in final[-1]: final[-1]["tool_calls"] = []
                final[-1]["tool_calls"].extend(m["tool_calls"])
        else:
            final.append(m)
    return final

# Configuration
CONFIG_PATH = os.environ.get("LITELLM_CONFIG", "litellm-config.yaml")
NIM_API_KEY = os.environ.get("NVIDIA_NIM_API_KEY", "")
DEFAULT_MODEL = os.environ.get("NIM_DEFAULT_MODEL", "nvidia/llama-3.1-nemotron-ultra-253b-v1")

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent-gateway")

app = FastAPI()

def load_router(config_path: str) -> Router:
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    l_set = config.get("litellm_settings", {})
    r_set = config.get("router_settings", {})
    if "drop_params" in l_set: litellm.drop_params = bool(l_set["drop_params"])
    return Router(
        model_list=config.get("model_list", []),
        num_retries=l_set.get("num_retries"),
        set_verbose=l_set.get("set_verbose", False),
        routing_strategy=r_set.get("routing_strategy", "simple-shuffle")
    )

router = load_router(CONFIG_PATH)

def safe_json_loads(s: str) -> Dict[str, Any]:
    if not s or not s.strip(): return {}
    try:
        clean_s = s.strip()
        if clean_s.startswith("```json"): clean_s = clean_s[7:-3].strip()
        elif clean_s.startswith("```"): clean_s = clean_s[3:-3].strip()
        return json.loads(clean_s)
    except: return {}

def sanitize_args(args, schema):
    if not schema: return args
    props = schema.get("properties", {})
    sanitized = {k: v for k, v in args.items() if k in props}
    for r in schema.get("required", []):
        if r not in sanitized: sanitized[r] = None
    return sanitized

@app.post("/v1/messages")
async def messages(request: Request):
    body = await request.json()
    model = body.get("model", DEFAULT_MODEL)
    stream = body.get("stream", False)
    tool_schemas = {t["name"]: t.get("input_schema", {}) for t in body.get("tools", [])}
    
    try:
        msgs = translate_anthropic_to_openai(body.get("messages", []))
        system = body.get("system")
        if system:
            sys_text = system if isinstance(system, str) else "\n".join([b["text"] if isinstance(b, dict) else b for b in system])
            msgs.insert(0, {"role": "system", "content": sys_text})

        l_kwargs = {
            "model": model, "messages": msgs, "max_tokens": body.get("max_tokens", 4096),
            "stream": stream, "temperature": body.get("temperature", 1.0), "top_p": body.get("top_p", 1.0)
        }
        
        # Only add tools if the model supports them (check against known compatible models)
        tool_compatible_models = ["nvidia/llama-3.1-nemotron-ultra-253b-v1", "qwen/qwen3-coder-480b-a35b-instruct"]
        if body.get("tools") and any(model.startswith(m) for m in tool_compatible_models):
            try:
                l_kwargs["tools"] = [{"type": "function", "function": {"name": t["name"], "description": t.get("description", ""), "parameters": t.get("input_schema", {})}} for t in body["tools"]]
            except Exception:
                # If tools formatting fails, proceed without tools
                pass

        if stream:
            return StreamingResponse(stream_handler(model, l_kwargs, tool_schemas), media_type="text/event-stream")
        else:
            resp = await router.acompletion(**l_kwargs)
            return JSONResponse(process_sync_response(resp, model, tool_schemas))
    except Exception as e:
        logger.exception(f"Error: {e}")
        # Try fallback if this was a tool calling error
        if "tools" in str(e) or "404" in str(e) or "NotFound" in str(e):
            logger.info("Attempting fallback without tools...")
            try:
                l_kwargs_no_tools = {k: v for k, v in l_kwargs.items() if k != "tools"}
                resp = await router.acompletion(**l_kwargs_no_tools)
                return JSONResponse(process_sync_response(resp, model, {}))
            except Exception as fallback_error:
                logger.exception(f"Fallback also failed: {fallback_error}")
        
        return JSONResponse({"type": "error", "error": {"type": "api_error", "message": str(e)}}, status_code=500)

async def stream_handler(model, kwargs, tool_schemas):
    try:
        response_stream = await router.acompletion(**kwargs)
        yield f"event: message_start\ndata: {json.dumps({'type': 'message_start', 'message': {'id': 'msg_1', 'type': 'message', 'role': 'assistant', 'model': model, 'content': [], 'usage': {'input_tokens': 0, 'output_tokens': 0}}})}\n\n"
        b_idx, cur_tc = 0, None
        async for chunk in response_stream:
            if not chunk.choices: continue
            delta = chunk.choices[0].delta
            if delta.content:
                yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': b_idx, 'content_block': {'type': 'text', 'text': ''}})}\n\n"
                yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': b_idx, 'delta': {'type': 'text_delta', 'text': delta.content}})}\n\n"
                yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': b_idx})}\n\n"
                b_idx += 1
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    if tc.function.name:
                        cur_tc = {"id": tc.id, "name": tc.function.name, "input_raw": ""}
                        yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': b_idx, 'content_block': {'type': 'tool_use', 'id': tc.id, 'name': tc.function.name, 'input': {}}})}\n\n"
                    if tc.function.arguments:
                        cur_tc["input_raw"] += tc.function.arguments
                        yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': b_idx, 'delta': {'type': 'input_json_delta', 'partial_json': tc.function.arguments}})}\n\n"
            if chunk.choices[0].finish_reason and cur_tc:
                yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': b_idx})}\n\n"
                b_idx += 1
                cur_tc = None
        yield f"event: message_delta\ndata: {json.dumps({'type': 'message_delta', 'delta': {'stop_reason': 'end_turn', 'stop_sequence': None}, 'usage': {'output_tokens': 0}})}\n\n"
        yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'type': 'error', 'error': {'type': 'api_error', 'message': str(e)}})}\n\n"

def process_sync_response(resp, req_model, tool_schemas):
    msg = resp.choices[0].message
    content = [{"type": "text", "text": msg.content}] if msg.content else []
    if msg.tool_calls:
        for tc in msg.tool_calls:
            args = safe_json_loads(tc.function.arguments)
            content.append({"type": "tool_use", "id": tc.id, "name": tc.function.name, "input": sanitize_args(args, tool_schemas.get(tc.function.name, {}))})
    if content and content[0]["type"] == "tool_use": content.insert(0, {"type": "text", "text": ""})
    return {"id": resp.id, "type": "message", "role": "assistant", "model": req_model, "content": content, "stop_reason": "tool_use" if msg.tool_calls else "end_turn", "stop_sequence": None, "usage": {"input_tokens": resp.usage.prompt_tokens, "output_tokens": resp.usage.completion_tokens}}

@app.get("/ping")
async def ping(): return "pong"

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PROXY_PORT", 8742)))
