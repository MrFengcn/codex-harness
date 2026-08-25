#!/usr/bin/env python3
"""
Codex Harness — 本地压缩策略

使用本地 LLM 生成对话摘要。
对应 Codex 的 compact.rs。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any, Optional
from compression.base import CompressionStrategy, CompressionResult
from core import estimate_tokens


# ============================================================================
# 摘要提示模板
# ============================================================================

SUMMARIZATION_PROMPT = """请将以下对话历史压缩成简洁的摘要，保留关键信息：

{history}

要求：
1. 保留所有重要的决策和结论
2. 保留所有代码修改和文件操作
3. 保留所有错误和解决方案
4. 压缩到原来的 1/3 左右
5. 使用清晰的结构"""

SUMMARY_PREFIX = "以下是之前对话的摘要：\n\n"


# ============================================================================
# 本地压缩策略
# ============================================================================

class LocalCompression(CompressionStrategy):
    """
    本地压缩策略。
    对应 Codex 的 compact.rs。

    使用本地 LLM 生成对话摘要。
    """

    def __init__(
        self,
        summarization_prompt: Optional[str] = None,
        summary_prefix: Optional[str] = None,
        max_summary_tokens: int = 2000,
        min_history_length: int = 3,
    ):
        """
        初始化本地压缩策略。

        参数:
            summarization_prompt: 摘要提示模板
            summary_prefix: 摘要前缀
            max_summary_tokens: 摘要最大 Token 数
            min_history_length: 最小历史消息数 (少于此数不压缩)
        """
        self.summarization_prompt = summarization_prompt or SUMMARIZATION_PROMPT
        self.summary_prefix = summary_prefix or SUMMARY_PREFIX
        self.max_summary_tokens = max_summary_tokens
        self.min_history_length = min_history_length

    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return "local"

    def get_priority(self) -> int:
        """获取优先级 (本地压缩优先级较高)"""
        return 50

    def get_description(self) -> str:
        """获取策略描述"""
        return "本地 LLM 压缩 - 使用本地模型生成对话摘要"

    def can_compress(self, messages: List[Dict[str, Any]], token_count: int) -> bool:
        """
        检查是否可以使用本地压缩。

        条件:
        1. 消息格式有效
        2. 历史消息数 >= min_history_length
        3. 有用户和助手消息

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

        # 检查是否有用户和助手消息
        has_user = any(m.get('role') == 'user' for m in non_system)
        has_assistant = any(m.get('role') == 'assistant' for m in non_system)

        return has_user and has_assistant

    def compress(
        self,
        messages: List[Dict[str, Any]],
        target_tokens: int,
        keep_recent: int = 10,
    ) -> CompressionResult:
        """
        执行本地压缩。

        流程:
        1. 提取系统消息
        2. 提取历史消息
        3. 提取最近消息
        4. 生成历史摘要
        5. 组装压缩后的消息

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

        # 1. 提取消息
        system_messages = self.extract_system_messages(messages)
        history_messages = self.extract_history_messages(messages, keep_recent)
        recent_messages = self.extract_recent_messages(messages, keep_recent)

        # 计算原始 Token 数
        original_tokens = estimate_tokens(str(messages))

        # 2. 生成历史摘要
        summary = self._generate_summary(history_messages)
        summary_tokens = estimate_tokens(summary)

        # 3. 组装压缩后的消息
        compressed_messages = []

        # 添加系统消息
        compressed_messages.extend(system_messages)

        # 添加摘要消息
        if summary:
            compressed_messages.append({
                'role': 'assistant',
                'content': summary,
            })

        # 添加最近消息
        compressed_messages.extend(recent_messages)

        # 计算压缩后 Token 数
        compressed_tokens = estimate_tokens(str(compressed_messages))

        # 4. 检查是否达到目标
        success = compressed_tokens <= target_tokens or compressed_tokens < original_tokens

        return CompressionResult(
            success=success,
            compressed_messages=compressed_messages,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            strategy_name=self.get_strategy_name(),
            metadata={
                "summary_tokens": summary_tokens,
                "history_messages": len(history_messages),
                "recent_messages": len(recent_messages),
                "keep_recent": keep_recent,
            },
        )

    def _generate_summary(self, history_messages: List[Dict[str, Any]]) -> str:
        """
        生成历史摘要。

        参数:
            history_messages: 历史消息列表

        返回:
            摘要字符串
        """
        if not history_messages:
            return ""

        # 构建历史文本
        history_text = self._format_history(history_messages)

        # 构建提示
        prompt = self.summarization_prompt.format(history=history_text)

        # 调用 LLM 生成摘要
        summary = self._call_llm(prompt)

        if summary:
            return self.summary_prefix + summary
        else:
            # 如果 LLM 调用失败，使用简单摘要
            return self._simple_summary(history_messages)

    def _format_history(self, history_messages: List[Dict[str, Any]]) -> str:
        """
        格式化历史消息。

        参数:
            history_messages: 历史消息列表

        返回:
            格式化的历史文本
        """
        parts = []
        for msg in history_messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            if content:
                parts.append(f"[{role}]: {content[:500]}")
        return "\n".join(parts)

    def _call_llm(self, prompt: str) -> Optional[str]:
        """
        调用 LLM 生成摘要。

        参数:
            prompt: 提示文本

        返回:
            摘要文本，如果调用失败返回 None
        """
        # 这里应该调用实际的 LLM API
        # 目前返回 None，使用简单摘要作为回退
        # TODO: 集成 Hermes 的 LLM 调用
        return None

    def _simple_summary(self, history_messages: List[Dict[str, Any]]) -> str:
        """
        生成简单摘要 (LLM 调用失败时的回退)。

        参数:
            history_messages: 历史消息列表

        返回:
            简单摘要字符串
        """
        if not history_messages:
            return ""

        # 提取关键信息
        user_messages = [m for m in history_messages if m.get('role') == 'user']
        assistant_messages = [m for m in history_messages if m.get('role') == 'assistant']

        # 简洁摘要
        parts = []
        parts.append(f"对话历史: {len(user_messages)}轮")

        # 提取最后一条用户消息的关键内容
        if user_messages:
            last_user = user_messages[-1].get('content', '')
            # 只取前 100 个字符
            if len(last_user) > 100:
                last_user = last_user[:100] + "..."
            parts.append(f"最后请求: {last_user}")

        return " | ".join(parts)
