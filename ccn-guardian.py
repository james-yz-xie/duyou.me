#!/usr/bin/env python3
import time
import os
import re
import subprocess
import signal

# 配置路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = "/tmp/nim-proxy.log"
CONFIG_PATH = os.path.join(BASE_DIR, "litellm-config.yaml")
PROXY_SCRIPT = os.path.join(BASE_DIR, "nim-proxy.py")

class ccnGuardian:
    def __init__(self):
        self.last_pos = 0
        print("🛡️  CCN Guardian (Advanced Self-Healer) started.")

    def restart_gateway(self):
        print("↻ Detected critical fix. Restarting CCN Gateway...")
        try:
            # 杀掉旧进程
            pids = subprocess.check_output(["lsof", "-ti", ":8742"]).decode().strip().split('\n')
            for pid in pids:
                if pid: os.kill(int(pid), signal.SIGKILL)
            time.sleep(1)
            # 重新启动
            venv_python = os.path.join(BASE_DIR, ".venv-nim-gateway/bin/python")
            subprocess.Popen([venv_python, PROXY_SCRIPT], 
                             env=os.environ, 
                             stdout=open(LOG_FILE, "a"), 
                             stderr=subprocess.STDOUT)
            print("✅ Gateway code reloaded and service resumed.")
        except Exception as e:
            print(f"❌ Restart failed: {e}")

    def apply_config_fix(self, search, replacement):
        with open(CONFIG_PATH, "r") as f:
            content = f.read()
        if search in content and replacement not in content:
            with open(CONFIG_PATH, "w") as f:
                f.write(content.replace(search, replacement))
            return True
        return False

    def apply_code_patch(self, strategy_id, search_str, replace_str):
        with open(PROXY_SCRIPT, "r") as f:
            content = f.read()
        if search_str in content and replace_str not in content:
            print(f"💉 Healing Code: Applying strategy [{strategy_id}]...")
            with open(PROXY_SCRIPT, "w") as f:
                f.write(content.replace(search_str, replace_str))
            return True
        return False

    def heal(self, line):
        healed = False

        # 策略 A: 自动注入 System Message 合并逻辑
        if "Unsupported parameter: system" in line:
            search = '        litellm_kwargs = {\n            "model": model,\n            "messages": body.get("messages", []),\n            "max_tokens": body.get("max_tokens", 4096),\n            "stream": stream,\n            "tools": None,\n            "temperature": body.get("temperature", 1.0),\n            "top_p": body.get("top_p", 1.0),\n            "system": body.get("system"),\n        }'
            replacement = """        # Auto-Healed: Merging system into messages
        messages = body.get("messages", [])
        system = body.get("system")
        if system:
            if isinstance(system, str):
                messages.insert(0, {"role": "system", "content": system})
            elif isinstance(system, list):
                sys_text = "\\n".join([b["text"] if isinstance(b, dict) else b for b in system])
                messages.insert(0, {"role": "system", "content": sys_text})

        litellm_kwargs = {
            "model": model,
            "messages": messages,
            "max_tokens": body.get("max_tokens", 4096),
            "stream": stream,
            "tools": None,
            "temperature": body.get("temperature", 1.0),
            "top_p": body.get("top_p", 1.0),
        }"""
            if self.apply_code_patch("MERGE_SYSTEM_PROMPT", search, replacement):
                healed = True

        # 策略 B: 自动增加 Fallback 触发器
        if "NotFoundError" in line or "404" in line:
            if self.apply_config_fix('"authentication_error"', '"authentication_error", "not_found_error"'):
                print("🩹 Healing Config: Added not_found_error fallback.")
                healed = True

        # 策略 C: 修复消息格式无效 (Invalid user message / Alternating roles)
        if "Invalid user message" in line or "valid OpenAI chat completion messages" in line:
            clean_func_def = """def clean_messages_for_nim(messages):
    \"\"\"Refines messages for NIM: maps tool roles and merges consecutive roles.\"\"\"
    if not messages: return []
    step1 = []
    for msg in messages:
        role, content = msg.get("role"), msg.get("content")
        is_tool_result = isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content)
        actual_role = "tool" if is_tool_result else role
        if isinstance(content, list):
            content = [b for b in content if not (isinstance(b, dict) and b.get("type") == "text" and not b.get("text", "").strip())]
        if content: step1.append({"role": actual_role, "content": content})
    
    final_messages = []
    for msg in step1:
        if final_messages and final_messages[-1]["role"] == msg["role"] and msg["role"] != "tool":
            curr, nxt = final_messages[-1]["content"], msg["content"]
            if isinstance(curr, list) and isinstance(nxt, list): final_messages[-1]["content"] += nxt
            elif isinstance(curr, str) and isinstance(nxt, str): final_messages[-1]["content"] += "\\n\\n" + nxt
            else: final_messages[-1]["content"] = [curr if isinstance(curr, dict) else {"type":"text","text":str(curr)}, nxt if isinstance(nxt, dict) else {"type":"text","text":str(nxt)}]
        else: final_messages.append(msg)
    return final_messages
"""
            if self.apply_code_patch("DEFINE_ROBUST_CLEAN", "import yaml", "import yaml\n\n" + clean_func_def):
                healed = True
            
            if self.apply_code_patch("CALL_ROBUST_CLEAN", 'messages = body.get("messages", [])', 'messages = clean_messages_for_nim(body.get("messages", []))'):
                healed = True

        if healed:
            self.restart_gateway()

    def watch(self):
        if not os.path.exists(LOG_FILE): open(LOG_FILE, 'w').close()
        while True:
            with open(LOG_FILE, "r") as f:
                f.seek(0, os.SEEK_END)
                if f.tell() < self.last_pos: self.last_pos = 0
                f.seek(self.last_pos)
                lines = f.readlines()
                self.last_pos = f.tell()
                for line in lines:
                    if any(err in line for err in ["ERROR", "Exception", "BadRequestError", "APIConnectionError"]):
                        self.heal(line)
            time.sleep(1)

if __name__ == "__main__":
    guardian = ccnGuardian()
    try:
        guardian.watch()
    except KeyboardInterrupt:
        print("\n👋 Guardian retired.")
