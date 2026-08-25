#!/usr/bin/env python3
"""
Codex Harness — 事件映射系统

定义事件类型和映射规则。
对应 Codex 的 event_mapping 模块。

Python 兼容性: 3.6+
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
import time


# ============================================================================
# 事件类型
# ============================================================================

class EventType(Enum):
    """
    事件类型。
    对应 Codex 的事件分类。

    属性:
        TOOL_CALL: 工具调用事件
        TOOL_RESULT: 工具结果事件
        MESSAGE: 消息事件
        ERROR: 错误事件
        STATE_CHANGE: 状态变更事件
        APPROVAL: 审批事件
        COMPACTION: 压缩事件
        CUSTOM: 自定义事件
    """
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    MESSAGE = "message"
    ERROR = "error"
    STATE_CHANGE = "state_change"
    APPROVAL = "approval"
    COMPACTION = "compaction"
    CUSTOM = "custom"


class EventPriority(Enum):
    """事件优先级"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class Event:
    """
    事件。

    属性:
        id: 事件 ID
        type: 事件类型
        priority: 事件优先级
        source: 事件来源
        data: 事件数据
        timestamp: 时间戳
        metadata: 元数据
    """
    def __init__(
        self,
        type: EventType,
        source: str = "",
        data: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = str(int(time.time() * 1000))
        self.type = type
        self.priority = priority
        self.source = source
        self.data = data or {}
        self.timestamp = time.time()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


# ============================================================================
# 映射规则
# ============================================================================

class MappingRule:
    """
    映射规则。
    定义事件到处理函数的映射。

    属性:
        name: 规则名称
        source_type: 源事件类型
        target_type: 目标事件类型
        condition: 条件函数
        transform: 转换函数
        enabled: 是否启用
    """
    def __init__(
        self,
        name: str,
        source_type: EventType,
        target_type: EventType,
        condition: Optional[Callable[[Event], bool]] = None,
        transform: Optional[Callable[[Event], Event]] = None,
        enabled: bool = True,
    ):
        self.name = name
        self.source_type = source_type
        self.target_type = target_type
        self.condition = condition
        self.transform = transform
        self.enabled = enabled

    def matches(self, event: Event) -> bool:
        """
        检查事件是否匹配规则。

        参数:
            event: 事件

        返回:
            True 如果匹配
        """
        if not self.enabled:
            return False

        if event.type != self.source_type:
            return False

        if self.condition and not self.condition(event):
            return False

        return True

    def apply(self, event: Event) -> Event:
        """
        应用映射规则。

        参数:
            event: 源事件

        返回:
            目标事件
        """
        if self.transform:
            return self.transform(event)

        return Event(
            type=self.target_type,
            source=event.source,
            data=event.data,
            priority=event.priority,
            metadata=event.metadata,
        )


# ============================================================================
# 事件转换器
# ============================================================================

class EventTransformer(ABC):
    """
    事件转换器基类。
    对应 Codex 的事件转换逻辑。
    """

    @abstractmethod
    def transform(self, event: Event) -> Event:
        """
        转换事件。

        参数:
            event: 源事件

        返回:
            转换后的事件
        """
        pass


class ToolCallTransformer(EventTransformer):
    """工具调用转换器"""

    def transform(self, event: Event) -> Event:
        """转换工具调用事件"""
        return Event(
            type=EventType.TOOL_CALL,
            source=event.source,
            data={
                "tool": event.data.get("tool", ""),
                "args": event.data.get("args", {}),
                "original_data": event.data,
            },
            priority=event.priority,
        )


class ErrorTransformer(EventTransformer):
    """错误转换器"""

    def transform(self, event: Event) -> Event:
        """转换错误事件"""
        return Event(
            type=EventType.ERROR,
            source=event.source,
            data={
                "error": event.data.get("error", ""),
                "stack_trace": event.data.get("stack_trace", ""),
                "original_data": event.data,
            },
            priority=EventPriority.HIGH,
        )


# ============================================================================
# 事件映射器
# ============================================================================

class EventMapper:
    """
    事件映射器。
    管理事件映射规则和转换。

    功能:
    - 注册映射规则
    - 应用映射规则
    - 事件转换
    """

    def __init__(self):
        """初始化事件映射器"""
        self.rules: List[MappingRule] = []
        self.transformers: Dict[str, EventTransformer] = {}

    def add_rule(self, rule: MappingRule):
        """
        添加映射规则。

        参数:
            rule: 映射规则
        """
        self.rules.append(rule)

    def remove_rule(self, name: str) -> bool:
        """
        移除映射规则。

        参数:
            name: 规则名称

        返回:
            True 如果移除成功
        """
        for i, rule in enumerate(self.rules):
            if rule.name == name:
                self.rules.pop(i)
                return True
        return False

    def register_transformer(self, name: str, transformer: EventTransformer):
        """
        注册转换器。

        参数:
            name: 转换器名称
            transformer: 转换器实例
        """
        self.transformers[name] = transformer

    def map_event(self, event: Event) -> List[Event]:
        """
        映射事件。

        参数:
            event: 源事件

        返回:
            映射后的事件列表
        """
        results = []

        for rule in self.rules:
            if rule.matches(event):
                mapped = rule.apply(event)
                results.append(mapped)

        return results

    def transform_event(self, event: Event, transformer_name: str) -> Event:
        """
        转换事件。

        参数:
            event: 源事件
            transformer_name: 转换器名称

        返回:
            转换后的事件
        """
        transformer = self.transformers.get(transformer_name)
        if transformer:
            return transformer.transform(event)
        return event

    def get_rules(self) -> List[MappingRule]:
        """获取所有规则"""
        return self.rules

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "rules": len(self.rules),
            "transformers": len(self.transformers),
        }


# ============================================================================
# 全局事件映射器
# ============================================================================

_global_mapper: Optional[EventMapper] = None


def get_global_event_mapper() -> EventMapper:
    """
    获取全局事件映射器。

    返回:
        全局事件映射器实例
    """
    global _global_mapper
    if _global_mapper is None:
        _global_mapper = EventMapper()
    return _global_mapper
