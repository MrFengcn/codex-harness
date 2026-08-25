#!/usr/bin/env python3
"""
Codex Harness — 共享基础库

所有其他模块共享的类型、策略和工具函数。
对应 Codex 的 codex-protocol + codex-sandboxing + codex-utils crate。

来源:
- codex-rs/protocol/src/approvals.rs (审批类型)
- codex-rs/core/src/tools/sandboxing.rs (沙箱类型)
- codex-rs/core/src/guardian/mod.rs (Guardian 类型)
- codex-rs/context-fragments/src/fragment.rs (上下文片段)
- codex-rs/hooks/src/lib.rs (Hook 事件)
- codex-rs/core/src/agent/ (代理类型)

Python 兼容性: 3.6+
"""


import re
import shlex
from collections import deque
from enum import Enum
from typing import Any, Deque, Dict, List, Optional, Tuple


# ============================================================================
# 安全级别 (对应 Codex SandboxType)
# ============================================================================

class SecurityLevel(Enum):
    """
    安全级别，从最低到最高限制。
    对应 Codex 的 SandboxType + ExecApprovalRequirement 的安全级别。
    """
    NONE = "none"           # 读操作，无限制
    LOW = "low"             # 基本检查，无沙箱
    MEDIUM = "medium"       # 命令白名单，网络限制
    HIGH = "high"           # 完整沙箱，Guardian 审查
    MAXIMUM = "maximum"     # Guardian + 用户确认


# ============================================================================
# 安全策略 (对应 Codex 的 permission profile)
# ============================================================================

def matches_pattern(path: str, pattern: str) -> bool:
    """
    检查路径是否匹配 glob 模式。
    支持 * 和 ** 通配符。
    """
    # 转换为正则表达式
    regex = pattern
    regex = regex.replace(".", r"\.")
    regex = regex.replace("**/", "(.+/)?")  # ** 匹配任意目录
    regex = regex.replace("*", "[^/]*")      # * 匹配单层
    regex = regex.replace("?", "[^/]")
    regex = f"^{regex}$"
    return bool(re.match(regex, path))


class FilePolicy:
    """
    文件访问安全策略。
    对应 Codex 的 FileSystemSandboxPolicy。
    """
    ALLOW_PATTERNS = [
        "./src/*", "./tests/*", "./docs/*", "./lib/*",
        "./*", "~/*", "/tmp/*",
    ]

    DENY_PATTERNS = [
        "/etc/*", "/usr/*", "/sys/*", "/proc/*",
        "/dev/*", "/boot/*", "/sbin/*", "/bin/*",
    ]

    @classmethod
    def check(cls, path: str) -> str:
        """
        检查文件路径是否被策略允许。
        返回: "allow" / "deny" / "review"
        """
        import os
        path = os.path.expanduser(path)
        path = os.path.abspath(path)

        for pattern in cls.DENY_PATTERNS:
            if matches_pattern(path, pattern):
                return "deny"

        for pattern in cls.ALLOW_PATTERNS:
            if matches_pattern(path, pattern):
                return "allow"

        return "review"


class CommandPolicy:
    """
    命令执行安全策略。
    对应 Codex 的 ExecPolicy。
    """
    ALLOW_COMMANDS = {
        "git", "npm", "npx", "yarn", "pnpm",
        "python", "python3", "pip", "pip3", "uv",
        "cargo", "rustc", "rustup",
        "go", "go build", "go test", "go run",
        "make", "cmake",
        "docker", "docker-compose",
        "ls", "cat", "head", "tail", "grep", "find", "wc",
        "echo", "printf", "date", "env", "which", "whoami",
        "curl", "wget",
        "node", "deno", "bun",
        "java", "javac", "mvn", "gradle",
        "ruby", "gem", "bundle",
        "php", "composer",
    }

    DENY_COMMANDS = {
        "rm -rf /", "rm -rf /*", "sudo rm -rf",
        "dd if=/dev/zero", "dd if=/dev/random",
        "mkfs", "fdisk",
        ":(){ :|:& };:",  # fork bomb
        "chmod -R 777 /",
        "chown -R",
    }

    REVIEW_COMMANDS = {
        "sudo", "su",
        "docker rm", "docker kill", "docker stop",
        "kubectl delete", "kubectl apply",
        "systemctl", "service",
        "iptables", "ufw",
        "mount", "umount",
        "useradd", "userdel", "usermod",
    }

    @classmethod
    def check(cls, command: str) -> str:
        """
        检查命令是否被策略允许。
        返回: "allow" / "deny" / "review"
        """
        command_lower = command.strip().lower()

        # 检查禁止命令
        for denied in cls.DENY_COMMANDS:
            if denied.lower() in command_lower:
                return "deny"

        # 检查需审查命令
        for reviewed in cls.REVIEW_COMMANDS:
            if command_lower.startswith(reviewed.lower()):
                return "review"

        # 检查允许命令
        base_cmd = command_lower.split()[0] if command_lower.split() else ""
        if base_cmd in cls.ALLOW_COMMANDS:
            return "allow"

        return "review"


class NetworkPolicy:
    """
    网络访问安全策略。
    对应 Codex 的 NetworkSandboxPolicy。
    """
    ALLOW_DOMAINS = {
        "github.com", "api.github.com", "raw.githubusercontent.com",
        "npmjs.org", "registry.npmjs.org",
        "pypi.org", "files.pythonhosted.org",
        "crates.io", "static.crates.io",
        "hub.docker.com", "registry-1.docker.io",
        "google.com", "www.google.com",
        "stackoverflow.com", "stackexchange.com",
        "developer.mozilla.org",
        "docs.python.org", "docs.rs",
    }

    @classmethod
    def check(cls, url: str) -> str:
        """
        检查 URL 是否被策略允许。
        返回: "allow" / "deny" / "review"
        """
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            domain = parsed.hostname or ""
        except Exception:
            return "review"

        for allowed in cls.ALLOW_DOMAINS:
            if domain == allowed or domain.endswith(f".{allowed}"):
                return "allow"

        return "review"


class SecretPolicy:
    """
    密钥检测策略。
    用于扫描代码和命令中的潜在密钥。
    """
    SECRET_PATTERNS = [
        r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\'][^"\']{10,}',
        r'(?i)(secret|password|passwd|pwd)\s*[:=]\s*["\'][^"\']{6,}',
        r'(?i)(token|bearer)\s*[:=]\s*["\'][^"\']{10,}',
        r'(?:sk|pk|rk)_(?:live|test)_[a-zA-Z0-9]{20,}',  # Stripe
        r'ghp_[a-zA-Z0-9]{36}',  # GitHub personal
        r'gho_[a-zA-Z0-9]{36}',  # GitHub OAuth
        r'glpat-[a-zA-Z0-9\-]{20,}',  # GitLab
        r'xox[bpors]-[a-zA-Z0-9\-]{10,}',  # Slack
        r'AKIA[0-9A-Z]{16}',  # AWS access key
        r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----',
    ]

    @classmethod
    def scan(cls, content: str) -> List[str]:
        """
        扫描内容中的潜在密钥。
        返回: 匹配到的密钥列表
        """
        findings = []
        for pattern in cls.SECRET_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                findings.extend(matches)
        return findings


# ============================================================================
# 审批需求 (对应 Codex ExecApprovalRequirement)
# 来源: codex-rs/core/src/tools/sandboxing.rs
# ============================================================================

class ExecApprovalType(Enum):
    """审批需求类型"""
    SKIP = "skip"                    # 自动批准
    FORBIDDEN = "forbidden"          # 禁止
    NEEDS_APPROVAL = "needs_approval" # 需要审批


class ExecPolicyAmendment:
    """
    提议的执行策略修正。
    当 Skip 时，可以提议将此命令加入未来的自动批准列表。
    """
    def __init__(self, command_prefix: str, description: str):
        self.command_prefix = command_prefix
        self.description = description

    def to_dict(self) -> Dict[str, str]:
        return {
            "command_prefix": self.command_prefix,
            "description": self.description,
        }


class ExecApprovalRequirement:
    """
    工具调用的审批需求。
    对应 Codex 的 ExecApprovalRequirement 枚举。

    三种类型:
    - Skip: 自动批准 (可选 bypass_sandbox)
    - Forbidden: 禁止执行
    - NeedsApproval: 需要用户审批
    """
    def __init__(
        self,
        approval_type: ExecApprovalType,
        reason: Optional[str] = None,
        security_level: SecurityLevel = SecurityLevel.NONE,
        strict_auto_review: bool = False,
        bypass_sandbox: bool = False,
        proposed_execpolicy_amendment: Optional[ExecPolicyAmendment] = None,
    ):
        self.approval_type = approval_type
        self.reason = reason
        self.security_level = security_level
        self.strict_auto_review = strict_auto_review
        self.bypass_sandbox = bypass_sandbox
        self.proposed_execpolicy_amendment = proposed_execpolicy_amendment

    @property
    def needs_approval(self) -> bool:
        return self.approval_type == ExecApprovalType.NEEDS_APPROVAL

    @property
    def is_forbidden(self) -> bool:
        return self.approval_type == ExecApprovalType.FORBIDDEN

    @property
    def is_skip(self) -> bool:
        return self.approval_type == ExecApprovalType.SKIP

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.approval_type.value,
            "reason": self.reason,
            "security_level": self.security_level.value,
            "strict_auto_review": self.strict_auto_review,
            "bypass_sandbox": self.bypass_sandbox,
        }
        if self.proposed_execpolicy_amendment:
            result["amendment"] = self.proposed_execpolicy_amendment.to_dict()
        return result


# ============================================================================
# 沙箱尝试 (对应 Codex SandboxAttempt)
# 来源: codex-rs/core/src/tools/sandboxing.rs
# ============================================================================

class SandboxAttempt:
    """
    一次沙箱执行尝试。
    记录安全级别、是否请求沙箱、尝试次数、是否升级。
    """
    def __init__(
        self,
        security_level: SecurityLevel,
        sandbox_requested: bool = False,
        attempt_number: int = 1,
        escalated: bool = False,
    ):
        self.security_level = security_level
        self.sandbox_requested = sandbox_requested
        self.attempt_number = attempt_number
        self.escalated = escalated

    def to_dict(self) -> Dict[str, Any]:
        return {
            "security_level": self.security_level.value,
            "sandbox_requested": self.sandbox_requested,
            "attempt_number": self.attempt_number,
            "escalated": self.escalated,
        }


# ============================================================================
# 沙箱覆盖 (对应 Codex SandboxOverride)
# 来源: codex-rs/core/src/tools/sandboxing.rs
# ============================================================================

class SandboxOverrideType(Enum):
    """沙箱覆盖类型"""
    NO_OVERRIDE = "no_override"              # 不覆盖，使用默认策略
    BYPASS_FIRST_ATTEMPT = "bypass_first_attempt"  # 第一次尝试绕过沙箱


# ============================================================================
# Guardian 评估 (对应 Codex GuardianAssessment)
# 来源: codex-rs/protocol/src/approvals.rs + codex-rs/core/src/guardian/mod.rs
# ============================================================================

class GuardianRiskLevel(Enum):
    """Guardian 风险等级"""
    Low = "low"
    Medium = "medium"
    High = "high"
    Critical = "critical"


class GuardianUserAuthorization(Enum):
    """Guardian 用户授权级别"""
    Unknown = "unknown"
    Low = "low"
    Medium = "medium"
    High = "high"


class GuardianAssessmentOutcome(Enum):
    """Guardian 评估结果"""
    Allow = "allow"
    Deny = "deny"


class GuardianAssessment:
    """
    Guardian 安全评估结果。
    对应 Codex 的 GuardianAssessment 结构体。

    包含 4 个字段:
    - risk_level: 风险等级
    - user_authorization: 用户授权级别
    - outcome: 允许/拒绝
    - rationale: 评估理由
    """
    def __init__(
        self,
        risk_level: GuardianRiskLevel,
        user_authorization: GuardianUserAuthorization,
        outcome: GuardianAssessmentOutcome,
        rationale: str,
    ):
        self.risk_level = risk_level
        self.user_authorization = user_authorization
        self.outcome = outcome
        self.rationale = rationale

    @property
    def is_allowed(self) -> bool:
        return self.outcome == GuardianAssessmentOutcome.Allow

    @property
    def is_denied(self) -> bool:
        return self.outcome == GuardianAssessmentOutcome.Deny

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_level": self.risk_level.value,
            "user_authorization": self.user_authorization.value,
            "outcome": self.outcome.value,
            "rationale": self.rationale,
        }


# ============================================================================
# Guardian 断路器 (对应 Codex GuardianRejectionCircuitBreaker)
# 来源: codex-rs/core/src/guardian/mod.rs
# ============================================================================

class CircuitBreakerPolicy(Enum):
    """断路器策略"""
    Standard = "standard"      # 标准策略: 3 次连续拒绝或 10 次窗口拒绝
    CyberModel = "cyber_model"  # 网络安全模型: 1 次连续拒绝或 1 次窗口拒绝


class CircuitBreakerAction(Enum):
    """断路器动作"""
    Continue = "continue"           # 继续执行
    InterruptTurn = "interrupt_turn"  # 中断当前 turn


class CircuitBreakerTurnState:
    """单个 turn 的断路器状态"""
    def __init__(self):
        self.consecutive_denials: int = 0
        self.recent_denials: Deque[bool] = deque(maxlen=50)
        self.interrupt_triggered: bool = False


class CircuitBreakerState:
    """
    Guardian 拒绝断路器。
    对应 Codex 的 GuardianRejectionCircuitBreaker。

    按 turn_id 隔离追踪，支持 Standard 和 CyberModel 两种策略。
    当连续拒绝次数或窗口拒绝次数超过阈值时触发中断。
    """
    def __init__(self):
        self.turns: Dict[str, CircuitBreakerTurnState] = {}

    def record_denial(self, turn_id: str, policy: CircuitBreakerPolicy) -> CircuitBreakerAction:
        """
        记录一次拒绝。
        返回: CircuitBreakerAction.Continue 或 InterruptTurn
        """
        if turn_id not in self.turns:
            self.turns[turn_id] = CircuitBreakerTurnState()

        state = self.turns[turn_id]
        state.consecutive_denials += 1
        state.recent_denials.append(True)

        # 根据策略确定阈值
        if policy == CircuitBreakerPolicy.CyberModel:
            max_consecutive = 1
            max_recent = 1
        else:  # Standard
            max_consecutive = 3
            max_recent = 10

        # 检查是否触发中断
        recent_true_count = sum(1 for x in state.recent_denials if x)
        if state.consecutive_denials >= max_consecutive or recent_true_count >= max_recent:
            state.interrupt_triggered = True
            return CircuitBreakerAction.InterruptTurn

        return CircuitBreakerAction.Continue

    def record_approval(self, turn_id: str):
        """记录一次批准，重置连续拒绝计数"""
        if turn_id in self.turns:
            state = self.turns[turn_id]
            state.consecutive_denials = 0
            state.recent_denials.append(False)

    def clear_turn(self, turn_id: str):
        """清除指定 turn 的断路器状态"""
        self.turns.pop(turn_id, None)

    def is_interrupted(self, turn_id: str) -> bool:
        """检查指定 turn 是否已被中断"""
        if turn_id in self.turns:
            return self.turns[turn_id].interrupt_triggered
        return False


# ============================================================================
# 上下文片段 (对应 Codex ContextualUserFragment)
# 来源: codex-rs/context-fragments/src/fragment.rs
# ============================================================================

class ContextualUserFragment:
    """
    上下文片段基类。
    对应 Codex 的 ContextualUserFragment trait。

    每个具体的上下文片段类型继承此类并实现抽象方法。
    片段可以注入到模型上下文中，带有角色、标记和内容。

    用法示例:
        class TimeFragment(ContextualUserFragment):
            def role(self): return "system"
            def markers(self): return ("<current_time>", "</current_time>")
            def body(self): return datetime.now().isoformat()
            @classmethod
            def type_markers(cls): return ("<current_time>", "</current_time>")
    """

    def role(self) -> str:
        """
        返回消息角色。
        Codex 中的值: "system" / "developer" / "user" / "assistant"
        """
        raise NotImplementedError("Subclass must implement role()")

    def requires_separate_message(self) -> bool:
        """
        是否必须作为独立消息记录。
        如果返回 True，此片段不能与其他片段合并为同一条消息。
        默认: False
        """
        return False

    def markers(self) -> Tuple[str, str]:
        """
        返回 XML 标记 (open, close)。
        用于包裹片段内容，例如 ("<current_time>", "</current_time>")
        """
        raise NotImplementedError("Subclass must implement markers()")

    def body(self) -> str:
        """返回片段的实际文本内容"""
        raise NotImplementedError("Subclass must implement body()")

    @classmethod
    def type_markers(cls) -> Tuple[str, str]:
        """
        返回类型标记 (open, close)。
        用于识别历史消息中的片段类型，支持去重。
        """
        raise NotImplementedError("Subclass must implement type_markers()")

    @classmethod
    def matches_text(cls, text: str) -> bool:
        """
        检查文本是否匹配此片段类型。
        用于从历史消息中识别已有片段，避免重复注入。
        """
        open_marker, close_marker = cls.type_markers()
        return open_marker in text and close_marker in text

    def token_count(self) -> int:
        """估算此片段的 token 数量"""
        return estimate_tokens(self.body())

    def to_message(self) -> Dict[str, str]:
        """
        转换为消息格式 (用于注入到上下文)。
        返回 {"role": ..., "content": ...}
        """
        open_marker, close_marker = self.markers()
        return {
            "role": self.role(),
            "content": f"{open_marker}\n{self.body()}\n{close_marker}",
        }


# ============================================================================
# Token 预算 (对应 Codex TokenBudget)
# 来源: codex-rs/core/src/compact_token_budget.rs
# ============================================================================

class TokenBudgetStatus(Enum):
    """Token 预算状态"""
    OK = "ok"             # < 70%
    WARNING = "warning"   # 70-80%
    CRITICAL = "critical" # 80-90%
    EXCEEDED = "exceeded" # > 90%


class TokenBudget:
    """
    Token 预算追踪器。
    对应 Codex 的 TokenBudget。

    用于追踪上下文窗口的 token 使用情况，
    并在接近限制时发出警告和触发压缩。
    """
    def __init__(self, total: int, used: int = 0):
        self.total = total
        self.used = used

    @property
    def remaining(self) -> int:
        return max(0, self.total - self.used)

    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.used / self.total) * 100

    @property
    def status(self) -> TokenBudgetStatus:
        pct = self.percentage
        if pct < 70:
            return TokenBudgetStatus.OK
        elif pct < 80:
            return TokenBudgetStatus.WARNING
        elif pct < 90:
            return TokenBudgetStatus.CRITICAL
        else:
            return TokenBudgetStatus.EXCEEDED

    def add(self, tokens: int):
        """添加 token 使用量"""
        self.used += tokens

    def check_can_add(self, tokens: int) -> bool:
        """检查是否可以添加指定数量的 token"""
        return (self.used + tokens) <= self.total

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "used": self.used,
            "remaining": self.remaining,
            "percentage": round(self.percentage, 1),
            "status": self.status.value,
        }


# ============================================================================
# Hook 事件 (对应 Codex HOOK_EVENT_NAMES)
# 来源: codex-rs/hooks/src/lib.rs — 顺序与 Codex 一致
# ============================================================================

class HookEvent(Enum):
    """
    Hook 生命周期事件。
    对应 Codex 的 HOOK_EVENT_NAMES 常量。

    顺序与 Codex 源码一致。
    """
    PRE_TOOL_USE = "PreToolUse"
    PERMISSION_REQUEST = "PermissionRequest"
    POST_TOOL_USE = "PostToolUse"
    PRE_COMPACT = "PreCompact"
    POST_COMPACT = "PostCompact"
    SESSION_START = "SessionStart"
    SESSION_END = "SessionEnd"
    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    SUBAGENT_START = "SubagentStart"
    SUBAGENT_STOP = "SubagentStop"
    STOP = "Stop"


# Codex 中有 matcher 的事件 (可以按工具名/触发器匹配)
HOOK_EVENTS_WITH_MATCHERS = {
    HookEvent.PRE_TOOL_USE,
    HookEvent.PERMISSION_REQUEST,
    HookEvent.POST_TOOL_USE,
    HookEvent.PRE_COMPACT,
    HookEvent.POST_COMPACT,
    HookEvent.SESSION_START,
    HookEvent.SESSION_END,
    HookEvent.SUBAGENT_START,
    HookEvent.SUBAGENT_STOP,
}


# ============================================================================
# 代理模板 (对应 Codex AgentTemplate)
# 来源: codex-rs/core/src/agent/
# ============================================================================

class AgentTemplate:
    """
    代理模板。
    定义代理的角色、可用工具和行为策略。
    """
    def __init__(
        self,
        name: str,
        role: str,
        description: str,
        tools: List[str],
        auto_approve: List[str],
        require_approval: List[str],
    ):
        self.name = name
        self.role = role
        self.description = description
        self.tools = tools
        self.auto_approve = auto_approve
        self.require_approval = require_approval

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "tools": self.tools,
            "auto_approve": self.auto_approve,
            "require_approval": self.require_approval,
        }


# ============================================================================
# 工具函数
# ============================================================================

def estimate_tokens(text: str) -> int:
    """
    估算文本的 token 数量。
    粗略估算: 英文约 4 字符/token，中文约 2 字符/token。
    """
    if not text:
        return 0
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    non_ascii = len(text) - ascii_chars
    return (ascii_chars // 4) + (non_ascii // 2)


def shell_escape(value: str) -> str:
    """Shell 转义。使用 shlex.quote 确保值在 shell 命令中安全使用。"""
    return shlex.quote(value)


def validate_path(path: str, allowed_dirs: Optional[List[str]] = None, must_exist: bool = False) -> str:
    """
    验证文件路径安全性。防止路径遍历攻击。

    参数:
        path: 要验证的路径
        allowed_dirs: 允许的目录列表 (None 表示不限制)
        must_exist: 是否要求路径存在

    返回: 规范化后的安全路径

    异常:
        ValueError: 路径不安全或不存在
    """
    import os
    normalized = os.path.normpath(os.path.expanduser(path))
    if '..' in normalized.split(os.sep):
        raise ValueError(f"Path traversal detected: {path}")
    if must_exist and not os.path.exists(normalized):
        raise ValueError(f"Path does not exist: {path}")
    return normalized


def classify_tool(tool_name: str, tool_args: Dict[str, Any]) -> str:
    """
    分类工具调用。
    返回: "auto_approve" / "policy_check" / "command_review" / "guardian_review"
    """
    auto_approve_tools = {
        "read_file", "search_files", "session_search", "skill_view",
        "skills_list", "tool_search", "tool_describe",
    }

    guardian_review_tools = {
        "apply_patch",
        "send_message", "cronjob", "delegate_task", "text_to_speech",
    }

    command_review_tools = {
        "terminal", "execute_code", "browser_navigate", "browser_click",
        "browser_type", "browser_press", "browser_scroll",
    }

    if tool_name in auto_approve_tools:
        return "auto_approve"
    if tool_name in guardian_review_tools:
        return "guardian_review"
    if tool_name in command_review_tools:
        return "command_review"
    return "policy_check"


def determine_approval_requirement(
    tool_name: str,
    tool_args: Dict[str, Any],
    approval_policy: str = "auto",
    strict_auto_review: bool = False,
) -> ExecApprovalRequirement:
    """
    确定工具调用的审批需求。
    对应 Codex 的 default_exec_approval_requirement()。

    参数:
        tool_name: 工具名称
        tool_args: 工具参数
        approval_policy: 审批策略 ("auto" / "suggest" / "auto_edit" / "full_auto")
        strict_auto_review: 是否严格自动审查 (即使 Skip 也需要 Guardian)

    返回: ExecApprovalRequirement
    """
    classification = classify_tool(tool_name, tool_args)

    # 自动批准
    if classification == "auto_approve":
        return ExecApprovalRequirement(
            approval_type=ExecApprovalType.SKIP,
            security_level=SecurityLevel.NONE,
            strict_auto_review=strict_auto_review,
            bypass_sandbox=True,
        )

    # 文件操作检查
    if tool_name in ("write_file", "patch"):
        path = tool_args.get("path", "")
        file_check = FilePolicy.check(path)
        if file_check == "deny":
            return ExecApprovalRequirement(
                approval_type=ExecApprovalType.FORBIDDEN,
                reason=f"File access denied by policy: {path}",
                security_level=SecurityLevel.HIGH,
            )
        if file_check == "review":
            return ExecApprovalRequirement(
                approval_type=ExecApprovalType.NEEDS_APPROVAL,
                reason=f"File access requires review: {path}",
                security_level=SecurityLevel.MEDIUM,
            )
        return ExecApprovalRequirement(
            approval_type=ExecApprovalType.SKIP,
            security_level=SecurityLevel.LOW,
            strict_auto_review=strict_auto_review,
        )

    # 命令执行检查
    if tool_name in ("terminal", "execute_code"):
        command = tool_args.get("command", "")
        cmd_check = CommandPolicy.check(command)
        if cmd_check == "deny":
            return ExecApprovalRequirement(
                approval_type=ExecApprovalType.FORBIDDEN,
                reason=f"Command denied by policy: {command[:100]}",
                security_level=SecurityLevel.MAXIMUM,
            )
        if cmd_check == "review":
            return ExecApprovalRequirement(
                approval_type=ExecApprovalType.NEEDS_APPROVAL,
                reason=f"Command requires review: {command[:100]}",
                security_level=SecurityLevel.HIGH,
            )
        # 检查密钥
        secrets = SecretPolicy.scan(command)
        if secrets:
            return ExecApprovalRequirement(
                approval_type=ExecApprovalType.NEEDS_APPROVAL,
                reason="Command contains potential secrets",
                security_level=SecurityLevel.MAXIMUM,
            )
        return ExecApprovalRequirement(
            approval_type=ExecApprovalType.SKIP,
            security_level=SecurityLevel.LOW,
            strict_auto_review=strict_auto_review,
            proposed_execpolicy_amendment=ExecPolicyAmendment(
                command_prefix=command.split()[0] if command.split() else "",
                description=f"Auto-approve {command.split()[0]} commands",
            ),
        )

    # 网络访问检查
    if tool_name in ("browser_navigate",):
        url = tool_args.get("url", "")
        net_check = NetworkPolicy.check(url)
        if net_check == "deny":
            return ExecApprovalRequirement(
                approval_type=ExecApprovalType.FORBIDDEN,
                reason=f"Network access denied: {url}",
                security_level=SecurityLevel.HIGH,
            )
        if net_check == "review":
            return ExecApprovalRequirement(
                approval_type=ExecApprovalType.NEEDS_APPROVAL,
                reason=f"Network access requires review: {url}",
                security_level=SecurityLevel.MEDIUM,
            )
        return ExecApprovalRequirement(
            approval_type=ExecApprovalType.SKIP,
            security_level=SecurityLevel.LOW,
            strict_auto_review=strict_auto_review,
        )

    # 敏感操作
    if classification == "guardian_review":
        return ExecApprovalRequirement(
            approval_type=ExecApprovalType.NEEDS_APPROVAL,
            reason=f"Sensitive operation requires Guardian review: {tool_name}",
            security_level=SecurityLevel.HIGH,
        )

    # 默认: 低安全级别
    return ExecApprovalRequirement(
        approval_type=ExecApprovalType.SKIP,
        security_level=SecurityLevel.LOW,
        strict_auto_review=strict_auto_review,
    )


# ============================================================================
# CLI 接口
# ============================================================================

def main() -> None:
    """CLI 入口，用于测试和查询"""
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Codex Harness Core Library")
    subparsers = parser.add_subparsers(dest="command")

    # types 命令: 列出所有类型
    subparsers.add_parser("types", help="List all defined types")

    # classify 命令: 分类工具调用
    classify_parser = subparsers.add_parser("classify", help="Classify a tool call")
    classify_parser.add_argument("tool_name", help="Tool name")
    classify_parser.add_argument("--args", default="{}", help="Tool args JSON")

    # approve 命令: 确定审批需求
    approve_parser = subparsers.add_parser("approve", help="Determine approval requirement")
    approve_parser.add_argument("tool_name", help="Tool name")
    approve_parser.add_argument("--args", default="{}", help="Tool args JSON")
    approve_parser.add_argument("--policy", default="auto", help="Approval policy")
    approve_parser.add_argument("--strict", action="store_true", help="Strict auto review")

    # guardian 命令: Guardian 评估
    guardian_parser = subparsers.add_parser("guardian", help="Create Guardian assessment")
    guardian_parser.add_argument("--risk", default="low", help="Risk level")
    guardian_parser.add_argument("--auth", default="unknown", help="User authorization")
    guardian_parser.add_argument("--outcome", default="allow", help="Outcome")
    guardian_parser.add_argument("--rationale", default="", help="Rationale")

    # budget 命令: Token 预算
    budget_parser = subparsers.add_parser("budget", help="Check token budget")
    budget_parser.add_argument("--total", type=int, required=True, help="Total tokens")
    budget_parser.add_argument("--used", type=int, required=True, help="Used tokens")

    # hook 命令: 列出 Hook 事件
    subparsers.add_parser("hooks", help="List all hook events")

    args = parser.parse_args()

    if args.command == "types":
        types = [
            "SecurityLevel", "FilePolicy", "CommandPolicy", "NetworkPolicy", "SecretPolicy",
            "ExecApprovalType", "ExecPolicyAmendment", "ExecApprovalRequirement",
            "SandboxAttempt", "SandboxOverrideType",
            "GuardianRiskLevel", "GuardianUserAuthorization",
            "GuardianAssessmentOutcome", "GuardianAssessment",
            "CircuitBreakerPolicy", "CircuitBreakerAction",
            "CircuitBreakerTurnState", "CircuitBreakerState",
            "ContextualUserFragment", "TokenBudget", "HookEvent", "AgentTemplate",
        ]
        print(json.dumps({"types": types, "count": len(types)}, indent=2))

    elif args.command == "classify":
        tool_args = json.loads(args.args)
        classification = classify_tool(args.tool_name, tool_args)
        print(json.dumps({
            "tool": args.tool_name,
            "classification": classification,
        }, indent=2))

    elif args.command == "approve":
        tool_args = json.loads(args.args)
        requirement = determine_approval_requirement(
            args.tool_name, tool_args, args.policy, args.strict,
        )
        print(json.dumps(requirement.to_dict(), indent=2))

    elif args.command == "guardian":
        assessment = GuardianAssessment(
            risk_level=GuardianRiskLevel(args.risk),
            user_authorization=GuardianUserAuthorization(args.auth),
            outcome=GuardianAssessmentOutcome(args.outcome),
            rationale=args.rationale,
        )
        print(json.dumps(assessment.to_dict(), indent=2))

    elif args.command == "budget":
        budget = TokenBudget(total=args.total, used=args.used)
        print(json.dumps(budget.to_dict(), indent=2))

    elif args.command == "hooks":
        events = [e.value for e in HookEvent]
        print(json.dumps({"events": events, "count": len(events)}, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()


# ============================================================================
# 沙箱错误 (对应 Codex SandboxErr)
# 来源: codex-rs/protocol/src/error.rs
# ============================================================================

class SandboxErrorType(Enum):
    """沙箱错误类型"""
    DENIED = "denied"          # 沙箱拒绝
    TIMEOUT = "timeout"        # 沙箱超时
    SIGNAL = "signal"          # 沙箱信号
    VIOLATION = "violation"    # 沙箱违规


class SandboxError(Exception):
    """
    沙箱错误。
    对应 Codex 的 SandboxErr。

    用于精确标识沙箱相关的错误，而不是通过字符串匹配。
    """
    def __init__(
        self,
        error_type: SandboxErrorType,
        message: str,
        output: Optional[str] = None,
        network_policy_decision: Optional[bool] = None,
    ):
        self.error_type = error_type
        self.message = message
        self.output = output
        self.network_policy_decision = network_policy_decision
        super().__init__(message)

    def is_denied(self) -> bool:
        return self.error_type == SandboxErrorType.DENIED

    def is_timeout(self) -> bool:
        return self.error_type == SandboxErrorType.TIMEOUT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "output": self.output[:200] if self.output else None,
            "network_policy_decision": self.network_policy_decision,
        }
