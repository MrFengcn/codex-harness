#!/usr/bin/env python3
"""
Codex Harness — 补丁安全检查器

验证补丁安全性。
对应 Codex 的 assess_patch_safety。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any, Optional
from patch.action import (
    PatchAction,
    FileChange,
    SafetyCheck,
    SafetyCheckResult,
)


# ============================================================================
# 安全策略
# ============================================================================

class PatchSecurityPolicy:
    """
    补丁安全策略。
    定义允许和禁止的路径模式。
    """

    # 禁止的路径前缀
    DENY_PATHS = {
        '/etc',
        '/proc',
        '/sys',
        '/dev',
        '/boot',
        '/usr',
        '/var',
        '/tmp',
    }

    # 允许的路径前缀 (相对于当前目录)
    ALLOW_PATHS = {
        '.',
        './',
    }

    # 禁止的文件扩展名
    DENY_EXTENSIONS = {
        '.exe',
        '.dll',
        '.so',
        '.dylib',
        '.bin',
        '.sh',
        '.bash',
    }

    # 敏感文件
    SENSITIVE_FILES = {
        '.env',
        '.env.local',
        '.env.production',
        'id_rsa',
        'id_ed25519',
        '.htpasswd',
        '.htaccess',
    }


# ============================================================================
# 补丁安全检查器
# ============================================================================

class PatchSafetyChecker:
    """
    补丁安全检查器。
    对应 Codex 的 assess_patch_safety。

    检查:
    1. 路径遍历
    2. 文件权限
    3. 文件存在性
    4. 路径白名单/黑名单
    5. 敏感文件
    """

    def __init__(
        self,
        policy: Optional[PatchSecurityPolicy] = None,
        allowed_dirs: Optional[List[str]] = None,
        check_file_exists: bool = True,
    ):
        """
        初始化安全检查器。

        参数:
            policy: 安全策略
            allowed_dirs: 允许的目录列表
            check_file_exists: 是否检查文件存在性
        """
        self.policy = policy or PatchSecurityPolicy()
        self.allowed_dirs = allowed_dirs or ['.']
        self.check_file_exists = check_file_exists

    def check(self, changes: List[FileChange]) -> SafetyCheckResult:
        """
        检查补丁安全性。

        参数:
            changes: 文件变更列表

        返回:
            SafetyCheckResult 安全检查结果
        """
        for change in changes:
            # 1. 检查路径遍历
            if not self._check_path_traversal(change):
                return SafetyCheckResult(
                    check=SafetyCheck.REJECT,
                    reason=f"Path traversal detected: {change.path}",
                    details={"path": change.path},
                )

            # 2. 检查禁止路径
            if not self._check_denied_paths(change):
                return SafetyCheckResult(
                    check=SafetyCheck.REJECT,
                    reason=f"Access denied to path: {change.path}",
                    details={"path": change.path},
                )

            # 3. 检查敏感文件
            if not self._check_sensitive_files(change):
                return SafetyCheckResult(
                    check=SafetyCheck.REJECT,
                    reason=f"Access to sensitive file: {change.path}",
                    details={"path": change.path},
                )

            # 4. 检查文件扩展名
            if not self._check_denied_extensions(change):
                return SafetyCheckResult(
                    check=SafetyCheck.REJECT,
                    reason=f"Denied file extension: {change.path}",
                    details={"path": change.path},
                )

            # 5. 检查路径白名单
            if not self._check_allowed_paths(change):
                return SafetyCheckResult(
                    check=SafetyCheck.ASK_USER,
                    reason=f"Path not in allowed directories: {change.path}",
                    details={"path": change.path},
                )

        # 所有检查通过
        return SafetyCheckResult(check=SafetyCheck.AUTO_APPROVE)

    def _check_path_traversal(self, change: FileChange) -> bool:
        """
        检查路径遍历。

        参数:
            change: 文件变更

        返回:
            True 如果安全
        """
        path = change.path

        # 检查 .. 路径遍历
        if '..' in path:
            return False

        # 检查绝对路径
        if os.path.isabs(path):
            # 绝对路径需要在允许的目录下
            for allowed_dir in self.allowed_dirs:
                allowed_abs = os.path.abspath(allowed_dir)
                if path.startswith(allowed_abs):
                    return True
            return False

        return True

    def _check_denied_paths(self, change: FileChange) -> bool:
        """
        检查禁止路径。

        参数:
            change: 文件变更

        返回:
            True 如果安全
        """
        path = change.path

        # 检查禁止的路径前缀
        for denied in self.policy.DENY_PATHS:
            if path.startswith(denied):
                return False

        return True

    def _check_sensitive_files(self, change: FileChange) -> bool:
        """
        检查敏感文件。

        参数:
            change: 文件变更

        返回:
            True 如果安全
        """
        filename = os.path.basename(change.path)

        # 检查敏感文件
        if filename in self.policy.SENSITIVE_FILES:
            return False

        # 检查隐藏文件 (以 . 开头)
        if filename.startswith('.') and filename not in {'.gitignore', '.gitkeep'}:
            # 需要用户确认
            return True

        return True

    def _check_denied_extensions(self, change: FileChange) -> bool:
        """
        检查禁止的文件扩展名。

        参数:
            change: 文件变更

        返回:
            True 如果安全
        """
        _, ext = os.path.splitext(change.path)

        # 检查禁止的扩展名
        if ext.lower() in self.policy.DENY_EXTENSIONS:
            return False

        return True

    def _check_allowed_paths(self, change: FileChange) -> bool:
        """
        检查路径白名单。

        参数:
            change: 文件变更

        返回:
            True 如果在白名单中
        """
        path = change.path

        # 检查是否在允许的目录下
        for allowed_dir in self.allowed_dirs:
            allowed_abs = os.path.abspath(allowed_dir)
            change_abs = os.path.abspath(path)

            if change_abs.startswith(allowed_abs):
                return True

        return False

    def check_file_exists(self, path: str) -> bool:
        """
        检查文件是否存在。

        参数:
            path: 文件路径

        返回:
            True 如果文件存在
        """
        if not self.check_file_exists:
            return True

        return os.path.exists(path)

    def check_write_permission(self, path: str) -> bool:
        """
        检查写权限。

        参数:
            path: 文件路径

        返回:
            True 如果有写权限
        """
        # 检查父目录是否存在
        parent_dir = os.path.dirname(path)
        if not os.path.exists(parent_dir):
            return False

        # 检查写权限
        return os.access(parent_dir, os.W_OK)


# ============================================================================
# 补丁安全检查结果
# ============================================================================

class PatchSafetyResult:
    """
    补丁安全检查结果。

    属性:
        check: 安全检查结果
        reason: 原因
        details: 详细信息
        path: 检查的路径
    """
    def __init__(
        self,
        check: SafetyCheck,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        path: Optional[str] = None,
    ):
        """
        初始化安全检查结果。

        参数:
            check: 安全检查结果
            reason: 原因
            details: 详细信息
            path: 检查的路径
        """
        self.check = check
        self.reason = reason
        self.details = details or {}
        self.path = path

    @property
    def is_safe(self) -> bool:
        """是否安全"""
        return self.check == SafetyCheck.AUTO_APPROVE

    @property
    def needs_approval(self) -> bool:
        """是否需要审批"""
        return self.check == SafetyCheck.ASK_USER

    @property
    def is_rejected(self) -> bool:
        """是否被拒绝"""
        return self.check == SafetyCheck.REJECT

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "check": self.check.value,
            "reason": self.reason,
            "details": self.details,
            "path": self.path,
        }

    def __repr__(self) -> str:
        return f"PatchSafetyResult(check={self.check.value}, path={self.path!r})"
