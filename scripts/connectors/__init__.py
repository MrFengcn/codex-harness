#!/usr/bin/env python3
"""
Codex Harness — 连接器系统

提供外部应用连接器能力。
对应 Codex 的 connectors 模块。

Python 兼容性: 3.6+
"""

from connectors.types import (
    ConnectorStatus,
    ConnectorType,
    AppInfo,
    ConnectorConfig,
    Connector,
    ConnectorRegistry,
    ConnectorManager,
    get_global_connector_manager,
)
from connectors.discovery import (
    AppBranding,
    AppMetadata,
    ConnectorDiscovery,
    ConnectorRegistryManager,
    SimpleConnector,
)

__all__ = [
    'ConnectorStatus',
    'ConnectorType',
    'AppInfo',
    'ConnectorConfig',
    'Connector',
    'ConnectorRegistry',
    'ConnectorManager',
    'get_global_connector_manager',
    'AppBranding',
    'AppMetadata',
    'ConnectorDiscovery',
    'ConnectorRegistryManager',
    'SimpleConnector',
]
