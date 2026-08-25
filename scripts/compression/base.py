#!/usr/bin/env python3
"""
Codex Harness — 压缩策略基类

定义压缩策略的抽象接口。
对应 Codex 的 compact 系统。

Python 兼容性: 3.6+
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class CompressionResult:
    """
    压缩结果。
    对应 Codex 的 CompactedHistoryMetadata。
    """
    def __init__(
        self,
        success: bool,
        compressed_messages: List[Dict[str, Any]],
        original_tokens: int,
        compressed_tokens: int,
        strategy_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化压缩结果。

        参数:
            success: 压缩是否成功
            compressed_messages: 压缩后的消息列表
            original_tokens: 原始 Token 数
            compressed_tokens: 压缩后 Token 数
            strategy_name: 使用的策略名称
            metadata: 额外元数据
        """
        self.success = success
        self.compressed_messages = compressed_messages
        self.original_tokens = original_tokens
        self.compressed_tokens = compressed_tokens
        self.strategy_name = strategy_name
        self.metadata = metadata or {}

    @property
    def compression_ratio(self) -> float:
        """压缩率 (0.0 - 1.0)"""
        if self.original_tokens == 0:
            return 0.0
        return 1.0 - (self.compressed_tokens / self.original_tokens)

    @property
    def tokens_saved(self) -> int:
        """节省的 Token 数"""
        return max(0, self.original_tokens - self.compressed_tokens)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "original_tokens": self.original_tokens,
            "compressed_tokens": self.compressed_tokens,
            "compression_ratio": round(self.compression_ratio, 3),
            "tokens_saved": self.tokens_saved,
            "strategy_name": self.strategy_name,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return (
            f"CompressionResult(success={self.success}, "
            f"ratio={self.compression_ratio:.1%}, "
            f"saved={self.tokens_saved} tokens)"
        )


class CompressionStrategy(ABC):
    """
    压缩策略抽象基类。
    对应 Codex 的压缩策略接口。

    所有压缩策略必须继承此类并实现抽象方法。
    """

    @abstractmethod
    def can_compress(self, messages: List[Dict[str, Any]], token_count: int) -> bool:
        """
        检查是否可以使用此策略进行压缩。

        参数:
            messages: 当前消息列表
            token_count: 当前 Token 数

        返回:
            True 如果可以使用此策略
        """
        pass

    @abstractmethod
    def compress(
        self,
        messages: List[Dict[str, Any]],
        target_tokens: int,
        keep_recent: int = 10,
    ) -> CompressionResult:
        """
        执行压缩。

        参数:
            messages: 当前消息列表
            target_tokens: 目标 Token 数
            keep_recent: 保留最近的消息数

        返回:
            CompressionResult 压缩结果
        """
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """
        获取策略名称。

        返回:
            策略名称字符串
        """
        pass

    def get_priority(self) -> int:
        """
        获取策略优先级 (数字越小优先级越高)。
        默认优先级为 100。

        返回:
            优先级整数
        """
        return 100

    def get_description(self) -> str:
        """
        获取策略描述。

        返回:
            策略描述字符串
        """
        return self.get_strategy_name()

    def validate_messages(self, messages: List[Dict[str, Any]]) -> bool:
        """
        验证消息格式是否有效。

        参数:
            messages: 消息列表

        返回:
            True 如果消息格式有效
        """
        if not isinstance(messages, list):
            return False

        for msg in messages:
            if not isinstance(msg, dict):
                return False
            if 'role' not in msg:
                return False
            if msg['role'] not in ('system', 'user', 'assistant', 'tool'):
                return False

        return True

    def extract_recent_messages(
        self,
        messages: List[Dict[str, Any]],
        keep_recent: int,
    ) -> List[Dict[str, Any]]:
        """
        提取最近的消息。

        参数:
            messages: 消息列表
            keep_recent: 保留最近的消息数

        返回:
            最近的消息列表
        """
        if keep_recent <= 0:
            return []
        if keep_recent >= len(messages):
            return messages
        return messages[-keep_recent:]

    def extract_system_messages(
        self,
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        提取系统消息。

        参数:
            messages: 消息列表

        返回:
            系统消息列表
        """
        return [msg for msg in messages if msg.get('role') == 'system']

    def extract_history_messages(
        self,
        messages: List[Dict[str, Any]],
        keep_recent: int,
    ) -> List[Dict[str, Any]]:
        """
        提取历史消息 (排除系统消息和最近消息)。

        参数:
            messages: 消息列表
            keep_recent: 保留最近的消息数

        返回:
            历史消息列表
        """
        system_messages = self.extract_system_messages(messages)
        recent_messages = self.extract_recent_messages(messages, keep_recent)

        # 排除系统消息和最近消息
        history = []
        for msg in messages:
            if msg not in system_messages and msg not in recent_messages:
                history.append(msg)

        return history
