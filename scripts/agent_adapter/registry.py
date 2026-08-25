#!/usr/bin/env python3
"""
Codex Harness — Agent 适配器注册表

管理所有 Agent 适配器。

Python 兼容性: 3.6+
"""

from typing import List, Dict, Any, Optional
from agent_adapter.interface import AgentAdapter


class AgentAdapterRegistry:
    """
    Agent 适配器注册表。
    管理所有 Agent 适配器。

    功能:
    - 注册适配器
    - 发现适配器
    - 自动检测
    """

    def __init__(self):
        """初始化适配器注册表"""
        self.adapters: Dict[str, AgentAdapter] = {}

    def register(self, adapter: AgentAdapter) -> bool:
        """
        注册适配器。

        参数:
            adapter: Agent 适配器实例

        返回:
            True 如果注册成功
        """
        name = adapter.get_name()
        self.adapters[name] = adapter
        return True

    def unregister(self, name: str) -> bool:
        """
        注销适配器。

        参数:
            name: 适配器名称

        返回:
            True 如果注销成功
        """
        if name in self.adapters:
            del self.adapters[name]
            return True
        return False

    def get(self, name: str) -> Optional[AgentAdapter]:
        """
        获取适配器。

        参数:
            name: 适配器名称

        返回:
            AgentAdapter 实例
        """
        return self.adapters.get(name)

    def list_adapters(self) -> List[str]:
        """
        列出所有适配器。

        返回:
            适配器名称列表
        """
        return list(self.adapters.keys())

    def auto_detect(self) -> Optional[AgentAdapter]:
        """
        自动检测当前 Agent。

        返回:
            检测到的适配器，如果没有返回 None
        """
        # 检测 Hermes
        try:
            import hermes_tools
            hermes_adapter = self.adapters.get('hermes')
            if hermes_adapter:
                return hermes_adapter
        except ImportError:
            pass

        # 检测 OpenClaw
        try:
            import openclaw
            openclaw_adapter = self.adapters.get('openclaw')
            if openclaw_adapter:
                return openclaw_adapter
        except ImportError:
            pass

        # 检测 LangChain
        try:
            import langchain
            langchain_adapter = self.adapters.get('langchain')
            if langchain_adapter:
                return langchain_adapter
        except ImportError:
            pass

        return None

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息。

        返回:
            统计字典
        """
        return {
            "total": len(self.adapters),
            "adapters": list(self.adapters.keys()),
        }


# ============================================================================
# 全局注册表
# ============================================================================

_global_registry: Optional[AgentAdapterRegistry] = None


def get_global_registry() -> AgentAdapterRegistry:
    """
    获取全局适配器注册表。

    返回:
        全局适配器注册表实例
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentAdapterRegistry()
    return _global_registry
