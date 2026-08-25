#!/usr/bin/env python3
"""
Codex Harness — 命令规范化系统

提供命令规范化和审批缓存能力。
对应 Codex 的 command_canonicalization 系统。

Python 兼容性: 3.6+
"""

from canonicalization.parser import (
    parse_shell_lc_plain_commands,
    extract_bash_command,
    extract_powershell_command,
    extract_script_from_command,
    is_shell_command,
    get_shell_type,
    split_command_string,
    join_command_args,
)
from canonicalization.canonicalizer import (
    canonicalize_command_for_approval,
    canonicalize_command_string,
    commands_match,
    get_command_signature,
    classify_command,
    get_command_complexity,
    CANONICAL_BASH_SCRIPT_PREFIX,
    CANONICAL_POWERSHELL_SCRIPT_PREFIX,
)
from canonicalization.cache import (
    ApprovalCache,
    ApprovalCacheManager,
    get_global_cache,
    check_approval_cache,
    set_approval_cache,
    clear_approval_cache,
)

__all__ = [
    'parse_shell_lc_plain_commands',
    'extract_bash_command',
    'extract_powershell_command',
    'extract_script_from_command',
    'is_shell_command',
    'get_shell_type',
    'split_command_string',
    'join_command_args',
    'canonicalize_command_for_approval',
    'canonicalize_command_string',
    'commands_match',
    'get_command_signature',
    'classify_command',
    'get_command_complexity',
    'CANONICAL_BASH_SCRIPT_PREFIX',
    'CANONICAL_POWERSHELL_SCRIPT_PREFIX',
    'ApprovalCache',
    'ApprovalCacheManager',
    'get_global_cache',
    'check_approval_cache',
    'set_approval_cache',
    'clear_approval_cache',
]
