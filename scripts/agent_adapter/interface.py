#!/usr/bin/env python3
"""
Codex Harness — Agent 适配器接口

定义通用 Agent 适配器接口，支持多种 Agent 框架。

Python 兼容性: 3.6+
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


# ============================================================================
# 记忆接口
# ============================================================================

class MemoryInterface(ABC):
    """
    记忆接口。
    定义记忆存储和检索的通用接口。
    """

    @abstractmethod
    def store(self, key: str, value: Any) -> bool:
        """
        存储记忆。

        参数:
            key: 记忆键
            value: 记忆值

        返回:
            True 如果存储成功
        """
        pass

    @abstractmethod
    def retrieve(self, key: str) -> Optional[Any]:
        """
        检索记忆。

        参数:
            key: 记忆键

        返回:
            记忆值，如果不存在返回 None
        """
        pass

    @abstractmethod
    def search(self, query: str) -> List[Any]:
        """
        搜索记忆。

        参数:
            query: 搜索查询

        返回:
            匹配的记忆列表
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        删除记忆。

        参数:
            key: 记忆键

        返回:
            True 如果删除成功
        """
        pass

    @abstractmethod
    def list_keys(self) -> List[str]:
        """
        列出所有记忆键。

        返回:
            键列表
        """
        pass


# ============================================================================
# 上下文接口
# ============================================================================

class ContextInterface(ABC):
    """
    上下文接口。
    定义对话上下文管理的通用接口。
    """

    @abstractmethod
    def get_messages(self) -> List[Dict[str, Any]]:
        """
        获取所有消息。

        返回:
            消息列表
        """
        pass

    @abstractmethod
    def add_message(self, role: str, content: str) -> bool:
        """
        添加消息。

        参数:
            role: 消息角色
            content: 消息内容

        返回:
            True 如果添加成功
        """
        pass

    @abstractmethod
    def get_token_count(self) -> int:
        """
        获取 Token 数量。

        返回:
            Token 数量
        """
        pass

    @abstractmethod
    def clear(self) -> bool:
        """
        清空上下文。

        返回:
            True 如果清空成功
        """
        pass

    @abstractmethod
    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """
        获取最后一条消息。

        返回:
            最后一条消息，如果没有返回 None
        """
        pass


# ============================================================================
# 工具接口
# ============================================================================

class ToolInterface(ABC):
    """
    工具接口。
    定义工具调用和管理的通用接口。
    """

    @abstractmethod
    def list_tools(self) -> List[str]:
        """
        列出所有工具。

        返回:
            工具名称列表
        """
        pass

    @abstractmethod
    def execute(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """
        执行工具。

        参数:
            tool_name: 工具名称
            args: 工具参数

        返回:
            工具执行结果
        """
        pass

    @abstractmethod
    def register_tool(self, name: str, tool: Any) -> bool:
        """
        注册工具。

        参数:
            name: 工具名称
            tool: 工具实例

        返回:
            True 如果注册成功
        """
        pass

    @abstractmethod
    def unregister_tool(self, name: str) -> bool:
        """
        注销工具。

        参数:
            name: 工具名称

        返回:
            True 如果注销成功
        """
        pass

    @abstractmethod
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具信息。

        参数:
            name: 工具名称

        返回:
            工具信息字典
        """
        pass


# ============================================================================
# 配置接口
# ============================================================================

class ConfigInterface(ABC):
    """
    配置接口。
    定义配置管理的通用接口。
    """

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值。

        参数:
            key: 配置键
            default: 默认值

        返回:
            配置值
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> bool:
        """
        设置配置值。

        参数:
            key: 配置键
            value: 配置值

        返回:
            True 如果设置成功
        """
        pass

    @abstractmethod
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置。

        返回:
            配置字典
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        删除配置。

        参数:
            key: 配置键

        返回:
            True 如果删除成功
        """
        pass

    @abstractmethod
    def has(self, key: str) -> bool:
        """
        检查配置是否存在。

        参数:
            key: 配置键

        返回:
            True 如果存在
        """
        pass


# ============================================================================
# Agent 适配器基类
# ============================================================================

class AgentAdapter(ABC):
    """
    Agent 适配器基类。
    定义 Agent 适配器的通用接口。

    所有 Agent 适配器必须实现此接口。
    """

    @abstractmethod
    def get_name(self) -> str:
        """
        获取 Agent 名称。

        返回:
            Agent 名称
        """
        pass

    @abstractmethod
    def get_version(self) -> str:
        """
        获取 Agent 版本。

        返回:
            Agent 版本
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        获取 Agent 能力列表。

        返回:
            能力列表
        """
        pass

    @abstractmethod
    def get_memory(self) -> MemoryInterface:
        """
        获取记忆接口。

        返回:
            MemoryInterface 实例
        """
        pass

    @abstractmethod
    def get_context(self) -> ContextInterface:
        """
        获取上下文接口。

        返回:
            ContextInterface 实例
        """
        pass

    @abstractmethod
    def get_tools(self) -> ToolInterface:
        """
        获取工具接口。

        返回:
            ToolInterface 实例
        """
        pass

    @abstractmethod
    def get_config(self) -> ConfigInterface:
        """
        获取配置接口。

        返回:
            ConfigInterface 实例
        """
        pass

    def get_stats(self) -> Dict[str, Any]:
        """
        获取 Agent 统计信息。

        返回:
            统计字典
        """
        return {
            "name": self.get_name(),
            "version": self.get_version(),
            "capabilities": self.get_capabilities(),
        }

    def is_compatible(self, required_capabilities: List[str]) -> bool:
        """
        检查是否兼容所需能力。

        参数:
            required_capabilities: 所需能力列表

        返回:
            True 如果兼容
        """
        capabilities = set(self.get_capabilities())
        required = set(required_capabilities)
        return required.issubset(capabilities)
