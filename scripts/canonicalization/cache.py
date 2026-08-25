#!/usr/bin/env python3
"""
Codex Harness — 审批缓存

存储已审批的命令，避免重复审批。
对应 Codex 的审批缓存系统。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from typing import List, Dict, Any, Optional
from canonicalization.canonicalizer import get_command_signature


# ============================================================================
# 审批缓存
# ============================================================================

class ApprovalCache:
    """
    审批缓存。
    存储已审批的命令，避免重复审批。

    功能:
    - 缓存审批结果
    - 自动过期
    - 缓存统计
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600,
    ):
        """
        初始化审批缓存。

        参数:
            max_size: 最大缓存大小
            ttl_seconds: 缓存过期时间 (秒)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}

    def get(self, command: List[str]) -> Optional[bool]:
        """
        获取审批结果。

        参数:
            command: 命令参数列表

        返回:
            审批结果，如果不在缓存中返回 None
        """
        key = get_command_signature(command)

        if key not in self.cache:
            return None

        entry = self.cache[key]

        # 检查是否过期
        if self._is_expired(entry):
            del self.cache[key]
            return None

        # 更新访问时间
        entry['last_accessed'] = time.time()
        entry['access_count'] += 1

        return entry['approved']

    def set(self, command: List[str], approved: bool):
        """
        设置审批结果。

        参数:
            command: 命令参数列表
            approved: 是否批准
        """
        key = get_command_signature(command)

        # 如果缓存已满，删除最旧的条目
        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        self.cache[key] = {
            'approved': approved,
            'created': time.time(),
            'last_accessed': time.time(),
            'access_count': 0,
        }

    def has(self, command: List[str]) -> bool:
        """
        检查命令是否在缓存中。

        参数:
            command: 命令参数列表

        返回:
            True 如果在缓存中
        """
        return self.get(command) is not None

    def remove(self, command: List[str]):
        """
        从缓存中删除命令。

        参数:
            command: 命令参数列表
        """
        key = get_command_signature(command)
        if key in self.cache:
            del self.cache[key]

    def clear(self):
        """清除所有缓存"""
        self.cache.clear()

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """
        检查条目是否过期。

        参数:
            entry: 缓存条目

        返回:
            True 如果过期
        """
        return time.time() - entry['created'] > self.ttl_seconds

    def _evict_oldest(self):
        """删除最旧的条目"""
        if not self.cache:
            return

        # 找到最旧的条目
        oldest_key = min(self.cache, key=lambda k: self.cache[k]['last_accessed'])
        del self.cache[oldest_key]

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计。

        返回:
            统计字典
        """
        if not self.cache:
            return {
                'size': 0,
                'max_size': self.max_size,
                'hit_rate': 0.0,
                'total_accesses': 0,
            }

        total_accesses = sum(entry['access_count'] for entry in self.cache.values())

        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'total_accesses': total_accesses,
            'ttl_seconds': self.ttl_seconds,
        }

    def cleanup(self):
        """清理过期条目"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if self._is_expired(entry)
        ]

        for key in expired_keys:
            del self.cache[key]


# ============================================================================
# 全局审批缓存
# ============================================================================

# 全局缓存实例
_global_cache: Optional[ApprovalCache] = None


def get_global_cache() -> ApprovalCache:
    """
    获取全局审批缓存。

    返回:
        全局审批缓存实例
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = ApprovalCache()
    return _global_cache


def check_approval_cache(command: List[str]) -> Optional[bool]:
    """
    检查审批缓存。

    参数:
        command: 命令参数列表

    返回:
        审批结果，如果不在缓存中返回 None
    """
    cache = get_global_cache()
    return cache.get(command)


def set_approval_cache(command: List[str], approved: bool):
    """
    设置审批缓存。

    参数:
        command: 命令参数列表
        approved: 是否批准
    """
    cache = get_global_cache()
    cache.set(command, approved)


def clear_approval_cache():
    """清除审批缓存"""
    cache = get_global_cache()
    cache.clear()


# ============================================================================
# 审批缓存管理器
# ============================================================================

class ApprovalCacheManager:
    """
    审批缓存管理器。
    提供高级缓存管理功能。

    功能:
    - 批量操作
    - 缓存预热
    - 缓存导出/导入
    """

    def __init__(self, cache: Optional[ApprovalCache] = None):
        """
        初始化审批缓存管理器。

        参数:
            cache: 审批缓存实例 (None 使用全局缓存)
        """
        self.cache = cache or get_global_cache()

    def warmup(self, commands: List[Dict[str, Any]]):
        """
        预热缓存。

        参数:
            commands: 命令列表 [{'command': [...], 'approved': True}, ...]
        """
        for entry in commands:
            command = entry.get('command', [])
            approved = entry.get('approved', False)
            self.cache.set(command, approved)

    def export_cache(self) -> List[Dict[str, Any]]:
        """
        导出缓存。

        返回:
            缓存条目列表
        """
        result = []
        for key, entry in self.cache.cache.items():
            result.append({
                'key': key,
                'approved': entry['approved'],
                'created': entry['created'],
                'last_accessed': entry['last_accessed'],
                'access_count': entry['access_count'],
            })
        return result

    def import_cache(self, data: List[Dict[str, Any]]):
        """
        导入缓存。

        参数:
            data: 缓存条目列表
        """
        for entry in data:
            key = entry.get('key', '')
            self.cache.cache[key] = {
                'approved': entry.get('approved', False),
                'created': entry.get('created', time.time()),
                'last_accessed': entry.get('last_accessed', time.time()),
                'access_count': entry.get('access_count', 0),
            }

    def get_most_accessed(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取访问次数最多的命令。

        参数:
            limit: 返回数量

        返回:
            命令列表
        """
        sorted_entries = sorted(
            self.cache.cache.items(),
            key=lambda x: x[1]['access_count'],
            reverse=True,
        )

        return [
            {
                'key': key,
                'approved': entry['approved'],
                'access_count': entry['access_count'],
            }
            for key, entry in sorted_entries[:limit]
        ]
