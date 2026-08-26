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
from agent_adapter.adapters.cursor import CursorAdapter
from agent_adapter.adapters.claude_code import ClaudeCodeAdapter
from agent_adapter.adapters.trae import TraeAdapter
from agent_adapter.adapters.qoder import QoderAdapter
from agent_adapter.adapters.codebuddy import CodeBuddyAdapter
from agent_adapter.adapters.comate import ComateAdapter
from agent_adapter.adapters.deepseek import DeepSeekAdapter

__all__ = [
    'HermesAdapter',
    'OpenClawAdapter',
    'LangChainAdapter',
    'AutoGPTAdapter',
    'MetaGPTAdapter',
    'CrewAIAdapter',
    'BabyAGIAdapter',
    'AgentGPTAdapter',
    'CursorAdapter',
    'ClaudeCodeAdapter',
    'TraeAdapter',
    'QoderAdapter',
    'CodeBuddyAdapter',
    'ComateAdapter',
    'DeepSeekAdapter',
]
