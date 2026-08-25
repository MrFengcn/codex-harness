#!/usr/bin/env python3
"""
Codex Harness — 补丁解析器

解析 unified diff 格式的补丁。
对应 Codex 的 StreamingPatchParser。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from typing import List, Dict, Any
from patch.action import PatchAction, FileChange


# ============================================================================
# 补丁解析器
# ============================================================================

class PatchParser:
    """
    补丁解析器。
    对应 Codex 的 StreamingPatchParser。

    解析 unified diff 格式的补丁，生成 FileChange 列表。
    """

    # Unified diff 文件头模式
    FILE_HEADER_PATTERN = re.compile(r'^--- (.+)$', re.MULTILINE)
    NEW_FILE_PATTERN = re.compile(r'^\+\+\+ (.+)$', re.MULTILINE)

    # Hunk 头模式
    HUNK_HEADER_PATTERN = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', re.MULTILINE)

    def parse(self, patch_text: str) -> List[FileChange]:
        """
        解析补丁文本。

        参数:
            patch_text: unified diff 格式的补丁文本

        返回:
            FileChange 列表
        """
        if not patch_text or not patch_text.strip():
            return []

        changes = []
        lines = patch_text.split('\n')

        i = 0
        while i < len(lines):
            # 查找文件头
            if lines[i].startswith('--- '):
                change, i = self._parse_file_change(lines, i)
                if change:
                    changes.append(change)
            else:
                i += 1

        return changes

    def _parse_file_change(self, lines: List[str], start: int) -> tuple:
        """
        解析单个文件变更。

        参数:
            lines: 补丁行列表
            start: 开始行索引

        返回:
            (FileChange, 下一个行索引)
        """
        # 解析 --- 行
        old_file_match = self.FILE_HEADER_PATTERN.match(lines[start])
        if not old_file_match:
            return None, start + 1

        old_file = old_file_match.group(1)

        # 解析 +++ 行
        if start + 1 >= len(lines):
            return None, start + 1

        new_file_match = self.NEW_FILE_PATTERN.match(lines[start + 1])
        if not new_file_match:
            return None, start + 1

        new_file = new_file_match.group(1)

        # 判断动作类型
        if old_file == '/dev/null':
            action = PatchAction.ADD
            path = new_file
        elif new_file == '/dev/null':
            action = PatchAction.DELETE
            path = old_file
        else:
            action = PatchAction.UPDATE
            path = new_file

        # 解析 hunk
        hunks = []
        i = start + 2
        current_hunk = None

        while i < len(lines):
            line = lines[i]

            # 检查是否是新的文件头
            if line.startswith('--- '):
                break

            # 检查是否是 hunk 头
            hunk_match = self.HUNK_HEADER_PATTERN.match(line)
            if hunk_match:
                if current_hunk:
                    hunks.append(current_hunk)
                current_hunk = {
                    'old_start': int(hunk_match.group(1)),
                    'old_count': int(hunk_match.group(2)) if hunk_match.group(2) else 1,
                    'new_start': int(hunk_match.group(3)),
                    'new_count': int(hunk_match.group(4)) if hunk_match.group(4) else 1,
                    'lines': [],
                }
                i += 1
                continue

            # 收集 hunk 内容
            if current_hunk is not None:
                current_hunk['lines'].append(line)

            i += 1

        # 添加最后一个 hunk
        if current_hunk:
            hunks.append(current_hunk)

        # 构建 FileChange
        if action == PatchAction.ADD:
            content = self._extract_add_content(hunks)
            return FileChange(path=path, action=action, content=content), i
        elif action == PatchAction.DELETE:
            content = self._extract_delete_content(hunks)
            return FileChange(path=path, action=action, content=content), i
        else:
            unified_diff = self._build_unified_diff(old_file, new_file, hunks)
            return FileChange(path=path, action=action, unified_diff=unified_diff), i

    def _extract_add_content(self, hunks: List[Dict]) -> str:
        """
        提取添加的内容。

        参数:
            hunks: hunk 列表

        返回:
            文件内容
        """
        lines = []
        for hunk in hunks:
            for line in hunk['lines']:
                if line.startswith('+'):
                    lines.append(line[1:])
                elif line.startswith(' '):
                    lines.append(line[1:])
        return '\n'.join(lines)

    def _extract_delete_content(self, hunks: List[Dict]) -> str:
        """
        提取删除的内容。

        参数:
            hunks: hunk 列表

        返回:
            文件内容
        """
        lines = []
        for hunk in hunks:
            for line in hunk['lines']:
                if line.startswith('-'):
                    lines.append(line[1:])
                elif line.startswith(' '):
                    lines.append(line[1:])
        return '\n'.join(lines)

    def _build_unified_diff(self, old_file: str, new_file: str, hunks: List[Dict]) -> str:
        """
        构建 unified diff。

        参数:
            old_file: 旧文件路径
            new_file: 新文件路径
            hunks: hunk 列表

        返回:
            unified diff 字符串
        """
        parts = []
        parts.append(f'--- {old_file}')
        parts.append(f'+++ {new_file}')

        for hunk in hunks:
            old_count = hunk['old_count']
            new_count = hunk['new_count']
            parts.append(f'@@ -{hunk["old_start"]},{old_count} +{hunk["new_start"]},{new_count} @@')
            parts.extend(hunk['lines'])

        return '\n'.join(parts)


class PatchValidator:
    """
    补丁验证器。
    验证补丁格式和内容。
    """

    def validate(self, patch_text: str) -> Dict[str, Any]:
        """
        验证补丁文本。

        参数:
            patch_text: 补丁文本

        返回:
            验证结果字典
        """
        if not patch_text or not patch_text.strip():
            return {
                "valid": False,
                "error": "Empty patch",
            }

        # 检查是否包含 --- 和 +++
        if '--- ' not in patch_text or '+++ ' not in patch_text:
            return {
                "valid": False,
                "error": "Missing file headers",
            }

        # 检查是否包含 @@
        if '@@' not in patch_text:
            return {
                "valid": False,
                "error": "Missing hunk headers",
            }

        # 尝试解析
        parser = PatchParser()
        changes = parser.parse(patch_text)

        if not changes:
            return {
                "valid": False,
                "error": "No changes found",
            }

        # 验证每个变更
        errors = []
        for change in changes:
            if not change.validate():
                errors.append(f"Invalid change: {change.path}")

        if errors:
            return {
                "valid": False,
                "errors": errors,
            }

        return {
            "valid": True,
            "changes": len(changes),
        }
