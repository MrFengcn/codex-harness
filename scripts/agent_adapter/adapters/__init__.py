#!/usr/bin/env python3
"""
Codex Harness — Agent 适配器集合

包含所有 Agent 适配器实现。
"""

from agent_adapter.adapters.hermes import HermesAdapter
from agent_adapter.adapters.openclaw import OpenClawAdapter
from agent_adapter.adapters.langchain import LangChainAdapter
from agent_adapter.adapters.autogpt import AutoGPTAdapter
from agent_adapter.adapters.metagpt import MetaGPTAdapter
from agent_adapter.adapters.crewai import CrewAIAdapter
from agent_adapter.adapters.babyagi import BabyAGIAdapter
from agent_adapter.adapters.agentgpt import AgentGPTAdapter

__all__ = [
    'HermesAdapter',
    'OpenClawAdapter',
    'LangChainAdapter',
    'AutoGPTAdapter',
    'MetaGPTAdapter',
    'CrewAIAdapter',
    'BabyAGIAdapter',
    'AgentGPTAdapter',
]
