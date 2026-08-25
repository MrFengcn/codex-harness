#!/usr/bin/env python3
"""
Codex Harness — 安全类型

定义安全级别、安全检查结果和安全结果详情。
对应 Codex 的 SafetyCheck 枚举。

Python 兼容性: 3.6+
"""

from enum import Enum
from typing import Dict, Any, Optional


class SafetyLevel(Enum):
    """
    安全级别。
    对应 Codex 的安全级别定义。

    属性:
        LOW: 低风险 (读取文件、查看状态)
        MEDIUM: 中风险 (写入文件、执行命令)
        HIGH: 高风险 (删除文件、修改系统)
        CRITICAL: 极高风险 (sudo、rm -rf)
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            order = {
                SafetyLevel.LOW: 0,
                SafetyLevel.MEDIUM: 1,
                SafetyLevel.HIGH: 2,
                SafetyLevel.CRITICAL: 3,
            }
            return order[self] >= order[other]
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            order = {
                SafetyLevel.LOW: 0,
                SafetyLevel.MEDIUM: 1,
                SafetyLevel.HIGH: 2,
                SafetyLevel.CRITICAL: 3,
            }
            return order[self] > order[other]
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            order = {
                SafetyLevel.LOW: 0,
                SafetyLevel.MEDIUM: 1,
                SafetyLevel.HIGH: 2,
                SafetyLevel.CRITICAL: 3,
            }
            return order[self] <= order[other]
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            order = {
                SafetyLevel.LOW: 0,
                SafetyLevel.MEDIUM: 1,
                SafetyLevel.HIGH: 2,
                SafetyLevel.CRITICAL: 3,
            }
            return order[self] < order[other]
        return NotImplemented


class SafetyCheck(Enum):
    """
    安全检查结果。
    对应 Codex 的 SafetyCheck 枚举。

    属性:
        AUTO_APPROVE: 自动批准
        ASK_USER: 需要用户确认
        REJECT: 拒绝
    """
    AUTO_APPROVE = "auto_approve"
    ASK_USER = "ask_user"
    REJECT = "reject"


class SafetyResult:
    """
    安全检查结果详情。

    属性:
        check: 安全检查结果
        level: 安全级别
        reason: 原因
        details: 详细信息
        path: 检查的路径 (如果有)
        operation: 检查的操作
    """
    def __init__(
        self,
        check: SafetyCheck,
        level: SafetyLevel = SafetyLevel.LOW,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        path: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        """
        初始化安全检查结果。

        参数:
            check: 安全检查结果
            level: 安全级别
            reason: 原因
            details: 详细信息
            path: 检查的路径
            operation: 检查的操作
        """
        self.check = check
        self.level = level
        self.reason = reason
        self.details = details or {}
        self.path = path
        self.operation = operation

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

    @property
    def is_safe(self) -> bool:
        """是否安全 (自动批准)"""
        return self.check == SafetyCheck.AUTO_APPROVE

    @property
    def needs_approval(self) -> bool:
        """是否需要审批"""
        return self.check == SafetyCheck.ASK_USER

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "check": self.check.value,
            "level": self.level.value,
            "is_auto_approve": self.is_auto_approve,
            "is_ask_user": self.is_ask_user,
            "is_reject": self.is_reject,
            "is_safe": self.is_safe,
            "needs_approval": self.needs_approval,
        }
        if self.reason:
            result["reason"] = self.reason
        if self.details:
            result["details"] = self.details
        if self.path:
            result["path"] = self.path
        if self.operation:
            result["operation"] = self.operation
        return result

    def __repr__(self) -> str:
        return (
            f"SafetyResult(check={self.check.value}, "
            f"level={self.level.value}, "
            f"reason={self.reason!r})"
        )


class SafetyPolicy:
    """
    安全策略。
    定义各种安全规则。

    属性:
        allowed_dirs: 允许的目录列表
        denied_paths: 禁止的路径列表
        denied_commands: 禁止的命令列表
        sensitive_files: 敏感文件列表
        max_file_size: 最大文件大小 (字节)
    """
    def __init__(
        self,
        allowed_dirs: Optional[list] = None,
        denied_paths: Optional[list] = None,
        denied_commands: Optional[list] = None,
        sensitive_files: Optional[list] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
    ):
        """
        初始化安全策略。

        参数:
            allowed_dirs: 允许的目录列表
            denied_paths: 禁止的路径列表
            denied_commands: 禁止的命令列表
            sensitive_files: 敏感文件列表
            max_file_size: 最大文件大小 (字节)
        """
        self.allowed_dirs = allowed_dirs or ['.']
        self.denied_paths = denied_paths or [
            '/etc', '/proc', '/sys', '/dev', '/boot', '/usr', '/var', '/tmp',
        ]
        self.denied_commands = denied_commands or [
            'rm -rf /', 'mkfs', 'dd if=', ':(){:|:&};:',
        ]
        self.sensitive_files = sensitive_files or [
            '.env', '.env.local', '.env.production',
            'id_rsa', 'id_ed25519', '.htpasswd', '.htaccess',
        ]
        self.max_file_size = max_file_size

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "allowed_dirs": self.allowed_dirs,
            "denied_paths": self.denied_paths,
            "denied_commands": self.denied_commands,
            "sensitive_files": self.sensitive_files,
            "max_file_size": self.max_file_size,
        }
