#!/usr/bin/env python3
"""
Codex Harness — 补丁系统

提供安全的代码补丁应用能力。
对应 Codex 的 apply_patch 系统。

Python 兼容性: 3.6+
"""

from patch.action import (
    PatchAction,
    FileChange,
    PatchResult,
    SafetyCheck,
    SafetyCheckResult,
)
from patch.parser import PatchParser, PatchValidator
from patch.safety import PatchSafetyChecker, PatchSecurityPolicy, PatchSafetyResult
from patch.applicator import PatchApplicator, DryRunApplicator
from patch.manager import PatchManager, PatchConfig

__all__ = [
    'PatchAction',
    'FileChange',
    'PatchResult',
    'SafetyCheck',
    'SafetyCheckResult',
    'PatchParser',
    'PatchValidator',
    'PatchSafetyChecker',
    'PatchSecurityPolicy',
    'PatchSafetyResult',
    'PatchApplicator',
    'DryRunApplicator',
    'PatchManager',
    'PatchConfig',
]
