#!/usr/bin/env python3
"""
Codex Harness — 命令解析函数

解析 shell、bash、powershell 命令。
对应 Codex 的 command_canonicalization 辅助函数。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from typing import List, Optional, Tuple


# ============================================================================
# Shell 命令解析
# ============================================================================

# 常用 shell 路径
SHELL_PATHS = {
    'bash', '/bin/bash', '/usr/bin/bash',
    'sh', '/bin/sh', '/usr/bin/sh',
    'zsh', '/bin/zsh', '/usr/bin/zsh',
}

POWERSHELL_PATHS = {
    'powershell', 'pwsh',
}

# Shell 模式标志
SHELL_MODE_FLAGS = {'-c', '-lc', '-l', '-i'}


def parse_shell_lc_plain_commands(command: List[str]) -> Optional[List[List[str]]]:
    """
    解析 shell -lc 命令。

    将 bash -lc "git status" 解析为 [['git', 'status']]

    参数:
        command: 命令参数列表

    返回:
        解析后的命令列表，如果无法解析返回 None
    """
    if not command or len(command) < 3:
        return None

    # 检查是否是 shell 命令
    shell_name = command[0]
    if shell_name not in SHELL_PATHS:
        return None

    # 检查是否是 -lc 或 -c 模式
    if command[1] not in ('-lc', '-c'):
        return None

    # 获取脚本内容
    script = command[2]

    # 尝试解析简单命令 (没有管道、重定向等)
    if _is_simple_command(script):
        return [script.split()]

    return None


def _is_simple_command(script: str) -> bool:
    """
    检查是否是简单命令。

    简单命令: 没有管道、重定向、&&、|| 等

    参数:
        script: 脚本内容

    返回:
        True 如果是简单命令
    """
    # 检查是否包含特殊字符
    special_chars = {'|', '>', '<', '&', ';', '(', ')', '{', '}'}
    for char in special_chars:
        if char in script:
            return False

    return True


def extract_bash_command(command: List[str]) -> Optional[Tuple[str, str]]:
    """
    提取 bash 命令。

    将 bash -c "script" 提取为 ('bash', 'script')

    参数:
        command: 命令参数列表

    返回:
        (shell, script) 或 None
    """
    if not command or len(command) < 2:
        return None

    # 检查是否是 bash
    shell_name = command[0]
    if shell_name not in ('bash', '/bin/bash', '/usr/bin/bash'):
        return None

    # 提取脚本
    if len(command) >= 3 and command[1] in ('-c', '-lc', '-l'):
        script = command[2]
        return (shell_name, script)

    # 如果没有 -c，后面的都是脚本
    script = ' '.join(command[1:])
    return (shell_name, script)


def extract_powershell_command(command: List[str]) -> Optional[Tuple[str, str]]:
    """
    提取 powershell 命令。

    将 powershell -Command "script" 提取为 ('powershell', 'script')

    参数:
        command: 命令参数列表

    返回:
        (shell, script) 或 None
    """
    if not command or len(command) < 2:
        return None

    # 检查是否是 powershell
    shell_name = command[0]
    if shell_name not in POWERSHELL_PATHS:
        return None

    # 提取脚本
    if len(command) >= 3 and command[1] in ('-Command', '-c', '-C'):
        script = command[2]
        return (shell_name, script)

    # 如果没有 -Command，后面的都是脚本
    script = ' '.join(command[1:])
    return (shell_name, script)


def extract_script_from_command(command: List[str]) -> Optional[str]:
    """
    从命令中提取脚本内容。

    参数:
        command: 命令参数列表

    返回:
        脚本内容，如果无法提取返回 None
    """
    # 尝试提取 bash 脚本
    bash_result = extract_bash_command(command)
    if bash_result:
        return bash_result[1]

    # 尝试提取 powershell 脚本
    powershell_result = extract_powershell_command(command)
    if powershell_result:
        return powershell_result[1]

    # 尝试解析 shell -lc 命令
    parsed = parse_shell_lc_plain_commands(command)
    if parsed and len(parsed) == 1:
        return ' '.join(parsed[0])

    return None


def is_shell_command(command: List[str]) -> bool:
    """
    检查是否是 shell 命令。

    参数:
        command: 命令参数列表

    返回:
        True 如果是 shell 命令
    """
    if not command:
        return False

    return command[0] in SHELL_PATHS or command[0] in POWERSHELL_PATHS


def get_shell_type(command: List[str]) -> Optional[str]:
    """
    获取 shell 类型。

    参数:
        command: 命令参数列表

    返回:
        shell 类型 ('bash', 'sh', 'powershell' 等)，如果不是 shell 命令返回 None
    """
    if not command:
        return None

    shell_name = command[0]

    if shell_name in ('bash', '/bin/bash', '/usr/bin/bash'):
        return 'bash'
    elif shell_name in ('sh', '/bin/sh', '/usr/bin/sh'):
        return 'sh'
    elif shell_name in ('zsh', '/bin/zsh', '/usr/bin/zsh'):
        return 'zsh'
    elif shell_name in POWERSHELL_PATHS:
        return 'powershell'

    return None


def split_command_string(command_str: str) -> List[str]:
    """
    拆分命令字符串为参数列表。

    处理引号和转义字符。

    参数:
        command_str: 命令字符串

    返回:
        参数列表
    """
    import shlex

    try:
        return shlex.split(command_str)
    except ValueError:
        # 如果解析失败，简单拆分
        return command_str.split()


def join_command_args(command: List[str]) -> str:
    """
    将命令参数列表合并为字符串。

    参数:
        command: 命令参数列表

    返回:
        命令字符串
    """
    import shlex

    # 对包含空格的参数添加引号
    quoted = []
    for arg in command:
        if ' ' in arg or '\t' in arg:
            quoted.append(shlex.quote(arg))
        else:
            quoted.append(arg)

    return ' '.join(quoted)
