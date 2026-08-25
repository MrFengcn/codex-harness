#!/usr/bin/env python3
"""
Codex Harness — 补丁应用器

应用补丁到文件系统。
对应 Codex 的 ApplyPatchHandler。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import shutil
import time
from typing import List, Optional
from patch.action import PatchAction, FileChange, PatchResult


# ============================================================================
# 补丁应用器
# ============================================================================

class PatchApplicator:
    """
    补丁应用器。
    对应 Codex 的 ApplyPatchHandler。

    功能:
    - 应用文件变更
    - 创建备份
    - 回滚变更
    """

    def __init__(
        self,
        backup_dir: Optional[str] = None,
        create_backup: bool = True,
        dry_run: bool = False,
    ):
        """
        初始化补丁应用器。

        参数:
            backup_dir: 备份目录 (None 使用默认)
            create_backup: 是否创建备份
            dry_run: 是否为干运行模式
        """
        self.backup_dir = backup_dir or os.path.join(os.getcwd(), '.patch_backups')
        self.create_backup = create_backup
        self.dry_run = dry_run

    def apply(self, changes: List[FileChange]) -> PatchResult:
        """
        应用补丁。

        参数:
            changes: 文件变更列表

        返回:
            PatchResult 补丁结果
        """
        if not changes:
            return PatchResult(success=True, changes_applied=0, changes_failed=0)

        # 创建备份目录
        backup_path = None
        if self.create_backup:
            backup_path = self._create_backup_dir()

        # 应用变更
        applied = 0
        failed = 0
        errors = []

        for change in changes:
            try:
                if self._apply_change(change, backup_path):
                    applied += 1
                else:
                    failed += 1
                    errors.append(f"Failed to apply: {change.path}")
            except Exception as e:
                failed += 1
                errors.append(f"Error applying {change.path}: {str(e)}")

        success = failed == 0

        return PatchResult(
            success=success,
            changes_applied=applied,
            changes_failed=failed,
            errors=errors,
            backup_path=backup_path,
        )

    def _create_backup_dir(self) -> str:
        """
        创建备份目录。

        返回:
            备份目录路径
        """
        timestamp = int(time.time())
        backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}")

        if not self.dry_run:
            os.makedirs(backup_path, exist_ok=True)

        return backup_path

    def _apply_change(self, change: FileChange, backup_path: Optional[str]) -> bool:
        """
        应用单个变更。

        参数:
            change: 文件变更
            backup_path: 备份路径

        返回:
            True 如果成功
        """
        if change.action == PatchAction.ADD:
            return self._apply_add(change, backup_path)
        elif change.action == PatchAction.DELETE:
            return self._apply_delete(change, backup_path)
        elif change.action == PatchAction.UPDATE:
            return self._apply_update(change, backup_path)
        else:
            return False

    def _apply_add(self, change: FileChange, backup_path: Optional[str]) -> bool:
        """
        应用添加文件。

        参数:
            change: 文件变更
            backup_path: 备份路径

        返回:
            True 如果成功
        """
        path = change.path

        # 检查文件是否已存在
        if os.path.exists(path):
            # 备份现有文件
            if backup_path:
                self._backup_file(path, backup_path)

        # 创建目录
        dir_path = os.path.dirname(path)
        if dir_path and not self.dry_run:
            os.makedirs(dir_path, exist_ok=True)

        # 写入文件
        if not self.dry_run:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(change.content)

        return True

    def _apply_delete(self, change: FileChange, backup_path: Optional[str]) -> bool:
        """
        应用删除文件。

        参数:
            change: 文件变更
            backup_path: 备份路径

        返回:
            True 如果成功
        """
        path = change.path

        # 检查文件是否存在
        if not os.path.exists(path):
            return False

        # 备份文件
        if backup_path:
            self._backup_file(path, backup_path)

        # 删除文件
        if not self.dry_run:
            os.remove(path)

        return True

    def _apply_update(self, change: FileChange, backup_path: Optional[str]) -> bool:
        """
        应用更新文件。

        参数:
            change: 文件变更
            backup_path: 备份路径

        返回:
            True 如果成功
        """
        path = change.path

        # 检查文件是否存在
        if not os.path.exists(path):
            return False

        # 备份文件
        if backup_path:
            self._backup_file(path, backup_path)

        # 读取现有内容
        with open(path, 'r', encoding='utf-8') as f:
            existing_content = f.read()

        # 应用 diff
        new_content = self._apply_diff(existing_content, change.unified_diff)

        # 写入新内容
        if not self.dry_run:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)

        return True

    def _backup_file(self, path: str, backup_path: str):
        """
        备份文件。

        参数:
            path: 文件路径
            backup_path: 备份目录
        """
        if self.dry_run:
            return

        # 创建备份文件路径
        rel_path = os.path.relpath(path, os.getcwd())
        backup_file = os.path.join(backup_path, rel_path)

        # 创建备份目录
        backup_dir = os.path.dirname(backup_file)
        os.makedirs(backup_dir, exist_ok=True)

        # 复制文件
        shutil.copy2(path, backup_file)

    def _apply_diff(self, content: str, diff: str) -> str:
        """
        应用 diff 到内容。

        参数:
            content: 原始内容
            diff: unified diff

        返回:
            新内容
        """
        # 简化的 diff 应用
        # 实际实现应该解析 hunk 并正确应用
        lines = content.split('\n')
        diff_lines = diff.split('\n')

        result_lines = []
        i = 0

        for diff_line in diff_lines:
            if diff_line.startswith('+'):
                # 添加行
                result_lines.append(diff_line[1:])
            elif diff_line.startswith('-'):
                # 删除行 (跳过)
                i += 1
            elif diff_line.startswith(' '):
                # 上下文行
                result_lines.append(diff_line[1:])
                i += 1
            elif diff_line.startswith('@@'):
                # Hunk 头
                continue

        return '\n'.join(result_lines)

    def rollback(self, backup_path: str) -> PatchResult:
        """
        回滚补丁。

        参数:
            backup_path: 备份路径

        返回:
            PatchResult 补丁结果
        """
        if not os.path.exists(backup_path):
            return PatchResult(
                success=False,
                changes_applied=0,
                changes_failed=1,
                errors=[f"Backup path not found: {backup_path}"],
            )

        # 恢复备份文件
        applied = 0
        failed = 0
        errors = []

        for root, dirs, files in os.walk(backup_path):
            for file in files:
                backup_file = os.path.join(root, file)
                rel_path = os.path.relpath(backup_file, backup_path)
                original_file = os.path.join(os.getcwd(), rel_path)

                try:
                    # 创建目录
                    dir_path = os.path.dirname(original_file)
                    os.makedirs(dir_path, exist_ok=True)

                    # 复制文件
                    shutil.copy2(backup_file, original_file)
                    applied += 1
                except Exception as e:
                    failed += 1
                    errors.append(f"Error restoring {rel_path}: {str(e)}")

        success = failed == 0

        return PatchResult(
            success=success,
            changes_applied=applied,
            changes_failed=failed,
            errors=errors,
            backup_path=backup_path,
        )


# ============================================================================
# 干运行应用器
# ============================================================================

class DryRunApplicator(PatchApplicator):
    """
    干运行应用器。
    不实际修改文件，只检查是否可以应用。
    """

    def __init__(self):
        """初始化干运行应用器。"""
        super().__init__(dry_run=True)

    def apply(self, changes: List[FileChange]) -> PatchResult:
        """
        干运行应用补丁。

        参数:
            changes: 文件变更列表

        返回:
            PatchResult 补丁结果
        """
        # 检查每个变更
        applied = 0
        failed = 0
        errors = []

        for change in changes:
            if self._check_change(change):
                applied += 1
            else:
                failed += 1
                errors.append(f"Cannot apply: {change.path}")

        success = failed == 0

        return PatchResult(
            success=success,
            changes_applied=applied,
            changes_failed=failed,
            errors=errors,
        )

    def _check_change(self, change: FileChange) -> bool:
        """
        检查变更是否可以应用。

        参数:
            change: 文件变更

        返回:
            True 如果可以应用
        """
        path = change.path

        if change.action == PatchAction.ADD:
            # 检查目录是否可写
            dir_path = os.path.dirname(path)
            if dir_path and not os.path.exists(dir_path):
                # 检查父目录是否可写
                parent_dir = os.path.dirname(dir_path)
                if parent_dir and not os.access(parent_dir, os.W_OK):
                    return False
            return True

        elif change.action == PatchAction.DELETE:
            # 检查文件是否存在
            if not os.path.exists(path):
                return False
            # 检查文件是否可写
            if not os.access(path, os.W_OK):
                return False
            return True

        elif change.action == PatchAction.UPDATE:
            # 检查文件是否存在
            if not os.path.exists(path):
                return False
            # 检查文件是否可写
            if not os.access(path, os.W_OK):
                return False
            return True

        return False
