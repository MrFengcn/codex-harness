#!/usr/bin/env python3
"""
Codex Harness — 网络检测系统

检测用户网络环境，判断是否在中国大陆网络。
支持 DNS 检测、HTTP 检测、IP 地理位置检测。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import socket
import time
from enum import Enum
from typing import List, Dict, Any, Optional


# ============================================================================
# 网络类型
# ============================================================================

class NetworkType(Enum):
    """网络类型"""
    CHINA = "china"           # 中国大陆网络
    INTERNATIONAL = "international"  # 国际网络
    UNKNOWN = "unknown"       # 未知网络


class NetworkStatus(Enum):
    """网络状态"""
    ONLINE = "online"
    OFFLINE = "offline"
    SLOW = "slow"
    UNKNOWN = "unknown"


# ============================================================================
# DNS 检测器
# ============================================================================

class DNSDetector:
    """
    DNS 检测器。
    通过 DNS 解析判断网络环境。

    原理:
    - 中国大陆 DNS 服务器会返回不同的 IP 地址
    - 通过比较不同 DNS 服务器的结果判断网络
    """

    # 中国大陆 DNS 服务器
    CHINA_DNS = [
        "114.114.114.114",  # 114 DNS
        "223.5.5.5",        # 阿里 DNS
        "119.29.29.29",     # 腾讯 DNS
    ]

    # 国际 DNS 服务器
    INTERNATIONAL_DNS = [
        "8.8.8.8",          # Google DNS
        "1.1.1.1",          # Cloudflare DNS
        "208.67.222.222",   # OpenDNS
    ]

    # 测试域名
    TEST_DOMAINS = [
        "www.baidu.com",
        "www.google.com",
        "github.com",
    ]

    def detect(self) -> NetworkType:
        """
        通过 DNS 检测网络类型。

        返回:
            NetworkType 网络类型
        """
        try:
            # 测试解析中国域名
            china_accessible = self._test_dns_resolution("www.baidu.com", self.CHINA_DNS)

            # 测试解析国际域名
            international_accessible = self._test_dns_resolution("www.google.com", self.INTERNATIONAL_DNS)

            if china_accessible and not international_accessible:
                return NetworkType.CHINA
            elif international_accessible and not china_accessible:
                return NetworkType.INTERNATIONAL
            elif china_accessible and international_accessible:
                return NetworkType.INTERNATIONAL  # 都能访问，认为是国际网络
            else:
                return NetworkType.UNKNOWN
        except Exception:
            return NetworkType.UNKNOWN

    def _test_dns_resolution(self, domain: str, dns_servers: List[str]) -> bool:
        """
        测试 DNS 解析。

        参数:
            domain: 域名
            dns_servers: DNS 服务器列表

        返回:
            True 如果解析成功
        """
        try:
            # 使用系统默认 DNS 解析
            socket.setdefaulttimeout(3)
            socket.getaddrinfo(domain, 80)
            return True
        except Exception:
            return False


# ============================================================================
# HTTP 检测器
# ============================================================================

class HTTPDetector:
    """
    HTTP 检测器。
    通过 HTTP 请求判断网络环境。

    原理:
    - 尝试访问特定网站
    - 根据响应判断网络类型
    """

    # 中国大陆网站
    CHINA_URLS = [
        "https://www.baidu.com",
        "https://www.taobao.com",
        "https://www.qq.com",
    ]

    # 国际网站
    INTERNATIONAL_URLS = [
        "https://www.google.com",
        "https://github.com",
        "https://www.youtube.com",
    ]

    def detect(self) -> NetworkType:
        """
        通过 HTTP 检测网络类型。

        返回:
            NetworkType 网络类型
        """
        try:
            import urllib.request

            # 测试访问中国网站
            china_accessible = self._test_url("https://www.baidu.com")

            # 测试访问国际网站
            international_accessible = self._test_url("https://www.google.com")

            if china_accessible and not international_accessible:
                return NetworkType.CHINA
            elif international_accessible and not china_accessible:
                return NetworkType.INTERNATIONAL
            elif china_accessible and international_accessible:
                return NetworkType.INTERNATIONAL
            else:
                return NetworkType.UNKNOWN
        except Exception:
            return NetworkType.UNKNOWN

    def _test_url(self, url: str, timeout: int = 5) -> bool:
        """
        测试 URL 可访问性。

        参数:
            url: URL 地址
            timeout: 超时时间

        返回:
            True 如果可访问
        """
        try:
            import urllib.request
            response = urllib.request.urlopen(url, timeout=timeout)
            return response.getcode() == 200
        except Exception:
            return False


# ============================================================================
# IP 地理位置检测器
# ============================================================================

class IPGeoDetector:
    """
    IP 地理位置检测器。
    通过 IP 地址判断地理位置。

    原理:
    - 使用免费 IP 地理位置 API
    - 根据返回的国家代码判断
    """

    # IP 地理位置 API
    GEO_APIS = [
        "https://ipapi.co/json/",
        "https://ip-api.com/json/",
        "https://ipinfo.io/json",
    ]

    # 中国大陆国家代码
    CHINA_CODES = {"CN", "HK", "MO", "TW"}

    def detect(self) -> NetworkType:
        """
        通过 IP 地理位置检测网络类型。

        返回:
            NetworkType 网络类型
        """
        try:
            import urllib.request
            import json

            for api in self.GEO_APIS:
                try:
                    response = urllib.request.urlopen(api, timeout=5)
                    data = json.loads(response.read().decode())
                    country_code = data.get("country_code", data.get("country", ""))

                    if country_code in self.CHINA_CODES:
                        return NetworkType.CHINA
                    elif country_code:
                        return NetworkType.INTERNATIONAL
                except Exception:
                    continue

            return NetworkType.UNKNOWN
        except Exception:
            return NetworkType.UNKNOWN


# ============================================================================
# 网络检测管理器
# ============================================================================

class NetworkDetector:
    """
    网络检测管理器。
    统一管理所有检测方法。

    功能:
    - 多种检测方法
    - 结果缓存
    - 自动检测
    """

    def __init__(self, use_cache: bool = True, cache_ttl: int = 300):
        """
        初始化网络检测管理器。

        参数:
            use_cache: 是否使用缓存
            cache_ttl: 缓存过期时间 (秒)
        """
        self.dns_detector = DNSDetector()
        self.http_detector = HTTPDetector()
        self.geo_detector = IPGeoDetector()

        self.use_cache = use_cache
        self.cache_ttl = cache_ttl

        self._cache: Optional[NetworkType] = None
        self._cache_time: float = 0

    def detect(self, force: bool = False) -> NetworkType:
        """
        检测网络类型。

        参数:
            force: 是否强制检测 (忽略缓存)

        返回:
            NetworkType 网络类型
        """
        # 检查缓存
        if not force and self.use_cache and self._cache is not None:
            if time.time() - self._cache_time < self.cache_ttl:
                return self._cache

        # 使用多种方法检测
        results = []

        # DNS 检测
        dns_result = self.dns_detector.detect()
        results.append(("dns", dns_result))

        # HTTP 检测
        http_result = self.http_detector.detect()
        results.append(("http", http_result))

        # IP 地理位置检测
        geo_result = self.geo_detector.detect()
        results.append(("geo", geo_result))

        # 投票决定最终结果
        final_result = self._vote(results)

        # 更新缓存
        if self.use_cache:
            self._cache = final_result
            self._cache_time = time.time()

        return final_result

    def _vote(self, results: List[tuple]) -> NetworkType:
        """
        投票决定最终结果。

        参数:
            results: 检测结果列表

        返回:
            NetworkType 网络类型
        """
        china_count = sum(1 for _, r in results if r == NetworkType.CHINA)
        international_count = sum(1 for _, r in results if r == NetworkType.INTERNATIONAL)

        if china_count > international_count:
            return NetworkType.CHINA
        elif international_count > china_count:
            return NetworkType.INTERNATIONAL
        else:
            return NetworkType.UNKNOWN

    def is_china_network(self) -> bool:
        """
        检查是否是中国大陆网络。

        返回:
            True 如果是中国大陆网络
        """
        return self.detect() == NetworkType.CHINA

    def is_international_network(self) -> bool:
        """
        检查是否是国际网络。

        返回:
            True 如果是国际网络
        """
        return self.detect() == NetworkType.INTERNATIONAL

    def get_network_info(self) -> Dict[str, Any]:
        """
        获取网络信息。

        返回:
            网络信息字典
        """
        network_type = self.detect()

        return {
            "type": network_type.value,
            "is_china": network_type == NetworkType.CHINA,
            "is_international": network_type == NetworkType.INTERNATIONAL,
            "cached": self._cache is not None,
        }

    def clear_cache(self):
        """清除缓存"""
        self._cache = None
        self._cache_time = 0


# ============================================================================
# 全局检测器
# ============================================================================

_global_detector: Optional[NetworkDetector] = None


def get_global_network_detector() -> NetworkDetector:
    """
    获取全局网络检测器。

    返回:
        全局网络检测器实例
    """
    global _global_detector
    if _global_detector is None:
        _global_detector = NetworkDetector()
    return _global_detector


def is_china_network() -> bool:
    """
    检查是否是中国大陆网络。

    返回:
        True 如果是中国大陆网络
    """
    detector = get_global_network_detector()
    return detector.is_china_network()


def is_international_network() -> bool:
    """
    检查是否是国际网络。

    返回:
        True 如果是国际网络
    """
    detector = get_global_network_detector()
    return detector.is_international_network()


# ============================================================================
# 网络监控器
# ============================================================================

class NetworkMonitor:
    """
    网络监控器。
    监控网络状态变化。

    功能:
    - 定期检测网络状态
    - 记录网络变化事件
    - 提供网络状态回调
    """

    def __init__(self, detector: NetworkDetector, check_interval: int = 60):
        """
        初始化网络监控器。

        参数:
            detector: 网络检测器
            check_interval: 检查间隔 (秒)
        """
        self.detector = detector
        self.check_interval = check_interval
        self.current_type: Optional[NetworkType] = None
        self.history: List[Dict[str, Any]] = []
        self.callbacks: List = []

    def check(self) -> NetworkType:
        """
        检查网络状态。

        返回:
            NetworkType 网络类型
        """
        new_type = self.detector.detect(force=True)

        # 检查是否变化
        if self.current_type is not None and new_type != self.current_type:
            self._on_change(self.current_type, new_type)

        self.current_type = new_type
        return new_type

    def _on_change(self, old_type: NetworkType, new_type: NetworkType):
        """
        网络类型变化回调。

        参数:
            old_type: 旧网络类型
            new_type: 新网络类型
        """
        event = {
            "old_type": old_type.value,
            "new_type": new_type.value,
            "timestamp": time.time(),
        }
        self.history.append(event)

        # 调用回调
        for callback in self.callbacks:
            try:
                callback(event)
            except Exception:
                pass

    def add_callback(self, callback):
        """
        添加回调函数。

        参数:
            callback: 回调函数
        """
        self.callbacks.append(callback)

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取历史记录。

        参数:
            limit: 返回数量

        返回:
            历史记录列表
        """
        return self.history[-limit:]


# ============================================================================
# 网络配置
# ============================================================================

class NetworkConfig:
    """
    网络配置。
    管理网络检测配置。

    属性:
        use_cache: 是否使用缓存
        cache_ttl: 缓存过期时间
        check_interval: 检查间隔
        force_china: 强制使用中国网络
        force_international: 强制使用国际网络
    """

    def __init__(
        self,
        use_cache: bool = True,
        cache_ttl: int = 300,
        check_interval: int = 60,
        force_china: bool = False,
        force_international: bool = False,
    ):
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self.check_interval = check_interval
        self.force_china = force_china
        self.force_international = force_international

    def get_network_type(self) -> NetworkType:
        """
        获取网络类型 (考虑强制设置)。

        返回:
            NetworkType 网络类型
        """
        if self.force_china:
            return NetworkType.CHINA
        elif self.force_international:
            return NetworkType.INTERNATIONAL
        else:
            return NetworkType.UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "use_cache": self.use_cache,
            "cache_ttl": self.cache_ttl,
            "check_interval": self.check_interval,
            "force_china": self.force_china,
            "force_international": self.force_international,
        }
