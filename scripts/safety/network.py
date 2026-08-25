#!/usr/bin/env python3
"""
Codex Harness — 网络安全检查器

检查网络操作安全性。
对应 Codex 的网络安全检查逻辑。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from typing import List, Dict, Optional
from safety.types import SafetyLevel, SafetyCheck, SafetyResult, SafetyPolicy


# ============================================================================
# 网络安全检查器
# ============================================================================

class NetworkSafetyChecker:
    """
    网络安全检查器。
    对应 Codex 的网络安全检查逻辑。

    检查:
    1. URL 安全
    2. 域名白名单
    3. 协议安全
    4. 端口安全
    """

    # 危险域名
    DANGEROUS_DOMAINS = {
        'malware.com', 'phishing.com', 'hack.com',
    }

    # 允许的协议
    ALLOWED_PROTOCOLS = {'http', 'https', 'ftp', 'ftps'}

    # 危险端口
    DANGEROUS_PORTS = {
        21,   # FTP
        23,   # Telnet
        25,   # SMTP
        135,  # RPC
        139,  # NetBIOS
        445,  # SMB
        3389, # RDP
    }

    def __init__(
        self,
        policy: Optional[SafetyPolicy] = None,
        allowed_domains: Optional[List[str]] = None,
    ):
        """
        初始化网络安全检查器。

        参数:
            policy: 安全策略
            allowed_domains: 允许的域名列表
        """
        self.policy = policy or SafetyPolicy()
        self.allowed_domains = allowed_domains or []

    def check_url(self, url: str) -> SafetyResult:
        """
        检查 URL 安全性。

        参数:
            url: URL 字符串

        返回:
            SafetyResult 安全检查结果
        """
        if not url or not url.strip():
            return SafetyResult(
                check=SafetyCheck.AUTO_APPROVE,
                level=SafetyLevel.LOW,
                operation='browser_navigate',
            )

        url = url.strip()

        # 1. 检查协议
        protocol_result = self._check_protocol(url)
        if protocol_result:
            return protocol_result

        # 2. 检查危险域名
        domain_result = self._check_dangerous_domains(url)
        if domain_result:
            return domain_result

        # 3. 检查域名白名单
        whitelist_result = self._check_domain_whitelist(url)
        if whitelist_result:
            return whitelist_result

        # 4. 检查端口
        port_result = self._check_port(url)
        if port_result:
            return port_result

        # 5. 默认允许
        return SafetyResult(
            check=SafetyCheck.AUTO_APPROVE,
            level=SafetyLevel.LOW,
            operation='browser_navigate',
        )

    def check_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> SafetyResult:
        """
        检查 HTTP 请求安全性。

        参数:
            method: HTTP 方法
            url: URL
            headers: 请求头

        返回:
            SafetyResult 安全检查结果
        """
        # 1. 检查 URL
        url_result = self.check_url(url)
        if url_result.is_reject:
            return url_result

        # 2. 检查方法
        if method.upper() in ('DELETE', 'PUT', 'PATCH'):
            return SafetyResult(
                check=SafetyCheck.ASK_USER,
                level=SafetyLevel.MEDIUM,
                reason=f"HTTP {method} requires confirmation",
                details={"method": method, "url": url},
                operation='http_request',
            )

        # 3. 检查敏感头
        if headers:
            sensitive_headers = {'Authorization', 'Cookie', 'X-API-Key'}
            for header in headers:
                if header in sensitive_headers:
                    return SafetyResult(
                        check=SafetyCheck.ASK_USER,
                        level=SafetyLevel.MEDIUM,
                        reason=f"Request contains sensitive header: {header}",
                        details={"header": header},
                        operation='http_request',
                    )

        return SafetyResult(
            check=SafetyCheck.AUTO_APPROVE,
            level=SafetyLevel.LOW,
            operation='http_request',
        )

    def _check_protocol(self, url: str) -> Optional[SafetyResult]:
        """
        检查协议安全性。

        参数:
            url: URL 字符串

        返回:
            SafetyResult 如果协议不安全，否则 None
        """
        # 提取协议
        match = re.match(r'^(\w+)://', url)
        if not match:
            return None

        protocol = match.group(1).lower()

        if protocol not in self.ALLOWED_PROTOCOLS:
            return SafetyResult(
                check=SafetyCheck.REJECT,
                level=SafetyLevel.HIGH,
                reason=f"Denied protocol: {protocol}",
                details={"url": url, "protocol": protocol},
                operation='browser_navigate',
            )

        return None

    def _check_dangerous_domains(self, url: str) -> Optional[SafetyResult]:
        """
        检查危险域名。

        参数:
            url: URL 字符串

        返回:
            SafetyResult 如果域名危险，否则 None
        """
        domain = self._extract_domain(url)

        for dangerous in self.DANGEROUS_DOMAINS:
            if dangerous in domain:
                return SafetyResult(
                    check=SafetyCheck.REJECT,
                    level=SafetyLevel.CRITICAL,
                    reason=f"Dangerous domain: {dangerous}",
                    details={"url": url, "domain": domain},
                    operation='browser_navigate',
                )

        return None

    def _check_domain_whitelist(self, url: str) -> Optional[SafetyResult]:
        """
        检查域名白名单。

        参数:
            url: URL 字符串

        返回:
            SafetyResult 如果不在白名单，否则 None
        """
        if not self.allowed_domains:
            return None

        domain = self._extract_domain(url)

        for allowed in self.allowed_domains:
            if allowed in domain:
                return None

        return SafetyResult(
            check=SafetyCheck.ASK_USER,
            level=SafetyLevel.MEDIUM,
            reason=f"Domain not in whitelist: {domain}",
            details={"url": url, "domain": domain},
            operation='browser_navigate',
        )

    def _check_port(self, url: str) -> Optional[SafetyResult]:
        """
        检查端口安全性。

        参数:
            url: URL 字符串

        返回:
            SafetyResult 如果端口危险，否则 None
        """
        # 提取端口
        match = re.search(r':(\d+)', url)
        if not match:
            return None

        port = int(match.group(1))

        if port in self.DANGEROUS_PORTS:
            return SafetyResult(
                check=SafetyCheck.ASK_USER,
                level=SafetyLevel.HIGH,
                reason=f"Dangerous port: {port}",
                details={"url": url, "port": port},
                operation='browser_navigate',
            )

        return None

    def _extract_domain(self, url: str) -> str:
        """
        提取域名。

        参数:
            url: URL 字符串

        返回:
            域名字符串
        """
        # 移除协议
        domain = re.sub(r'^\w+://', '', url)

        # 移除路径
        domain = domain.split('/')[0]

        # 移除端口
        domain = domain.split(':')[0]

        return domain.lower()


# ============================================================================
# URL 分类器
# ============================================================================

class URLClassifier:
    """
    URL 分类器。
    将 URL 分为不同类别。
    """

    # 可信域名
    TRUSTED_DOMAINS = {
        'github.com', 'gitlab.com', 'bitbucket.org',
        'google.com', 'microsoft.com', 'apple.com',
        'stackoverflow.com', 'wikipedia.org',
    }

    def classify(self, url: str) -> str:
        """
        分类 URL。

        参数:
            url: URL 字符串

        返回:
            URL 类别: 'trusted', 'unknown', 'dangerous'
        """
        domain = self._extract_domain(url)

        for trusted in self.TRUSTED_DOMAINS:
            if trusted in domain:
                return 'trusted'

        return 'unknown'

    def get_risk_level(self, url: str) -> SafetyLevel:
        """
        获取 URL 风险级别。

        参数:
            url: URL 字符串

        返回:
            SafetyLevel 风险级别
        """
        category = self.classify(url)

        if category == 'trusted':
            return SafetyLevel.LOW
        elif category == 'unknown':
            return SafetyLevel.MEDIUM
        else:
            return SafetyLevel.HIGH

    def _extract_domain(self, url: str) -> str:
        """提取域名"""
        domain = re.sub(r'^\w+://', '', url)
        domain = domain.split('/')[0]
        domain = domain.split(':')[0]
        return domain.lower()
