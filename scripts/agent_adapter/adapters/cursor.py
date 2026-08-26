#!/usr/bin/env python3
"""
Codex Harness — Cursor 适配器

Cursor AI 代码编辑器的适配器实现。
Cursor 是基于 VS Code 的 AI 代码编辑器。

Python 兼容性: 3.6+
"""

from typing import List, Dict, Any, Optional
from agent_adapter.interface import (
    MemoryInterface, ContextInterface, ToolInterface, ConfigInterface, AgentAdapter,
)


class CursorMemory(MemoryInterface):
    def __init__(self):
        self.store_dict: Dict[str, Any] = {}

    def store(self, key: str, value: Any) -> bool:
        self.store_dict[key] = value
        return True

    def retrieve(self, key: str) -> Optional[Any]:
        return self.store_dict.get(key)

    def search(self, query: str) -> List[Any]:
        return [v for k, v in self.store_dict.items() if query.lower() in str(k).lower()]

    def delete(self, key: str) -> bool:
        if key in self.store_dict:
            del self.store_dict[key]
            return True
        return False

    def list_keys(self) -> List[str]:
        return list(self.store_dict.keys())


class CursorContext(ContextInterface):
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []

    def get_messages(self) -> List[Dict[str, Any]]:
        return self.messages

    def add_message(self, role: str, content: str) -> bool:
        self.messages.append({"role": role, "content": content})
        return True

    def get_token_count(self) -> int:
        return sum(len(m.get("content", "")) for m in self.messages) // 4

    def clear(self) -> bool:
        self.messages.clear()
        return True

    def get_last_message(self) -> Optional[Dict[str, Any]]:
        return self.messages[-1] if self.messages else None


class CursorTools(ToolInterface):
    def __init__(self):
        self.tools: Dict[str, Any] = {}

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())

    def execute(self, tool_name: str, args: Dict[str, Any]) -> Any:
        tool = self.tools.get(tool_name)
        if tool:
            try:
                return tool(**args)
            except Exception as e:
                return {"error": str(e)}
        return {"error": f"Tool not found: {tool_name}"}

    def register_tool(self, name: str, tool: Any) -> bool:
        self.tools[name] = tool
        return True

    def unregister_tool(self, name: str) -> bool:
        if name in self.tools:
            del self.tools[name]
            return True
        return False

    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        return {"name": name, "type": type(self.tools[name]).__name__} if name in self.tools else None


class CursorConfig(ConfigInterface):
    def __init__(self):
        self.config: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        self.config[key] = value
        return True

    def get_all(self) -> Dict[str, Any]:
        return self.config.copy()

    def delete(self, key: str) -> bool:
        if key in self.config:
            del self.config[key]
            return True
        return False

    def has(self, key: str) -> bool:
        return key in self.config


class CursorAdapter(AgentAdapter):
    """Cursor AI 代码编辑器适配器"""
    def __init__(self):
        self.memory = CursorMemory()
        self.context = CursorContext()
        self.tools = CursorTools()
        self.config = CursorConfig()

    def get_name(self) -> str:
        return "cursor"

    def get_version(self) -> str:
        return "0.1.0"

    def get_capabilities(self) -> List[str]:
        return [
            "code_completion", "code_generation", "code_explanation",
            "refactoring", "debugging", "terminal", "file_read", "file_write",
            "vscode_extension", "ai_chat", "inline_edit",
        ]

    def get_memory(self) -> MemoryInterface:
        return self.memory

    def get_context(self) -> ContextInterface:
        return self.context

    def get_tools(self) -> ToolInterface:
        return self.tools

    def get_config(self) -> ConfigInterface:
        return self.config
