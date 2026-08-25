#!/usr/bin/env python3
"""
Codex Harness — 线程管理器

管理并发线程和任务。
对应 Codex 的 thread_manager 模块。

Python 兼容性: 3.6+
"""

from enum import Enum
from typing import Dict, Any, Optional, Callable
import time
import threading


class ThreadStatus(Enum):
    """线程状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ThreadTask:
    """
    线程任务。

    属性:
        id: 任务 ID
        name: 任务名称
        func: 执行函数
        args: 参数
        status: 状态
        result: 结果
    """
    def __init__(
        self,
        id: str,
        name: str,
        func: Callable,
        args: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.name = name
        self.func = func
        self.args = args or {}
        self.status = ThreadStatus.PENDING
        self.result = None
        self.error = None
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class ThreadPool:
    """
    线程池。
    管理并发线程执行。

    功能:
    - 提交任务
    - 等待完成
    - 获取结果
    """

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.tasks: Dict[str, ThreadTask] = {}
        self.task_counter = 0

    def submit(
        self,
        name: str,
        func: Callable,
        args: Optional[Dict[str, Any]] = None,
    ) -> str:
        self.task_counter += 1
        task_id = f"task-{self.task_counter}"

        task = ThreadTask(id=task_id, name=name, func=func, args=args)
        self.tasks[task_id] = task

        # 在新线程中执行
        thread = threading.Thread(target=self._execute_task, args=(task_id,))
        thread.daemon = True
        thread.start()

        return task_id

    def _execute_task(self, task_id: str):
        task = self.tasks.get(task_id)
        if not task:
            return

        task.status = ThreadStatus.RUNNING
        task.started_at = time.time()

        try:
            task.result = task.func(**task.args)
            task.status = ThreadStatus.COMPLETED
        except Exception as e:
            task.error = str(e)
            task.status = ThreadStatus.FAILED

        task.completed_at = time.time()

    def get_task(self, task_id: str) -> Optional[ThreadTask]:
        return self.tasks.get(task_id)

    def get_stats(self) -> Dict[str, Any]:
        total = len(self.tasks)
        by_status = {}
        for task in self.tasks.values():
            status = task.status.value
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total": total,
            "by_status": by_status,
            "max_workers": self.max_workers,
        }


class ThreadManager:
    """
    线程管理器。
    统一管理线程池和任务。
    """

    def __init__(self, max_workers: int = 4):
        self.pool = ThreadPool(max_workers)

    def submit(self, name: str, func: Callable, args: Optional[Dict[str, Any]] = None) -> str:
        return self.pool.submit(name, func, args)

    def get_task(self, task_id: str) -> Optional[ThreadTask]:
        return self.pool.get_task(task_id)

    def get_stats(self) -> Dict[str, Any]:
        return self.pool.get_stats()


_global_manager = None

def get_global_thread_manager() -> ThreadManager:
    global _global_manager
    if _global_manager is None:
        _global_manager = ThreadManager()
    return _global_manager
