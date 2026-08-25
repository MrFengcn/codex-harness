#!/usr/bin/env python3
"""
Codex Harness — 压缩系统

提供对话上下文压缩能力。
对应 Codex 的 compact 系统。

Python 兼容性: 3.6+
"""

from compression.base import CompressionStrategy, CompressionResult
from compression.local import LocalCompression
from compression.remote import RemoteCompression
from compression.remote_v2 import RemoteCompressionV2
from compression.fallback import ModelFallbackCompression
from compression.token_budget import TokenBudgetCompression
from compression.manager import CompressionManager, CompressionConfig

__all__ = [
    'CompressionStrategy',
    'CompressionResult',
    'LocalCompression',
    'RemoteCompression',
    'RemoteCompressionV2',
    'ModelFallbackCompression',
    'TokenBudgetCompression',
    'CompressionManager',
    'CompressionConfig',
]
