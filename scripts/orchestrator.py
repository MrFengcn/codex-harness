#!/usr/bin/env python3
"""
Codex Harness — 工具编排器

只负责: 审批 → 安全级别 → 沙箱选择 → 执行 → 重试升级
对应 Codex: codex-rs/core/src/tools/orchestrator.rs

所有共享类型从 core.py 导入。
Guardian/Context/Parallel/Hook/Agent 在各自独立的模块中。

Python 兼容性: 3.6+
"""

import json
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional

# 从 core.py 导入所有共享类型
from core import (
    SecurityLevel,
    ExecApprovalType,
    ExecApprovalRequirement,
    ExecPolicyAmendment,
    SandboxAttempt,
    SandboxOverrideType,
    SandboxError,
    SandboxErrorType,
    FilePolicy,
    CommandPolicy,
    NetworkPolicy,
    SecretPolicy,
    classify_tool,
    determine_approval_requirement,
    shell_escape,
)


# ============================================================================
# 编排结果 (对应 Codex OrchestratorRunResult)
# ============================================================================

class OrchestratorResult:
    """
    工具编排结果。
    对应 Codex 的 OrchestratorRunResult。
    """
    def __init__(
        self,
        success: bool,
        output: Any = None,
        error: Optional[str] = None,
        attempts: Optional[List[Dict[str, Any]]] = None,
        final_security_level: SecurityLevel = SecurityLevel.NONE,
        total_duration_ms: float = 0.0,
        escalated: bool = False,
        guardian_approved: bool = False,
    ):
        """初始化编排结果。"""
        self.success = success
        self.output = output
        self.error = error
        self.attempts = attempts or []
        self.final_security_level = final_security_level
        self.total_duration_ms = total_duration_ms
        self.escalated = escalated
        self.guardian_approved = guardian_approved

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            "success": self.success,
            "output": str(self.output)[:500] if self.output else None,
            "error": self.error,
            "attempts": self.attempts,
            "final_security_level": self.final_security_level.value,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "escalated": self.escalated,
            "guardian_approved": self.guardian_approved,
        }


# ============================================================================
# 工具编排器 (对应 Codex ToolOrchestrator)
# 来源: codex-rs/core/src/tools/orchestrator.rs
# ============================================================================

class ToolOrchestrator:
    """
    工具执行编排器。
    对应 Codex 的 ToolOrchestrator。

    核心流程 (与 Codex 一致):
    1. 审批检查 (ExecApprovalRequirement: Skip/Forbidden/NeedsApproval)
    2. 沙箱选择 (基于安全级别和策略)
    3. 第一次执行尝试
    4. 如果沙箱违规: 升级安全级别重试 (无需重新审批)
    5. 返回结果

    关键 Codex 概念已实现:
    - strict_auto_review: 即使 Skip 也需要 Guardian 审查
    - bypass_sandbox: Skip 时是否绕过沙箱
    - SandboxOverride: BypassSandboxFirstAttempt
    - 审批缓存: 升级重试时无需重新审批
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化工具编排器。"""
        self.config = config or {}
        self.max_retries = self.config.get("max_retries", 3)
        self.escalation_delay_ms = self.config.get("escalation_delay_ms", 1000)
        self.auto_approve_reads = self.config.get("auto_approve_reads", True)
        self.guardian_enabled = self.config.get("guardian_enabled", True)

    def select_security_level(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        approval: ExecApprovalRequirement,
    ) -> SecurityLevel:
        """
        选择适当的安全级别。
        对应 Codex 的 SandboxManager::select_initial()。
        """
        # 如果审批已经有明确的安全级别，使用它
        if approval.security_level != SecurityLevel.NONE:
            return approval.security_level

        # 根据工具类型自动选择
        if tool_name in ("read_file", "search_files", "session_search"):
            return SecurityLevel.NONE
        if tool_name in ("write_file", "patch"):
            return SecurityLevel.LOW
        if tool_name in ("terminal", "execute_code"):
            command = tool_args.get("command", "")
            if any(danger in command for danger in ["sudo", "rm -rf", "docker"]):
                return SecurityLevel.HIGH
            return SecurityLevel.MEDIUM
        if tool_name in ("browser_navigate",):
            return SecurityLevel.LOW

        return SecurityLevel.LOW

    def determine_sandbox_override(
        self,
        approval: ExecApprovalRequirement,
        security_level: SecurityLevel,
    ) -> SandboxOverrideType:
        """
        确定沙箱覆盖。
        对应 Codex 的 sandbox_override_for_first_attempt()。

        如果 approval 是 Skip 且 bypass_sandbox=True，
        则第一次尝试绕过沙箱。
        """
        if approval.is_skip and approval.bypass_sandbox:
            return SandboxOverrideType.BYPASS_FIRST_ATTEMPT
        return SandboxOverrideType.NO_OVERRIDE

    def compute_unsandboxed_allowed(
        self,
        owner_network_policy: bool,
        approval: ExecApprovalRequirement,
    ) -> bool:
        """
        计算是否允许无沙箱执行。
        对应 Codex: unsandboxed_allowed = !owner_network_policy && unsandboxed_execution_allowed(file_system_sandbox_policy)

        在 Hermes 中简化为:
        - 如果 owner_network_policy=True，不允许无沙箱
        - 如果 approval 是 Skip + bypass_sandbox，允许无沙箱
        - 否则不允许无沙箱
        """
        # 对应 Codex: !owner_network_policy
        if owner_network_policy:
            return False

        # 对应 Codex: unsandboxed_execution_allowed(file_system_sandbox_policy)
        # 在 Hermes 中，如果 approval 允许绕过沙箱，则允许无沙箱执行
        if approval.is_skip and approval.bypass_sandbox:
            return True

        return False

    def escalate_security_level(self, current: SecurityLevel) -> SecurityLevel:
        """
        升级安全级别。
        对应 Codex 的重试升级逻辑。
        """
        escalation_order = [
            SecurityLevel.NONE,
            SecurityLevel.LOW,
            SecurityLevel.MEDIUM,
            SecurityLevel.HIGH,
            SecurityLevel.MAXIMUM,
        ]
        current_idx = escalation_order.index(current)
        if current_idx < len(escalation_order) - 1:
            return escalation_order[current_idx + 1]
        return current  # 已经是最高级别

    def orchestrate(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        execute_fn: Optional[Callable] = None,
        approval_policy: str = "auto",
        strict_auto_review: bool = False,
        guardian_review_fn: Optional[Callable] = None,
        owner_network_policy: bool = False,
        unsandboxed_allowed: Optional[bool] = None,
    ) -> OrchestratorResult:
        """
        主编排入口。驱动完整管线 (与 Codex orchestrator.rs 一致):
        1. 检查 owner_network_policy (附件网络策略不能被沙箱升级绕过)
        2. 检查审批需求 (Skip/Forbidden/NeedsApproval)
        3. 如果 strict_auto_review 且 Skip，仍然需要 Guardian
        4. 如果 NeedsApproval，调用 Guardian
        5. 选择安全级别
        6. 确定沙箱覆盖 (bypass_sandbox + unsandboxed_allowed)
        7. 执行尝试
        8. 如果沙箱违规: 检查是否允许升级，升级重试 (无需重新审批)

        参数:
            tool_name: 工具名称
            tool_args: 工具参数
            execute_fn: 执行函数 fn(tool_name, tool_args, security_level) -> (success, output, error)
            approval_policy: 审批策略 ("auto" / "suggest" / "auto_edit" / "full_auto")
            strict_auto_review: 是否严格自动审查
            guardian_review_fn: Guardian 审查函数 fn(tool_name, tool_args) -> (allowed, reason)
            owner_network_policy: 是否有附件拥有的网络策略 (不能被沙箱升级绕过)
            unsandboxed_allowed: 是否允许无沙箱执行 (受文件系统策略约束)

        返回: OrchestratorResult
        """
        start_time = time.time()
        attempt_history = []
        already_approved = False  # 审批缓存: 升级重试时无需重新审批

        # Step 1: 检查 owner_network_policy
        # 对应 Codex: "attachment-owned network policy cannot be bypassed by sandbox escalation"
        # Codex 源码: if owner_network_policy && tool.sandbox_permissions(req).requires_escalated_permissions()
        #              → return Err(ToolError::Rejected("attachment-owned network policy cannot be bypassed"))
        if owner_network_policy:
            # 检查是否需要升级权限 (HIGH 或 MAXIMUM 安全级别)
            # 如果需要升级权限，直接拒绝
            preliminary_approval = determine_approval_requirement(
                tool_name, tool_args, approval_policy, strict_auto_review,
            )
            if preliminary_approval.security_level in (SecurityLevel.HIGH, SecurityLevel.MAXIMUM):
                total_duration = (time.time() - start_time) * 1000
                return OrchestratorResult(
                    success=False,
                    error="attachment-owned network policy cannot be bypassed by sandbox escalation",
                    final_security_level=preliminary_approval.security_level,
                    total_duration_ms=total_duration,
                )

        # Step 2: 检查审批需求
        approval = determine_approval_requirement(
            tool_name, tool_args, approval_policy, strict_auto_review,
        )

        # Step 2.5: 自动计算 unsandboxed_allowed (如果未显式提供)
        # 对应 Codex: unsandboxed_allowed = !owner_network_policy && unsandboxed_execution_allowed(file_system_sandbox_policy)
        if unsandboxed_allowed is None:
            unsandboxed_allowed = self.compute_unsandboxed_allowed(owner_network_policy, approval)

        # Step 3: 处理 Forbidden
        if approval.is_forbidden:
            total_duration = (time.time() - start_time) * 1000
            return OrchestratorResult(
                success=False,
                error=approval.reason,
                final_security_level=approval.security_level,
                total_duration_ms=total_duration,
            )

        # Step 4: 如果 strict_auto_review 且 Skip，仍然需要 Guardian
        guardian_approved = False
        if strict_auto_review and approval.is_skip and guardian_review_fn:
            allowed, reason = guardian_review_fn(tool_name, tool_args)
            if not allowed:
                total_duration = (time.time() - start_time) * 1000
                return OrchestratorResult(
                    success=False,
                    error=f"Guardian denied: {reason}",
                    final_security_level=approval.security_level,
                    total_duration_ms=total_duration,
                    guardian_approved=False,
                )
            guardian_approved = True
            already_approved = True  # Guardian 已审批

        # Step 5: 如果 NeedsApproval，调用 Guardian
        if approval.needs_approval and guardian_review_fn:
            allowed, reason = guardian_review_fn(tool_name, tool_args)
            if not allowed:
                total_duration = (time.time() - start_time) * 1000
                return OrchestratorResult(
                    success=False,
                    error=f"Guardian denied: {reason}",
                    final_security_level=approval.security_level,
                    total_duration_ms=total_duration,
                    guardian_approved=False,
                )
            guardian_approved = True
            already_approved = True  # Guardian 已审批

        # Step 6: 选择安全级别
        security_level = self.select_security_level(tool_name, tool_args, approval)

        # Step 7: 确定沙箱覆盖
        # 对应 Codex: sandbox_override_for_first_attempt()
        # 如果 unsandboxed_allowed=False，不能绕过沙箱
        if not unsandboxed_allowed:
            sandbox_override = SandboxOverrideType.NO_OVERRIDE
        else:
            sandbox_override = self.determine_sandbox_override(approval, security_level)

        # Step 8: 执行循环 (带重试)
        # 对应 Codex: "no re-approval thanks to caching"
        current_level = security_level
        for attempt_num in range(1, self.max_retries + 1):
            attempt_start = time.time()
            attempt_info = {
                "attempt": attempt_num,
                "security_level": current_level.value,
                "sandbox_override": sandbox_override.value if attempt_num == 1 else "no_override",
                "escalated": attempt_num > 1,
            }

            if execute_fn:
                try:
                    success, output, error = execute_fn(
                        tool_name, tool_args, current_level,
                    )

                    attempt_info["success"] = success
                    attempt_info["error"] = error
                    attempt_info["duration_ms"] = round(
                        (time.time() - attempt_start) * 1000, 2,
                    )
                    attempt_history.append(attempt_info)

                    if success:
                        total_duration = (time.time() - start_time) * 1000
                        return OrchestratorResult(
                            success=True,
                            output=output,
                            attempts=attempt_history,
                            final_security_level=current_level,
                            total_duration_ms=total_duration,
                            escalated=attempt_num > 1,
                            guardian_approved=guardian_approved,
                        )

                    # 检查是否是沙箱违规
                    # 对应 Codex: SandboxErr::Denied { output, network_policy_decision }
                    # 使用 SandboxError 类型检查而不是字符串匹配
                    is_sandbox_error = False
                    if isinstance(error, SandboxError) and error.is_denied():
                        is_sandbox_error = True
                    elif error and isinstance(error, str):
                        # 向后兼容: 如果 error 是字符串，使用更精确的匹配
                        # 只匹配明确的沙箱错误模式，避免误判
                        error_lower = error.lower()
                        if ("sandbox denied" in error_lower
                            or "permission denied" in error_lower
                            or "access denied" in error_lower
                            or "sandbox violation" in error_lower):
                            is_sandbox_error = True

                    if is_sandbox_error:
                        # === 条件 1: escalate_on_failure ===
                        # 对应 Codex: if !tool.escalate_on_failure() { return Err }
                        # 如果工具不允许升级，直接返回错误
                        # 在 Hermes 中，通过配置控制 (默认允许升级)
                        if not self.config.get("allow_escalation", True):
                            break

                        # === 条件 2: owner_network_policy ===
                        # 对应 Codex: 附件网络策略不能被沙箱升级绕过
                        if owner_network_policy:
                            break

                        # === 条件 3: wants_no_sandbox_approval ===
                        # 对应 Codex: 检查审批策略是否允许无沙箱审批
                        # "Never" 或 "OnRequest" 策略下，不重试无沙箱
                        if approval_policy in ("never",):
                            # "Never" 策略: 不允许无沙箱审批
                            break

                        # === 条件 4: unsandboxed_allowed ===
                        # 对应 Codex: if !unsandboxed_allowed && network_approval_context.is_none()
                        # 如果有 network_approval_context，可以绕过此检查
                        network_ctx = check_network_approval(tool_name, tool_args)
                        if not unsandboxed_allowed and network_ctx is None:
                            # 不允许无沙箱执行，且没有网络审批上下文
                            # 不能通过升级绕过
                            break

                        # 升级安全级别
                        new_level = self.escalate_security_level(current_level)
                        if new_level == current_level:
                            # 已经是最高级别，无法升级
                            break

                        current_level = new_level

                        # === 重试时的沙箱重新评估 ===
                        # 对应 Codex: retry_sandbox_requested = !unsandboxed_allowed && self.sandbox.should_sandbox(...)
                        # 在 Hermes 中，根据新的安全级别重新评估是否需要沙箱
                        if not unsandboxed_allowed:
                            # 不允许无沙箱执行，重试时仍然需要沙箱
                            # 根据新的安全级别选择沙箱类型
                            retry_approval = determine_approval_requirement(
                                tool_name, tool_args, approval_policy, strict_auto_review,
                            )
                            retry_sandbox_level = self.select_security_level(
                                tool_name, tool_args, retry_approval,
                            )
                            # 使用更高的安全级别
                            if retry_sandbox_level.value < current_level.value:
                                current_level = retry_sandbox_level

                        # === 条件 5: should_bypass_approval ===
                        # 对应 Codex: bypass_retry_approval 逻辑
                        # 决定升级重试时是否需要重新审批
                        need_re_approval = False

                        # 5a: strict_auto_review 时，总是需要重新审批
                        if strict_auto_review:
                            need_re_approval = True

                        # 5b: 如果之前没有审批过，需要审批
                        elif not already_approved:
                            need_re_approval = True

                        # 5c: "OnRequest" 策略 + NeedsApproval，需要审批
                        elif approval_policy == "on_request" and approval.needs_approval:
                            need_re_approval = True

                        # 如果需要重新审批，调用 Guardian
                        if need_re_approval and guardian_review_fn:
                            allowed, reason = guardian_review_fn(tool_name, tool_args)
                            if not allowed:
                                # Guardian 拒绝，不重试
                                break
                            already_approved = True

                        # 延迟后重试
                        time.sleep(self.escalation_delay_ms / 1000)
                        continue

                    # 非沙箱错误，不重试
                    break

                except Exception as e:
                    attempt_info["success"] = False
                    attempt_info["error"] = str(e)
                    attempt_info["duration_ms"] = round(
                        (time.time() - attempt_start) * 1000, 2,
                    )
                    attempt_history.append(attempt_info)
                    break
            else:
                # 没有 execute_fn，只返回审批结果
                attempt_info["success"] = True
                attempt_info["duration_ms"] = 0
                attempt_history.append(attempt_info)
                break

        # 所有尝试失败
        total_duration = (time.time() - start_time) * 1000
        last_error = attempt_history[-1].get("error", "No attempts made") if attempt_history else "No attempts made"
        return OrchestratorResult(
            success=False,
            error=last_error,
            attempts=attempt_history,
            final_security_level=current_level,
            total_duration_ms=total_duration,
            escalated=len(attempt_history) > 1,
            guardian_approved=guardian_approved,
        )


# ============================================================================
# CLI 接口
# ============================================================================

def main() -> None:
    """CLI 入口，用于测试和查询。"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Codex Harness Tool Orchestrator",
        epilog="All shared types are in core.py. This module only handles orchestration.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # status 命令
    subparsers.add_parser("status", help="Show orchestrator status")

    # orchestrate 命令
    orch_parser = subparsers.add_parser("orchestrate", help="Run orchestration pipeline")
    orch_parser.add_argument("tool_name", help="Tool name")
    orch_parser.add_argument("--args", default="{}", help="Tool args JSON")
    orch_parser.add_argument("--policy", default="auto", help="Approval policy")
    orch_parser.add_argument("--strict", action="store_true", help="Strict auto review")
    orch_parser.add_argument("--owner-network", action="store_true", help="Owner network policy (cannot bypass sandbox)")
    orch_parser.add_argument("--no-unsandboxed", action="store_true", help="Disallow unsandboxed execution")

    # security-level 命令
    sl_parser = subparsers.add_parser("security-level", help="Determine security level")
    sl_parser.add_argument("tool_name", help="Tool name")
    sl_parser.add_argument("--args", default="{}", help="Tool args JSON")

    args = parser.parse_args()

    if args.command == "status":
        orch = ToolOrchestrator()
        print(json.dumps({
            "orchestrator": {
                "max_retries": orch.max_retries,
                "escalation_delay_ms": orch.escalation_delay_ms,
                "auto_approve_reads": orch.auto_approve_reads,
                "guardian_enabled": orch.guardian_enabled,
            },
            "note": "Shared types (22) are in core.py",
        }, indent=2))

    elif args.command == "orchestrate":
        tool_args = json.loads(args.args)
        orch = ToolOrchestrator()
        result = orch.orchestrate(
            args.tool_name,
            tool_args,
            approval_policy=args.policy,
            strict_auto_review=args.strict,
            owner_network_policy=args.owner_network,
            unsandboxed_allowed=not args.no_unsandboxed,
        )
        print(json.dumps(result.to_dict(), indent=2))

    elif args.command == "security-level":
        tool_args = json.loads(args.args)
        orch = ToolOrchestrator()
        approval = determine_approval_requirement(
            args.tool_name, tool_args, "auto", False,
        )
        level = orch.select_security_level(args.tool_name, tool_args, approval)
        override = orch.determine_sandbox_override(approval, level)
        print(json.dumps({
            "tool": args.tool_name,
            "security_level": level.value,
            "sandbox_override": override.value,
            "approval_type": approval.approval_type.value,
            "bypass_sandbox": approval.bypass_sandbox,
        }, indent=2))

    else:
        parser.print_help()



# ============================================================================
# 网络审批上下文 (简化版)
# 对应 Codex 的 NetworkApprovalSpec + network_approval_context_from_payload
# =============================================================================

class NetworkApprovalContext:
    """
    网络审批上下文 (简化版)。
    对应 Codex 的 NetworkApprovalContext。

    在 Hermes 中没有原生网络审批系统，这里提供简化实现:
    - 检查工具是否需要网络访问
    - 检查目标域名是否被允许
    """
    def __init__(self, host: str, allowed: bool, reason: Optional[str] = None):
        """初始化网络审批上下文。"""
        self.host = host
        self.allowed = allowed
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            "host": self.host,
            "allowed": self.allowed,
            "reason": self.reason,
        }


def check_network_approval(tool_name: str, tool_args: Dict[str, Any]) -> Optional[NetworkApprovalContext]:
    """
    检查工具调用是否需要网络审批。
    对应 Codex 的 network_approval_spec()。

    返回: NetworkApprovalContext 或 None (如果不需要网络访问)
    """
    # 只有浏览器工具需要网络访问
    if tool_name not in ("browser_navigate",):
        return None

    url = tool_args.get("url", "")
    if not url:
        return None

    # 检查域名是否被允许
    net_check = NetworkPolicy.check(url)
    if net_check == "allow":
        return NetworkApprovalContext(host=url, allowed=True)
    elif net_check == "deny":
        return NetworkApprovalContext(host=url, allowed=False, reason=f"Domain denied by policy")
    else:
        return NetworkApprovalContext(host=url, allowed=False, reason=f"Domain requires review")


# ============================================================================
# CLI 入口
# ============================================================================

if __name__ == "__main__":
    main()


# ============================================================================
# 补丁审批集成
# ============================================================================

class PatchApprovalHandler:
    """
    补丁审批处理器。
    集成补丁系统到编排器的审批流程。

    功能:
    - 补丁安全检查
    - 补丁审批决策
    - 补丁应用
    """

    def __init__(self, patch_manager=None):
        """
        初始化补丁审批处理器。

        参数:
            patch_manager: 补丁管理器实例 (None 自动创建)
        """
        if patch_manager is None:
            from patch import PatchManager, PatchConfig
            config = PatchConfig(
                allowed_dirs=['.'],
                create_backup=True,
                check_safety=True,
            )
            self.patch_manager = PatchManager(config)
        else:
            self.patch_manager = patch_manager

    def handle_patch_request(
        self,
        patch_text: str,
        approval_policy: str = "auto",
        strict_auto_review: bool = False,
        guardian_review_fn=None,
    ) -> ExecApprovalRequirement:
        """
        处理补丁请求。

        参数:
            patch_text: 补丁文本
            approval_policy: 审批策略
            strict_auto_review: 是否严格自动审查
            guardian_review_fn: Guardian 审查函数

        返回:
            ExecApprovalRequirement 审批需求
        """
        # 1. 安全检查
        safety_result = self.patch_manager.check_safety(patch_text)

        # 2. 如果安全检查失败，返回 Forbidden
        if safety_result.get('rejected', False):
            reason = safety_result.get('reason', 'Safety check failed')
            return ExecApprovalRequirement(
                ExecApprovalType.FORBIDDEN,
                reason=reason,
            )

        # 3. 如果需要审批，返回 NeedsApproval
        if safety_result.get('needs_approval', False):
            reason = safety_result.get('reason', 'Patch needs approval')
            return ExecApprovalRequirement(
                ExecApprovalType.NEEDS_APPROVAL,
                reason=reason,
            )

        # 4. 如果是严格自动审查，返回 NeedsApproval
        if strict_auto_review:
            return ExecApprovalRequirement(
                ExecApprovalType.NEEDS_APPROVAL,
                reason="Strict auto review enabled",
            )

        # 5. 默认返回 Skip
        return ExecApprovalRequirement(
            ExecApprovalType.SKIP,
            bypass_sandbox=False,
        )

    def apply_patch_with_approval(
        self,
        patch_text: str,
        approval_policy: str = "auto",
        strict_auto_review: bool = False,
        guardian_review_fn=None,
    ):
        """
        带审批的补丁应用。

        参数:
            patch_text: 补丁文本
            approval_policy: 审批策略
            strict_auto_review: 是否严格自动审查
            guardian_review_fn: Guardian 审查函数

        返回:
            PatchResult 补丁结果
        """
        # 1. 获取审批需求
        approval = self.handle_patch_request(
            patch_text,
            approval_policy,
            strict_auto_review,
            guardian_review_fn,
        )

        # 2. 如果是 Forbidden，返回错误
        if approval.is_forbidden:
            from patch import PatchResult
            return PatchResult(
                success=False,
                changes_applied=0,
                changes_failed=1,
                errors=[f"Patch forbidden: {approval.reason}"],
            )

        # 3. 如果是 NeedsApproval，调用 Guardian
        if approval.needs_approval and guardian_review_fn:
            allowed, reason = guardian_review_fn('apply_patch', {'patch': patch_text})
            if not allowed:
                from patch import PatchResult
                return PatchResult(
                    success=False,
                    changes_applied=0,
                    changes_failed=1,
                    errors=[f"Guardian rejected: {reason}"],
                )

        # 4. 应用补丁
        return self.patch_manager.apply_patch(patch_text)


def apply_patch_tool(
    patch_text: str,
    approval_policy: str = "auto",
    strict_auto_review: bool = False,
    guardian_review_fn=None,
) -> Dict[str, Any]:
    """
    apply_patch 工具入口。
    供 agent 调用来应用补丁。

    参数:
        patch_text: 补丁文本
        approval_policy: 审批策略
        strict_auto_review: 是否严格自动审查
        guardian_review_fn: Guardian 审查函数

    返回:
        结果字典
    """
    handler = PatchApprovalHandler()
    result = handler.apply_patch_with_approval(
        patch_text,
        approval_policy,
        strict_auto_review,
        guardian_review_fn,
    )

    return {
        "success": result.success,
        "changes_applied": result.changes_applied,
        "changes_failed": result.changes_failed,
        "errors": result.errors,
        "backup_path": result.backup_path,
    }


# ============================================================================
# AGENTS.md 配置集成
# ============================================================================

class AgentsMdIntegration:
    """
    AGENTS.md 配置集成。
    将 AGENTS.md 配置系统集成到编排器。

    功能:
    - 加载 AGENTS.md 配置
    - 提供配置查询
    - 格式化配置为提示词
    """

    def __init__(self, start_path: str = "."):
        """
        初始化 AGENTS.md 集成。

        参数:
            start_path: 起始路径
        """
        from agents_md import AgentsMdConfigManager

        self.config_manager = AgentsMdConfigManager(start_path)

    def load(self) -> Dict[str, Any]:
        """
        加载配置。

        返回:
            配置字典
        """
        return self.config_manager.load()

    def get_rules(self) -> List[str]:
        """
        获取规则列表。

        返回:
            规则列表
        """
        return self.config_manager.get_rules()

    def get_constraints(self) -> List[str]:
        """
        获取约束列表。

        返回:
            约束列表
        """
        return self.config_manager.get_constraints()

    def get_preferences(self) -> List[str]:
        """
        获取偏好列表。

        返回:
            偏好列表
        """
        return self.config_manager.get_preferences()

    def get_tools(self) -> List[str]:
        """
        获取工具列表。

        返回:
            工具列表
        """
        return self.config_manager.get_tools()

    def format_for_prompt(self) -> str:
        """
        格式化配置为提示词。

        返回:
            格式化的提示词
        """
        return self.config_manager.format_for_prompt()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息。

        返回:
            统计字典
        """
        config = self.load()
        return {
            "rules": len(config.get("rules", [])),
            "constraints": len(config.get("constraints", [])),
            "preferences": len(config.get("preferences", [])),
            "tools": len(config.get("tools", [])),
        }
