#!/usr/bin/env python3
"""
Codex Harness — 安全管理器

统一管理所有安全检查器。
对应 Codex 的安全管理器。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from typing import List, Dict, Any, Optional
from safety.types import SafetyLevel, SafetyCheck, SafetyResult, SafetyPolicy
from safety.command import CommandSafetyChecker, CommandClassifier
from safety.file import FileSafetyChecker, FileClassifier
from safety.network import NetworkSafetyChecker, URLClassifier
from safety.patch import PatchSafetyChecker, PatchRiskAssessor


# ============================================================================
# 安全管理器
# ============================================================================

class SafetyManager:
    """
    安全管理器。
    统一管理所有安全检查器。

    功能:
    - 注册安全检查器
    - 统一安全检查接口
    - 安全事件记录
    - 安全统计
    """

    def __init__(self, policy: Optional[SafetyPolicy] = None):
        """
        初始化安全管理器。

        参数:
            policy: 安全策略 (None 使用默认策略)
        """
        self.policy = policy or SafetyPolicy()

        # 初始化检查器
        self.command_checker = CommandSafetyChecker(self.policy)
        self.file_checker = FileSafetyChecker(self.policy)
        self.network_checker = NetworkSafetyChecker(self.policy)
        self.patch_checker = PatchSafetyChecker(self.policy)

        # 初始化分类器
        self.command_classifier = CommandClassifier()
        self.file_classifier = FileClassifier()
        self.url_classifier = URLClassifier()
        self.patch_risk_assessor = PatchRiskAssessor()

        # 安全事件记录
        self.events: List[Dict[str, Any]] = []

    def check_operation(
        self,
        operation: str,
        args: Dict[str, Any],
    ) -> SafetyResult:
        """
        统一安全检查接口。

        参数:
            operation: 操作类型 (terminal, read_file, write_file, browser_navigate, apply_patch)
            args: 操作参数

        返回:
            SafetyResult 安全检查结果
        """
        start_time = time.time()

        # 根据操作类型选择检查器
        if operation == 'terminal':
            command = args.get('command', '')
            result = self.command_checker.check(command)
        elif operation == 'read_file':
            path = args.get('path', '')
            result = self.file_checker.check_read(path)
        elif operation == 'write_file':
            path = args.get('path', '')
            result = self.file_checker.check_write(path)
        elif operation == 'patch':
            path = args.get('path', '')
            result = self.file_checker.check_write(path)
        elif operation == 'browser_navigate':
            url = args.get('url', '')
            result = self.network_checker.check_url(url)
        elif operation == 'apply_patch':
            changes = args.get('changes', [])
            result = self.patch_checker.check(changes)
        else:
            # 未知操作，默认需要审查
            result = SafetyResult(
                check=SafetyCheck.ASK_USER,
                level=SafetyLevel.MEDIUM,
                reason=f"Unknown operation: {operation}",
                operation=operation,
            )

        # 记录事件
        duration_ms = (time.time() - start_time) * 1000
        self._record_event(operation, args, result, duration_ms)

        return result

    def check_command(self, command: str) -> SafetyResult:
        """
        检查命令安全性。

        参数:
            command: 命令字符串

        返回:
            SafetyResult 安全检查结果
        """
        return self.command_checker.check(command)

    def check_file_read(self, path: str) -> SafetyResult:
        """
        检查文件读取安全性。

        参数:
            path: 文件路径

        返回:
            SafetyResult 安全检查结果
        """
        return self.file_checker.check_read(path)

    def check_file_write(self, path: str) -> SafetyResult:
        """
        检查文件写入安全性。

        参数:
            path: 文件路径

        返回:
            SafetyResult 安全检查结果
        """
        return self.file_checker.check_write(path)

    def check_url(self, url: str) -> SafetyResult:
        """
        检查 URL 安全性。

        参数:
            url: URL 字符串

        返回:
            SafetyResult 安全检查结果
        """
        return self.network_checker.check_url(url)

    def check_patch(self, changes: List[Dict[str, Any]]) -> SafetyResult:
        """
        检查补丁安全性。

        参数:
            changes: 文件变更列表

        返回:
            SafetyResult 安全检查结果
        """
        return self.patch_checker.check(changes)

    def classify_command(self, command: str) -> str:
        """
        分类命令。

        参数:
            command: 命令字符串

        返回:
            命令类别
        """
        return self.command_classifier.classify(command)

    def classify_file(self, path: str) -> str:
        """
        分类文件。

        参数:
            path: 文件路径

        返回:
            文件类别
        """
        return self.file_classifier.classify(path)

    def classify_url(self, url: str) -> str:
        """
        分类 URL。

        参数:
            url: URL 字符串

        返回:
            URL 类别
        """
        return self.url_classifier.classify(url)

    def assess_patch_risk(self, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        评估补丁风险。

        参数:
            changes: 文件变更列表

        返回:
            风险评估字典
        """
        return self.patch_risk_assessor.assess(changes)

    def _record_event(
        self,
        operation: str,
        args: Dict[str, Any],
        result: SafetyResult,
        duration_ms: float,
    ):
        """
        记录安全事件。

        参数:
            operation: 操作类型
            args: 操作参数
            result: 安全检查结果
            duration_ms: 耗时
        """
        self.events.append({
            "timestamp": time.time(),
            "operation": operation,
            "check": result.check.value,
            "level": result.level.value,
            "reason": result.reason,
            "duration_ms": round(duration_ms, 2),
        })

    def get_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取安全事件。

        参数:
            limit: 返回数量

        返回:
            事件列表
        """
        return self.events[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """
        获取安全统计。

        返回:
            统计字典
        """
        if not self.events:
            return {
                "total_checks": 0,
                "auto_approve": 0,
                "ask_user": 0,
                "reject": 0,
                "average_duration_ms": 0.0,
            }

        total = len(self.events)
        auto_approve = sum(1 for e in self.events if e["check"] == "auto_approve")
        ask_user = sum(1 for e in self.events if e["check"] == "ask_user")
        reject = sum(1 for e in self.events if e["check"] == "reject")
        average_duration = sum(e["duration_ms"] for e in self.events) / total

        return {
            "total_checks": total,
            "auto_approve": auto_approve,
            "ask_user": ask_user,
            "reject": reject,
            "average_duration_ms": round(average_duration, 2),
        }

    def clear_events(self):
        """清除安全事件"""
        self.events.clear()


# ============================================================================
# 全局安全管理器
# ============================================================================

# 全局安全管理器实例
_global_manager: Optional[SafetyManager] = None


def get_global_safety_manager() -> SafetyManager:
    """
    获取全局安全管理器。

    返回:
        全局安全管理器实例
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = SafetyManager()
    return _global_manager


def check_operation(operation: str, args: Dict[str, Any]) -> SafetyResult:
    """
    统一安全检查接口 (全局函数)。

    参数:
        operation: 操作类型
        args: 操作参数

    返回:
        SafetyResult 安全检查结果
    """
    manager = get_global_safety_manager()
    return manager.check_operation(operation, args)
