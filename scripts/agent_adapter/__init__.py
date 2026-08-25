#!/usr/bin/env python3
"""
Codex Harness — Agent 适配器系统

提供通用 Agent 适配器接口，支持多种 Agent 框架。

Python 兼容性: 3.6+
"""

from agent_adapter.interface import (
    MemoryInterface,
    ContextInterface,
    ToolInterface,
    ConfigInterface,
    AgentAdapter,
)
from agent_adapter.registry import (
    AgentAdapterRegistry,
    get_global_registry,
)
from agent_adapter.manager import (
    AgentAdapterManager,
    get_global_adapter_manager,
)
from agent_adapter.adapters import (
    HermesAdapter,
    OpenClawAdapter,
    LangChainAdapter,
    AutoGPTAdapter,
    MetaGPTAdapter,
    CrewAIAdapter,
    BabyAGIAdapter,
    AgentGPTAdapter,
)

__all__ = [
    'MemoryInterface',
    'ContextInterface',
    'ToolInterface',
    'ConfigInterface',
    'AgentAdapter',
    'AgentAdapterRegistry',
    'get_global_registry',
    'AgentAdapterManager',
    'get_global_adapter_manager',
    'HermesAdapter',
    'OpenClawAdapter',
    'LangChainAdapter',
    'AutoGPTAdapter',
    'MetaGPTAdapter',
    'CrewAIAdapter',
    'BabyAGIAdapter',
    'AgentGPTAdapter',
]
