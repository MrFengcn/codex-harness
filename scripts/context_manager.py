#!/usr/bin/env python3
"""
Context Management Engine
=========================

Manages the conversation context window for AI agents. Handles token
counting, budget monitoring, auto-compaction, and context fragment
injection. Based on Codex's context module.

Features:
  - Token counting (tiktoken-based with fallback heuristic)
  - Budget checking with ok/warning/critical levels
  - Auto-compaction (standard and aggressive modes)
  - Context fragment injection (time, budget, task info)
  - Summary generation for compacted history

Usage:
  python context_manager.py count --text "Hello world"
  python context_manager.py budget --used 50000 --total 128000
  python context_manager.py compact --input history.json --mode standard
  python context_manager.py inject --fragments '["time","budget"]'
  python context_manager.py summary --input history.json
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import TokenBudget, estimate_tokens

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import argparse
import json
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Token counting
# ---------------------------------------------------------------------------

# Try tiktoken first, fall back to heuristic
_TOKENIZER = None

def _get_tokenizer():
    """Lazy-load tokenizer."""
    global _TOKENIZER
    if _TOKENIZER is not None:
        return _TOKENIZER
    try:
        import tiktoken
        _TOKENIZER = tiktoken.get_encoding("cl100k_base")
        return _TOKENIZER
    except ImportError:
        return None


def count_tokens(text: str) -> int:
    """
    Count tokens in text. Uses tiktoken if available, otherwise
    uses a character-based heuristic (~4 chars per token for English).
    """
    if not text:
        return 0
    tokenizer = _get_tokenizer()
    if tokenizer:
        return len(tokenizer.encode(text))
    # Heuristic: ~4 chars per token, with adjustments for non-ASCII
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    non_ascii = len(text) - ascii_chars
    return (ascii_chars + 3) // 4 + (non_ascii + 1) // 2


def count_message_tokens(messages: List[Dict[str, str]]) -> int:
    """Count tokens across a list of messages (OpenAI format)."""
    total = 0
    for msg in messages:
        # Overhead per message (role, formatting)
        total += 4
        for key, value in msg.items():
            if isinstance(value, str):
                total += count_tokens(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and "text" in item:
                        total += count_tokens(item["text"])
    total += 2  # Reply priming
    return total


# ---------------------------------------------------------------------------
# Budget management
# ---------------------------------------------------------------------------

class BudgetLevel(Enum):
    """Budget usage levels."""
    OK = "ok"              # < 70% used
    WARNING = "warning"    # 70-85% used
    CRITICAL = "critical"  # 85-95% used
    EXCEEDED = "exceeded"  # > 95% used



class BudgetStatus:
    """Current budget status."""
    level: BudgetLevel
    used: int
    total: int
    remaining: int
    percentage: float
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "used": self.used,
            "total": self.total,
            "remaining": self.remaining,
            "percentage": round(self.percentage, 1),
            "message": self.message,
        }


def check_budget(used: int, total: int, thresholds: Optional[Dict[str, float]] = None) -> BudgetStatus:
    """
    Check context budget usage level.

    Args:
        used: Tokens currently used
        total: Total token budget
        thresholds: Optional custom thresholds {ok, warning, critical, exceeded}

    Returns:
        BudgetStatus with level and details
    """
    thresholds = thresholds or {
        "ok": 0.70,
        "warning": 0.85,
        "critical": 0.95,
        "exceeded": 1.0,
    }

    if total <= 0:
        return BudgetStatus(
            level=BudgetLevel.EXCEEDED,
            used=used,
            total=total,
            remaining=0,
            percentage=100.0,
            message="Invalid total budget",
        )

    remaining = max(0, total - used)
    pct = (used / total) * 100.0

    if pct >= thresholds["exceeded"] * 100:
        level = BudgetLevel.EXCEEDED
        msg = f"BUDGET EXCEEDED: {pct:.1f}% used ({used}/{total}). Immediate compaction required."
    elif pct >= thresholds["critical"] * 100:
        level = BudgetLevel.CRITICAL
        msg = f"CRITICAL: {pct:.1f}% used ({used}/{total}). Aggressive compaction recommended."
    elif pct >= thresholds["warning"] * 100:
        level = BudgetLevel.WARNING
        msg = f"WARNING: {pct:.1f}% used ({used}/{total}). Consider compacting."
    else:
        level = BudgetLevel.OK
        msg = f"OK: {pct:.1f}% used ({used}/{total}). {remaining} tokens remaining."

    return BudgetStatus(
        level=level,
        used=used,
        total=total,
        remaining=remaining,
        percentage=pct,
        message=msg,
    )


# ---------------------------------------------------------------------------
# Compaction engine
# ---------------------------------------------------------------------------


class CompactionResult:
    """Result of a compaction operation."""
    def __init__(
        self,
        original_tokens: int = 0,
        compacted_tokens: int = 0,
        messages_removed: int = 0,
        messages_summarized: int = 0,
        summary: str = "",
        compacted_messages: Optional[List[Dict[str, str]]] = None,
    ):
        self.original_tokens = original_tokens
        self.compacted_tokens = compacted_tokens
        self.messages_removed = messages_removed
        self.messages_summarized = messages_summarized
        self.summary = summary
        self.compacted_messages = compacted_messages or []
        self.savings_pct = (1.0 - (compacted_tokens / original_tokens)) * 100 if original_tokens > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_tokens": self.original_tokens,
            "compacted_tokens": self.compacted_tokens,
            "messages_removed": self.messages_removed,
            "messages_summarized": self.messages_summarized,
            "summary": self.summary,
            "savings_pct": round(self.savings_pct, 1),
            "compacted_messages": self.compacted_messages,
        }


class ContextCompactor:
    """
    Handles context compaction with two modes:
      - standard: Remove old tool outputs, keep conversation flow
      - aggressive: Summarize everything except recent messages
    """

    def __init__(self, keep_recent: int = 5, summary_max_tokens: int = 500):
        self.keep_recent = keep_recent
        self.summary_max_tokens = summary_max_tokens

    def compact(self, messages: List[Dict[str, str]], mode: str = "standard",
                target_tokens: Optional[int] = None) -> CompactionResult:
        """
        Compact a message history.

        Args:
            messages: List of messages in OpenAI format
            mode: 'standard' or 'aggressive'
            target_tokens: Optional target token count to compact toward

        Returns:
            CompactionResult with compacted messages and stats
        """
        original_tokens = count_message_tokens(messages)

        if mode == "aggressive":
            return self._compact_aggressive(messages, original_tokens, target_tokens)
        else:
            return self._compact_standard(messages, original_tokens, target_tokens)

    def _compact_standard(self, messages: List[Dict[str, str]],
                          original_tokens: int,
                          target_tokens: Optional[int]) -> CompactionResult:
        """
        Standard compaction: Remove/middle-truncate old tool outputs,
        keep conversation flow intact.
        """
        if len(messages) <= self.keep_recent:
            return CompactionResult(
                original_tokens=original_tokens,
                compacted_tokens=original_tokens,
                messages_removed=0,
                messages_summarized=0,
                summary="No compaction needed (too few messages)",
                compacted_messages=list(messages),
                savings_pct=0.0,
            )

        # Split into old and recent
        old_messages = messages[:-self.keep_recent]
        recent_messages = messages[-self.keep_recent:]

        # Process old messages: truncate tool outputs, keep user/assistant
        compacted_old = []
        removed = 0
        summarized = 0

        for msg in old_messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "tool":
                # Truncate tool outputs to first/last N chars
                if isinstance(content, str) and len(content) > 500:
                    truncated = content[:250] + "\n... [truncated] ...\n" + content[-250:]
                    compacted_old.append({**msg, "content": truncated})
                    summarized += 1
                else:
                    compacted_old.append(msg)
            elif role == "system":
                # Keep system messages as-is
                compacted_old.append(msg)
            else:
                # For long assistant messages, truncate if needed
                if isinstance(content, str) and count_tokens(content) > 200:
                    # Keep first 100 tokens worth (~400 chars)
                    trunc = content[:400] + "\n... [compacted]"
                    compacted_old.append({**msg, "content": trunc})
                    summarized += 1
                else:
                    compacted_old.append(msg)

        # Check if we hit target
        compacted = compacted_old + recent_messages
        compacted_tokens = count_message_tokens(compacted)

        # If still over target, do deeper cuts
        if target_tokens and compacted_tokens > target_tokens:
            # Remove oldest messages beyond system
            system_msgs = [m for m in compacted_old if m.get("role") == "system"]
            non_system = [m for m in compacted_old if m.get("role") != "system"]

            while non_system and compacted_tokens > target_tokens:
                non_system.pop(0)
                removed += 1
                compacted = system_msgs + non_system + recent_messages
                compacted_tokens = count_message_tokens(compacted)

        summary = self._generate_summary(messages[:len(messages) - self.keep_recent])

        savings = ((original_tokens - compacted_tokens) / original_tokens * 100) if original_tokens > 0 else 0

        return CompactionResult(
            original_tokens=original_tokens,
            compacted_tokens=compacted_tokens,
            messages_removed=removed,
            messages_summarized=summarized,
            summary=summary,
            compacted_messages=compacted,
            savings_pct=savings,
        )

    def _compact_aggressive(self, messages: List[Dict[str, str]],
                            original_tokens: int,
                            target_tokens: Optional[int]) -> CompactionResult:
        """
        Aggressive compaction: Replace all but recent messages with a summary.
        Used when context is critically over budget.
        """
        if len(messages) <= self.keep_recent:
            return CompactionResult(
                original_tokens=original_tokens,
                compacted_tokens=original_tokens,
                messages_removed=0,
                messages_summarized=0,
                summary="No compaction needed",
                compacted_messages=list(messages),
                savings_pct=0.0,
            )

        # Keep system messages and recent
        system_msgs = [m for m in messages if m.get("role") == "system"]
        recent = messages[-self.keep_recent:]
        old = messages[len(system_msgs):-self.keep_recent]

        # Generate summary of old messages
        summary = self._generate_summary(old)

        # Build compacted: system + summary + recent
        summary_msg = {
            "role": "assistant",
            "content": f"[Context Compaction Summary]\n{summary}",
        }
        compacted = system_msgs + [summary_msg] + recent
        compacted_tokens = count_message_tokens(compacted)

        # If still over target with aggressive, truncate summary
        if target_tokens and compacted_tokens > target_tokens:
            excess = compacted_tokens - target_tokens
            summary_tokens = count_tokens(summary)
            if summary_tokens > excess:
                # Truncate summary
                chars_to_keep = max(100, (summary_tokens - excess) * 4)
                summary = summary[:int(chars_to_keep)] + "\n... [further truncated]"
                summary_msg["content"] = f"[Context Compaction Summary]\n{summary}"
                compacted = system_msgs + [summary_msg] + recent
                compacted_tokens = count_message_tokens(compacted)

        savings = ((original_tokens - compacted_tokens) / original_tokens * 100) if original_tokens > 0 else 0

        return CompactionResult(
            original_tokens=original_tokens,
            compacted_tokens=compacted_tokens,
            messages_removed=len(old),
            messages_summarized=len(old),
            summary=summary,
            compacted_messages=compacted,
            savings_pct=savings,
        )

    def _generate_summary(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a summary of messages. This produces a structured
        extractive summary without requiring an LLM call.
        """
        if not messages:
            return "No messages to summarize."

        topics = []
        actions = []
        decisions = []
        user_turns = 0
        assistant_turns = 0
        tool_calls = 0

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if not isinstance(content, str):
                content = str(content) if content else ""

            if role == "user":
                user_turns += 1
                # Extract key user requests
                if content and len(content) > 10:
                    first_line = content.split('\n')[0][:150]
                    topics.append(first_line)
            elif role == "assistant":
                assistant_turns += 1
                # Extract decisions or conclusions
                if content:
                    for line in content.split('\n'):
                        line = line.strip()
                        if any(kw in line.lower() for kw in ['created', 'wrote', 'built', 'fixed', 'implemented', 'added']):
                            actions.append(line[:150])
            elif role == "tool":
                tool_calls += 1

        parts = [f"Conversation: {user_turns} user turns, {assistant_turns} assistant turns, {tool_calls} tool calls."]

        if topics:
            parts.append("Key topics: " + "; ".join(topics[:5]))
        if actions:
            parts.append("Actions taken: " + "; ".join(actions[:5]))

        return " ".join(parts)


# ---------------------------------------------------------------------------
# Context Fragment Injection
# ---------------------------------------------------------------------------

class ContextInjector:
    """Injects contextual fragments into the conversation."""

    def __init__(self, task_description: str = "", budget_total: int = 128000,
                 budget_used: int = 0):
        self.task_description = task_description
        self.budget_total = budget_total
        self.budget_used = budget_used

    def inject(self, messages: List[Dict[str, str]],
               fragments: List[str]) -> List[Dict[str, str]]:
        """
        Inject context fragments into the message list.

        Args:
            messages: Current message list
            fragments: List of fragment types to inject:
                'time' - Current time context
                'budget' - Budget status
                'task' - Task description
                'system_info' - System information

        Returns:
            Updated message list with injected fragments
        """
        injected_parts = []

        for frag in fragments:
            if frag == "time":
                injected_parts.append(self._time_fragment())
            elif frag == "budget":
                injected_parts.append(self._budget_fragment())
            elif frag == "task":
                injected_parts.append(self._task_fragment())
            elif frag == "system_info":
                injected_parts.append(self._system_info_fragment())

        if not injected_parts:
            return messages

        # Inject as system message at the beginning (after any existing system msg)
        fragment_text = "\n".join(injected_parts)
        fragment_msg = {
            "role": "system",
            "content": f"[Context Fragments]\n{fragment_text}",
        }

        # Find insertion point (after first system message if present)
        result = list(messages)
        insert_idx = 0
        for i, msg in enumerate(result):
            if msg.get("role") == "system":
                insert_idx = i + 1
                break

        result.insert(insert_idx, fragment_msg)
        return result

    def _time_fragment(self) -> str:
        """Generate time context fragment."""
        now = datetime.now(timezone.utc)
        return (
            f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"Day: {now.strftime('%A')}"
        )

    def _budget_fragment(self) -> str:
        """Generate budget status fragment."""
        status = check_budget(self.budget_used, self.budget_total)
        return (
            f"Token budget: {status.percentage:.1f}% used "
            f"({status.used}/{status.total}), "
            f"Level: {status.level.value}"
        )

    def _task_fragment(self) -> str:
        """Generate task context fragment."""
        if self.task_description:
            return f"Current task: {self.task_description}"
        return "No active task"

    def _system_info_fragment(self) -> str:
        """Generate system info fragment."""
        import platform
        return (
            f"Platform: {platform.system()} {platform.release()}\n"
            f"Python: {platform.python_version()}\n"
            f"CWD: {os.getcwd()}"
        )


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------

def cmd_count(args) -> None:
    """Count tokens in text."""
    if args.file:
        with open(args.file) as f:
            text = f.read()
    elif args.text:
        text = args.text
    elif args.stdin:
        text = sys.stdin.read()
    else:
        text = ""

    tokens = count_tokens(text)
    result = {
        "tokens": tokens,
        "chars": len(text),
        "chars_per_token": round(len(text) / tokens, 2) if tokens > 0 else 0,
    }
    print(json.dumps(result, indent=2))


def cmd_budget(args) -> None:
    """Check budget status."""
    status = check_budget(args.used, args.total)
    print(json.dumps(status.to_dict(), indent=2))
    sys.exit(0 if status.level in (BudgetLevel.OK, BudgetLevel.WARNING) else 1)


def cmd_compact(args) -> None:
    """Compact a message history."""
    if args.input:
        with open(args.input) as f:
            messages = json.load(f)
    else:
        messages = json.loads(sys.stdin.read())

    compactor = ContextCompactor(
        keep_recent=args.keep_recent,
        summary_max_tokens=args.summary_tokens,
    )

    result = compactor.compact(
        messages,
        mode=args.mode,
        target_tokens=args.target,
    )

    output = result.to_dict()
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=2)
        print(json.dumps({"status": "written", "output_file": args.output}, indent=2))
    else:
        print(json.dumps(output, indent=2))


def cmd_inject(args) -> None:
    """Inject context fragments."""
    fragments = json.loads(args.fragments)

    injector = ContextInjector(
        task_description=args.task or "",
        budget_total=args.budget_total,
        budget_used=args.budget_used,
    )

    if args.input:
        with open(args.input) as f:
            messages = json.load(f)
    else:
        messages = []

    result = injector.inject(messages, fragments)
    print(json.dumps(result, indent=2))


def cmd_summary(args) -> None:
    """Generate a summary of a message history."""
    if args.input:
        with open(args.input) as f:
            messages = json.load(f)
    else:
        messages = json.loads(sys.stdin.read())

    compactor = ContextCompactor()
    summary = compactor._generate_summary(messages)
    tokens = count_tokens(summary)

    print(json.dumps({
        "summary": summary,
        "tokens": tokens,
        "messages_count": len(messages),
    }, indent=2))




# ============================================================================
# WorldState 差异系统 (对应 Codex WorldState)
# 来源: codex-rs/core/src/context/world_state/
# ============================================================================

class WorldStateSection:
    """
    世界状态片段。
    对应 Codex 的 WorldStateSection trait。

    每个片段有:
    - id: 唯一标识
    - snapshot: 当前状态快照
    - fingerprint: SHA1 指纹 (用于变更检测)
    """
    def __init__(self, section_id: str, content: str):
        """初始化世界状态片段。"""
        self.section_id = section_id
        self.content = content
        self.fingerprint = self._compute_fingerprint(content)

    def _compute_fingerprint(self, content: str) -> str:
        """计算 SHA1 指纹。"""
        import hashlib
        return hashlib.sha1(content.encode('utf-8')).hexdigest()

    def has_changed(self, other: 'WorldStateSection') -> bool:
        """检查是否有变更。"""
        return self.fingerprint != other.fingerprint

    def to_dict(self) -> Dict[str, str]:
        return {
            "section_id": self.section_id,
            "fingerprint": self.fingerprint,
            "content_length": len(self.content),
        }


class WorldState:
    """
    世界状态管理器。
    对应 Codex 的 WorldState。

    管理多个 WorldStateSection，支持:
    - 添加/更新/删除片段
    - 差异检测 (基于 SHA1 指纹)
    - 差异渲染
    """
    def __init__(self):
        """初始化世界状态。"""
        self.sections: Dict[str, WorldStateSection] = {}
        self.previous_sections: Dict[str, WorldStateSection] = {}

    def update_section(self, section_id: str, content: str):
        """更新片段内容。"""
        # 保存旧状态
        if section_id in self.sections:
            self.previous_sections[section_id] = self.sections[section_id]
        # 更新新状态
        self.sections[section_id] = WorldStateSection(section_id, content)

    def remove_section(self, section_id: str):
        """删除片段。"""
        if section_id in self.sections:
            self.previous_sections[section_id] = self.sections[section_id]
            del self.sections[section_id]

    def get_changes(self) -> List[Dict[str, Any]]:
        """获取所有变更。"""
        changes = []
        for sid, section in self.sections.items():
            prev = self.previous_sections.get(sid)
            if prev is None:
                changes.append({"type": "added", "section_id": sid})
            elif section.has_changed(prev):
                changes.append({"type": "modified", "section_id": sid})
        for sid in self.previous_sections:
            if sid not in self.sections:
                changes.append({"type": "removed", "section_id": sid})
        return changes

    def render_diff(self) -> str:
        """渲染差异。"""
        changes = self.get_changes()
        if not changes:
            return "No changes"
        parts = []
        for change in changes:
            parts.append(f"[{change['type']}] {change['section_id']}")
        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sections": {sid: s.to_dict() for sid, s in self.sections.items()},
            "changes": self.get_changes(),
        }
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Context Management Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-command")

    # count
    p_count = subparsers.add_parser("count", help="Count tokens in text")
    p_count.add_argument("--text", help="Text to count tokens for")
    p_count.add_argument("--file", help="File to count tokens for")
    p_count.add_argument("--stdin", action="store_true", help="Read from stdin")

    # budget
    p_budget = subparsers.add_parser("budget", help="Check budget status")
    p_budget.add_argument("--used", type=int, required=True, help="Tokens used")
    p_budget.add_argument("--total", type=int, required=True, help="Total token budget")

    # compact
    p_compact = subparsers.add_parser("compact", help="Compact message history")
    p_compact.add_argument("--input", help="JSON file with messages")
    p_compact.add_argument("--output", help="Output file for compacted messages")
    p_compact.add_argument("--mode", choices=["standard", "aggressive"],
                           default="standard", help="Compaction mode")
    p_compact.add_argument("--keep-recent", type=int, default=5,
                           help="Number of recent messages to keep")
    p_compact.add_argument("--summary-tokens", type=int, default=500,
                           help="Max tokens for summary")
    p_compact.add_argument("--target", type=int, help="Target token count")

    # inject
    p_inject = subparsers.add_parser("inject", help="Inject context fragments")
    p_inject.add_argument("--fragments", required=True,
                          help='JSON array of fragment types: ["time","budget","task","system_info"]')
    p_inject.add_argument("--input", help="JSON file with messages")
    p_inject.add_argument("--task", help="Task description")
    p_inject.add_argument("--budget-total", type=int, default=128000)
    p_inject.add_argument("--budget-used", type=int, default=0)

    # summary
    p_summary = subparsers.add_parser("summary", help="Generate summary")
    p_summary.add_argument("--input", help="JSON file with messages")

    args = parser.parse_args()

    if args.command == "count":
        cmd_count(args)
    elif args.command == "budget":
        cmd_budget(args)
    elif args.command == "compact":
        cmd_compact(args)
    elif args.command == "inject":
        cmd_inject(args)
    elif args.command == "summary":
        cmd_summary(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()


# ============================================================================
# 压缩管理器集成
# ============================================================================

class ContextCompressionManager:
    """
    上下文压缩管理器。
    集成 compression 模块到 context_manager。

    功能:
    - 自动检测是否需要压缩
    - 使用 CompressionManager 执行压缩
    - 集成 WorldState 和 TokenBudget
    """

    def __init__(
        self,
        max_tokens: int = 128000,
        compression_threshold: float = 0.8,
        keep_recent: int = 10,
        enable_hooks: bool = True,
    ):
        """
        初始化上下文压缩管理器。

        参数:
            max_tokens: 最大 Token 数
            compression_threshold: 压缩阈值
            keep_recent: 保留最近消息数
            enable_hooks: 启用 Hook
        """
        self.max_tokens = max_tokens
        self.compression_threshold = compression_threshold
        self.keep_recent = keep_recent
        self.enable_hooks = enable_hooks

        # 导入压缩模块
        from compression import CompressionManager, CompressionConfig

        # 创建配置
        self.config = CompressionConfig(
            compression_threshold=compression_threshold,
            keep_recent=keep_recent,
            enable_hooks=enable_hooks,
        )

        # 创建管理器
        self.manager = CompressionManager(self.config)

        # 创建 Token 预算
        self.token_budget = TokenBudget(max_tokens, 0)

    def set_hook_engine(self, hook_engine):
        """
        设置 Hook 引擎。

        参数:
            hook_engine: Hook 引擎实例
        """
        self.manager.set_hook_engine(hook_engine)

    def check_and_compress(
        self,
        messages: List[Dict[str, Any]],
        current_tokens: Optional[int] = None,
    ) -> Optional[CompactionResult]:
        """
        检查并执行压缩。

        参数:
            messages: 当前消息列表
            current_tokens: 当前 Token 数 (None 自动计算)

        返回:
            CompactionResult 如果执行了压缩，否则 None
        """
        if current_tokens is None:
            current_tokens = estimate_tokens(str(messages))

        # 更新 Token 预算
        self.token_budget = TokenBudget(self.max_tokens, current_tokens)

        # 检查是否需要压缩
        if not self.manager.should_compress(current_tokens, self.max_tokens):
            return None

        # 计算目标 Token 数
        target_tokens = int(self.max_tokens * 0.6)  # 压缩到 60%

        # 执行压缩
        result = self.manager.compress(messages, target_tokens, self.keep_recent)

        # 转换为 CompactionResult
        return CompactionResult(
            original_tokens=result.original_tokens,
            compacted_tokens=result.compressed_tokens,
            summary=f"Compressed using {result.strategy_name}",
            messages_removed=result.original_tokens - result.compressed_tokens,
        )

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息。

        返回:
            统计字典
        """
        stats = self.manager.get_compression_stats()
        stats['max_tokens'] = self.max_tokens
        stats['compression_threshold'] = self.compression_threshold
        stats['token_budget'] = self.token_budget.to_dict()
        return stats

    def get_strategies(self) -> List[Dict[str, Any]]:
        """
        获取可用策略。

        返回:
            策略信息列表
        """
        return self.manager.get_strategies()
