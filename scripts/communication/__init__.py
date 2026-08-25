#!/usr/bin/env python3
"""
Codex Harness — Agent 通信系统

提供代理间通信能力。
对应 Codex 的 agent_communication 系统。

Python 兼容性: 3.6+
"""

from communication.types import (
    MessageType,
    AgentMessage,
    AgentInfo,
    CommunicationResult,
)
from communication.messaging import (
    MessageBus,
    AgentRegistry,
    CommunicationManager,
    get_global_communication_manager,
)
from communication.task_coordination import (
    TaskDistributor,
    ResultCollector,
    TaskCoordinator,
)

__all__ = [
    'MessageType',
    'AgentMessage',
    'AgentInfo',
    'CommunicationResult',
    'MessageBus',
    'AgentRegistry',
    'CommunicationManager',
    'get_global_communication_manager',
    'TaskDistributor',
    'ResultCollector',
    'TaskCoordinator',
]
