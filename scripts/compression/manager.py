#!/usr/bin/env python3
"""
Codex Harness — 压缩管理器

统一管理所有压缩策略。
对应 Codex 的压缩管理系统。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from typing import List, Dict, Any, Optional
from compression.base import CompressionStrategy, CompressionResult
from compression.local import LocalCompression
from compression.remote import RemoteCompression
from compression.remote_v2 import RemoteCompressionV2
from compression.fallback import ModelFallbackCompression
from compression.token_budget import TokenBudgetCompression
from core import estimate_tokens


# ============================================================================
# 压缩配置
# ============================================================================

class CompressionConfig:
    """
    压缩配置。
    对应 Codex 的压缩配置系统。
    """
    def __init__(
        self,
        compression_threshold: float = 0.8,
        keep_recent: int = 10,
        max_summary_tokens: int = 2000,
        enable_local: bool = True,
        enable_remote: bool = False,
        enable_remote_v2: bool = False,
        enable_fallback: bool = True,
        remote_api_url: Optional[str] = None,
        remote_api_key: Optional[str] = None,
        remote_model: str = "gpt-4",
        enable_hooks: bool = True,
    ):
        """
        初始化压缩配置。

        参数:
            compression_threshold: 触发压缩的 Token 比例 (0.0-1.0)
            keep_recent: 保留最近的消息数
            max_summary_tokens: 摘要最大 Token 数
            enable_local: 启用本地压缩
            enable_remote: 启用远程压缩
            enable_remote_v2: 启用远程压缩 V2
            enable_fallback: 启用回退压缩
            remote_api_url: 远程 API URL
            remote_api_key: 远程 API 密钥
            remote_model: 远程模型
            enable_hooks: 启用 Hook
        """
        self.compression_threshold = compression_threshold
        self.keep_recent = keep_recent
        self.max_summary_tokens = max_summary_tokens
        self.enable_local = enable_local
        self.enable_remote = enable_remote
        self.enable_remote_v2 = enable_remote_v2
        self.enable_fallback = enable_fallback
        self.remote_api_url = remote_api_url
        self.remote_api_key = remote_api_key
        self.remote_model = remote_model
        self.enable_hooks = enable_hooks

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "compression_threshold": self.compression_threshold,
            "keep_recent": self.keep_recent,
            "max_summary_tokens": self.max_summary_tokens,
            "enable_local": self.enable_local,
            "enable_remote": self.enable_remote,
            "enable_remote_v2": self.enable_remote_v2,
            "enable_fallback": self.enable_fallback,
            "remote_api_url": self.remote_api_url,
            "remote_model": self.remote_model,
            "enable_hooks": self.enable_hooks,
        }


# ============================================================================
# 压缩管理器
# ============================================================================

class CompressionManager:
    """
    压缩管理器。
    统一管理所有压缩策略。

    功能:
    - 策略注册
    - 策略选择
    - 压缩执行
    - 结果收集
    - Hook 集成
    """

    def __init__(self, config: Optional[CompressionConfig] = None):
        """
        初始化压缩管理器。

        参数:
            config: 压缩配置 (None 使用默认配置)
        """
        self.config = config or CompressionConfig()
        self.strategies: List[CompressionStrategy] = []
        self.hook_engine: Optional[Any] = None
        self.compression_history: List[Dict[str, Any]] = []

        # 自动注册策略
        self._auto_register_strategies()

    def _auto_register_strategies(self):
        """自动注册压缩策略"""
        # Token 预算压缩 (优先级最高)
        self.register_strategy(TokenBudgetCompression())

        # 本地压缩
        if self.config.enable_local:
            self.register_strategy(LocalCompression(
                max_summary_tokens=self.config.max_summary_tokens,
            ))

        # 远程压缩
        if self.config.enable_remote and self.config.remote_api_key:
            self.register_strategy(RemoteCompression(
                api_url=self.config.remote_api_url,
                api_key=self.config.remote_api_key,
                model=self.config.remote_model,
                max_summary_tokens=self.config.max_summary_tokens,
            ))

        # 远程压缩 V2
        if self.config.enable_remote_v2 and self.config.remote_api_key:
            self.register_strategy(RemoteCompressionV2(
                api_url=self.config.remote_api_url,
                api_key=self.config.remote_api_key,
                model=self.config.remote_model,
                max_summary_tokens=self.config.max_summary_tokens,
            ))

        # 回退压缩
        if self.config.enable_fallback:
            primary = self.strategies[0] if self.strategies else None
            fallback = ModelFallbackCompression(
                primary_strategy=primary,
                fallback_strategies=self.strategies[1:] if len(self.strategies) > 1 else [],
            )
            self.register_strategy(fallback)

    def register_strategy(self, strategy: CompressionStrategy):
        """
        注册压缩策略。

        参数:
            strategy: 压缩策略
        """
        self.strategies.append(strategy)
        # 按优先级排序
        self.strategies.sort(key=lambda s: s.get_priority())

    def set_hook_engine(self, hook_engine: Any):
        """
        设置 Hook 引擎。

        参数:
            hook_engine: Hook 引擎实例
        """
        self.hook_engine = hook_engine

    def should_compress(self, token_count: int, max_tokens: int) -> bool:
        """
        检查是否需要压缩。

        参数:
            token_count: 当前 Token 数
            max_tokens: 最大 Token 数

        返回:
            True 如果需要压缩
        """
        if max_tokens <= 0:
            return False
        ratio = token_count / max_tokens
        return ratio >= self.config.compression_threshold

    def compress(
        self,
        messages: List[Dict[str, Any]],
        target_tokens: int,
        keep_recent: Optional[int] = None,
    ) -> CompressionResult:
        """
        执行压缩。

        流程:
        1. 触发 PreCompact Hook
        2. 选择策略
        3. 执行压缩
        4. 记录历史
        5. 触发 PostCompact Hook
        6. 返回结果

        参数:
            messages: 当前消息列表
            target_tokens: 目标 Token 数
            keep_recent: 保留最近的消息数 (None 使用配置)

        返回:
            CompressionResult 压缩结果
        """
        if keep_recent is None:
            keep_recent = self.config.keep_recent

        original_tokens = estimate_tokens(str(messages))

        # 1. 触发 PreCompact Hook
        if self.hook_engine and self.config.enable_hooks:
            self.hook_engine.run_event('PreCompact', {
                'original_tokens': original_tokens,
                'target_tokens': target_tokens,
                'keep_recent': keep_recent,
            })

        # 2. 选择策略
        strategy = self._select_strategy(messages, original_tokens)

        # 3. 执行压缩
        start_time = time.time()
        result = strategy.compress(messages, target_tokens, keep_recent)
        duration_ms = (time.time() - start_time) * 1000

        # 4. 记录历史
        self._record_compression(
            strategy_name=strategy.get_strategy_name(),
            original_tokens=original_tokens,
            compressed_tokens=result.compressed_tokens,
            compression_ratio=result.compression_ratio,
            duration_ms=duration_ms,
            success=result.success,
        )

        # 5. 触发 PostCompact Hook
        if self.hook_engine and self.config.enable_hooks:
            self.hook_engine.run_event('PostCompact', {
                'result': result.to_dict(),
                'duration_ms': duration_ms,
            })

        return result

    def _select_strategy(
        self,
        messages: List[Dict[str, Any]],
        token_count: int,
    ) -> CompressionStrategy:
        """
        选择压缩策略。

        参数:
            messages: 消息列表
            token_count: Token 数

        返回:
            选择的压缩策略
        """
        # 按优先级顺序尝试
        for strategy in self.strategies:
            if strategy.can_compress(messages, token_count):
                return strategy

        # 默认使用 Token 预算压缩
        return TokenBudgetCompression()

    def _record_compression(
        self,
        strategy_name: str,
        original_tokens: int,
        compressed_tokens: int,
        compression_ratio: float,
        duration_ms: float,
        success: bool,
    ):
        """
        记录压缩历史。

        参数:
            strategy_name: 策略名称
            original_tokens: 原始 Token 数
            compressed_tokens: 压缩后 Token 数
            compression_ratio: 压缩率
            duration_ms: 耗时
            success: 是否成功
        """
        self.compression_history.append({
            "timestamp": time.time(),
            "strategy_name": strategy_name,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "compression_ratio": round(compression_ratio, 3),
            "duration_ms": round(duration_ms, 2),
            "success": success,
        })

    def get_compression_stats(self) -> Dict[str, Any]:
        """
        获取压缩统计。

        返回:
            统计字典
        """
        if not self.compression_history:
            return {
                "total_compressions": 0,
                "success_rate": 0.0,
                "average_compression_ratio": 0.0,
                "average_duration_ms": 0.0,
                "total_tokens_saved": 0,
            }

        total = len(self.compression_history)
        successful = sum(1 for c in self.compression_history if c["success"])
        success_rate = successful / total

        average_ratio = sum(c["compression_ratio"] for c in self.compression_history) / total
        average_duration = sum(c["duration_ms"] for c in self.compression_history) / total
        total_saved = sum(
            c["original_tokens"] - c["compressed_tokens"]
            for c in self.compression_history
            if c["success"]
        )

        return {
            "total_compressions": total,
            "success_rate": round(success_rate, 3),
            "average_compression_ratio": round(average_ratio, 3),
            "average_duration_ms": round(average_duration, 2),
            "total_tokens_saved": total_saved,
            "history": self.compression_history[-10:],  # 最近 10 条
        }

    def get_strategies(self) -> List[Dict[str, Any]]:
        """
        获取所有注册的策略。

        返回:
            策略信息列表
        """
        return [
            {
                "name": s.get_strategy_name(),
                "priority": s.get_priority(),
                "description": s.get_description(),
            }
            for s in self.strategies
        ]

    def clear_history(self):
        """清除压缩历史"""
        self.compression_history = []
