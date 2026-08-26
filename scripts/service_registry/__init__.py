#!/usr/bin/env python3
"""
Codex Harness — 服务替换系统

根据网络环境自动切换服务。
"""

from service_registry.types import (
    ServiceType,
    ServiceRegion,
    ServiceDefinition,
    ServiceRegistry,
    get_global_service_registry,
)
from service_registry.adapter import (
    ServiceAdapter,
    ServiceSwitcher,
    get_global_service_switcher,
)

__all__ = [
    'ServiceType',
    'ServiceRegion',
    'ServiceDefinition',
    'ServiceRegistry',
    'get_global_service_registry',
    'ServiceAdapter',
    'ServiceSwitcher',
    'get_global_service_switcher',
]
