#!/usr/bin/env python3
"""
Codex Harness — Agent 适配器管理器

统一管理 Agent 适配器的注册、发现和配置。

Python 兼容性: 3.6+
"""

from typing import List, Dict, Any, Optional
from agent_adapter.interface import AgentAdapter
from agent_adapter.registry import AgentAdapterRegistry, get_global_registry


class AgentAdapterManager:
    """
    Agent 适配器管理器。
    统一管理适配器的注册、发现和配置。

    功能:
    - 注册适配器
    - 发现适配器
    - 自动检测
    - 配置管理
    - 兼容性检查
    """

    def __init__(self):
        """初始化适配器管理器"""
        self.registry = get_global_registry()
        self._auto_register()

    def _auto_register(self):
        """自动注册所有已知适配器"""
        try:
            from agent_adapter.adapters import (
                HermesAdapter, OpenClawAdapter, LangChainAdapter, AutoGPTAdapter,
                MetaGPTAdapter, CrewAIAdapter, BabyAGIAdapter, AgentGPTAdapter,
            )

            adapters = [
                HermesAdapter(), OpenClawAdapter(), LangChainAdapter(), AutoGPTAdapter(),
                MetaGPTAdapter(), CrewAIAdapter(), BabyAGIAdapter(), AgentGPTAdapter(),
            ]

            for adapter in adapters:
                self.registry.register(adapter)
        except Exception:
            pass

    def get_adapter(self, name: str) -> Optional[AgentAdapter]:
        """
        获取适配器。

        参数:
            name: 适配器名称

        返回:
            AgentAdapter 实例
        """
        return self.registry.get(name)

    def get_current_adapter(self) -> Optional[AgentAdapter]:
        """
        获取当前 Agent 的适配器。

        返回:
            AgentAdapter 实例
        """
        return self.registry.auto_detect()

    def list_adapters(self) -> List[str]:
        """
        列出所有适配器。

        返回:
            适配器名称列表
        """
        return self.registry.list_adapters()

    def check_compatibility(
        self,
        adapter_name: str,
        required_capabilities: List[str],
    ) -> bool:
        """
        检查适配器兼容性。

        参数:
            adapter_name: 适配器名称
            required_capabilities: 所需能力列表

        返回:
            True 如果兼容
        """
        adapter = self.registry.get(adapter_name)
        if not adapter:
            return False
        return adapter.is_compatible(required_capabilities)

    def get_adapter_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取适配器信息。

        参数:
            name: 适配器名称

        返回:
            适配器信息字典
        """
        adapter = self.registry.get(name)
        if not adapter:
            return None

        return {
            "name": adapter.get_name(),
            "version": adapter.get_version(),
            "capabilities": adapter.get_capabilities(),
        }

    def get_all_info(self) -> List[Dict[str, Any]]:
        """
        获取所有适配器信息。

        返回:
            适配器信息列表
        """
        info = []
        for name in self.registry.list_adapters():
            adapter_info = self.get_adapter_info(name)
            if adapter_info:
                info.append(adapter_info)
        return info

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息。

        返回:
            统计字典
        """
        adapters = self.get_all_info()
        return {
            "total": len(adapters),
            "adapters": [a["name"] for a in adapters],
            "current": self.get_current_adapter().get_name() if self.get_current_adapter() else None,
        }


# ============================================================================
# 全局管理器
# ============================================================================

_global_manager: Optional[AgentAdapterManager] = None


def get_global_adapter_manager() -> AgentAdapterManager:
    """
    获取全局适配器管理器。

    返回:
        全局适配器管理器实例
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = AgentAdapterManager()
    return _global_manager
