#!/usr/bin/env python3
"""
Codex Harness — 事件映射系统

提供事件类型定义和映射规则能力。
对应 Codex 的 event_mapping 模块。

Python 兼容性: 3.6+
"""

from event_mapping.types import (
    EventType,
    EventPriority,
    Event,
    MappingRule,
    EventTransformer,
    ToolCallTransformer,
    ErrorTransformer,
    EventMapper,
    get_global_event_mapper,
)

__all__ = [
    'EventType',
    'EventPriority',
    'Event',
    'MappingRule',
    'EventTransformer',
    'ToolCallTransformer',
    'ErrorTransformer',
    'EventMapper',
    'get_global_event_mapper',
]
