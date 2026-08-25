#!/usr/bin/env python3
"""
Codex Harness — 命令安全检查器

检查命令安全性。
对应 Codex 的命令安全检查逻辑。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from typing import Optional
from safety.types import SafetyLevel, SafetyCheck, SafetyResult, SafetyPolicy


# ============================================================================
# 命令安全检查器
# ============================================================================

class CommandSafetyChecker:
    """
    命令安全检查器。
    对应 Codex 的命令安全检查逻辑。

    检查:
    1. 禁止命令
    2. 危险模式
    3. shell 注入
    4. 命令复杂度
    """

    # 危险命令模式
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf\s+/',           # rm -rf /
        r'mkfs',                    # mkfs
        r'dd\s+if=',               # dd if=
        r':\(\)\{.*\|.*\}',       # fork bomb
        r'chmod\s+777',            # chmod 777
        r'wget\s+http://',         # wget http://
        r'curl\s+http://',         # curl http://
    ]

    # shell 注入模式
    INJECTION_PATTERNS = [
        r';\s*rm\s',               # ; rm
        r'\|\s*rm\s',              # | rm
        r'`rm\s',                  # `rm`
        r'\$\(rm\s',              # $(rm
    ]

    def __init__(self, policy: Optional[SafetyPolicy] = None):
        """
        初始化命令安全检查器。

        参数:
            policy: 安全策略 (None 使用默认策略)
        """
        self.policy = policy or SafetyPolicy()

    def check(self, command: str) -> SafetyResult:
        """
        检查命令安全性。

        参数:
            command: 命令字符串

        返回:
            SafetyResult 安全检查结果
        """
        if not command or not command.strip():
            return SafetyResult(
                check=SafetyCheck.AUTO_APPROVE,
                level=SafetyLevel.LOW,
                operation='terminal',
            )

        command = command.strip()

        # 1. 检查禁止命令
        deny_result = self._check_denied_commands(command)
        if deny_result:
            return deny_result

        # 2. 检查危险模式
        danger_result = self._check_dangerous_patterns(command)
        if danger_result:
            return danger_result

        # 3. 检查 shell 注入
        injection_result = self._check_injection_patterns(command)
        if injection_result:
            return injection_result

        # 4. 检查命令复杂度
        complexity_result = self._check_complexity(command)
        if complexity_result:
            return complexity_result

        # 5. 默认允许
        return SafetyResult(
            check=SafetyCheck.AUTO_APPROVE,
            level=SafetyLevel.LOW,
            operation='terminal',
        )

    def _check_denied_commands(self, command: str) -> Optional[SafetyResult]:
        """
        检查禁止命令。

        参数:
            command: 命令字符串

        返回:
            SafetyResult 如果被禁止，否则 None
        """
        command_lower = command.lower()

        for denied in self.policy.denied_commands:
            if denied.lower() in command_lower:
                return SafetyResult(
                    check=SafetyCheck.REJECT,
                    level=SafetyLevel.CRITICAL,
                    reason=f"Denied command: {denied}",
                    details={"command": command, "denied_pattern": denied},
                    operation='terminal',
                )

        return None

    def _check_dangerous_patterns(self, command: str) -> Optional[SafetyResult]:
        """
        检查危险模式。

        参数:
            command: 命令字符串

        返回:
            SafetyResult 如果危险，否则 None
        """
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return SafetyResult(
                    check=SafetyCheck.REJECT,
                    level=SafetyLevel.CRITICAL,
                    reason=f"Dangerous pattern detected: {pattern}",
                    details={"command": command, "pattern": pattern},
                    operation='terminal',
                )

        return None

    def _check_injection_patterns(self, command: str) -> Optional[SafetyResult]:
        """
        检查 shell 注入模式。

        参数:
            command: 命令字符串

        返回:
            SafetyResult 如果有注入风险，否则 None
        """
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return SafetyResult(
                    check=SafetyCheck.ASK_USER,
                    level=SafetyLevel.HIGH,
                    reason=f"Potential shell injection: {pattern}",
                    details={"command": command, "pattern": pattern},
                    operation='terminal',
                )

        return None

    def _check_complexity(self, command: str) -> Optional[SafetyResult]:
        """
        检查命令复杂度。

        参数:
            command: 命令字符串

        返回:
            SafetyResult 如果复杂度高，否则 None
        """
        # 计算复杂度分数
        score = 0

        # 命令长度
        if len(command) > 1000:
            score += 2

        # 管道数量
        pipe_count = command.count('|')
        score += min(pipe_count, 3)

        # 重定向
        if '>' in command or '<' in command:
            score += 1

        # 后台执行
        if '&' in command:
            score += 1

        # 多命令
        if ';' in command:
            score += 1

        # 子shell
        if '`' in command or '$(' in command:
            score += 2

        # 根据分数返回结果
        if score >= 4:
            return SafetyResult(
                check=SafetyCheck.ASK_USER,
                level=SafetyLevel.HIGH,
                reason=f"High complexity command (score: {score})",
                details={"command": command, "score": score},
                operation='terminal',
            )

        return None


# ============================================================================
# 命令分类器
# ============================================================================

class CommandClassifier:
    """
    命令分类器。
    将命令分为不同类别。
    """

    # 安全命令 (自动批准)
    SAFE_COMMANDS = {
        'ls', 'pwd', 'whoami', 'date', 'echo', 'cat', 'head', 'tail',
        'grep', 'find', 'wc', 'sort', 'uniq', 'diff', 'file', 'stat',
        'which', 'whereis', 'type', 'history', 'env', 'printenv',
    }

    # 需要审查的命令
    REVIEW_COMMANDS = {
        'sudo', 'su', 'docker', 'kubectl', 'systemctl', 'service',
        'iptables', 'ufw', 'mount', 'umount', 'useradd', 'userdel',
        'usermod', 'groupadd', 'groupdel',
    }

    def classify(self, command: str) -> str:
        """
        分类命令。

        参数:
            command: 命令字符串

        返回:
            命令类别: 'safe', 'review', 'dangerous'
        """
        if not command:
            return 'safe'

        # 提取第一个命令
        parts = command.strip().split()
        if not parts:
            return 'safe'

        first_cmd = parts[0]

        # 检查安全命令
        if first_cmd in self.SAFE_COMMANDS:
            return 'safe'

        # 检查需要审查的命令
        if first_cmd in self.REVIEW_COMMANDS:
            return 'review'

        # 默认需要审查
        return 'review'

    def get_risk_level(self, command: str) -> SafetyLevel:
        """
        获取命令风险级别。

        参数:
            command: 命令字符串

        返回:
            SafetyLevel 风险级别
        """
        category = self.classify(command)

        if category == 'safe':
            return SafetyLevel.LOW
        elif category == 'review':
            return SafetyLevel.MEDIUM
        else:
            return SafetyLevel.HIGH
