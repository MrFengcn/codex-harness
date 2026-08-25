#!/usr/bin/env python3
"""
Codex Harness — 模型回退压缩策略

当主策略失败时回退到备用策略。
对应 Codex 的 compact_model_fallback.rs。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from typing import List, Dict, Any, Optional
from compression.base import CompressionStrategy, CompressionResult
from core import estimate_tokens


# ============================================================================
# 模型回退压缩策略
# ============================================================================

class ModelFallbackCompression(CompressionStrategy):
    """
    模型回退压缩策略。
    对应 Codex 的 compact_model_fallback.rs。

    当主策略失败时回退到备用策略。
    支持:
    - 多级回退
    - 回退记录
    - 回退统计
    """

    def __init__(
        self,
        primary_strategy: Optional[CompressionStrategy] = None,
        fallback_strategies: Optional[List[CompressionStrategy]] = None,
        max_fallback_attempts: int = 3,
        record_fallback: bool = True,
    ):
        """
        初始化模型回退压缩策略。

        参数:
            primary_strategy: 主压缩策略
            fallback_strategies: 备用策略列表
            max_fallback_attempts: 最大回退尝试次数
            record_fallback: 是否记录回退事件
        """
        self.primary_strategy = primary_strategy
        self.fallback_strategies = fallback_strategies or []
        self.max_fallback_attempts = max_fallback_attempts
        self.record_fallback = record_fallback
        self.fallback_history: List[Dict[str, Any]] = []

    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return "model_fallback"

    def get_priority(self) -> int:
        """获取优先级 (回退策略优先级最低)"""
        return 200

    def get_description(self) -> str:
        """获取策略描述"""
        strategies = []
        if self.primary_strategy:
            strategies.append(self.primary_strategy.get_strategy_name())
        for s in self.fallback_strategies:
            strategies.append(s.get_strategy_name())
        return f"模型回退压缩 - 主策略: {strategies[0] if strategies else '无'}, 备用: {len(self.fallback_strategies)}个"

    def add_fallback_strategy(self, strategy: CompressionStrategy):
        """
        添加备用策略。

        参数:
            strategy: 备用压缩策略
        """
        self.fallback_strategies.append(strategy)

    def set_primary_strategy(self, strategy: CompressionStrategy):
        """
        设置主策略。

        参数:
            strategy: 主压缩策略
        """
        self.primary_strategy = strategy

    def can_compress(self, messages: List[Dict[str, Any]], token_count: int) -> bool:
        """
        检查是否可以压缩。

        条件: 主策略或任一备用策略可以压缩。

        参数:
            messages: 当前消息列表
            token_count: 当前 Token 数

        返回:
            True 如果可以压缩
        """
        # 检查主策略
        if self.primary_strategy and self.primary_strategy.can_compress(messages, token_count):
            return True

        # 检查备用策略
        for strategy in self.fallback_strategies:
            if strategy.can_compress(messages, token_count):
                return True

        return False

    def compress(
        self,
        messages: List[Dict[str, Any]],
        target_tokens: int,
        keep_recent: int = 10,
    ) -> CompressionResult:
        """
        执行压缩 (带回退)。

        流程:
        1. 尝试主策略
        2. 如果失败，尝试备用策略
        3. 记录回退事件
        4. 返回最佳结果

        参数:
            messages: 当前消息列表
            target_tokens: 目标 Token 数
            keep_recent: 保留最近的消息数

        返回:
            CompressionResult 压缩结果
        """
        original_tokens = estimate_tokens(str(messages))

        # 1. 尝试主策略
        if self.primary_strategy:
            result = self._try_strategy(
                self.primary_strategy,
                messages,
                target_tokens,
                keep_recent,
                is_primary=True,
            )
            if result.success:
                return result

        # 2. 尝试备用策略
        for i, strategy in enumerate(self.fallback_strategies):
            result = self._try_strategy(
                strategy,
                messages,
                target_tokens,
                keep_recent,
                is_primary=False,
                fallback_index=i,
            )
            if result.success:
                return result

        # 3. 所有策略都失败
        return CompressionResult(
            success=False,
            compressed_messages=messages,
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            strategy_name=self.get_strategy_name(),
            metadata={
                "error": "All strategies failed",
                "primary_strategy": self.primary_strategy.get_strategy_name() if self.primary_strategy else None,
                "fallback_strategies": [s.get_strategy_name() for s in self.fallback_strategies],
                "fallback_history": self.fallback_history,
            },
        )

    def _try_strategy(
        self,
        strategy: CompressionStrategy,
        messages: List[Dict[str, Any]],
        target_tokens: int,
        keep_recent: int,
        is_primary: bool = True,
        fallback_index: int = -1,
    ) -> CompressionResult:
        """
        尝试使用指定策略压缩。

        参数:
            strategy: 压缩策略
            messages: 消息列表
            target_tokens: 目标 Token 数
            keep_recent: 保留最近消息数
            is_primary: 是否是主策略
            fallback_index: 备用策略索引

        返回:
            CompressionResult 压缩结果
        """
        start_time = time.time()

        try:
            # 检查是否可以压缩
            if not strategy.can_compress(messages, estimate_tokens(str(messages))):
                return CompressionResult(
                    success=False,
                    compressed_messages=messages,
                    original_tokens=estimate_tokens(str(messages)),
                    compressed_tokens=estimate_tokens(str(messages)),
                    strategy_name=strategy.get_strategy_name(),
                    metadata={"error": "Strategy cannot compress"},
                )

            # 执行压缩
            result = strategy.compress(messages, target_tokens, keep_recent)

            # 记录回退事件
            if self.record_fallback:
                self._record_fallback(
                    strategy_name=strategy.get_strategy_name(),
                    is_primary=is_primary,
                    fallback_index=fallback_index,
                    success=result.success,
                    duration_ms=(time.time() - start_time) * 1000,
                    compression_ratio=result.compression_ratio,
                )

            return result

        except Exception as e:
            # 记录失败
            if self.record_fallback:
                self._record_fallback(
                    strategy_name=strategy.get_strategy_name(),
                    is_primary=is_primary,
                    fallback_index=fallback_index,
                    success=False,
                    duration_ms=(time.time() - start_time) * 1000,
                    error=str(e),
                )

            return CompressionResult(
                success=False,
                compressed_messages=messages,
                original_tokens=estimate_tokens(str(messages)),
                compressed_tokens=estimate_tokens(str(messages)),
                strategy_name=strategy.get_strategy_name(),
                metadata={"error": str(e)},
            )

    def _record_fallback(
        self,
        strategy_name: str,
        is_primary: bool,
        fallback_index: int,
        success: bool,
        duration_ms: float,
        compression_ratio: float = 0.0,
        error: Optional[str] = None,
    ):
        """
        记录回退事件。

        参数:
            strategy_name: 策略名称
            is_primary: 是否是主策略
            fallback_index: 备用策略索引
            success: 是否成功
            duration_ms: 耗时 (毫秒)
            compression_ratio: 压缩率
            error: 错误信息
        """
        event = {
            "timestamp": time.time(),
            "strategy_name": strategy_name,
            "is_primary": is_primary,
            "fallback_index": fallback_index,
            "success": success,
            "duration_ms": round(duration_ms, 2),
            "compression_ratio": round(compression_ratio, 3),
        }

        if error:
            event["error"] = error

        self.fallback_history.append(event)

    def get_fallback_stats(self) -> Dict[str, Any]:
        """
        获取回退统计。

        返回:
            统计字典
        """
        if not self.fallback_history:
            return {
                "total_attempts": 0,
                "primary_success_rate": 0.0,
                "fallback_success_rate": 0.0,
                "average_duration_ms": 0.0,
            }

        total = len(self.fallback_history)
        primary_attempts = [e for e in self.fallback_history if e["is_primary"]]
        fallback_attempts = [e for e in self.fallback_history if not e["is_primary"]]

        primary_success = sum(1 for e in primary_attempts if e["success"])
        fallback_success = sum(1 for e in fallback_attempts if e["success"])

        primary_success_rate = primary_success / len(primary_attempts) if primary_attempts else 0.0
        fallback_success_rate = fallback_success / len(fallback_attempts) if fallback_attempts else 0.0

        average_duration = sum(e["duration_ms"] for e in self.fallback_history) / total

        return {
            "total_attempts": total,
            "primary_attempts": len(primary_attempts),
            "fallback_attempts": len(fallback_attempts),
            "primary_success_rate": round(primary_success_rate, 3),
            "fallback_success_rate": round(fallback_success_rate, 3),
            "average_duration_ms": round(average_duration, 2),
            "fallback_history": self.fallback_history[-10:],  # 最近 10 条
        }

    def clear_fallback_history(self):
        """清除回退历史"""
        self.fallback_history = []
