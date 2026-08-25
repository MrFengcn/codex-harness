#!/usr/bin/env python3
"""
Codex Harness — 任务分发和结果收集

实现代理间任务分发和结果收集。
对应 Codex 的任务协调逻辑。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from typing import List, Dict, Any, Optional


# ============================================================================
# 任务分发
# ============================================================================

class TaskDistributor:
    """
    任务分发器。
    将任务分发给合适的代理。

    功能:
    - 创建任务
    - 分配任务
    - 跟踪任务状态
    """

    def __init__(self):
        """初始化任务分发器"""
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.task_counter = 0

    def create_task(
        self,
        description: str,
        required_capability: Optional[str] = None,
        priority: int = 0,
    ) -> str:
        """
        创建任务。

        参数:
            description: 任务描述
            required_capability: 所需能力
            priority: 优先级 (0-10)

        返回:
            任务 ID
        """
        self.task_counter += 1
        task_id = f"task-{self.task_counter}"

        self.tasks[task_id] = {
            "id": task_id,
            "description": description,
            "required_capability": required_capability,
            "priority": priority,
            "status": "pending",
            "assigned_to": None,
            "created_at": time.time(),
            "started_at": None,
            "completed_at": None,
            "result": None,
        }

        return task_id

    def assign_task(
        self,
        task_id: str,
        agent_id: str,
    ) -> bool:
        """
        分配任务给代理。

        参数:
            task_id: 任务 ID
            agent_id: 代理 ID

        返回:
            True 如果分配成功
        """
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        if task["status"] != "pending":
            return False

        task["assigned_to"] = agent_id
        task["status"] = "assigned"
        task["started_at"] = time.time()

        return True

    def complete_task(
        self,
        task_id: str,
        result: str,
    ) -> bool:
        """
        完成任务。

        参数:
            task_id: 任务 ID
            result: 任务结果

        返回:
            True 如果完成成功
        """
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        if task["status"] not in ("assigned", "in_progress"):
            return False

        task["status"] = "completed"
        task["result"] = result
        task["completed_at"] = time.time()

        return True

    def fail_task(
        self,
        task_id: str,
        error: str,
    ) -> bool:
        """
        任务失败。

        参数:
            task_id: 任务 ID
            error: 错误信息

        返回:
            True 如果更新成功
        """
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        task["status"] = "failed"
        task["result"] = error
        task["completed_at"] = time.time()

        return True

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息。

        参数:
            task_id: 任务 ID

        返回:
            任务字典，如果不存在返回 None
        """
        return self.tasks.get(task_id)

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """
        获取待处理任务。

        返回:
            待处理任务列表
        """
        return [t for t in self.tasks.values() if t["status"] == "pending"]

    def get_assigned_tasks(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        获取代理已分配的任务。

        参数:
            agent_id: 代理 ID

        返回:
            已分配任务列表
        """
        return [
            t for t in self.tasks.values()
            if t["assigned_to"] == agent_id and t["status"] in ("assigned", "in_progress")
        ]

    def get_stats(self) -> Dict[str, Any]:
        """
        获取任务统计。

        返回:
            统计字典
        """
        total = len(self.tasks)
        by_status = {}
        for task in self.tasks.values():
            status = task["status"]
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total": total,
            "by_status": by_status,
        }


# ============================================================================
# 结果收集
# ============================================================================

class ResultCollector:
    """
    结果收集器。
    收集和汇总代理执行结果。

    功能:
    - 收集结果
    - 汇总结果
    - 过滤结果
    """

    def __init__(self):
        """初始化结果收集器"""
        self.results: Dict[str, List[Dict[str, Any]]] = {}

    def add_result(
        self,
        task_id: str,
        agent_id: str,
        result: str,
        success: bool = True,
    ):
        """
        添加结果。

        参数:
            task_id: 任务 ID
            agent_id: 代理 ID
            result: 结果内容
            success: 是否成功
        """
        if task_id not in self.results:
            self.results[task_id] = []

        self.results[task_id].append({
            "task_id": task_id,
            "agent_id": agent_id,
            "result": result,
            "success": success,
            "timestamp": time.time(),
        })

    def get_results(self, task_id: str) -> List[Dict[str, Any]]:
        """
        获取任务结果。

        参数:
            task_id: 任务 ID

        返回:
            结果列表
        """
        return self.results.get(task_id, [])

    def get_successful_results(self, task_id: str) -> List[Dict[str, Any]]:
        """
        获取成功结果。

        参数:
            task_id: 任务 ID

        返回:
            成功结果列表
        """
        return [r for r in self.get_results(task_id) if r["success"]]

    def get_failed_results(self, task_id: str) -> List[Dict[str, Any]]:
        """
        获取失败结果。

        参数:
            task_id: 任务 ID

        返回:
            失败结果列表
        """
        return [r for r in self.get_results(task_id) if not r["success"]]

    def summarize(self, task_id: str) -> Dict[str, Any]:
        """
        汇总任务结果。

        参数:
            task_id: 任务 ID

        返回:
            汇总字典
        """
        results = self.get_results(task_id)
        successful = self.get_successful_results(task_id)
        failed = self.get_failed_results(task_id)

        return {
            "task_id": task_id,
            "total": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results) if results else 0.0,
            "results": results,
        }


# ============================================================================
# 任务协调器
# ============================================================================

class TaskCoordinator:
    """
    任务协调器。
    统一管理任务分发和结果收集。

    功能:
    - 创建并分发任务
    - 收集任务结果
    - 协调多代理执行
    """

    def __init__(self):
        """初始化任务协调器"""
        self.distributor = TaskDistributor()
        self.collector = ResultCollector()

    def submit_task(
        self,
        description: str,
        required_capability: Optional[str] = None,
        priority: int = 0,
    ) -> str:
        """
        提交任务。

        参数:
            description: 任务描述
            required_capability: 所需能力
            priority: 优先级

        返回:
            任务 ID
        """
        return self.distributor.create_task(description, required_capability, priority)

    def assign_to_agent(
        self,
        task_id: str,
        agent_id: str,
    ) -> bool:
        """
        分配任务给代理。

        参数:
            task_id: 任务 ID
            agent_id: 代理 ID

        返回:
            True 如果分配成功
        """
        return self.distributor.assign_task(task_id, agent_id)

    def submit_result(
        self,
        task_id: str,
        agent_id: str,
        result: str,
        success: bool = True,
    ):
        """
        提交任务结果。

        参数:
            task_id: 任务 ID
            agent_id: 代理 ID
            result: 结果内容
            success: 是否成功
        """
        self.collector.add_result(task_id, agent_id, result, success)

        if success:
            self.distributor.complete_task(task_id, result)
        else:
            self.distributor.fail_task(task_id, result)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态。

        参数:
            task_id: 任务 ID

        返回:
            任务状态字典
        """
        task = self.distributor.get_task(task_id)
        if not task:
            return None

        summary = self.collector.summarize(task_id)

        return {
            **task,
            "results": summary,
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息。

        返回:
            统计字典
        """
        return {
            "tasks": self.distributor.get_stats(),
        }
