#!/usr/bin/env python3
"""
Codex Harness — Shell 集成系统

提供 Shell 命令执行和管理能力。
对应 Codex 的 shell 模块。

Python 兼容性: 3.6+
"""


from enum import Enum
from typing import List, Dict, Any, Optional
import time


class ShellType(Enum):
    """Shell 类型"""
    BASH = "bash"
    SH = "sh"
    ZSH = "zsh"
    POWERSHELL = "powershell"
    CMD = "cmd"


class ShellResult:
    """
    Shell 执行结果。

    属性:
        success: 是否成功
        stdout: 标准输出
        stderr: 标准错误
        return_code: 返回码
        duration_ms: 执行耗时
    """
    def __init__(
        self,
        success: bool,
        stdout: str = "",
        stderr: str = "",
        return_code: int = 0,
        duration_ms: float = 0.0,
    ):
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code
        self.duration_ms = duration_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "return_code": self.return_code,
            "duration_ms": self.duration_ms,
        }


class ShellSession:
    """
    Shell 会话。

    属性:
        id: 会话 ID
        shell_type: Shell 类型
        cwd: 工作目录
        env: 环境变量
    """
    def __init__(
        self,
        id: str,
        shell_type: ShellType = ShellType.BASH,
        cwd: str = ".",
        env: Optional[Dict[str, str]] = None,
    ):
        self.id = id
        self.shell_type = shell_type
        self.cwd = cwd
        self.env = env or {}
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "shell_type": self.shell_type.value,
            "cwd": self.cwd,
            "env": self.env,
            "created_at": self.created_at,
        }


class ShellManager:
    """
    Shell 管理器。
    管理 Shell 会话和命令执行。

    功能:
    - 创建会话
    - 执行命令
    - 管理环境
    """

    def __init__(self):
        self.sessions: Dict[str, ShellSession] = {}
        self.history: List[Dict[str, Any]] = []

    def create_session(
        self,
        shell_type: ShellType = ShellType.BASH,
        cwd: str = ".",
    ) -> ShellSession:
        session_id = f"shell-{len(self.sessions) + 1}"
        session = ShellSession(id=session_id, shell_type=shell_type, cwd=cwd)
        self.sessions[session_id] = session
        return session

    def _validate_command(self, command: str) -> bool:
        """
        验证命令安全性。

        参数:
            command: 命令字符串

        返回:
            True 如果命令安全
        """
        # 检查危险的递归删除模式
        if 'rm' in command and '-rf' in command and '/' in command:
            return False

        # 检查危险的磁盘操作
        if 'dd if=' in command:
            return False

        # 检查 fork bomb
        if ':(){' in command:
            return False

        return True

    def execute(
        self,
        session_id: str,
        command: str,
    ) -> ShellResult:
        session = self.sessions.get(session_id)
        if not session:
            return ShellResult(success=False, stderr=f"Session not found: {session_id}")

        # 验证命令安全性
        if not self._validate_command(command):
            return ShellResult(success=False, stderr="Command validation failed: dangerous pattern detected")

        start_time = time.time()
        import subprocess
        try:
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True,
                cwd=session.cwd,
                timeout=30,
            )
            duration_ms = (time.time() - start_time) * 1000

            shell_result = ShellResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                duration_ms=duration_ms,
            )

            self.history.append({
                "session_id": session_id,
                "command": command,
                "success": shell_result.success,
                "duration_ms": duration_ms,
                "timestamp": time.time(),
            })

            return shell_result
        except Exception as e:
            return ShellResult(success=False, stderr=str(e))

    def get_stats(self) -> Dict[str, Any]:
        return {
            "sessions": len(self.sessions),
            "history": len(self.history),
        }


_global_manager = None

def get_global_shell_manager() -> ShellManager:
    global _global_manager
    if _global_manager is None:
        _global_manager = ShellManager()
    return _global_manager
