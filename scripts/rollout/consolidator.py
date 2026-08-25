#!/usr/bin/env python3
"""
Codex Harness — 记忆合并器

合并和组织记忆。
对应 Codex 的记忆合并逻辑。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any
from rollout.types import MemoryEntry


# ============================================================================
# 记忆合并器
# ============================================================================

class MemoryConsolidator:
    """
    记忆合并器。
    对应 Codex 的记忆合并逻辑。

    功能:
    - 合并相似记忆
    - 组织记忆结构
    - 去重记忆
    """

    def consolidate(self, memories: List[MemoryEntry]) -> List[MemoryEntry]:
        """
        合并记忆。

        参数:
            memories: 记忆列表

        返回:
            合并后的记忆列表
        """
        if not memories:
            return []

        # 1. 按类型分组
        grouped = self._group_by_type(memories)

        # 2. 合并每组内的相似记忆
        consolidated = []
        for type_name, group in grouped.items():
            merged = self._merge_similar(group)
            consolidated.extend(merged)

        return consolidated

    def _group_by_type(
        self,
        memories: List[MemoryEntry],
    ) -> Dict[str, List[MemoryEntry]]:
        """
        按类型分组。

        参数:
            memories: 记忆列表

        返回:
            分组字典
        """
        groups: Dict[str, List[MemoryEntry]] = {}

        for memory in memories:
            type_name = memory.type.value
            if type_name not in groups:
                groups[type_name] = []
            groups[type_name].append(memory)

        return groups

    def _merge_similar(self, memories: List[MemoryEntry]) -> List[MemoryEntry]:
        """
        合并相似记忆。

        参数:
            memories: 同类型记忆列表

        返回:
            合并后的记忆列表
        """
        if len(memories) <= 1:
            return memories

        merged = []
        used = set()

        for i, mem1 in enumerate(memories):
            if i in used:
                continue

            # 查找相似记忆
            similar = [mem1]
            for j, mem2 in enumerate(memories[i + 1:], i + 1):
                if j in used:
                    continue

                if self._are_similar(mem1, mem2):
                    similar.append(mem2)
                    used.add(j)

            # 合并相似记忆
            if len(similar) > 1:
                merged_mem = self._merge_memories(similar)
                merged.append(merged_mem)
            else:
                merged.append(mem1)

            used.add(i)

        return merged

    def _are_similar(self, mem1: MemoryEntry, mem2: MemoryEntry) -> bool:
        """
        检查两个记忆是否相似。

        参数:
            mem1: 记忆1
            mem2: 记忆2

        返回:
            True 如果相似
        """
        # 检查内容相似度
        words1 = set(mem1.content.lower().split())
        words2 = set(mem2.content.lower().split())

        if not words1 or not words2:
            return False

        intersection = words1 & words2
        union = words1 | words2

        similarity = len(intersection) / len(union) if union else 0.0

        return similarity >= 0.6

    def _merge_memories(self, memories: List[MemoryEntry]) -> MemoryEntry:
        """
        合并多个记忆。

        参数:
            memories: 记忆列表

        返回:
            合并后的记忆
        """
        # 使用最长的内容
        longest = max(memories, key=lambda m: len(m.content))

        # 合并关键词
        all_keywords = []
        for mem in memories:
            all_keywords.extend(mem.keywords)
        unique_keywords = list(set(all_keywords))

        # 合并来源文件
        all_files = []
        for mem in memories:
            all_files.extend(mem.source_files)
        unique_files = list(set(all_files))

        # 合并使用次数
        total_usage = sum(m.usage_count for m in memories)

        return MemoryEntry(
            type=longest.type,
            content=longest.content,
            task=longest.task,
            task_group=longest.task_group,
            outcome=longest.outcome,
            keywords=unique_keywords,
            usage_count=total_usage,
            last_usage=max(m.last_usage for m in memories),
            created_at=min(m.created_at for m in memories),
            source_session=longest.source_session,
            source_files=unique_files,
        )


# ============================================================================
# 记忆组织器
# ============================================================================

class MemoryOrganizer:
    """
    记忆组织器。
    组织记忆结构。

    功能:
    - 按类型组织
    - 按任务组织
    - 按时间组织
    """

    def organize_by_type(
        self,
        memories: List[MemoryEntry],
    ) -> Dict[str, List[MemoryEntry]]:
        """
        按类型组织。

        参数:
            memories: 记忆列表

        返回:
            按类型分组的字典
        """
        groups: Dict[str, List[MemoryEntry]] = {}

        for memory in memories:
            type_name = memory.type.value
            if type_name not in groups:
                groups[type_name] = []
            groups[type_name].append(memory)

        return groups

    def organize_by_task(
        self,
        memories: List[MemoryEntry],
    ) -> Dict[str, List[MemoryEntry]]:
        """
        按任务组织。

        参数:
            memories: 记忆列表

        返回:
            按任务分组的字典
        """
        groups: Dict[str, List[MemoryEntry]] = {}

        for memory in memories:
            task = memory.task or "unknown"
            if task not in groups:
                groups[task] = []
            groups[task].append(memory)

        return groups

    def organize_by_time(
        self,
        memories: List[MemoryEntry],
    ) -> List[MemoryEntry]:
        """
        按时间组织 (最新优先)。

        参数:
            memories: 记忆列表

        返回:
            按时间排序的列表
        """
        return sorted(memories, key=lambda m: m.created_at, reverse=True)

    def get_summary(
        self,
        memories: List[MemoryEntry],
    ) -> Dict[str, Any]:
        """
        获取记忆摘要。

        参数:
            memories: 记忆列表

        返回:
            摘要字典
        """
        if not memories:
            return {"total": 0}

        by_type = self.organize_by_type(memories)

        return {
            "total": len(memories),
            "by_type": {k: len(v) for k, v in by_type.items()},
            "avg_content_length": sum(len(m.content) for m in memories) / len(memories),
            "total_usage": sum(m.usage_count for m in memories),
        }
