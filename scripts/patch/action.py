#!/usr/bin/env python3
"""
Codex Harness — 补丁动作和文件变更

定义补丁动作类型和文件变更结构。
对应 Codex 的 ApplyPatchAction 和 ApplyPatchFileChange。

Python 兼容性: 3.6+
"""

from enum import Enum
from typing import Optional, Dict, Any


class PatchAction(Enum):
    """
    补丁动作类型。
    对应 Codex 的 ApplyPatchFileChange。
    """
    ADD = "add"          # 添加文件
    DELETE = "delete"    # 删除文件
    UPDATE = "update"    # 更新文件


class FileChange:
    """
    文件变更。
    对应 Codex 的 ApplyPatchFileChange。

    属性:
        path: 文件路径
        action: 补丁动作
        content: 文件内容 (Add/Delete 时使用)
        unified_diff: unified diff (Update 时使用)
        move_path: 移动目标路径 (可选)
    """
    def __init__(
        self,
        path: str,
        action: PatchAction,
        content: Optional[str] = None,
        unified_diff: Optional[str] = None,
        move_path: Optional[str] = None,
    ):
        """
        初始化文件变更。

        参数:
            path: 文件路径
            action: 补丁动作
            content: 文件内容 (Add/Delete 时使用)
            unified_diff: unified diff (Update 时使用)
            move_path: 移动目标路径 (可选)
        """
        self.path = path
        self.action = action
        self.content = content
        self.unified_diff = unified_diff
        self.move_path = move_path

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "path": self.path,
            "action": self.action.value,
        }
        if self.content is not None:
            result["content"] = self.content
        if self.unified_diff is not None:
            result["unified_diff"] = self.unified_diff
        if self.move_path is not None:
            result["move_path"] = self.move_path
        return result

    def __repr__(self) -> str:
        return f"FileChange(path={self.path!r}, action={self.action.value})"

    def validate(self) -> bool:
        """
        验证文件变更是否有效。

        返回:
            True 如果有效
        """
        # 检查路径
        if not self.path:
            return False

        # 检查路径遍历
        if '..' in self.path:
            return False

        # 根据动作类型检查
        if self.action == PatchAction.ADD:
            if self.content is None:
                return False
        elif self.action == PatchAction.DELETE:
            if self.content is None:
                return False
        elif self.action == PatchAction.UPDATE:
            if self.unified_diff is None:
                return False

        return True

    def get_content_lines(self) -> int:
        """
        获取内容行数。

        返回:
            内容行数
        """
        if self.content:
            return len(self.content.split('\n'))
        return 0

    def get_diff_lines(self) -> int:
        """
        获取 diff 行数。

        返回:
            diff 行数
        """
        if self.unified_diff:
            return len(self.unified_diff.split('\n'))
        return 0


class PatchResult:
    """
    补丁应用结果。
    对应 Codex 的补丁应用结果。

    属性:
        success: 是否成功
        changes_applied: 成功应用的变更数
        changes_failed: 失败的变更数
        errors: 错误列表
        backup_path: 备份路径 (如果有)
    """
    def __init__(
        self,
        success: bool,
        changes_applied: int = 0,
        changes_failed: int = 0,
        errors: Optional[list] = None,
        backup_path: Optional[str] = None,
    ):
        """
        初始化补丁结果。

        参数:
            success: 是否成功
            changes_applied: 成功应用的变更数
            changes_failed: 失败的变更数
            errors: 错误列表
            backup_path: 备份路径
        """
        self.success = success
        self.changes_applied = changes_applied
        self.changes_failed = changes_failed
        self.errors = errors or []
        self.backup_path = backup_path

    @property
    def total_changes(self) -> int:
        """总变更数"""
        return self.changes_applied + self.changes_failed

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_changes == 0:
            return 0.0
        return self.changes_applied / self.total_changes

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "changes_applied": self.changes_applied,
            "changes_failed": self.changes_failed,
            "total_changes": self.total_changes,
            "success_rate": round(self.success_rate, 3),
            "errors": self.errors,
            "backup_path": self.backup_path,
        }

    def __repr__(self) -> str:
        return (
            f"PatchResult(success={self.success}, "
            f"applied={self.changes_applied}, "
            f"failed={self.changes_failed})"
        )


class SafetyCheck(Enum):
    """
    安全检查结果。
    对应 Codex 的 SafetyCheck。
    """
    AUTO_APPROVE = "auto_approve"  # 自动批准
    ASK_USER = "ask_user"          # 需要用户确认
    REJECT = "reject"              # 拒绝


class SafetyCheckResult:
    """
    安全检查结果详情。

    属性:
        check: 安全检查结果
        reason: 原因 (Reject 时使用)
        details: 详细信息
    """
    def __init__(
        self,
        check: SafetyCheck,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化安全检查结果。

        参数:
            check: 安全检查结果
            reason: 原因
            details: 详细信息
        """
        self.check = check
        self.reason = reason
        self.details = details or {}

    @property
    def is_auto_approve(self) -> bool:
        """是否自动批准"""
        return self.check == SafetyCheck.AUTO_APPROVE

    @property
    def is_ask_user(self) -> bool:
        """是否需要用户确认"""
        return self.check == SafetyCheck.ASK_USER

    @property
    def is_reject(self) -> bool:
        """是否拒绝"""
        return self.check == SafetyCheck.REJECT

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "check": self.check.value,
            "reason": self.reason,
            "details": self.details,
        }

    def __repr__(self) -> str:
        return f"SafetyCheckResult(check={self.check.value}, reason={self.reason!r})"
