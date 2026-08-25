#!/usr/bin/env python3
"""
Codex Harness — MCP 协议系统

实现 Model Context Protocol (MCP)。
对应 Codex 的 mcp 模块。

Python 兼容性: 3.6+
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional
import time
import json


# ============================================================================
# MCP 类型
# ============================================================================

class McpMessageType(Enum):
    """MCP 消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class McpToolType(Enum):
    """MCP 工具类型"""
    FUNCTION = "function"
    RESOURCE = "resource"
    PROMPT = "prompt"


class McpStatus(Enum):
    """MCP 连接状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


# ============================================================================
# MCP 消息
# ============================================================================

class McpMessage:
    """
    MCP 消息。

    属性:
        id: 消息 ID
        type: 消息类型
        method: 方法名
        params: 参数
        result: 结果
        error: 错误
    """
    def __init__(
        self,
        type: McpMessageType = McpMessageType.REQUEST,
        method: str = "",
        params: Optional[Dict[str, Any]] = None,
        result: Any = None,
        error: Optional[str] = None,
    ):
        self.id = str(int(time.time() * 1000))
        self.type = type
        self.method = method
        self.params = params or {}
        self.result = result
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        msg = {"jsonrpc": "2.0", "id": self.id}

        if self.type == McpMessageType.REQUEST:
            msg["method"] = self.method
            msg["params"] = self.params
        elif self.type == McpMessageType.RESPONSE:
            msg["result"] = self.result
        elif self.type == McpMessageType.ERROR:
            msg["error"] = {"code": -1, "message": self.error}

        return msg

    def to_json(self) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'McpMessage':
        """从字典创建"""
        if "method" in data:
            return cls(
                type=McpMessageType.REQUEST,
                method=data["method"],
                params=data.get("params", {}),
            )
        elif "result" in data:
            return cls(
                type=McpMessageType.RESPONSE,
                result=data["result"],
            )
        elif "error" in data:
            return cls(
                type=McpMessageType.ERROR,
                error=data["error"].get("message", ""),
            )
        return cls()


# ============================================================================
# MCP 工具
# ============================================================================

class McpTool:
    """
    MCP 工具。

    属性:
        name: 工具名称
        description: 工具描述
        type: 工具类型
        input_schema: 输入模式
    """
    def __init__(
        self,
        name: str,
        description: str = "",
        type: McpToolType = McpToolType.FUNCTION,
        input_schema: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.description = description
        self.type = type
        self.input_schema = input_schema or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


class McpResource:
    """
    MCP 资源。

    属性:
        uri: 资源 URI
        name: 资源名称
        description: 资源描述
        mime_type: MIME 类型
    """
    def __init__(
        self,
        uri: str,
        name: str = "",
        description: str = "",
        mime_type: str = "text/plain",
    ):
        self.uri = uri
        self.name = name
        self.description = description
        self.mime_type = mime_type

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type,
        }


# ============================================================================
# MCP 服务器
# ============================================================================

class McpServer(ABC):
    """
    MCP 服务器基类。
    对应 Codex 的 MCP 服务器接口。

    所有 MCP 服务器必须实现此接口。
    """

    @abstractmethod
    def get_name(self) -> str:
        """
        获取服务器名称。

        返回:
            服务器名称
        """
        pass

    @abstractmethod
    def get_tools(self) -> List[McpTool]:
        """
        获取工具列表。

        返回:
            工具列表
        """
        pass

    @abstractmethod
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        调用工具。

        参数:
            name: 工具名称
            arguments: 工具参数

        返回:
            工具结果
        """
        pass

    def get_resources(self) -> List[McpResource]:
        """
        获取资源列表。

        返回:
            资源列表
        """
        return []

    def read_resource(self, uri: str) -> str:
        """
        读取资源。

        参数:
            uri: 资源 URI

        返回:
            资源内容
        """
        return ""


# ============================================================================
# MCP 客户端
# ============================================================================

class McpClient:
    """
    MCP 客户端。
    管理 MCP 服务器连接。

    功能:
    - 连接服务器
    - 调用工具
    - 读取资源
    """

    def __init__(self):
        """初始化 MCP 客户端"""
        self.servers: Dict[str, McpServer] = {}
        self.status: McpStatus = McpStatus.DISCONNECTED

    def connect(self, server: McpServer) -> bool:
        """
        连接服务器。

        参数:
            server: MCP 服务器

        返回:
            True 如果连接成功
        """
        name = server.get_name()
        self.servers[name] = server
        self.status = McpStatus.CONNECTED
        return True

    def disconnect(self, name: str) -> bool:
        """
        断开服务器。

        参数:
            name: 服务器名称

        返回:
            True 如果断开成功
        """
        if name in self.servers:
            del self.servers[name]
            if not self.servers:
                self.status = McpStatus.DISCONNECTED
            return True
        return False

    def list_tools(self) -> List[McpTool]:
        """
        列出所有工具。

        返回:
            工具列表
        """
        tools = []
        for server in self.servers.values():
            tools.extend(server.get_tools())
        return tools

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        调用工具。

        参数:
            name: 工具名称
            arguments: 工具参数

        返回:
            工具结果
        """
        for server in self.servers.values():
            tools = server.get_tools()
            for tool in tools:
                if tool.name == name:
                    return server.call_tool(name, arguments)

        return {"error": f"Tool not found: {name}"}

    def list_resources(self) -> List[McpResource]:
        """
        列出所有资源。

        返回:
            资源列表
        """
        resources = []
        for server in self.servers.values():
            resources.extend(server.get_resources())
        return resources

    def read_resource(self, uri: str) -> str:
        """
        读取资源。

        参数:
            uri: 资源 URI

        返回:
            资源内容
        """
        for server in self.servers.values():
            resources = server.get_resources()
            for resource in resources:
                if resource.uri == uri:
                    return server.read_resource(uri)

        return ""

    def get_servers(self) -> List[str]:
        """
        获取服务器列表。

        返回:
            服务器名称列表
        """
        return list(self.servers.keys())

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息。

        返回:
            统计字典
        """
        return {
            "status": self.status.value,
            "servers": len(self.servers),
            "tools": len(self.list_tools()),
            "resources": len(self.list_resources()),
        }


# ============================================================================
# 全局 MCP 客户端
# ============================================================================

_global_client: Optional[McpClient] = None


def get_global_mcp_client() -> McpClient:
    """
    获取全局 MCP 客户端。

    返回:
        全局 MCP 客户端实例
    """
    global _global_client
    if _global_client is None:
        _global_client = McpClient()
    return _global_client
