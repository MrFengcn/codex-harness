#!/usr/bin/env python3
"""
Codex Harness — Turn 管理

管理对话 Turn。
对应 Codex 的 turn 模块。

Python 兼容性: 3.6+
"""

from enum import Enum
from typing import List, Dict, Any, Optional
import time


class TurnStatus(Enum):
    """Turn 状态"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class Turn:
    """Turn"""
    def __init__(self, id: str, messages: Optional[List[Dict]] = None):
        self.id = id
        self.messages = messages or []
        self.status = TurnStatus.PENDING
        self.created_at = time.time()
        self.completed_at = None

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content, "timestamp": time.time()})

    def complete(self):
        self.status = TurnStatus.COMPLETED
        self.completed_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "status": self.status.value,
            "messages": len(self.messages), "created_at": self.created_at,
        }


class TurnManager:
    """Turn 管理器"""
    def __init__(self):
        self.turns: Dict[str, Turn] = {}
        self.turn_counter = 0

    def create_turn(self) -> Turn:
        self.turn_counter += 1
        turn = Turn(id=f"turn-{self.turn_counter}")
        self.turns[turn.id] = turn
        return turn

    def get_turn(self, id: str) -> Optional[Turn]:
        return self.turns.get(id)

    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self.turns)}
