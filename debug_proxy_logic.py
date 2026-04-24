import json

def clean_messages_for_nim(messages):
    if not messages: return []
    step1 = []
    for msg in messages:
        role, content = msg.get("role"), msg.get("content")
        # 识别 tool_result
        is_tool_result = isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content)
        actual_role = "tool" if is_tool_result else role
        
        # 剔除空块
        if isinstance(content, list):
            content = [b for b in content if not (isinstance(b, dict) and b.get("type") == "text" and not b.get("text", "").strip())]
        
        if content:
            step1.append({"role": actual_role, "content": content})

    # 合并连续相同角色
    final_messages = []
    for msg in step1:
        if final_messages and final_messages[-1]["role"] == msg["role"] and msg["role"] != "tool":
            curr, nxt = final_messages[-1]["content"], msg["content"]
            if isinstance(curr, list) and isinstance(nxt, list):
                final_messages[-1]["content"] = curr + nxt
            elif isinstance(curr, str) and isinstance(nxt, str):
                final_messages[-1]["content"] = curr + "\n\n" + nxt
            else:
                final_messages[-1]["content"] = [curr if isinstance(curr, dict) else {"type":"text","text":str(curr)}, 
                                               nxt if isinstance(nxt, dict) else {"type":"text","text":str(nxt)}]
        else:
            final_messages.append(msg)
    return final_messages

# 复杂场景模拟
test_messages = [
    {"role": "user", "content": "查一下天气"},
    {"role": "assistant", "content": [{"type": "tool_use", "id": "call_1", "name": "get_weather", "input": {"city": "Shanghai"}}]},
    {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "call_1", "content": "晴天"}]},
    {"role": "user", "content": "再查一下北京的"}, # 这里的连续 user 是 NIM 最讨厌的
    {"role": "user", "content": [{"type": "text", "text": ""}]} # 这种空消息也会导致 index 错误
]

cleaned = clean_messages_for_nim(test_messages)
print(f"Original Count: {len(test_messages)}")
print(f"Cleaned Count: {len(cleaned)}")
for i, m in enumerate(cleaned):
    print(f"[{i}] {m['role']}: {json.dumps(m['content'], ensure_ascii=False)[:60]}...")

# 检查是否满足 OpenAI 交替原则
roles = [m['role'] for m in cleaned]
print(f"\nRole sequence: {' -> '.join(roles)}")
