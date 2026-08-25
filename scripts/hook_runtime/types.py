#!/usr/bin/env python3
"""
Codex Harness — Hook 运行时系统

管理 Hook 生命周期和执行。
对应 Codex 的 hook_runtime 模块。

Python 兼容性: 3.6+
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional
import time


# ============================================================================
# Hook 类型
# ============================================================================

class HookEvent(Enum):
    """Hook 事件类型"""
    PRE_TOOL_CALL = "pre_tool_call"
    POST_TOOL_CALL = "post_tool_call"
    PRE_APPROVAL = "pre_approval"
    POST_APPROVAL = "post_approval"
    PRE_COMPACTION = "pre_compaction"
    POST_COMPACTION = "post_compaction"
    ON_ERROR = "on_error"
    ON_START = "on_start"
    ON_END = "on_end"
    CUSTOM = "custom"


class HookPriority(Enum):
    """Hook 优先级"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class HookStatus(Enum):
    """Hook 状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


# ============================================================================
# Hook 定义
# ============================================================================

class HookResult:
    """
    Hook 执行结果。

    属性:
        success: 是否成功
        output: 输出内容
        error: 错误信息
        duration_ms: 执行耗时
        status: Hook 状态
    """
    def __init__(
        self,
        success: bool,
        output: Any = None,
        error: Optional[str] = None,
        duration_ms: float = 0.0,
        status: HookStatus = HookStatus.COMPLETED,
    ):
        self.success = success
        self.output = output
        self.error = error
        self.duration_ms = duration_ms
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
        }


class HookContext:
    """
    Hook 上下文。

    属性:
        event: 事件类型
        data: 事件数据
        metadata: 元数据
    """
    def __init__(
        self,
        event: HookEvent,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.event = event
        self.data = data or {}
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event": self.event.value,
            "data": self.data,
            "metadata": self.metadata,
        }


# ============================================================================
# Hook 接口
# ============================================================================

class Hook(ABC):
    """
    Hook 基类。
    对应 Codex 的 Hook 接口。

    所有 Hook 必须实现此接口。
    """

    @abstractmethod
    def get_name(self) -> str:
        """
        获取 Hook 名称。

        返回:
            Hook 名称
        """
        pass

    @abstractmethod
    def get_events(self) -> List[HookEvent]:
        """
        获取监听的事件列表。

        返回:
            事件列表
        """
        pass

    @abstractmethod
    def execute(self, context: HookContext) -> HookResult:
        """
        执行 Hook。

        参数:
            context: Hook 上下文

        返回:
            HookResult 执行结果
        """
        pass

    def get_priority(self) -> HookPriority:
        """
        获取优先级。

        返回:
            HookPriority 优先级
        """
        return HookPriority.NORMAL

    def get_timeout(self) -> float:
        """
        获取超时时间 (秒)。

        返回:
            超时时间
        """
        return 30.0


# ============================================================================
# Hook 运行时
# ============================================================================

class HookRuntime:
    """
    Hook 运行时。
    管理 Hook 注册和执行。

    功能:
    - 注册 Hook
    - 触发事件
    - 执行 Hook
    - 超时处理
    """

    def __init__(self):
        """初始化 Hook 运行时"""
        self.hooks: Dict[str, Hook] = {}
        self.event_hooks: Dict[HookEvent, List[str]] = {}
        self.history: List[Dict[str, Any]] = []

    def register(self, hook: Hook) -> bool:
        """
        注册 Hook。

        参数:
            hook: Hook 实例

        返回:
            True 如果注册成功
        """
        name = hook.get_name()
        self.hooks[name] = hook

        # 注册事件
        for event in hook.get_events():
            if event not in self.event_hooks:
                self.event_hooks[event] = []
            self.event_hooks[event].append(name)

        return True

    def unregister(self, name: str) -> bool:
        """
        注销 Hook。

        参数:
            name: Hook 名称

        返回:
            True 如果注销成功
        """
        if name not in self.hooks:
            return False

        hook = self.hooks[name]

        # 从事件中移除
        for event in hook.get_events():
            if event in self.event_hooks:
                if name in self.event_hooks[event]:
                    self.event_hooks[event].remove(name)

        del self.hooks[name]
        return True

    def trigger(
        self,
        event: HookEvent,
        data: Optional[Dict[str, Any]] = None,
    ) -> List[HookResult]:
        """
        触发事件。

        参数:
            event: 事件类型
            data: 事件数据

        返回:
            HookResult 列表
        """
        context = HookContext(event=event, data=data or {})
        results = []

        # 获取监听此事件的 Hook
        hook_names = self.event_hooks.get(event, [])

        # 按优先级排序
        sorted_hooks = sorted(
            hook_names,
            key=lambda name: self.hooks[name].get_priority().value,
            reverse=True,
        )

        # 执行 Hook
        for name in sorted_hooks:
            hook = self.hooks[name]
            result = self._execute_hook(hook, context)
            results.append(result)

            # 记录历史
            self._record_history(name, event, result)

        return results

    def _execute_hook(self, hook: Hook, context: HookContext) -> HookResult:
        """
        执行单个 Hook。

        参数:
            hook: Hook 实例
            context: Hook 上下文

        返回:
            HookResult 执行结果
        """
        start_time = time.time()

        try:
            result = hook.execute(context)
            result.duration_ms = (time.time() - start_time) * 1000
            return result
        except Exception as e:
            return HookResult(
                success=False,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
                status=HookStatus.FAILED,
            )

    def _record_history(
        self,
        hook_name: str,
        event: HookEvent,
        result: HookResult,
    ):
        """
        记录执行历史。

        参数:
            hook_name: Hook 名称
            event: 事件类型
            result: 执行结果
        """
        self.history.append({
            "hook": hook_name,
            "event": event.value,
            "success": result.success,
            "duration_ms": result.duration_ms,
            "timestamp": time.time(),
        })

    def get_hooks(self) -> List[str]:
        """
        获取所有 Hook 名称。

        返回:
            Hook 名称列表
        """
        return list(self.hooks.keys())

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取执行历史。

        参数:
            limit: 返回数量

        返回:
            历史记录列表
        """
        return self.history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息。

        返回:
            统计字典
        """
        total_hooks = len(self.hooks)
        total_events = len(self.event_hooks)
        total_history = len(self.history)

        success_count = sum(1 for h in self.history if h["success"])
        fail_count = total_history - success_count

        return {
            "total_hooks": total_hooks,
            "total_events": total_events,
            "total_history": total_history,
            "success_count": success_count,
            "fail_count": fail_count,
        }


# ============================================================================
# 全局 Hook 运行时
# ============================================================================

_global_runtime: Optional[HookRuntime] = None


def get_global_hook_runtime() -> HookRuntime:
    """
    获取全局 Hook 运行时。

    返回:
        全局 Hook 运行时实例
    """
    global _global_runtime
    if _global_runtime is None:
        _global_runtime = HookRuntime()
    return _global_runtime
