#!/usr/bin/env python3
"""
Codex Harness — 服务替换系统

根据网络环境自动切换服务。
支持 LLM、代码托管、模型仓库、包管理、搜索等服务。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional
from network_detector import NetworkType, get_global_network_detector


# ============================================================================
# 服务类型
# ============================================================================

class ServiceType(Enum):
    """服务类型"""
    LLM = "llm"                    # 大语言模型
    CODE_HOSTING = "code_hosting"  # 代码托管
    MODEL_REPO = "model_repo"     # 模型仓库
    PACKAGE_MANAGER = "package_manager"  # 包管理
    SEARCH = "search"              # 搜索引擎


class ServiceRegion(Enum):
    """服务区域"""
    CHINA = "china"
    INTERNATIONAL = "international"
    GLOBAL = "global"


# ============================================================================
# 服务定义
# ============================================================================

class ServiceDefinition:
    """
    服务定义。

    属性:
        name: 服务名称
        type: 服务类型
        region: 服务区域
        base_url: 基础 URL
        api_key_env: API 密钥环境变量
        description: 描述
        enabled: 是否启用
    """
    def __init__(
        self,
        name: str,
        type: ServiceType,
        region: ServiceRegion,
        base_url: str = "",
        api_key_env: str = "",
        description: str = "",
        enabled: bool = True,
    ):
        self.name = name
        self.type = type
        self.region = region
        self.base_url = base_url
        self.api_key_env = api_key_env
        self.description = description
        self.enabled = enabled

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "region": self.region.value,
            "base_url": self.base_url,
            "api_key_env": self.api_key_env,
            "description": self.description,
            "enabled": self.enabled,
        }


# ============================================================================
# 服务注册表
# ============================================================================

class ServiceRegistry:
    """
    服务注册表。
    管理所有服务定义。

    功能:
    - 注册服务
    - 按类型查询服务
    - 按区域查询服务
    - 自动选择最佳服务
    """

    def __init__(self):
        self.services: Dict[str, ServiceDefinition] = {}
        self._register_defaults()

    def _register_defaults(self):
        """注册默认服务"""
        # LLM 服务
        self.register(ServiceDefinition(
            name="openai",
            type=ServiceType.LLM,
            region=ServiceRegion.INTERNATIONAL,
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            description="OpenAI GPT",
        ))
        self.register(ServiceDefinition(
            name="deepseek",
            type=ServiceType.LLM,
            region=ServiceRegion.CHINA,
            base_url="https://api.deepseek.com/v1",
            api_key_env="DEEPSEEK_API_KEY",
            description="DeepSeek",
        ))
        self.register(ServiceDefinition(
            name="qwen",
            type=ServiceType.LLM,
            region=ServiceRegion.CHINA,
            base_url="https://dashscope.aliyuncs.com/api/v1",
            api_key_env="DASHSCOPE_API_KEY",
            description="通义千问",
        ))
        self.register(ServiceDefinition(
            name="ernie",
            type=ServiceType.LLM,
            region=ServiceRegion.CHINA,
            base_url="https://aip.baidubce.com/rpc/2.0/ai_custom/v1",
            api_key_env="ERNIE_API_KEY",
            description="文心一言",
        ))

        # 代码托管服务
        self.register(ServiceDefinition(
            name="github",
            type=ServiceType.CODE_HOSTING,
            region=ServiceRegion.INTERNATIONAL,
            base_url="https://api.github.com",
            api_key_env="GITHUB_TOKEN",
            description="GitHub",
        ))
        self.register(ServiceDefinition(
            name="gitee",
            type=ServiceType.CODE_HOSTING,
            region=ServiceRegion.CHINA,
            base_url="https://gitee.com/api/v5",
            api_key_env="GITEE_TOKEN",
            description="Gitee",
        ))

        # 模型仓库服务
        self.register(ServiceDefinition(
            name="huggingface",
            type=ServiceType.MODEL_REPO,
            region=ServiceRegion.INTERNATIONAL,
            base_url="https://huggingface.co/api",
            api_key_env="HF_TOKEN",
            description="HuggingFace",
        ))
        self.register(ServiceDefinition(
            name="modelscope",
            type=ServiceType.MODEL_REPO,
            region=ServiceRegion.CHINA,
            base_url="https://modelscope.cn/api/v1",
            api_key_env="MODELSCOPE_TOKEN",
            description="魔搭社区",
        ))

        # 包管理服务
        self.register(ServiceDefinition(
            name="pypi",
            type=ServiceType.PACKAGE_MANAGER,
            region=ServiceRegion.INTERNATIONAL,
            base_url="https://pypi.org/simple",
            description="PyPI",
        ))
        self.register(ServiceDefinition(
            name="tsinghua",
            type=ServiceType.PACKAGE_MANAGER,
            region=ServiceRegion.CHINA,
            base_url="https://pypi.tuna.tsinghua.edu.cn/simple",
            description="清华镜像",
        ))
        self.register(ServiceDefinition(
            name="aliyun",
            type=ServiceType.PACKAGE_MANAGER,
            region=ServiceRegion.CHINA,
            base_url="https://mirrors.aliyun.com/pypi/simple",
            description="阿里镜像",
        ))

        # 搜索服务
        self.register(ServiceDefinition(
            name="google",
            type=ServiceType.SEARCH,
            region=ServiceRegion.INTERNATIONAL,
            base_url="https://www.google.com/search",
            description="Google",
        ))
        self.register(ServiceDefinition(
            name="baidu",
            type=ServiceType.SEARCH,
            region=ServiceRegion.CHINA,
            base_url="https://www.baidu.com/s",
            description="百度",
        ))
        self.register(ServiceDefinition(
            name="bing",
            type=ServiceType.SEARCH,
            region=ServiceRegion.GLOBAL,
            base_url="https://www.bing.com/search",
            description="Bing",
        ))

    def register(self, service: ServiceDefinition):
        """注册服务"""
        self.services[service.name] = service

    def get(self, name: str) -> Optional[ServiceDefinition]:
        """获取服务"""
        return self.services.get(name)

    def get_by_type(self, type: ServiceType) -> List[ServiceDefinition]:
        """按类型获取服务"""
        return [s for s in self.services.values() if s.type == type and s.enabled]

    def get_by_region(self, region: ServiceRegion) -> List[ServiceDefinition]:
        """按区域获取服务"""
        return [s for s in self.services.values() if s.region == region and s.enabled]

    def get_best(self, type: ServiceType, network_type: NetworkType) -> Optional[ServiceDefinition]:
        """
        获取最佳服务。

        参数:
            type: 服务类型
            network_type: 网络类型

        返回:
            最佳服务定义
        """
        services = self.get_by_type(type)

        if not services:
            return None

        # 根据网络类型选择服务
        if network_type == NetworkType.CHINA:
            # 优先选择中国服务
            china_services = [s for s in services if s.region == ServiceRegion.CHINA]
            if china_services:
                return china_services[0]

        # 选择全球或国际服务
        global_services = [s for s in services if s.region == ServiceRegion.GLOBAL]
        if global_services:
            return global_services[0]

        international_services = [s for s in services if s.region == ServiceRegion.INTERNATIONAL]
        if international_services:
            return international_services[0]

        return services[0]

    def list_services(self) -> List[str]:
        """列出所有服务"""
        return list(self.services.keys())

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total": len(self.services),
            "by_type": {t.value: len(self.get_by_type(t)) for t in ServiceType},
            "by_region": {r.value: len(self.get_by_region(r)) for r in ServiceRegion},
        }


# ============================================================================
# 全局服务注册表
# ============================================================================

_global_registry: Optional[ServiceRegistry] = None


def get_global_service_registry() -> ServiceRegistry:
    """获取全局服务注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ServiceRegistry()
    return _global_registry
