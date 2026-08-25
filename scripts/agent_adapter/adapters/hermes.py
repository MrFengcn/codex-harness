#!/usr/bin/env python3
"""
Codex Harness — Hermes Agent 适配器

Hermes Agent 的适配器实现。

Python 兼容性: 3.6+
"""

from typing import List, Dict, Any, Optional
from agent_adapter.interface import (
    MemoryInterface,
    ContextInterface,
    ToolInterface,
    ConfigInterface,
    AgentAdapter,
)


# ============================================================================
# Hermes 记忆实现
# ============================================================================

class HermesMemory(MemoryInterface):
    """Hermes 记忆实现"""

    def __init__(self):
        """初始化 Hermes 记忆"""
        self.store_dict: Dict[str, Any] = {}

    def store(self, key: str, value: Any) -> bool:
        """存储记忆"""
        self.store_dict[key] = value
        return True

    def retrieve(self, key: str) -> Optional[Any]:
        """检索记忆"""
        return self.store_dict.get(key)

    def search(self, query: str) -> List[Any]:
        """搜索记忆"""
        results = []
        for key, value in self.store_dict.items():
            if query.lower() in str(key).lower() or query.lower() in str(value).lower():
                results.append(value)
        return results

    def delete(self, key: str) -> bool:
        """删除记忆"""
        if key in self.store_dict:
            del self.store_dict[key]
            return True
        return False

    def list_keys(self) -> List[str]:
        """列出所有键"""
        return list(self.store_dict.keys())


# ============================================================================
# Hermes 上下文实现
# ============================================================================

class HermesContext(ContextInterface):
    """Hermes 上下文实现"""

    def __init__(self):
        """初始化 Hermes 上下文"""
        self.messages: List[Dict[str, Any]] = []

    def get_messages(self) -> List[Dict[str, Any]]:
        """获取所有消息"""
        return self.messages

    def add_message(self, role: str, content: str) -> bool:
        """添加消息"""
        self.messages.append({
            "role": role,
            "content": content,
        })
        return True

    def get_token_count(self) -> int:
        """获取 Token 数量"""
        # 简单估算: 4 字符 = 1 Token
        total_chars = sum(len(m.get("content", "")) for m in self.messages)
        return total_chars // 4

    def clear(self) -> bool:
        """清空上下文"""
        self.messages.clear()
        return True

    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """获取最后一条消息"""
        if self.messages:
            return self.messages[-1]
        return None


# ============================================================================
# Hermes 工具实现
# ============================================================================

class HermesTools(ToolInterface):
    """Hermes 工具实现"""

    def __init__(self):
        """初始化 Hermes 工具"""
        self.tools: Dict[str, Any] = {}

    def list_tools(self) -> List[str]:
        """列出所有工具"""
        return list(self.tools.keys())

    def execute(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """执行工具"""
        tool = self.tools.get(tool_name)
        if tool:
            try:
                return tool(**args)
            except Exception as e:
                return {"error": str(e)}
        return {"error": f"Tool not found: {tool_name}"}

    def register_tool(self, name: str, tool: Any) -> bool:
        """注册工具"""
        self.tools[name] = tool
        return True

    def unregister_tool(self, name: str) -> bool:
        """注销工具"""
        if name in self.tools:
            del self.tools[name]
            return True
        return False

    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取工具信息"""
        if name in self.tools:
            return {"name": name, "type": type(self.tools[name]).__name__}
        return None


# ============================================================================
# Hermes 配置实现
# ============================================================================

class HermesConfig(ConfigInterface):
    """Hermes 配置实现"""

    def __init__(self):
        """初始化 Hermes 配置"""
        self.config: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """设置配置值"""
        self.config[key] = value
        return True

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config.copy()

    def delete(self, key: str) -> bool:
        """删除配置"""
        if key in self.config:
            del self.config[key]
            return True
        return False

    def has(self, key: str) -> bool:
        """检查配置是否存在"""
        return key in self.config


# ============================================================================
# Hermes 适配器
# ============================================================================

class HermesAdapter(AgentAdapter):
    """
    Hermes Agent 适配器。
    对应 Hermes Agent 的功能。
    """

    def __init__(self):
        """初始化 Hermes 适配器"""
        self.memory = HermesMemory()
        self.context = HermesContext()
        self.tools = HermesTools()
        self.config = HermesConfig()

    def get_name(self) -> str:
        """获取 Agent 名称"""
        return "hermes"

    def get_version(self) -> str:
        """获取 Agent 版本"""
        return "0.20.0"

    def get_capabilities(self) -> List[str]:
        """获取 Agent 能力列表"""
        return [
            "terminal",
            "file_read",
            "file_write",
            "memory",
            "skill",
            "cron",
            "delegate",
            "browser",
        ]

    def get_memory(self) -> MemoryInterface:
        """获取记忆接口"""
        return self.memory

    def get_context(self) -> ContextInterface:
        """获取上下文接口"""
        return self.context

    def get_tools(self) -> ToolInterface:
        """获取工具接口"""
        return self.tools

    def get_config(self) -> ConfigInterface:
        """获取配置接口"""
        return self.config
