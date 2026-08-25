#!/usr/bin/env python3
"""
Codex Harness — 补丁安全检查器 (安全模块版)

统一的补丁安全检查器，集成到安全检查系统。
对应 Codex 的 assess_patch_safety。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any, Optional
from safety.types import SafetyLevel, SafetyCheck, SafetyResult, SafetyPolicy


# ============================================================================
# 补丁安全检查器 (安全模块版)
# ============================================================================

class PatchSafetyChecker:
    """
    补丁安全检查器。
    对应 Codex 的 assess_patch_safety。

    集成到安全检查系统，提供统一的补丁安全评估。
    """

    def __init__(self, policy: Optional[SafetyPolicy] = None):
        """
        初始化补丁安全检查器。

        参数:
            policy: 安全策略 (None 使用默认策略)
        """
        self.policy = policy or SafetyPolicy()

    def check(
        self,
        changes: List[Dict[str, Any]],
        approval_policy: str = "auto",
    ) -> SafetyResult:
        """
        检查补丁安全性。

        参数:
            changes: 文件变更列表 [{'path': str, 'action': str, 'content': str}]
            approval_policy: 审批策略

        返回:
            SafetyResult 安全检查结果
        """
        if not changes:
            return SafetyResult(
                check=SafetyCheck.REJECT,
                level=SafetyLevel.LOW,
                reason="Empty patch",
                operation='apply_patch',
            )

        # 检查每个变更
        for change in changes:
            result = self._check_change(change, approval_policy)
            if result.is_reject:
                return result

        # 所有检查通过
        return SafetyResult(
            check=SafetyCheck.AUTO_APPROVE,
            level=SafetyLevel.MEDIUM,
            operation='apply_patch',
        )

    def check_single(
        self,
        path: str,
        action: str,
        content: Optional[str] = None,
    ) -> SafetyResult:
        """
        检查单个文件变更。

        参数:
            path: 文件路径
            action: 动作 (add/delete/update)
            content: 文件内容

        返回:
            SafetyResult 安全检查结果
        """
        change = {
            'path': path,
            'action': action,
            'content': content,
        }
        return self._check_change(change, "auto")

    def _check_change(
        self,
        change: Dict[str, Any],
        approval_policy: str,
    ) -> SafetyResult:
        """
        检查单个变更。

        参数:
            change: 文件变更
            approval_policy: 审批策略

        返回:
            SafetyResult 安全检查结果
        """
        path = change.get('path', '')
        action = change.get('action', '')

        # 1. 检查路径遍历
        if '..' in path:
            return SafetyResult(
                check=SafetyCheck.REJECT,
                level=SafetyLevel.HIGH,
                reason=f"Path traversal detected: {path}",
                details={"path": path, "action": action},
                path=path,
                operation='apply_patch',
            )

        # 2. 检查禁止路径
        for denied in self.policy.denied_paths:
            if path.startswith(denied):
                return SafetyResult(
                    check=SafetyCheck.REJECT,
                    level=SafetyLevel.CRITICAL,
                    reason=f"Access denied to path: {denied}",
                    details={"path": path, "action": action},
                    path=path,
                    operation='apply_patch',
                )

        # 3. 检查敏感文件
        filename = os.path.basename(path)
        for sensitive in self.policy.sensitive_files:
            if filename == sensitive:
                return SafetyResult(
                    check=SafetyCheck.REJECT,
                    level=SafetyLevel.HIGH,
                    reason=f"Access to sensitive file: {sensitive}",
                    details={"path": path, "action": action},
                    path=path,
                    operation='apply_patch',
                )

        # 4. 检查路径白名单
        if not self._is_in_allowed_dir(path):
            return SafetyResult(
                check=SafetyCheck.ASK_USER,
                level=SafetyLevel.MEDIUM,
                reason=f"Path not in allowed directories: {path}",
                details={"path": path, "action": action},
                path=path,
                operation='apply_patch',
            )

        # 5. 根据审批策略决定
        if approval_policy == "never":
            return SafetyResult(
                check=SafetyCheck.REJECT,
                level=SafetyLevel.HIGH,
                reason="Approval policy: never",
                details={"path": path, "action": action},
                path=path,
                operation='apply_patch',
            )

        return SafetyResult(
            check=SafetyCheck.AUTO_APPROVE,
            level=SafetyLevel.MEDIUM,
            path=path,
            operation='apply_patch',
        )

    def _is_in_allowed_dir(self, path: str) -> bool:
        """
        检查路径是否在允许的目录中。

        参数:
            path: 文件路径

        返回:
            True 如果在允许的目录中
        """
        normalized = os.path.normpath(os.path.abspath(path))

        for allowed in self.policy.allowed_dirs:
            allowed_abs = os.path.normpath(os.path.abspath(allowed))
            if normalized.startswith(allowed_abs):
                return True

        return False


# ============================================================================
# 补丁风险评估器
# ============================================================================

class PatchRiskAssessor:
    """
    补丁风险评估器。
    评估补丁的整体风险级别。
    """

    def assess(self, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        评估补丁风险。

        参数:
            changes: 文件变更列表

        返回:
            风险评估字典
        """
        if not changes:
            return {
                "risk_level": SafetyLevel.LOW.value,
                "total_changes": 0,
                "risk_factors": [],
            }

        risk_factors = []
        max_risk = SafetyLevel.LOW

        for change in changes:
            path = change.get('path', '')
            action = change.get('action', '')

            # 检查高风险操作
            if action == 'delete':
                risk_factors.append(f"Delete operation: {path}")
                max_risk = max(max_risk, SafetyLevel.HIGH)

            # 检查系统文件
            if path.startswith('/etc') or path.startswith('/usr'):
                risk_factors.append(f"System file: {path}")
                max_risk = max(max_risk, SafetyLevel.CRITICAL)

            # 检查配置文件
            if path.endswith(('.env', '.config', '.yaml', '.json')):
                risk_factors.append(f"Config file: {path}")
                max_risk = max(max_risk, SafetyLevel.MEDIUM)

        return {
            "risk_level": max_risk.value,
            "total_changes": len(changes),
            "risk_factors": risk_factors,
        }
