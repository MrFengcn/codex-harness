#!/usr/bin/env python3
"""
Codex Harness — 消息传递和代理发现

实现代理间消息传递和代理发现机制。
对应 Codex 的 agent_communication 核心逻辑。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from typing import List, Dict, Any, Optional
from communication.types import MessageType, AgentMessage, AgentInfo, CommunicationResult


# ============================================================================
# 消息传递
# ============================================================================

class MessageBus:
    """
    消息总线。
    管理代理间消息传递。

    功能:
    - 发送消息
    - 接收消息
    - 消息队列
    - 消息历史
    """

    def __init__(self):
        """初始化消息总线"""
        self.messages: List[AgentMessage] = []
        self.queues: Dict[str, List[AgentMessage]] = {}

    def send(self, message: AgentMessage) -> CommunicationResult:
        """
        发送消息。

        参数:
            message: 代理消息

        返回:
            CommunicationResult 通信结果
        """
        start_time = time.time()

        # 记录消息
        self.messages.append(message)

        # 添加到接收者队列
        if message.receiver not in self.queues:
            self.queues[message.receiver] = []
        self.queues[message.receiver].append(message)

        duration_ms = (time.time() - start_time) * 1000

        return CommunicationResult(
            success=True,
            message_id=message.id,
            duration_ms=duration_ms,
        )

    def receive(self, agent_id: str) -> Optional[AgentMessage]:
        """
        接收消息。

        参数:
            agent_id: 代理 ID

        返回:
            AgentMessage 消息，如果队列为空返回 None
        """
        if agent_id not in self.queues:
            return None

        queue = self.queues[agent_id]
        if not queue:
            return None

        return queue.pop(0)

    def peek(self, agent_id: str) -> Optional[AgentMessage]:
        """
        查看队列中的下一条消息 (不移除)。

        参数:
            agent_id: 代理 ID

        返回:
            AgentMessage 消息，如果队列为空返回 None
        """
        if agent_id not in self.queues:
            return None

        queue = self.queues[agent_id]
        if not queue:
            return None

        return queue[0]

    def get_queue_size(self, agent_id: str) -> int:
        """
        获取队列大小。

        参数:
            agent_id: 代理 ID

        返回:
            队列大小
        """
        if agent_id not in self.queues:
            return 0
        return len(self.queues[agent_id])

    def get_history(self, limit: int = 100) -> List[AgentMessage]:
        """
        获取消息历史。

        参数:
            limit: 返回数量

        返回:
            消息列表
        """
        return self.messages[-limit:]

    def clear(self):
        """清除所有消息"""
        self.messages.clear()
        self.queues.clear()


# ============================================================================
# 代理发现
# ============================================================================

class AgentRegistry:
    """
    代理注册表。
    管理代理注册和发现。

    功能:
    - 注册代理
    - 发现代理
    - 能力匹配
    - 状态管理
    """

    def __init__(self):
        """初始化代理注册表"""
        self.agents: Dict[str, AgentInfo] = {}

    def register(self, agent: AgentInfo) -> bool:
        """
        注册代理。

        参数:
            agent: 代理信息

        返回:
            True 如果注册成功
        """
        self.agents[agent.id] = agent
        return True

    def unregister(self, agent_id: str) -> bool:
        """
        注销代理。

        参数:
            agent_id: 代理 ID

        返回:
            True 如果注销成功
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False

    def get(self, agent_id: str) -> Optional[AgentInfo]:
        """
        获取代理信息。

        参数:
            agent_id: 代理 ID

        返回:
            AgentInfo 代理信息，如果不存在返回 None
        """
        return self.agents.get(agent_id)

    def find_by_capability(self, capability: str) -> List[AgentInfo]:
        """
        按能力查找代理。

        参数:
            capability: 能力名称

        返回:
            代理信息列表
        """
        result = []
        for agent in self.agents.values():
            if capability in agent.capabilities and agent.status == "active":
                result.append(agent)
        return result

    def find_by_name(self, name: str) -> Optional[AgentInfo]:
        """
        按名称查找代理。

        参数:
            name: 代理名称

        返回:
            AgentInfo 代理信息，如果不存在返回 None
        """
        for agent in self.agents.values():
            if agent.name == name:
                return agent
        return None

    def list_all(self) -> List[AgentInfo]:
        """
        列出所有代理。

        返回:
            代理信息列表
        """
        return list(self.agents.values())

    def list_active(self) -> List[AgentInfo]:
        """
        列出活跃代理。

        返回:
            活跃代理信息列表
        """
        return [a for a in self.agents.values() if a.status == "active"]

    def update_status(self, agent_id: str, status: str) -> bool:
        """
        更新代理状态。

        参数:
            agent_id: 代理 ID
            status: 新状态

        返回:
            True 如果更新成功
        """
        if agent_id in self.agents:
            self.agents[agent_id].status = status
            return True
        return False


# ============================================================================
# 通信管理器
# ============================================================================

class CommunicationManager:
    """
    通信管理器。
    统一管理消息传递和代理发现。

    功能:
    - 消息发送/接收
    - 代理注册/发现
    - 通信统计
    """

    def __init__(self):
        """初始化通信管理器"""
        self.message_bus = MessageBus()
        self.agent_registry = AgentRegistry()
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "agents_registered": 0,
        }

    def send_message(
        self,
        sender: str,
        receiver: str,
        content: str,
        type: MessageType = MessageType.MESSAGE,
    ) -> CommunicationResult:
        """
        发送消息。

        参数:
            sender: 发送者 ID
            receiver: 接收者 ID
            content: 消息内容
            type: 消息类型

        返回:
            CommunicationResult 通信结果
        """
        message = AgentMessage(
            type=type,
            sender=sender,
            receiver=receiver,
            content=content,
        )

        result = self.message_bus.send(message)

        if result.success:
            self.stats["messages_sent"] += 1

        return result

    def receive_message(self, agent_id: str) -> Optional[AgentMessage]:
        """
        接收消息。

        参数:
            agent_id: 代理 ID

        返回:
            AgentMessage 消息，如果队列为空返回 None
        """
        message = self.message_bus.receive(agent_id)

        if message:
            self.stats["messages_received"] += 1

        return message

    def register_agent(
        self,
        id: str,
        name: str,
        capabilities: Optional[List[str]] = None,
    ) -> bool:
        """
        注册代理。

        参数:
            id: 代理 ID
            name: 代理名称
            capabilities: 代理能力列表

        返回:
            True 如果注册成功
        """
        agent = AgentInfo(
            id=id,
            name=name,
            capabilities=capabilities or [],
        )

        result = self.agent_registry.register(agent)

        if result:
            self.stats["agents_registered"] += 1

        return result

    def find_agent_by_capability(self, capability: str) -> List[AgentInfo]:
        """
        按能力查找代理。

        参数:
            capability: 能力名称

        返回:
            代理信息列表
        """
        return self.agent_registry.find_by_capability(capability)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取通信统计。

        返回:
            统计字典
        """
        return {
            **self.stats,
            "active_agents": len(self.agent_registry.list_active()),
            "queue_sizes": {
                agent_id: self.message_bus.get_queue_size(agent_id)
                for agent_id in self.agent_registry.agents
            },
        }


# ============================================================================
# 全局通信管理器
# ============================================================================

_global_manager: Optional[CommunicationManager] = None


def get_global_communication_manager() -> CommunicationManager:
    """
    获取全局通信管理器。

    返回:
        全局通信管理器实例
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = CommunicationManager()
    return _global_manager
