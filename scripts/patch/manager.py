#!/usr/bin/env python3
"""
Codex Harness — 补丁管理器

统一管理补丁操作。
对应 Codex 的补丁管理系统。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from typing import List, Dict, Any, Optional
from patch.action import PatchResult, SafetyCheck
from patch.parser import PatchParser, PatchValidator
from patch.safety import PatchSafetyChecker, PatchSecurityPolicy
from patch.applicator import PatchApplicator, DryRunApplicator


# ============================================================================
# 补丁配置
# ============================================================================

class PatchConfig:
    """
    补丁配置。

    属性:
        allowed_dirs: 允许的目录列表
        create_backup: 是否创建备份
        dry_run: 是否为干运行模式
        check_safety: 是否检查安全性
    """
    def __init__(
        self,
        allowed_dirs: Optional[List[str]] = None,
        create_backup: bool = True,
        dry_run: bool = False,
        check_safety: bool = True,
    ):
        """
        初始化补丁配置。

        参数:
            allowed_dirs: 允许的目录列表
            create_backup: 是否创建备份
            dry_run: 是否为干运行模式
            check_safety: 是否检查安全性
        """
        self.allowed_dirs = allowed_dirs or ['.']
        self.create_backup = create_backup
        self.dry_run = dry_run
        self.check_safety = check_safety

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "allowed_dirs": self.allowed_dirs,
            "create_backup": self.create_backup,
            "dry_run": self.dry_run,
            "check_safety": self.check_safety,
        }


# ============================================================================
# 补丁管理器
# ============================================================================

class PatchManager:
    """
    补丁管理器。
    统一管理补丁操作。

    功能:
    - 补丁解析
    - 安全检查
    - 补丁应用
    - 补丁回滚
    - 历史记录
    """

    def __init__(self, config: Optional[PatchConfig] = None):
        """
        初始化补丁管理器。

        参数:
            config: 补丁配置 (None 使用默认配置)
        """
        self.config = config or PatchConfig()
        self.parser = PatchParser()
        self.validator = PatchValidator()
        self.checker = PatchSafetyChecker(
            allowed_dirs=self.config.allowed_dirs,
        )
        self.applicator = PatchApplicator(
            create_backup=self.config.create_backup,
            dry_run=self.config.dry_run,
        )
        self.history: List[Dict[str, Any]] = []

    def apply_patch(self, patch_text: str) -> PatchResult:
        """
        应用补丁。

        流程:
        1. 验证补丁格式
        2. 解析补丁
        3. 安全检查
        4. 应用补丁
        5. 记录历史

        参数:
            patch_text: unified diff 格式的补丁文本

        返回:
            PatchResult 补丁结果
        """
        start_time = time.time()

        # 1. 验证补丁格式
        validation = self.validator.validate(patch_text)
        if not validation['valid']:
            return PatchResult(
                success=False,
                changes_applied=0,
                changes_failed=1,
                errors=[f"Invalid patch: {validation.get('error', 'Unknown error')}"],
            )

        # 2. 解析补丁
        changes = self.parser.parse(patch_text)
        if not changes:
            return PatchResult(
                success=False,
                changes_applied=0,
                changes_failed=1,
                errors=["No changes found in patch"],
            )

        # 3. 安全检查
        if self.config.check_safety:
            safety_result = self.checker.check(changes)
            if safety_result.is_reject:
                return PatchResult(
                    success=False,
                    changes_applied=0,
                    changes_failed=len(changes),
                    errors=[f"Safety check failed: {safety_result.reason}"],
                )

        # 4. 应用补丁
        result = self.applicator.apply(changes)

        # 5. 记录历史
        duration_ms = (time.time() - start_time) * 1000
        self._record_history(
            patch_text=patch_text,
            changes=len(changes),
            result=result,
            duration_ms=duration_ms,
        )

        return result

    def dry_run(self, patch_text: str) -> PatchResult:
        """
        干运行补丁。

        参数:
            patch_text: unified diff 格式的补丁文本

        返回:
            PatchResult 补丁结果
        """
        # 创建干运行应用器
        dry_run_applicator = DryRunApplicator()

        # 验证补丁格式
        validation = self.validator.validate(patch_text)
        if not validation['valid']:
            return PatchResult(
                success=False,
                changes_applied=0,
                changes_failed=1,
                errors=[f"Invalid patch: {validation.get('error', 'Unknown error')}"],
            )

        # 解析补丁
        changes = self.parser.parse(patch_text)
        if not changes:
            return PatchResult(
                success=False,
                changes_applied=0,
                changes_failed=1,
                errors=["No changes found in patch"],
            )

        # 安全检查
        if self.config.check_safety:
            safety_result = self.checker.check(changes)
            if safety_result.is_reject:
                return PatchResult(
                    success=False,
                    changes_applied=0,
                    changes_failed=len(changes),
                    errors=[f"Safety check failed: {safety_result.reason}"],
                )

        # 干运行应用
        return dry_run_applicator.apply(changes)

    def rollback(self, backup_path: str) -> PatchResult:
        """
        回滚补丁。

        参数:
            backup_path: 备份路径

        返回:
            PatchResult 补丁结果
        """
        return self.applicator.rollback(backup_path)

    def validate_patch(self, patch_text: str) -> Dict[str, Any]:
        """
        验证补丁。

        参数:
            patch_text: 补丁文本

        返回:
            验证结果字典
        """
        return self.validator.validate(patch_text)

    def check_safety(self, patch_text: str) -> Dict[str, Any]:
        """
        检查补丁安全性。

        参数:
            patch_text: 补丁文本

        返回:
            安全检查结果字典
        """
        # 解析补丁
        changes = self.parser.parse(patch_text)
        if not changes:
            return {
                "safe": False,
                "error": "No changes found",
            }

        # 安全检查
        result = self.checker.check(changes)

        return {
            "safe": result.is_auto_approve,
            "needs_approval": result.is_ask_user,
            "rejected": result.is_reject,
            "reason": result.reason,
        }

    def get_history(self) -> List[Dict[str, Any]]:
        """
        获取补丁历史。

        返回:
            历史记录列表
        """
        return self.history

    def clear_history(self):
        """清除补丁历史"""
        self.history = []

    def _record_history(
        self,
        patch_text: str,
        changes: int,
        result: PatchResult,
        duration_ms: float,
    ):
        """
        记录补丁历史。

        参数:
            patch_text: 补丁文本
            changes: 变更数
            result: 补丁结果
            duration_ms: 耗时
        """
        self.history.append({
            "timestamp": time.time(),
            "patch_text_length": len(patch_text),
            "changes": changes,
            "success": result.success,
            "changes_applied": result.changes_applied,
            "changes_failed": result.changes_failed,
            "duration_ms": round(duration_ms, 2),
            "backup_path": result.backup_path,
        })

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息。

        返回:
            统计字典
        """
        if not self.history:
            return {
                "total_patches": 0,
                "success_rate": 0.0,
                "average_duration_ms": 0.0,
                "total_changes_applied": 0,
            }

        total = len(self.history)
        successful = sum(1 for h in self.history if h["success"])
        success_rate = successful / total

        average_duration = sum(h["duration_ms"] for h in self.history) / total
        total_applied = sum(h["changes_applied"] for h in self.history)

        return {
            "total_patches": total,
            "success_rate": round(success_rate, 3),
            "average_duration_ms": round(average_duration, 2),
            "total_changes_applied": total_applied,
            "history": self.history[-10:],  # 最近 10 条
        }
