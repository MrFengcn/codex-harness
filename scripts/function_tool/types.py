#!/usr/bin/env python3
"""
Codex Harness — 函数工具系统

定义和管理函数工具。
对应 Codex 的 function_tool 模块。

Python 兼容性: 3.6+
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
import time


# ============================================================================
# 工具类型
# ============================================================================

class ToolType(Enum):
    """工具类型"""
    FUNCTION = "function"
    SCRIPT = "script"
    API = "api"
    CUSTOM = "custom"


class ParameterType(Enum):
    """参数类型"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


# ============================================================================
# 工具定义
# ============================================================================

class ToolParameter:
    """
    工具参数定义。

    属性:
        name: 参数名称
        type: 参数类型
        description: 参数描述
        required: 是否必需
        default: 默认值
    """
    def __init__(
        self,
        name: str,
        type: ParameterType = ParameterType.STRING,
        description: str = "",
        required: bool = True,
        default: Any = None,
    ):
        self.name = name
        self.type = type
        self.description = description
        self.required = required
        self.default = default

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "required": self.required,
            "default": self.default,
        }

    def validate(self, value: Any) -> bool:
        """
        验证参数值。

        参数:
            value: 参数值

        返回:
            True 如果有效
        """
        if value is None:
            return not self.required

        if self.type == ParameterType.STRING:
            return isinstance(value, str)
        elif self.type == ParameterType.INTEGER:
            return isinstance(value, int)
        elif self.type == ParameterType.FLOAT:
            return isinstance(value, (int, float))
        elif self.type == ParameterType.BOOLEAN:
            return isinstance(value, bool)
        elif self.type == ParameterType.ARRAY:
            return isinstance(value, list)
        elif self.type == ParameterType.OBJECT:
            return isinstance(value, dict)

        return True


class ToolDefinition:
    """
    工具定义。

    属性:
        name: 工具名称
        description: 工具描述
        type: 工具类型
        parameters: 参数列表
        handler: 处理函数
    """
    def __init__(
        self,
        name: str,
        description: str = "",
        type: ToolType = ToolType.FUNCTION,
        parameters: Optional[List[ToolParameter]] = None,
        handler: Optional[Callable] = None,
    ):
        self.name = name
        self.description = description
        self.type = type
        self.parameters = parameters or []
        self.handler = handler

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "parameters": [p.to_dict() for p in self.parameters],
        }

    def validate_args(self, args: Dict[str, Any]) -> List[str]:
        """
        验证参数。

        参数:
            args: 参数字典

        返回:
            错误列表
        """
        errors = []

        for param in self.parameters:
            if param.required and param.name not in args:
                errors.append(f"Missing required parameter: {param.name}")
            elif param.name in args:
                if not param.validate(args[param.name]):
                    errors.append(f"Invalid type for parameter {param.name}")

        return errors


class ToolResult:
    """
    工具执行结果。

    属性:
        success: 是否成功
        output: 输出内容
        error: 错误信息
        duration_ms: 执行耗时
    """
    def __init__(
        self,
        success: bool,
        output: Any = None,
        error: Optional[str] = None,
        duration_ms: float = 0.0,
    ):
        self.success = success
        self.output = output
        self.error = error
        self.duration_ms = duration_ms

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


# ============================================================================
# 函数工具
# ============================================================================

class FunctionTool(ABC):
    """
    函数工具基类。
    对应 Codex 的 function_tool 接口。

    所有函数工具必须实现此接口。
    """

    @abstractmethod
    def get_definition(self) -> ToolDefinition:
        """
        获取工具定义。

        返回:
            ToolDefinition 工具定义
        """
        pass

    @abstractmethod
    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        执行工具。

        参数:
            args: 参数字典

        返回:
            ToolResult 执行结果
        """
        pass

    def validate(self, args: Dict[str, Any]) -> List[str]:
        """
        验证参数。

        参数:
            args: 参数字典

        返回:
            错误列表
        """
        definition = self.get_definition()
        return definition.validate_args(args)


# ============================================================================
# 工具注册表
# ============================================================================

class ToolRegistry:
    """
    工具注册表。
    管理所有函数工具。

    功能:
    - 注册工具
    - 发现工具
    - 执行工具
    """

    def __init__(self):
        """初始化工具注册表"""
        self.tools: Dict[str, FunctionTool] = {}

    def register(self, tool: FunctionTool) -> bool:
        """
        注册工具。

        参数:
            tool: 函数工具

        返回:
            True 如果注册成功
        """
        definition = tool.get_definition()
        self.tools[definition.name] = tool
        return True

    def unregister(self, name: str) -> bool:
        """
        注销工具。

        参数:
            name: 工具名称

        返回:
            True 如果注销成功
        """
        if name in self.tools:
            del self.tools[name]
            return True
        return False

    def get(self, name: str) -> Optional[FunctionTool]:
        """
        获取工具。

        参数:
            name: 工具名称

        返回:
            FunctionTool 工具实例
        """
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """
        列出所有工具。

        返回:
            工具名称列表
        """
        return list(self.tools.keys())

    def get_definitions(self) -> List[ToolDefinition]:
        """
        获取所有工具定义。

        返回:
            工具定义列表
        """
        return [tool.get_definition() for tool in self.tools.values()]

    def execute(self, name: str, args: Dict[str, Any]) -> ToolResult:
        """
        执行工具。

        参数:
            name: 工具名称
            args: 参数字典

        返回:
            ToolResult 执行结果
        """
        tool = self.tools.get(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool not found: {name}",
            )

        # 验证参数
        errors = tool.validate(args)
        if errors:
            return ToolResult(
                success=False,
                error=f"Validation errors: {', '.join(errors)}",
            )

        # 执行工具
        start_time = time.time()
        try:
            result = tool.execute(args)
            result.duration_ms = (time.time() - start_time) * 1000
            return result
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息。

        返回:
            统计字典
        """
        return {
            "total": len(self.tools),
            "tools": list(self.tools.keys()),
        }


# ============================================================================
# 工具管理器
# ============================================================================

class ToolManager:
    """
    工具管理器。
    统一管理工具注册和执行。

    功能:
    - 注册工具
    - 执行工具
    - 工具发现
    """

    def __init__(self):
        """初始化工具管理器"""
        self.registry = ToolRegistry()

    def register(self, tool: FunctionTool) -> bool:
        """
        注册工具。

        参数:
            tool: 函数工具

        返回:
            True 如果注册成功
        """
        return self.registry.register(tool)

    def execute(self, name: str, args: Dict[str, Any]) -> ToolResult:
        """
        执行工具。

        参数:
            name: 工具名称
            args: 参数字典

        返回:
            ToolResult 执行结果
        """
        return self.registry.execute(name, args)

    def list_tools(self) -> List[str]:
        """
        列出所有工具。

        返回:
            工具名称列表
        """
        return self.registry.list_tools()

    def get_definitions(self) -> List[ToolDefinition]:
        """
        获取所有工具定义。

        返回:
            工具定义列表
        """
        return self.registry.get_definitions()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息。

        返回:
            统计字典
        """
        return self.registry.get_stats()


# ============================================================================
# 全局工具管理器
# ============================================================================

_global_manager: Optional[ToolManager] = None


def get_global_tool_manager() -> ToolManager:
    """
    获取全局工具管理器。

    返回:
        全局工具管理器实例
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = ToolManager()
    return _global_manager
