#!/usr/bin/env python3
"""
Codex Harness — 命令规范化函数

规范化命令用于审批缓存匹配。
对应 Codex 的 canonicalize_command_for_approval。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List
from canonicalization.parser import (
    parse_shell_lc_plain_commands,
    extract_bash_command,
    extract_powershell_command,
)


# ============================================================================
# 规范化前缀
# ============================================================================

# 对应 Codex: CANONICAL_BASH_SCRIPT_PREFIX
CANONICAL_BASH_SCRIPT_PREFIX = "__codex_shell_script__"

# 对应 Codex: CANONICAL_POWERSHELL_SCRIPT_PREFIX
CANONICAL_POWERSHELL_SCRIPT_PREFIX = "__codex_powershell_script__"


# ============================================================================
# 命令规范化
# ============================================================================

def canonicalize_command_for_approval(command: List[str]) -> List[str]:
    """
    规范化命令用于审批缓存匹配。

    对应 Codex 的 canonicalize_command_for_approval。

    保持审批决策在不同的包装器路径和 shell 工具之间稳定。
    例如:
    - /bin/bash -lc "git status" → ['git', 'status']
    - bash -c "echo hello" → ['__codex_shell_script__', '-c', 'echo hello']

    参数:
        command: 命令参数列表

    返回:
        规范化后的命令列表
    """
    if not command:
        return []

    # 1. 尝试解析 shell -lc 命令
    parsed = parse_shell_lc_plain_commands(command)
    if parsed and len(parsed) == 1:
        return parsed[0]

    # 2. 尝试提取 bash 脚本
    bash_result = extract_bash_command(command)
    if bash_result:
        shell, script = bash_result
        shell_mode = command[1] if len(command) > 1 else ""
        return [CANONICAL_BASH_SCRIPT_PREFIX, shell_mode, script]

    # 3. 尝试提取 powershell 脚本
    powershell_result = extract_powershell_command(command)
    if powershell_result:
        shell, script = powershell_result
        return [CANONICAL_POWERSHELL_SCRIPT_PREFIX, script]

    # 4. 原样返回
    return command


def canonicalize_command_string(command_str: str) -> str:
    """
    规范化命令字符串。

    参数:
        command_str: 命令字符串

    返回:
        规范化后的命令字符串
    """
    from canonicalization.parser import split_command_string, join_command_args

    # 拆分命令
    command = split_command_string(command_str)

    # 规范化
    canonical = canonicalize_command_for_approval(command)

    # 合并回字符串
    return join_command_args(canonical)


def commands_match(command1: List[str], command2: List[str]) -> bool:
    """
    检查两个命令是否匹配 (规范化后)。

    参数:
        command1: 命令1参数列表
        command2: 命令2参数列表

    返回:
        True 如果匹配
    """
    canonical1 = canonicalize_command_for_approval(command1)
    canonical2 = canonicalize_command_for_approval(command2)

    return canonical1 == canonical2


def get_command_signature(command: List[str]) -> str:
    """
    获取命令签名 (用于缓存键)。

    参数:
        command: 命令参数列表

    返回:
        命令签名字符串
    """
    canonical = canonicalize_command_for_approval(command)
    return ' '.join(canonical)


# ============================================================================
# 命令分类
# ============================================================================

def classify_command(command: List[str]) -> str:
    """
    分类命令类型。

    参数:
        command: 命令参数列表

    返回:
        命令类型: 'simple', 'shell', 'script', 'complex'
    """
    if not command:
        return 'empty'

    # 检查是否是简单命令
    if len(command) == 1:
        return 'simple'

    # 检查是否是 shell 命令
    from canonicalization.parser import is_shell_command
    if is_shell_command(command):
        # 检查是否是简单 shell 命令
        parsed = parse_shell_lc_plain_commands(command)
        if parsed and len(parsed) == 1:
            return 'simple'
        return 'script'

    # 检查是否是复杂命令 (包含管道、重定向等)
    command_str = ' '.join(command)
    if any(char in command_str for char in ['|', '>', '<', '&', ';']):
        return 'complex'

    return 'simple'


def get_command_complexity(command: List[str]) -> int:
    """
    获取命令复杂度分数。

    参数:
        command: 命令参数列表

    返回:
        复杂度分数 (0-10)
    """
    if not command:
        return 0

    score = 0

    # 参数数量
    score += min(len(command), 5)

    # 是否是 shell 命令
    from canonicalization.parser import is_shell_command
    if is_shell_command(command):
        score += 2

    # 是否包含特殊字符
    command_str = ' '.join(command)
    if '|' in command_str:
        score += 2
    if '>' in command_str or '<' in command_str:
        score += 1
    if '&' in command_str:
        score += 1
    if ';' in command_str:
        score += 1

    return min(score, 10)
