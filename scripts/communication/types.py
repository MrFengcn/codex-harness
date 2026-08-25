#!/usr/bin/env python3
"""
Codex Harness — Agent 通信类型

定义代理通信的消息类型和格式。
对应 Codex 的 agent_communication 模块。

Python 兼容性: 3.6+
"""

from enum import Enum
from typing import List, Dict, Any, Optional
import time
import uuid


class MessageType(Enum):
    """
    消息类型。
    对应 Codex 的 AgentCommunicationKind。

    属性:
        SPAWN: 创建子代理
        MESSAGE: 发送消息
        FOLLOWUP: 后续消息
        RESULT: 结果消息
    """
    SPAWN = "spawn"
    MESSAGE = "message"
    FOLLOWUP = "followup"
    RESULT = "result"


class AgentMessage:
    """
    代理消息。

    属性:
        id: 消息 ID
        type: 消息类型
        sender: 发送者 ID
        receiver: 接收者 ID
        content: 消息内容
        timestamp: 时间戳
        parent_id: 父消息 ID (用于跟踪对话)
        metadata: 元数据
    """
    def __init__(
        self,
        type: MessageType,
        sender: str,
        receiver: str,
        content: str,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化代理消息。

        参数:
            type: 消息类型
            sender: 发送者 ID
            receiver: 接收者 ID
            content: 消息内容
            parent_id: 父消息 ID
            metadata: 元数据
        """
        self.id = str(uuid.uuid4())[:8]
        self.type = type
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.timestamp = time.time()
        self.parent_id = parent_id
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "type": self.type.value,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "timestamp": self.timestamp,
            "parent_id": self.parent_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """从字典创建消息"""
        return cls(
            type=MessageType(data.get('type', 'message')),
            sender=data.get('sender', ''),
            receiver=data.get('receiver', ''),
            content=data.get('content', ''),
            parent_id=data.get('parent_id'),
            metadata=data.get('metadata', {}),
        )

    def __repr__(self) -> str:
        return (
            f"AgentMessage(type={self.type.value}, "
            f"sender={self.sender}, receiver={self.receiver})"
        )


class AgentInfo:
    """
    代理信息。

    属性:
        id: 代理 ID
        name: 代理名称
        capabilities: 代理能力列表
        status: 代理状态
        created_at: 创建时间
    """
    def __init__(
        self,
        id: str,
        name: str,
        capabilities: Optional[List[str]] = None,
        status: str = "active",
    ):
        """
        初始化代理信息。

        参数:
            id: 代理 ID
            name: 代理名称
            capabilities: 代理能力列表
            status: 代理状态
        """
        self.id = id
        self.name = name
        self.capabilities = capabilities or []
        self.status = status
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "capabilities": self.capabilities,
            "status": self.status,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentInfo':
        """从字典创建代理信息"""
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            capabilities=data.get('capabilities', []),
            status=data.get('status', 'active'),
        )


class CommunicationResult:
    """
    通信结果。

    属性:
        success: 是否成功
        message_id: 消息 ID
        response: 响应内容
        error: 错误信息
        duration_ms: 耗时
    """
    def __init__(
        self,
        success: bool,
        message_id: str = "",
        response: Optional[str] = None,
        error: Optional[str] = None,
        duration_ms: float = 0.0,
    ):
        """
        初始化通信结果。

        参数:
            success: 是否成功
            message_id: 消息 ID
            response: 响应内容
            error: 错误信息
            duration_ms: 耗时
        """
        self.success = success
        self.message_id = message_id
        self.response = response
        self.error = error
        self.duration_ms = duration_ms

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "message_id": self.message_id,
            "response": self.response,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }
