#!/usr/bin/env python3
"""
Codex Harness — Hook 生命周期引擎

负责: 11 个生命周期事件 + 模式匹配 + YAML 配置 + 变量替换 + 超时处理
对应 Codex: codex-rs/hooks/

所有共享类型从 core.py 导入。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import fnmatch
import json
import re
import signal
import subprocess
import time
from typing import Any, Dict, List, Optional

from core import HookEvent, shell_escape


# ============================================================================
# Hook 定义
# ============================================================================


# Codex Hook 事件名称 (对应 Codex HOOK_EVENT_NAMES)
VALID_EVENTS = [
    "PreToolUse", "PermissionRequest", "PostToolUse",
    "PreCompact", "PostCompact",
    "SessionStart", "SessionEnd",
    "UserPromptSubmit",
    "SubagentStart", "SubagentStop",
    "Stop",
]
class HookDef:
    """Hook 定义。"""
    def __init__(
        self,
        name: str,
        event: str,
        command: str,
        match: str = "*",
        enabled: bool = True,
        timeout: int = 30,
        working_dir: Optional[str] = None,
        shell: str = "/bin/bash",
    ):
        """初始化 Hook 定义。"""
        self.name = name
        self.event = event
        self.command = command
        self.match = match
        self.enabled = enabled
        self.timeout = timeout
        self.working_dir = working_dir
        self.shell = shell

    def matches(self, context: Dict[str, Any]) -> bool:
        """检查 Hook 是否匹配给定上下文。"""
        if not self.enabled:
            return False
        if self.match == "*":
            return True
        tool_name = context.get("tool_name", "")
        return fnmatch.fnmatch(tool_name, self.match)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "event": self.event,
            "command": self.command,
            "match": self.match,
            "enabled": self.enabled,
            "timeout": self.timeout,
        }


# ============================================================================
# Hook 执行结果
# ============================================================================

class HookResult:
    """Hook 执行结果枚举。"""
    SUCCESS = "success"
    BLOCKED = "blocked"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


class HookExecResult:
    """单个 Hook 的执行结果。"""
    def __init__(
        self,
        hook_name: str,
        event: str,
        result: str,
        stdout: str = "",
        stderr: str = "",
        returncode: int = 0,
        duration_ms: float = 0.0,
        error: Optional[str] = None,
    ):
        """初始化执行结果。"""
        self.hook_name = hook_name
        self.event = event
        self.result = result
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.duration_ms = duration_ms
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hook_name": self.hook_name,
            "event": self.event,
            "result": self.result,
            "stdout": self.stdout[:500],
            "stderr": self.stderr[:500],
            "returncode": self.returncode,
            "duration_ms": round(self.duration_ms, 2),
            "error": self.error,
        }


class HookRunSummary:
    """一次 Hook 运行的汇总。"""
    def __init__(self, event: str, results: List[HookExecResult]):
        """初始化运行汇总。"""
        self.event = event
        self.results = results

    @property
    def any_blocked(self) -> bool:
        return any(r.result == HookResult.BLOCKED for r in self.results)

    @property
    def any_failed(self) -> bool:
        return any(r.result == HookResult.FAILED for r in self.results)

    @property
    def all_success(self) -> bool:
        return all(r.result in (HookResult.SUCCESS, HookResult.SKIPPED) for r in self.results)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event,
            "total": len(self.results),
            "blocked": sum(1 for r in self.results if r.result == HookResult.BLOCKED),
            "failed": sum(1 for r in self.results if r.result == HookResult.FAILED),
            "results": [r.to_dict() for r in self.results],
        }


# ============================================================================
# 变量替换
# ============================================================================

VAR_PATTERN = re.compile(r'\$\{(\w+)\}|\$(\w+)')


def validate_hook_command(command: str) -> bool:
    """
    验证 Hook 命令安全性。
    检查命令长度。
    """
    # 命令长度限制
    if len(command) > 10000:
        return False
    
    # 检查命令是否为空
    if not command.strip():
        return False
    
    return True


def substitute_variables(command: str, variables: Dict[str, str]) -> str:
    """
    替换命令中的变量。
    使用 shlex.quote 转义变量值防止注入。
    """
    def replacer(match):
        var_name = match.group(1) or match.group(2)
        if var_name in variables:
            return shell_escape(variables[var_name])
        return match.group(0)
    return VAR_PATTERN.sub(replacer, command)


def collect_variables(context: Dict[str, Any], extra_vars: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """从上下文收集变量。"""
    variables = {}
    for key, value in context.items():
        if isinstance(value, str):
            variables[key] = value
        elif isinstance(value, (int, float, bool)):
            variables[key] = str(value)
    if extra_vars:
        variables.update(extra_vars)
    return variables


# ============================================================================
# Hook 配置加载
# ============================================================================

class HookConfigLoader:
    """Hook 配置加载器。"""
    def load(self, path: str) -> List[HookDef]:
        """加载 Hook 配置文件。"""
        if not os.path.exists(path):
            return []
        if path.endswith(('.yaml', '.yml')):
            return self._load_yaml(path)
        elif path.endswith('.json'):
            return self._load_json(path)
        return []

    def _load_yaml(self, path: str) -> List[HookDef]:
        """加载 YAML 配置。"""
        try:
            import yaml
            with open(path) as f:
                data = yaml.safe_load(f)
            return self._parse_config(data)
        except Exception as e:
            print(f"Error loading YAML: {e}", file=sys.stderr)
            return []

    def _load_json(self, path: str) -> List[HookDef]:
        """加载 JSON 配置。"""
        try:
            with open(path) as f:
                data = json.load(f)
            return self._parse_config(data)
        except Exception as e:
            print(f"Error loading JSON: {e}", file=sys.stderr)
            return []

    def _parse_config(self, data: Any) -> List[HookDef]:
        """解析配置数据。"""
        hooks = []
        if not isinstance(data, dict):
            return hooks

        hooks_data = data.get("hooks", {})
        for event_name, hook_list in hooks_data.items():
            if not isinstance(hook_list, list):
                continue
            for i, item in enumerate(hook_list):
                if not isinstance(item, dict):
                    continue
                hook = HookDef(
                    name=item.get("name", f"{event_name}_{i}"),
                    event=event_name,
                    command=item.get("command", item.get("run", "")),
                    match=item.get("match", "*"),
                    enabled=item.get("enabled", True),
                    timeout=item.get("timeout", 30),
                    working_dir=item.get("working_dir"),
                    shell=item.get("shell", "/bin/bash"),
                )
                hooks.append(hook)
        return hooks


# ============================================================================
# Hook 引擎
# ============================================================================

class HookEngine:
    """
    Hook 生命周期引擎。
    对应 Codex 的 HookEngine。

    实现:
    - 11 个 Hook 事件
    - 模式匹配
    - 变量替换
    - 超时处理
    - 结果收集
    """
    def __init__(self, hooks: Optional[List[HookDef]] = None):
        """初始化 Hook 引擎。"""
        self.hooks = hooks or []
        self.loader = HookConfigLoader()

    def load_config(self, path: str):
        """加载 Hook 配置。"""
        self.hooks.extend(self.loader.load(path))

    def add_hook(self, hook: HookDef):
        """添加 Hook。"""
        self.hooks.append(hook)

    def run_event(self, event: str, context: Optional[Dict[str, Any]] = None) -> HookRunSummary:
        """
        运行指定事件的所有 Hook。
        对应 Codex 的 hook 执行流程。
        """
        context = context or {}
        variables = collect_variables(context)
        matching_hooks = [h for h in self.hooks if h.event == event and h.matches(context)]

        results = []
        for hook in matching_hooks:
            result = self._execute_hook(hook, variables, context)
            results.append(result)

        return HookRunSummary(event=event, results=results)

    def _execute_hook(self, hook: HookDef, variables: Dict[str, str], context: Dict[str, Any]) -> HookExecResult:
        """执行单个 Hook。"""
        command = substitute_variables(hook.command, variables)
        
        # 验证命令安全性
        if not validate_hook_command(command):
            return HookExecResult(
                hook_name=hook.name,
                event=hook.event,
                result=HookResult.FAILED,
                error='Command validation failed',
            )
        
        start_time = time.time()

        try:
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=hook.timeout,
                cwd=hook.working_dir,
            )
            duration_ms = (time.time() - start_time) * 1000

            if result.returncode == 0:
                exec_result = HookResult.SUCCESS
            elif result.returncode == 2:
                # 对应 Codex: exit code 2 表示阻止
                exec_result = HookResult.BLOCKED
            else:
                exec_result = HookResult.FAILED

            return HookExecResult(
                hook_name=hook.name,
                event=hook.event,
                result=exec_result,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                duration_ms=duration_ms,
            )

        except subprocess.TimeoutExpired:
            duration_ms = (time.time() - start_time) * 1000
            return HookExecResult(
                hook_name=hook.name,
                event=hook.event,
                result=HookResult.TIMEOUT,
                duration_ms=duration_ms,
                error=f"Hook timed out after {hook.timeout}s",
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HookExecResult(
                hook_name=hook.name,
                event=hook.event,
                result=HookResult.FAILED,
                duration_ms=duration_ms,
                error=str(e),
            )

    def list_hooks(self) -> List[Dict[str, Any]]:
        """列出所有 Hook。"""
        return [h.to_dict() for h in self.hooks]

    def get_events(self) -> List[str]:
        """获取所有已注册的事件。"""
        return list(set(h.event for h in self.hooks))


# ============================================================================
# CLI 接口
# ============================================================================

def cmd_run(args) -> None:
    """运行 Hook 事件。"""
    engine = HookEngine()
    if args.config:
        engine.load_config(args.config)

    context = {}
    if args.var:
        for var in args.var:
            key, _, value = var.partition("=")
            context[key] = value

    summary = engine.run_event(args.event, context)
    print(json.dumps(summary.to_dict(), indent=2))


def cmd_list(args) -> None:
    """列出所有 Hook。"""
    engine = HookEngine()
    if args.config:
        engine.load_config(args.config)
    hooks = engine.list_hooks()
    print(json.dumps({"hooks": hooks, "count": len(hooks)}, indent=2))


def cmd_events(args) -> None:
    """列出所有支持的事件。"""
    events = [e.value for e in HookEvent]
    print(json.dumps({"events": events, "count": len(events)}, indent=2))


def main() -> None:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description="Codex Harness Hook Engine")
    subparsers = parser.add_subparsers(dest="command")

    # run 命令
    run_parser = subparsers.add_parser("run", help="Run hook event")
    run_parser.add_argument("--event", required=True, help="Event name")
    run_parser.add_argument("--config", help="Hook config file")
    run_parser.add_argument("--var", action="append", help="Variable (key=value)")

    # list 命令
    list_parser = subparsers.add_parser("list", help="List hooks")
    list_parser.add_argument("--config", help="Hook config file")

    # events 命令
    subparsers.add_parser("events", help="List supported events")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "events":
        cmd_events(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
