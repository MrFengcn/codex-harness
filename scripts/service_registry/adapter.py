#!/usr/bin/env python3
"""
Codex Harness — 服务适配器和切换器

根据网络环境自动切换服务。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any, Optional
from service_registry.types import (
    ServiceType, ServiceRegion, ServiceDefinition, ServiceRegistry, get_global_service_registry,
)
from network_detector import NetworkType, get_global_network_detector


# ============================================================================
# 服务适配器
# ============================================================================

class ServiceAdapter:
    """
    服务适配器。
    提供统一的服务访问接口。

    功能:
    - 自动选择最佳服务
    - 服务健康检查
    - 服务切换
    """

    def __init__(self):
        """初始化服务适配器"""
        self.registry = get_global_service_registry()
        self.detector = get_global_network_detector()
        self._current_services: Dict[ServiceType, ServiceDefinition] = {}

    def get_service(self, type: ServiceType) -> Optional[ServiceDefinition]:
        """
        获取最佳服务。

        参数:
            type: 服务类型

        返回:
            服务定义
        """
        # 检查缓存
        if type in self._current_services:
            return self._current_services[type]

        # 获取网络类型
        network_type = self.detector.detect()

        # 获取最佳服务
        service = self.registry.get_best(type, network_type)

        # 缓存结果
        if service:
            self._current_services[type] = service

        return service

    def get_llm_service(self) -> Optional[ServiceDefinition]:
        """获取 LLM 服务"""
        return self.get_service(ServiceType.LLM)

    def get_code_hosting_service(self) -> Optional[ServiceDefinition]:
        """获取代码托管服务"""
        return self.get_service(ServiceType.CODE_HOSTING)

    def get_model_repo_service(self) -> Optional[ServiceDefinition]:
        """获取模型仓库服务"""
        return self.get_service(ServiceType.MODEL_REPO)

    def get_package_manager_service(self) -> Optional[ServiceDefinition]:
        """获取包管理服务"""
        return self.get_service(ServiceType.PACKAGE_MANAGER)

    def get_search_service(self) -> Optional[ServiceDefinition]:
        """获取搜索服务"""
        return self.get_service(ServiceType.SEARCH)

    def switch_service(self, type: ServiceType, name: str) -> bool:
        """
        切换服务。

        参数:
            type: 服务类型
            name: 服务名称

        返回:
            True 如果切换成功
        """
        service = self.registry.get(name)
        if service and service.type == type:
            self._current_services[type] = service
            return True
        return False

    def clear_cache(self):
        """清除服务缓存"""
        self._current_services.clear()

    def get_status(self) -> Dict[str, Any]:
        """
        获取服务状态。

        返回:
            状态字典
        """
        network_type = self.detector.detect()

        return {
            "network": network_type.value,
            "current_services": {
                type.value: service.name
                for type, service in self._current_services.items()
            },
        }


# ============================================================================
# 服务切换器
# ============================================================================

class ServiceSwitcher:
    """
    服务切换器。
    根据网络环境自动切换服务。

    功能:
    - 自动切换
    - 手动切换
    - 切换历史
    """

    def __init__(self):
        """初始化服务切换器"""
        self.adapter = ServiceAdapter()
        self.history: List[Dict[str, Any]] = []

    def auto_switch(self) -> Dict[str, ServiceDefinition]:
        """
        自动切换服务。

        返回:
            切换后的服务字典
        """
        network_type = self.adapter.detector.detect()

        # 获取所有服务类型
        service_types = [
            ServiceType.LLM,
            ServiceType.CODE_HOSTING,
            ServiceType.MODEL_REPO,
            ServiceType.PACKAGE_MANAGER,
            ServiceType.SEARCH,
        ]

        result = {}
        for type in service_types:
            service = self.adapter.get_service(type)
            if service:
                result[type] = service

        # 记录切换
        self.history.append({
            "network": network_type.value,
            "services": {t.value: s.name for t, s in result.items()},
        })

        return result

    def manual_switch(self, type: ServiceType, name: str) -> bool:
        """
        手动切换服务。

        参数:
            type: 服务类型
            name: 服务名称

        返回:
            True 如果切换成功
        """
        return self.adapter.switch_service(type, name)

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取切换历史"""
        return self.history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_switches": len(self.history),
            "current_status": self.adapter.get_status(),
        }


# ============================================================================
# 全局服务切换器
# ============================================================================

_global_switcher: Optional[ServiceSwitcher] = None


def get_global_service_switcher() -> ServiceSwitcher:
    """获取全局服务切换器"""
    global _global_switcher
    if _global_switcher is None:
        _global_switcher = ServiceSwitcher()
    return _global_switcher
