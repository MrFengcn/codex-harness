#!/usr/bin/env python3
"""
Codex Harness — 引导系统

提供用户交互引导能力。
对应 Codex 的 elicitation 模块。

Python 兼容性: 3.6+
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any


class ElicitationType(Enum):
    """引导类型"""
    CONFIRMATION = "confirmation"
    CHOICE = "choice"
    INPUT = "input"
    APPROVAL = "approval"


class ElicitationResult:
    """引导结果"""
    def __init__(self, confirmed: bool = False, value: Any = None, cancelled: bool = False):
        self.confirmed = confirmed
        self.value = value
        self.cancelled = cancelled

    def to_dict(self) -> Dict[str, Any]:
        return {"confirmed": self.confirmed, "value": self.value, "cancelled": self.cancelled}


class Elicitation(ABC):
    """引导基类"""
    @abstractmethod
    def get_type(self) -> ElicitationType:
        pass

    @abstractmethod
    def get_prompt(self) -> str:
        pass

    @abstractmethod
    def validate_response(self, response: Any) -> bool:
        pass


class ConfirmationElicitation(Elicitation):
    """确认引导"""
    def __init__(self, prompt: str):
        self.prompt = prompt

    def get_type(self) -> ElicitationType:
        return ElicitationType.CONFIRMATION

    def get_prompt(self) -> str:
        return self.prompt

    def validate_response(self, response: Any) -> bool:
        return isinstance(response, bool)


class ChoiceElicitation(Elicitation):
    """选择引导"""
    def __init__(self, prompt: str, choices: List[str]):
        self.prompt = prompt
        self.choices = choices

    def get_type(self) -> ElicitationType:
        return ElicitationType.CHOICE

    def get_prompt(self) -> str:
        return self.prompt

    def validate_response(self, response: Any) -> bool:
        return response in self.choices


class ElicitationManager:
    """引导管理器"""
    def __init__(self):
        self.history: List[Dict[str, Any]] = []

    def confirm(self, prompt: str) -> ElicitationResult:
        return ElicitationResult(confirmed=True)

    def choose(self, prompt: str, choices: List[str]) -> ElicitationResult:
        if choices:
            return ElicitationResult(confirmed=True, value=choices[0])
        return ElicitationResult(cancelled=True)

    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self.history)}
