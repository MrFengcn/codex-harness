#!/usr/bin/env python3
"""
Codex Harness — 连接器系统

提供外部应用连接器能力。
对应 Codex 的 connectors 模块。

Python 兼容性: 3.6+
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
import time


# ============================================================================
# 连接器类型
# ============================================================================

class ConnectorStatus(Enum):
    """连接器状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONNECTING = "connecting"


class ConnectorType(Enum):
    """连接器类型"""
    API = "api"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    MESSAGE_QUEUE = "message_queue"
    CACHE = "cache"
    CUSTOM = "custom"


class AppInfo:
    """
    应用信息。

    属性:
        id: 应用 ID
        name: 应用名称
        description: 应用描述
        version: 应用版本
        connector_type: 连接器类型
        status: 连接状态
        metadata: 元数据
    """
    def __init__(
        self,
        id: str,
        name: str,
        description: str = "",
        version: str = "1.0.0",
        connector_type: ConnectorType = ConnectorType.API,
        status: ConnectorStatus = ConnectorStatus.INACTIVE,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.version = version
        self.connector_type = connector_type
        self.status = status
        self.metadata = metadata or {}
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "connector_type": self.connector_type.value,
            "status": self.status.value,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class ConnectorConfig:
    """
    连接器配置。

    属性:
        name: 连接器名称
        type: 连接器类型
        config: 配置参数
        enabled: 是否启用
    """
    def __init__(
        self,
        name: str,
        type: ConnectorType = ConnectorType.API,
        config: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
    ):
        self.name = name
        self.type = type
        self.config = config or {}
        self.enabled = enabled

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "type": self.type.value,
            "config": self.config,
            "enabled": self.enabled,
        }


# ============================================================================
# 连接器接口
# ============================================================================

class Connector(ABC):
    """
    连接器基类。
    对应 Codex 的连接器接口。

    所有连接器必须实现此接口。
    """

    @abstractmethod
    def connect(self) -> bool:
        """
        建立连接。

        返回:
            True 如果连接成功
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        断开连接。

        返回:
            True 如果断开成功
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        检查是否已连接。

        返回:
            True 如果已连接
        """
        pass

    @abstractmethod
    def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行操作。

        参数:
            operation: 操作名称
            params: 操作参数

        返回:
            操作结果
        """
        pass

    def get_info(self) -> AppInfo:
        """
        获取连接器信息。

        返回:
            AppInfo 应用信息
        """
        return AppInfo(
            id=self.__class__.__name__,
            name=self.__class__.__name__,
            connector_type=ConnectorType.CUSTOM,
        )

    def get_status(self) -> ConnectorStatus:
        """
        获取连接状态。

        返回:
            ConnectorStatus 连接状态
        """
        if self.is_connected():
            return ConnectorStatus.ACTIVE
        return ConnectorStatus.INACTIVE


# ============================================================================
# 连接器注册表
# ============================================================================

class ConnectorRegistry:
    """
    连接器注册表。
    管理所有连接器。

    功能:
    - 注册连接器
    - 发现连接器
    - 管理连接器生命周期
    """

    def __init__(self):
        """初始化连接器注册表"""
        self.connectors: Dict[str, Connector] = {}
        self.configs: Dict[str, ConnectorConfig] = {}

    def register(self, name: str, connector: Connector) -> bool:
        """
        注册连接器。

        参数:
            name: 连接器名称
            connector: 连接器实例

        返回:
            True 如果注册成功
        """
        self.connectors[name] = connector
        return True

    def unregister(self, name: str) -> bool:
        """
        注销连接器。

        参数:
            name: 连接器名称

        返回:
            True 如果注销成功
        """
        if name in self.connectors:
            # 断开连接
            connector = self.connectors[name]
            if connector.is_connected():
                connector.disconnect()
            del self.connectors[name]
            return True
        return False

    def get(self, name: str) -> Optional[Connector]:
        """
        获取连接器。

        参数:
            name: 连接器名称

        返回:
            Connector 连接器实例
        """
        return self.connectors.get(name)

    def list_all(self) -> List[str]:
        """
        列出所有连接器。

        返回:
            连接器名称列表
        """
        return list(self.connectors.keys())

    def list_connected(self) -> List[str]:
        """
        列出已连接的连接器。

        返回:
            已连接的连接器名称列表
        """
        return [
            name for name, conn in self.connectors.items()
            if conn.is_connected()
        ]

    def connect_all(self) -> Dict[str, bool]:
        """
        连接所有连接器。

        返回:
            连接结果字典
        """
        results = {}
        for name, connector in self.connectors.items():
            try:
                results[name] = connector.connect()
            except Exception:
                results[name] = False
        return results

    def disconnect_all(self) -> Dict[str, bool]:
        """
        断开所有连接器。

        返回:
            断开结果字典
        """
        results = {}
        for name, connector in self.connectors.items():
            try:
                results[name] = connector.disconnect()
            except Exception:
                results[name] = False
        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息。

        返回:
            统计字典
        """
        total = len(self.connectors)
        connected = len(self.list_connected())

        return {
            "total": total,
            "connected": connected,
            "disconnected": total - connected,
        }


# ============================================================================
# 连接器管理器
# ============================================================================

class ConnectorManager:
    """
    连接器管理器。
    统一管理连接器生命周期。

    功能:
    - 注册连接器
    - 连接管理
    - 操作执行
    """

    def __init__(self):
        """初始化连接器管理器"""
        self.registry = ConnectorRegistry()

    def register(self, name: str, connector: Connector) -> bool:
        """
        注册连接器。

        参数:
            name: 连接器名称
            connector: 连接器实例

        返回:
            True 如果注册成功
        """
        return self.registry.register(name, connector)

    def connect(self, name: str) -> bool:
        """
        连接指定连接器。

        参数:
            name: 连接器名称

        返回:
            True 如果连接成功
        """
        connector = self.registry.get(name)
        if not connector:
            return False
        return connector.connect()

    def disconnect(self, name: str) -> bool:
        """
        断开指定连接器。

        参数:
            name: 连接器名称

        返回:
            True 如果断开成功
        """
        connector = self.registry.get(name)
        if not connector:
            return False
        return connector.disconnect()

    def execute(
        self,
        name: str,
        operation: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        执行连接器操作。

        参数:
            name: 连接器名称
            operation: 操作名称
            params: 操作参数

        返回:
            操作结果
        """
        connector = self.registry.get(name)
        if not connector:
            return {"success": False, "error": f"Connector not found: {name}"}

        if not connector.is_connected():
            return {"success": False, "error": f"Connector not connected: {name}"}

        try:
            return connector.execute(operation, params)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_status(self, name: str) -> Optional[ConnectorStatus]:
        """
        获取连接器状态。

        参数:
            name: 连接器名称

        返回:
            ConnectorStatus 状态
        """
        connector = self.registry.get(name)
        if not connector:
            return None
        return connector.get_status()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息。

        返回:
            统计字典
        """
        return self.registry.get_stats()


# ============================================================================
# 全局连接器管理器
# ============================================================================

_global_manager: Optional[ConnectorManager] = None


def get_global_connector_manager() -> ConnectorManager:
    """
    获取全局连接器管理器。

    返回:
        全局连接器管理器实例
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = ConnectorManager()
    return _global_manager
