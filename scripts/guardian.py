#!/usr/bin/env python3
"""
Codex Harness — Guardian 安全审查引擎

负责: 安全策略匹配 + 风险评估 + 断路器 + 转录构建
对应 Codex: codex-rs/core/src/guardian/

所有共享类型从 core.py 导入。
安全策略 (FilePolicy, CommandPolicy, NetworkPolicy, SecretPolicy) 在 core.py 中。

Python 兼容性: 3.6+
"""

import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# 从 core.py 导入所有共享类型
from core import (
    GuardianAssessment,
    GuardianRiskLevel,
    GuardianUserAuthorization,
    GuardianAssessmentOutcome,
    CircuitBreakerState,
    CircuitBreakerPolicy,
    CircuitBreakerAction,
    FilePolicy,
    CommandPolicy,
    NetworkPolicy,
    SecretPolicy,
    estimate_tokens,
)


# ============================================================================
# Guardian 配置
# ============================================================================

class GuardianConfig:
    """Guardian 配置。对应 Codex 的 Guardian 配置系统。"""
    def __init__(
        self,
        timeout_seconds: int = 30,
        max_denials_per_turn: int = 3,
        max_consecutive_cyber_denials: int = 1,
        max_recent_auto_review_denials: int = 10,
        auto_review_denial_window_size: int = 50,
        enabled: bool = True,
    ):
        """初始化 Guardian 配置。"""
        self.timeout_seconds = timeout_seconds
        self.max_denials_per_turn = max_denials_per_turn
        self.max_consecutive_cyber_denials = max_consecutive_cyber_denials
        self.max_recent_auto_review_denials = max_recent_auto_review_denials
        self.auto_review_denial_window_size = auto_review_denial_window_size
        self.enabled = enabled

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            "timeout_seconds": self.timeout_seconds,
            "max_denials_per_turn": self.max_denials_per_turn,
            "max_consecutive_cyber_denials": self.max_consecutive_cyber_denials,
            "max_recent_auto_review_denials": self.max_recent_auto_review_denials,
            "auto_review_denial_window_size": self.auto_review_denial_window_size,
            "enabled": self.enabled,
        }


# ============================================================================
# Guardian 转录 (对应 Codex GuardianTranscript)
# ============================================================================

class GuardianTranscriptEntry:
    """Guardian 转录条目。"""
    def __init__(self, kind: str, text: str):
        """初始化转录条目。"""
        self.kind = kind
        self.text = text

    def to_dict(self) -> Dict[str, str]:
        """转换为字典格式。"""
        return {"kind": self.kind, "text": self.text}


class GuardianTranscript:
    """
    Guardian 转录。对应 Codex 的 GuardianTranscript。
    双预算: 消息 (10K tokens) + 工具 (10K tokens)
    """
    MAX_MESSAGE_TOKENS = 10000
    MAX_TOOL_TOKENS = 10000
    MAX_MESSAGE_ENTRY_TOKENS = 2000
    MAX_TOOL_ENTRY_TOKENS = 1000
    RECENT_ENTRY_LIMIT = 40

    def __init__(self):
        """初始化 Guardian 转录。"""
        self.entries: List[GuardianTranscriptEntry] = []

    def add_entry(self, kind: str, text: str):
        """添加转录条目。"""
        entry = GuardianTranscriptEntry(kind, text)
        self.entries.append(entry)

    def build_compact(self) -> str:
        """构建紧凑转录。双预算: 消息 (10K) + 工具 (10K)。"""
        recent_entries = self.entries[-self.RECENT_ENTRY_LIMIT:]
        message_entries = [e for e in recent_entries if e.kind in ("developer", "user", "assistant")]
        tool_entries = [e for e in recent_entries if e.kind == "tool"]

        message_parts = []
        message_tokens = 0
        for entry in reversed(message_entries):
            entry_tokens = estimate_tokens(entry.text)
            if message_tokens + entry_tokens > self.MAX_MESSAGE_TOKENS:
                remaining = self.MAX_MESSAGE_TOKENS - message_tokens
                if remaining > 0:
                    truncated = entry.text[:remaining * 4]
                    message_parts.insert(0, f"[{entry.kind}]: {truncated}...[truncated]")
                break
            message_parts.insert(0, f"[{entry.kind}]: {entry.text}")
            message_tokens += entry_tokens

        tool_parts = []
        tool_tokens = 0
        for entry in reversed(tool_entries):
            entry_tokens = estimate_tokens(entry.text)
            if tool_tokens + entry_tokens > self.MAX_TOOL_TOKENS:
                remaining = self.MAX_TOOL_TOKENS - tool_tokens
                if remaining > 0:
                    truncated = entry.text[:remaining * 4]
                    tool_parts.insert(0, f"[tool]: {truncated}...[truncated]")
                break
            tool_parts.insert(0, f"[tool]: {entry.text}")
            tool_tokens += entry_tokens

        parts = []
        if message_parts:
            parts.append("=== Recent Messages ===\n" + "\n".join(message_parts))
        if tool_parts:
            parts.append("=== Recent Tool Calls ===\n" + "\n".join(tool_parts))
        return "\n\n".join(parts)


# ============================================================================
# Guardian 审查器 (对应 Codex GuardianReviewer)
# ============================================================================

class GuardianReviewer:
    """
    Guardian 安全审查器。对应 Codex 的 GuardianReviewer。
    实现: 安全策略匹配 + 风险评估 + 断路器 + 转录构建 + Fail-closed
    """
    def __init__(self, config: Optional[GuardianConfig] = None):
        """初始化 Guardian 审查器。"""
        self.config = config or GuardianConfig()
        self.circuit_breaker = CircuitBreakerState()
        self.denial_log: List[Dict[str, Any]] = []
        self.transcript = GuardianTranscript()

    def review(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        turn_id: str = "default",
        context: Optional[Dict[str, Any]] = None,
    ) -> GuardianAssessment:
        """审查工具调用。返回 GuardianAssessment。"""
        if not self.config.enabled:
            return GuardianAssessment(
                risk_level=GuardianRiskLevel.Low,
                user_authorization=GuardianUserAuthorization.Unknown,
                outcome=GuardianAssessmentOutcome.Allow,
                rationale="Guardian disabled",
            )

        if self.circuit_breaker.is_interrupted(turn_id):
            return GuardianAssessment(
                risk_level=GuardianRiskLevel.High,
                user_authorization=GuardianUserAuthorization.Unknown,
                outcome=GuardianAssessmentOutcome.Deny,
                rationale="Circuit breaker interrupted",
            )

        action = self._build_action_description(tool_name, tool_args)
        risk_level = GuardianRiskLevel.Low
        denial_reasons = []

        # 1. 文件策略检查
        if tool_name in ("write_file", "patch"):
            path = tool_args.get("path", "")
            file_check = FilePolicy.check(path)
            if file_check == "deny":
                risk_level = GuardianRiskLevel.Critical
                denial_reasons.append(f"File access denied: {path}")
            elif file_check == "review":
                risk_level = max(risk_level, GuardianRiskLevel.Medium, key=lambda x: x.value)

        # 2. 命令策略检查
        if tool_name in ("terminal", "execute_code"):
            command = tool_args.get("command", "")
            cmd_check = CommandPolicy.check(command)
            if cmd_check == "deny":
                risk_level = GuardianRiskLevel.Critical
                denial_reasons.append(f"Command denied: {command[:100]}")
            elif cmd_check == "review":
                risk_level = max(risk_level, GuardianRiskLevel.Medium, key=lambda x: x.value)
            secrets = SecretPolicy.scan(command)
            if secrets:
                risk_level = GuardianRiskLevel.Critical
                denial_reasons.append("Command contains potential secrets")

        # 3. 网络策略检查
        if tool_name in ("browser_navigate",):
            url = tool_args.get("url", "")
            net_check = NetworkPolicy.check(url)
            if net_check == "deny":
                risk_level = GuardianRiskLevel.Critical
                denial_reasons.append(f"Network access denied: {url}")
            elif net_check == "review":
                risk_level = max(risk_level, GuardianRiskLevel.Medium, key=lambda x: x.value)

        # 4. 敏感操作检查
        sensitive_tools = {"send_message", "cronjob", "delegate_task"}
        if tool_name in sensitive_tools:
            risk_level = max(risk_level, GuardianRiskLevel.Medium, key=lambda x: x.value)

        # 构建评估结果
        if denial_reasons:
            outcome = GuardianAssessmentOutcome.Deny
            rationale = "; ".join(denial_reasons)
            self._log_denial(tool_name, tool_args, turn_id, rationale)
            policy = CircuitBreakerPolicy.CyberModel if risk_level == GuardianRiskLevel.Critical else CircuitBreakerPolicy.Standard
            self.circuit_breaker.record_denial(turn_id, policy)
        else:
            outcome = GuardianAssessmentOutcome.Allow
            rationale = "All security policies passed"
            self.circuit_breaker.record_approval(turn_id)

        user_auth = self._assess_user_authorization(tool_name, tool_args, context)

        return GuardianAssessment(
            risk_level=risk_level,
            user_authorization=user_auth,
            outcome=outcome,
            rationale=rationale,
        )

    def _build_action_description(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """构建操作描述。"""
        if tool_name == "terminal":
            return f"Execute command: {tool_args.get('command', '')}"
        elif tool_name in ("write_file", "patch"):
            return f"Write file: {tool_args.get('path', '')}"
        elif tool_name == "browser_navigate":
            return f"Navigate to: {tool_args.get('url', '')}"
        else:
            return f"Tool call: {tool_name}"

    def _assess_user_authorization(
        self, tool_name: str, tool_args: Dict[str, Any], context: Optional[Dict[str, Any]],
    ) -> GuardianUserAuthorization:
        """评估用户授权级别。"""
        if tool_name in ("read_file", "search_files", "session_search"):
            return GuardianUserAuthorization.Low
        if tool_name in ("write_file", "patch"):
            return GuardianUserAuthorization.Medium
        if tool_name in ("terminal", "execute_code", "send_message", "cronjob", "delegate_task"):
            return GuardianUserAuthorization.High
        return GuardianUserAuthorization.Unknown

    def _log_denial(self, tool_name: str, tool_args: Dict[str, Any], turn_id: str, reason: str):
        """记录拒绝日志。"""
        self.denial_log.append({
            "timestamp": time.time(),
            "tool_name": tool_name,
            "tool_args": tool_args,
            "turn_id": turn_id,
            "reason": reason,
        })

    def clear_turn(self, turn_id: str):
        """清除指定 turn 的状态。"""
        self.circuit_breaker.clear_turn(turn_id)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息。"""
        return {
            "total_denials": len(self.denial_log),
            "circuit_breaker_turns": len(self.circuit_breaker.turns),
            "config": self.config.to_dict(),
        }


# ============================================================================
# CLI 接口
# ============================================================================

def cmd_review(args) -> None:
    """审查工具调用。"""
    reviewer = GuardianReviewer()
    tool_args = json.loads(args.args) if args.args else {}
    assessment = reviewer.review(args.tool_name, tool_args, turn_id=args.turn_id)
    print(json.dumps(assessment.to_dict(), indent=2))


def cmd_stats(args) -> None:
    """显示统计信息。"""
    reviewer = GuardianReviewer()
    print(json.dumps(reviewer.get_stats(), indent=2))


def main() -> None:
    """CLI 入口。"""
    import argparse
    parser = argparse.ArgumentParser(
        description="Codex Harness Guardian Security Review Engine",
        epilog="All security policies are in core.py.",
    )
    subparsers = parser.add_subparsers(dest="command")

    review_parser = subparsers.add_parser("review", help="Review a tool call")
    review_parser.add_argument("tool_name", help="Tool name")
    review_parser.add_argument("--args", default="{}", help="Tool args JSON")
    review_parser.add_argument("--turn-id", default="default", help="Turn ID")

    subparsers.add_parser("stats", help="Show Guardian statistics")

    args = parser.parse_args()

    if args.command == "review":
        cmd_review(args)
    elif args.command == "stats":
        cmd_stats(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()


# ============================================================================
# 安全管理器集成
# ============================================================================

class GuardianSafetyIntegration:
    """
    Guardian 安全管理器集成。
    将安全检查系统集成到 Guardian。

    功能:
    - 使用 SafetyManager 进行安全检查
    - 集成 GuardianReview
    - 统一安全评估
    """

    def __init__(self, guardian_config: Optional[GuardianConfig] = None):
        """
        初始化 Guardian 安全管理器集成。

        参数:
            guardian_config: Guardian 配置 (None 使用默认配置)
        """
        from safety import SafetyManager, SafetyPolicy

        # 创建 Guardian
        self.guardian = GuardianReviewer(guardian_config)

        # 创建安全管理器
        self.safety_manager = SafetyManager()

    def review_with_safety(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        turn_id: str = "default",
    ) -> Dict[str, Any]:
        """
        使用安全管理器进行 Guardian 审查。

        参数:
            tool_name: 工具名称
            tool_args: 工具参数
            turn_id: Turn ID

        返回:
            审查结果字典
        """
        # 1. 使用安全管理器检查
        safety_result = self.safety_manager.check_operation(tool_name, tool_args)

        # 2. 使用 Guardian 审查
        guardian_result = self.guardian.review(tool_name, tool_args, turn_id)

        # 3. 合并结果
        return {
            "safety": safety_result.to_dict(),
            "guardian": guardian_result.to_dict(),
            "allowed": safety_result.is_safe and guardian_result.is_allowed,
            "risk_level": max(safety_result.level, guardian_result.risk_level, key=lambda x: x.value).value,
        }

    def check_operation(self, operation: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查操作安全性。

        参数:
            operation: 操作类型
            args: 操作参数

        返回:
            检查结果字典
        """
        result = self.safety_manager.check_operation(operation, args)
        return result.to_dict()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息。

        返回:
            统计字典
        """
        return {
            "guardian": self.guardian.get_stats(),
            "safety": self.safety_manager.get_stats(),
        }
