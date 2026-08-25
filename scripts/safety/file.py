#!/usr/bin/env python3
"""
Codex Harness — 文件安全检查器

检查文件操作安全性。
对应 Codex 的文件安全检查逻辑。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional
from safety.types import SafetyLevel, SafetyCheck, SafetyResult, SafetyPolicy


# ============================================================================
# 文件安全检查器
# ============================================================================

class FileSafetyChecker:
    """
    文件安全检查器。
    对应 Codex 的文件安全检查逻辑。

    检查:
    1. 路径遍历
    2. 禁止路径
    3. 敏感文件
    4. 文件大小
    5. 文件权限
    """

    def __init__(self, policy: Optional[SafetyPolicy] = None):
        """
        初始化文件安全检查器。

        参数:
            policy: 安全策略 (None 使用默认策略)
        """
        self.policy = policy or SafetyPolicy()

    def check_read(self, path: str) -> SafetyResult:
        """
        检查文件读取安全性。

        参数:
            path: 文件路径

        返回:
            SafetyResult 安全检查结果
        """
        # 1. 检查路径遍历
        traversal_result = self._check_path_traversal(path)
        if traversal_result:
            return traversal_result

        # 2. 检查禁止路径
        denied_result = self._check_denied_paths(path)
        if denied_result:
            return denied_result

        # 3. 检查敏感文件
        sensitive_result = self._check_sensitive_files(path)
        if sensitive_result:
            return sensitive_result

        # 4. 默认允许读取
        return SafetyResult(
            check=SafetyCheck.AUTO_APPROVE,
            level=SafetyLevel.LOW,
            path=path,
            operation='read_file',
        )

    def check_write(self, path: str) -> SafetyResult:
        """
        检查文件写入安全性。

        参数:
            path: 文件路径

        返回:
            SafetyResult 安全检查结果
        """
        # 1. 检查路径遍历
        traversal_result = self._check_path_traversal(path)
        if traversal_result:
            return traversal_result

        # 2. 检查禁止路径
        denied_result = self._check_denied_paths(path)
        if denied_result:
            return denied_result

        # 3. 检查敏感文件
        sensitive_result = self._check_sensitive_files(path)
        if sensitive_result:
            return sensitive_result

        # 4. 检查文件大小 (如果文件存在)
        if os.path.exists(path):
            size_result = self._check_file_size(path)
            if size_result:
                return size_result

        # 5. 检查路径白名单
        whitelist_result = self._check_allowed_paths(path)
        if whitelist_result:
            return whitelist_result

        # 6. 默认允许写入
        return SafetyResult(
            check=SafetyCheck.AUTO_APPROVE,
            level=SafetyLevel.MEDIUM,
            path=path,
            operation='write_file',
        )

    def check_delete(self, path: str) -> SafetyResult:
        """
        检查文件删除安全性。

        参数:
            path: 文件路径

        返回:
            SafetyResult 安全检查结果
        """
        # 1. 检查路径遍历
        traversal_result = self._check_path_traversal(path)
        if traversal_result:
            return traversal_result

        # 2. 检查禁止路径
        denied_result = self._check_denied_paths(path)
        if denied_result:
            return denied_result

        # 3. 检查敏感文件
        sensitive_result = self._check_sensitive_files(path)
        if sensitive_result:
            return sensitive_result

        # 4. 检查文件是否存在
        if not os.path.exists(path):
            return SafetyResult(
                check=SafetyCheck.AUTO_APPROVE,
                level=SafetyLevel.LOW,
                path=path,
                operation='delete_file',
            )

        # 5. 删除操作需要用户确认
        return SafetyResult(
            check=SafetyCheck.ASK_USER,
            level=SafetyLevel.HIGH,
            reason="Delete operation requires confirmation",
            path=path,
            operation='delete_file',
        )

    def _check_path_traversal(self, path: str) -> Optional[SafetyResult]:
        """
        检查路径遍历。

        参数:
            path: 文件路径

        返回:
            SafetyResult 如果有路径遍历，否则 None
        """
        if '..' in path:
            return SafetyResult(
                check=SafetyCheck.REJECT,
                level=SafetyLevel.HIGH,
                reason=f"Path traversal detected: {path}",
                path=path,
                operation='file',
            )

        return None

    def _check_denied_paths(self, path: str) -> Optional[SafetyResult]:
        """
        检查禁止路径。

        参数:
            path: 文件路径

        返回:
            SafetyResult 如果在禁止路径，否则 None
        """
        # 规范化路径
        normalized = os.path.normpath(path)

        for denied in self.policy.denied_paths:
            if normalized.startswith(denied):
                return SafetyResult(
                    check=SafetyCheck.REJECT,
                    level=SafetyLevel.CRITICAL,
                    reason=f"Access denied to path: {denied}",
                    details={"path": path, "denied_path": denied},
                    path=path,
                    operation='file',
                )

        return None

    def _check_sensitive_files(self, path: str) -> Optional[SafetyResult]:
        """
        检查敏感文件。

        参数:
            path: 文件路径

        返回:
            SafetyResult 如果是敏感文件，否则 None
        """
        filename = os.path.basename(path)

        for sensitive in self.policy.sensitive_files:
            if filename == sensitive:
                return SafetyResult(
                    check=SafetyCheck.REJECT,
                    level=SafetyLevel.HIGH,
                    reason=f"Access to sensitive file: {sensitive}",
                    details={"path": path, "sensitive_file": sensitive},
                    path=path,
                    operation='file',
                )

        return None

    def _check_file_size(self, path: str) -> Optional[SafetyResult]:
        """
        检查文件大小。

        参数:
            path: 文件路径

        返回:
            SafetyResult 如果文件太大，否则 None
        """
        try:
            size = os.path.getsize(path)
            if size > self.policy.max_file_size:
                return SafetyResult(
                    check=SafetyCheck.ASK_USER,
                    level=SafetyLevel.MEDIUM,
                    reason=f"File too large: {size} bytes (max: {self.policy.max_file_size})",
                    details={"path": path, "size": size, "max_size": self.policy.max_file_size},
                    path=path,
                    operation='file',
                )
        except OSError:
            pass

        return None

    def _check_allowed_paths(self, path: str) -> Optional[SafetyResult]:
        """
        检查路径白名单。

        参数:
            path: 文件路径

        返回:
            SafetyResult 如果不在白名单，否则 None
        """
        normalized = os.path.normpath(os.path.abspath(path))

        for allowed in self.policy.allowed_dirs:
            allowed_abs = os.path.normpath(os.path.abspath(allowed))
            if normalized.startswith(allowed_abs):
                return None

        # 不在白名单中，需要用户确认
        return SafetyResult(
            check=SafetyCheck.ASK_USER,
            level=SafetyLevel.MEDIUM,
            reason=f"Path not in allowed directories: {path}",
            details={"path": path, "allowed_dirs": self.policy.allowed_dirs},
            path=path,
            operation='file',
        )


# ============================================================================
# 文件分类器
# ============================================================================

class FileClassifier:
    """
    文件分类器。
    将文件分为不同类别。
    """

    # 代码文件扩展名
    CODE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h',
        '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.sh',
    }

    # 配置文件扩展名
    CONFIG_EXTENSIONS = {
        '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    }

    # 文档文件扩展名
    DOC_EXTENSIONS = {
        '.md', '.txt', '.rst', '.doc', '.docx', '.pdf',
    }

    def classify(self, path: str) -> str:
        """
        分类文件。

        参数:
            path: 文件路径

        返回:
            文件类别: 'code', 'config', 'doc', 'other'
        """
        _, ext = os.path.splitext(path)

        if ext.lower() in self.CODE_EXTENSIONS:
            return 'code'
        elif ext.lower() in self.CONFIG_EXTENSIONS:
            return 'config'
        elif ext.lower() in self.DOC_EXTENSIONS:
            return 'doc'
        else:
            return 'other'

    def get_risk_level(self, path: str) -> SafetyLevel:
        """
        获取文件风险级别。

        参数:
            path: 文件路径

        返回:
            SafetyLevel 风险级别
        """
        category = self.classify(path)

        if category == 'code':
            return SafetyLevel.MEDIUM
        elif category == 'config':
            return SafetyLevel.MEDIUM
        elif category == 'doc':
            return SafetyLevel.LOW
        else:
            return SafetyLevel.LOW
