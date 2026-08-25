#!/usr/bin/env python3
"""
Codex Harness — 连接器发现和应用品牌

实现代理发现和应用品牌管理。
对应 Codex 的 connectors 发现逻辑。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from typing import List, Dict, Any, Optional
from connectors.types import (
    ConnectorStatus, ConnectorType, AppInfo, ConnectorConfig,
    Connector, ConnectorRegistry, ConnectorManager,
)


# ============================================================================
# 应用品牌
# ============================================================================

class AppBranding:
    """
    应用品牌。
    定义应用的视觉和交互品牌。

    属性:
        name: 应用名称
        icon: 应用图标
        color: 主题颜色
        description: 应用描述
        url: 应用 URL
    """
    def __init__(
        self,
        name: str,
        icon: str = "",
        color: str = "#000000",
        description: str = "",
        url: str = "",
    ):
        self.name = name
        self.icon = icon
        self.color = color
        self.description = description
        self.url = url

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "icon": self.icon,
            "color": self.color,
            "description": self.description,
            "url": self.url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppBranding':
        """从字典创建"""
        return cls(
            name=data.get("name", ""),
            icon=data.get("icon", ""),
            color=data.get("color", "#000000"),
            description=data.get("description", ""),
            url=data.get("url", ""),
        )


class AppMetadata:
    """
    应用元数据。

    属性:
        app_info: 应用信息
        branding: 应用品牌
        capabilities: 能力列表
        config: 配置
    """
    def __init__(
        self,
        app_info: AppInfo,
        branding: Optional[AppBranding] = None,
        capabilities: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.app_info = app_info
        self.branding = branding or AppBranding(name=app_info.name)
        self.capabilities = capabilities or []
        self.config = config or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "app_info": self.app_info.to_dict(),
            "branding": self.branding.to_dict(),
            "capabilities": self.capabilities,
            "config": self.config,
        }


# ============================================================================
# 连接器发现
# ============================================================================

class ConnectorDiscovery:
    """
    连接器发现。
    自动发现和注册连接器。

    功能:
    - 扫描目录
    - 加载配置
    - 自动注册
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化连接器发现。

        参数:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.discovered: Dict[str, AppMetadata] = {}

    def discover(self, search_paths: Optional[List[str]] = None) -> List[AppMetadata]:
        """
        发现连接器。

        参数:
            search_paths: 搜索路径列表

        返回:
            发现的连接器列表
        """
        if search_paths is None:
            search_paths = ['.']

        discovered = []

        for path in search_paths:
            # 扫描配置文件
            configs = self._scan_config_files(path)
            for config_file in configs:
                metadata = self._load_config(config_file)
                if metadata:
                    discovered.append(metadata)
                    self.discovered[metadata.app_info.id] = metadata

        return discovered

    def _scan_config_files(self, path: str) -> List[str]:
        """
        扫描配置文件。

        参数:
            path: 扫描路径

        返回:
            配置文件路径列表
        """
        config_files = []
        config_names = [
            'connector.json',
            'connector.yaml',
            'connector.yml',
            '.connector.json',
        ]

        for root, dirs, files in os.walk(path):
            for name in config_names:
                if name in files:
                    config_files.append(os.path.join(root, name))

        return config_files

    def _load_config(self, filepath: str) -> Optional[AppMetadata]:
        """
        加载配置文件。

        参数:
            filepath: 配置文件路径

        返回:
            AppMetadata 应用元数据
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                if filepath.endswith('.json'):
                    data = json.load(f)
                else:
                    # 简单的 YAML 解析
                    data = self._parse_simple_yaml(f.read())

            return self._create_metadata(data)
        except Exception:
            return None

    def _parse_simple_yaml(self, content: str) -> Dict[str, Any]:
        """
        简单的 YAML 解析。

        参数:
            content: YAML 内容

        返回:
            解析后的字典
        """
        result = {}
        for line in content.split('\n'):
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip()
        return result

    def _create_metadata(self, data: Dict[str, Any]) -> Optional[AppMetadata]:
        """
        创建应用元数据。

        参数:
            data: 配置数据

        返回:
            AppMetadata 应用元数据
        """
        try:
            app_info = AppInfo(
                id=data.get('id', ''),
                name=data.get('name', ''),
                description=data.get('description', ''),
                version=data.get('version', '1.0.0'),
            )

            branding = AppBranding(
                name=data.get('name', ''),
                icon=data.get('icon', ''),
                color=data.get('color', '#000000'),
                description=data.get('description', ''),
                url=data.get('url', ''),
            )

            return AppMetadata(
                app_info=app_info,
                branding=branding,
                capabilities=data.get('capabilities', []),
                config=data.get('config', {}),
            )
        except Exception:
            return None

    def get_discovered(self) -> List[AppMetadata]:
        """
        获取已发现的连接器。

        返回:
            已发现的连接器列表
        """
        return list(self.discovered.values())

    def get_by_id(self, id: str) -> Optional[AppMetadata]:
        """
        按 ID 获取连接器。

        参数:
            id: 连接器 ID

        返回:
            AppMetadata 应用元数据
        """
        return self.discovered.get(id)


# ============================================================================
# 连接器注册表管理器
# ============================================================================

class ConnectorRegistryManager:
    """
    连接器注册表管理器。
    统一管理连接器发现和注册。

    功能:
    - 发现连接器
    - 注册连接器
    - 管理连接器生命周期
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化注册表管理器。

        参数:
            config_path: 配置文件路径
        """
        self.discovery = ConnectorDiscovery(config_path)
        self.manager = ConnectorManager()

    def discover_and_register(
        self,
        search_paths: Optional[List[str]] = None,
    ) -> int:
        """
        发现并注册连接器。

        参数:
            search_paths: 搜索路径列表

        返回:
            注册的连接器数量
        """
        discovered = self.discovery.discover(search_paths)
        registered = 0

        for metadata in discovered:
            # 创建简单的连接器
            connector = SimpleConnector(metadata)
            if self.manager.register(metadata.app_info.id, connector):
                registered += 1

        return registered

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息。

        返回:
            统计字典
        """
        return {
            "discovered": len(self.discovery.get_discovered()),
            "registered": self.manager.get_stats(),
        }


# ============================================================================
# 简单连接器
# ============================================================================

class SimpleConnector(Connector):
    """
    简单连接器。
    基于配置的简单连接器实现。
    """

    def __init__(self, metadata: AppMetadata):
        """
        初始化简单连接器。

        参数:
            metadata: 应用元数据
        """
        self.metadata = metadata
        self.connected = False

    def connect(self) -> bool:
        """建立连接"""
        self.connected = True
        return True

    def disconnect(self) -> bool:
        """断开连接"""
        self.connected = False
        return True

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.connected

    def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行操作"""
        return {
            "success": True,
            "operation": operation,
            "connector": self.metadata.app_info.id,
        }

    def get_info(self) -> AppInfo:
        """获取连接器信息"""
        return self.metadata.app_info
