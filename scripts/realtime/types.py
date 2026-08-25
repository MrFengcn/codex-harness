#!/usr/bin/env python3
"""
Codex Harness — 实时系统

提供实时事件流能力。
对应 Codex 的 realtime 模块。

Python 兼容性: 3.6+
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Callable
import time


class RealtimeEventType(Enum):
    """实时事件类型"""
    MESSAGE = "message"
    STATUS = "status"
    PROGRESS = "progress"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class RealtimeEvent:
    """实时事件"""
    def __init__(self, type: RealtimeEventType, data: Any = None):
        self.id = str(int(time.time() * 1000))
        self.type = type
        self.data = data
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "type": self.type.value, "data": self.data, "timestamp": self.timestamp}


class RealtimeChannel:
    """实时通道"""
    def __init__(self, name: str):
        self.name = name
        self.subscribers: List[Callable] = []
        self.events: List[RealtimeEvent] = []

    def subscribe(self, callback: Callable):
        self.subscribers.append(callback)

    def publish(self, event: RealtimeEvent):
        self.events.append(event)
        for callback in self.subscribers:
            try:
                callback(event)
            except Exception:
                pass

    def get_stats(self) -> Dict[str, Any]:
        return {"name": self.name, "subscribers": len(self.subscribers), "events": len(self.events)}


class RealtimeManager:
    """实时管理器"""
    def __init__(self):
        self.channels: Dict[str, RealtimeChannel] = {}

    def create_channel(self, name: str) -> RealtimeChannel:
        channel = RealtimeChannel(name)
        self.channels[name] = channel
        return channel

    def get_channel(self, name: str) -> Optional[RealtimeChannel]:
        return self.channels.get(name)

    def get_stats(self) -> Dict[str, Any]:
        return {"channels": len(self.channels)}
