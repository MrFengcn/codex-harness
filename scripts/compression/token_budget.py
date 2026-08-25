#!/usr/bin/env python3
"""
Codex Harness — Token 预算压缩策略

跳过摘要生成，直接截断历史消息。
对应 Codex 的 compact_token_budget.rs。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any
from compression.base import CompressionStrategy, CompressionResult
from core import estimate_tokens


# ============================================================================
# Token 预算压缩策略
# ============================================================================

class TokenBudgetCompression(CompressionStrategy):
    """
    Token 预算压缩策略。
    对应 Codex 的 compact_token_budget.rs。

    跳过模型/服务器摘要，安装全新的上下文窗口。
    仍然遵循压缩生命周期。

    特点:
    - 不调用 LLM 生成摘要
    - 直接截断历史消息
    - 保留最近的 N 条消息
    - 保留系统消息
    - 速度最快
    """

    def __init__(
        self,
        min_history_length: int = 3,
        preserve_system_messages: bool = True,
        preserve_recent_count: int = 10,
    ):
        """
        初始化 Token 预算压缩策略。

        参数:
            min_history_length: 最小历史消息数 (少于此数不压缩)
            preserve_system_messages: 是否保留系统消息
            preserve_recent_count: 保留最近的消息数
        """
        self.min_history_length = min_history_length
        self.preserve_system_messages = preserve_system_messages
        self.preserve_recent_count = preserve_recent_count

    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return "token_budget"

    def get_priority(self) -> int:
        """获取优先级 (Token 预算压缩优先级最高，因为最快)"""
        return 10

    def get_description(self) -> str:
        """获取策略描述"""
        return "Token 预算压缩 - 直接截断，跳过摘要，速度最快"

    def can_compress(self, messages: List[Dict[str, Any]], token_count: int) -> bool:
        """
        检查是否可以压缩。

        条件:
        1. 消息格式有效
        2. 历史消息数 >= min_history_length

        参数:
            messages: 当前消息列表
            token_count: 当前 Token 数

        返回:
            True 如果可以压缩
        """
        if not self.validate_messages(messages):
            return False

        # 统计非系统消息
        non_system = [m for m in messages if m.get('role') != 'system']

        # 检查历史消息数
        if len(non_system) < self.min_history_length:
            return False

        return True

    def compress(
        self,
        messages: List[Dict[str, Any]],
        target_tokens: int,
        keep_recent: int = 10,
    ) -> CompressionResult:
        """
        执行 Token 预算压缩。

        流程:
        1. 提取系统消息
        2. 提取最近消息
        3. 截断历史消息到目标 Token 数
        4. 组装压缩后的消息

        参数:
            messages: 当前消息列表
            target_tokens: 目标 Token 数
            keep_recent: 保留最近的消息数

        返回:
            CompressionResult 压缩结果
        """
        if not self.validate_messages(messages):
            return CompressionResult(
                success=False,
                compressed_messages=messages,
                original_tokens=estimate_tokens(str(messages)),
                compressed_tokens=estimate_tokens(str(messages)),
                strategy_name=self.get_strategy_name(),
                metadata={"error": "Invalid message format"},
            )

        # 计算原始 Token 数
        original_tokens = estimate_tokens(str(messages))

        # 1. 提取消息
        if self.preserve_system_messages:
            system_messages = self.extract_system_messages(messages)
        else:
            system_messages = []

        recent_messages = self.extract_recent_messages(messages, keep_recent)
        history_messages = self.extract_history_messages(messages, keep_recent)

        # 2. 计算系统消息和最近消息的 Token 数
        system_tokens = estimate_tokens(str(system_messages))
        recent_tokens = estimate_tokens(str(recent_messages))

        # 3. 计算可用于历史消息的 Token 数
        available_tokens = target_tokens - system_tokens - recent_tokens

        # 如果可用 Token 不足，减少最近消息
        if available_tokens < 0:
            # 减少最近消息数
            reduced_recent = max(1, keep_recent // 2)
            recent_messages = self.extract_recent_messages(messages, reduced_recent)
            recent_tokens = estimate_tokens(str(recent_messages))
            available_tokens = target_tokens - system_tokens - recent_tokens

        # 4. 截断历史消息
        truncated_history = self._truncate_history(history_messages, available_tokens)

        # 5. 组装压缩后的消息
        compressed_messages = []
        compressed_messages.extend(system_messages)
        compressed_messages.extend(truncated_history)
        compressed_messages.extend(recent_messages)

        # 计算压缩后 Token 数
        compressed_tokens = estimate_tokens(str(compressed_messages))

        # 6. 检查是否达到目标
        success = compressed_tokens <= target_tokens or compressed_tokens < original_tokens

        return CompressionResult(
            success=success,
            compressed_messages=compressed_messages,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            strategy_name=self.get_strategy_name(),
            metadata={
                "system_messages": len(system_messages),
                "history_messages": len(history_messages),
                "truncated_history": len(truncated_history),
                "recent_messages": len(recent_messages),
                "keep_recent": keep_recent,
                "available_tokens": available_tokens,
            },
        )

    def _truncate_history(
        self,
        history_messages: List[Dict[str, Any]],
        available_tokens: int,
    ) -> List[Dict[str, Any]]:
        """
        截断历史消息到可用 Token 数。

        参数:
            history_messages: 历史消息列表
            available_tokens: 可用 Token 数

        返回:
            截断后的历史消息列表
        """
        if not history_messages or available_tokens <= 0:
            return []

        # 从最新的历史消息开始保留
        truncated = []
        current_tokens = 0

        # 反向遍历，优先保留最新的
        for msg in reversed(history_messages):
            msg_tokens = estimate_tokens(str(msg))

            # 检查是否超过可用 Token
            if current_tokens + msg_tokens > available_tokens:
                # 尝试截断这条消息
                content = msg.get('content', '')
                if content:
                    # 估算可以保留多少字符
                    chars_per_token = 4
                    max_chars = (available_tokens - current_tokens) * chars_per_token
                    if max_chars > 50:  # 至少保留 50 个字符
                        truncated_content = content[:max_chars] + "...[truncated]"
                        truncated_msg = msg.copy()
                        truncated_msg['content'] = truncated_content
                        truncated.insert(0, truncated_msg)
                break

            truncated.insert(0, msg)
            current_tokens += msg_tokens

        return truncated

    def estimate_compressed_tokens(
        self,
        messages: List[Dict[str, Any]],
        target_tokens: int,
        keep_recent: int,
    ) -> int:
        """
        估算压缩后的 Token 数。

        参数:
            messages: 消息列表
            target_tokens: 目标 Token 数
            keep_recent: 保留最近消息数

        返回:
            估算的压缩后 Token 数
        """
        # 提取消息
        system_messages = self.extract_system_messages(messages) if self.preserve_system_messages else []
        recent_messages = self.extract_recent_messages(messages, keep_recent)

        # 计算系统消息和最近消息的 Token 数
        system_tokens = estimate_tokens(str(system_messages))
        recent_tokens = estimate_tokens(str(recent_messages))

        # 可用于历史消息的 Token 数
        available_tokens = target_tokens - system_tokens - recent_tokens

        # 历史消息数
        history_messages = self.extract_history_messages(messages, keep_recent)

        if not history_messages:
            return system_tokens + recent_tokens

        # 估算截断后的历史消息 Token 数
        history_tokens = estimate_tokens(str(history_messages))
        truncated_history_tokens = min(history_tokens, max(0, available_tokens))

        return system_tokens + truncated_history_tokens + recent_tokens
