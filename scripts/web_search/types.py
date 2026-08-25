#!/usr/bin/env python3
"""
Codex Harness — Web 搜索系统

提供 Web 搜索能力。
对应 Codex 的 web_search 模块。

Python 兼容性: 3.6+
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import time


class SearchResult:
    """搜索结果"""
    def __init__(self, title: str, url: str, snippet: str = ""):
        self.title = title
        self.url = url
        self.snippet = snippet

    def to_dict(self) -> Dict[str, Any]:
        return {"title": self.title, "url": self.url, "snippet": self.snippet}


class SearchProvider(ABC):
    """搜索提供者基类"""
    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass


class WebSearchManager:
    """Web 搜索管理器"""
    def __init__(self):
        self.providers: Dict[str, SearchProvider] = {}
        self.history: List[Dict[str, Any]] = []

    def register_provider(self, provider: SearchProvider):
        self.providers[provider.get_name()] = provider

    def search(self, query: str, provider_name: str = "", limit: int = 10) -> List[SearchResult]:
        provider = None
        if provider_name:
            provider = self.providers.get(provider_name)
        elif self.providers:
            provider = list(self.providers.values())[0]

        if not provider:
            return []

        start_time = time.time()
        results = provider.search(query, limit)
        duration_ms = (time.time() - start_time) * 1000

        self.history.append({
            "query": query, "provider": provider.get_name(),
            "results": len(results), "duration_ms": duration_ms,
        })

        return results

    def get_stats(self) -> Dict[str, Any]:
        return {"providers": len(self.providers), "searches": len(self.history)}
