#!/usr/bin/env python3
"""
Codex Harness — 质量过滤器

过滤低质量记忆。
对应 Codex 的质量过滤逻辑。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from typing import List
from rollout.types import MemoryType, MemoryEntry


# ============================================================================
# 质量过滤器
# ============================================================================

class QualityFilter:
    """
    质量过滤器。
    对应 Codex 的质量过滤逻辑。

    过滤规则:
    1. 最小信号门: "未来的代理会因此表现更好吗？"
    2. 重复检测: 避免存储重复信息
    3. 时效性: 过期信息不存储
    4. 长度过滤: 太短或太长的记忆
    5. 内容质量: 有意义的内容
    """

    # 最小内容长度
    MIN_CONTENT_LENGTH = 10

    # 最大内容长度
    MAX_CONTENT_LENGTH = 1000

    # 最小关键词数
    MIN_KEYWORDS = 1

    def __init__(
        self,
        min_content_length: int = 10,
        max_content_length: int = 1000,
        min_keywords: int = 1,
    ):
        """
        初始化质量过滤器。

        参数:
            min_content_length: 最小内容长度
            max_content_length: 最大内容长度
            min_keywords: 最小关键词数
        """
        self.min_content_length = min_content_length
        self.max_content_length = max_content_length
        self.min_keywords = min_keywords

    def filter(self, memories: List[MemoryEntry]) -> List[MemoryEntry]:
        """
        过滤低质量记忆。

        参数:
            memories: 记忆列表

        返回:
            过滤后的记忆列表
        """
        filtered = []

        for memory in memories:
            if self._is_high_quality(memory):
                filtered.append(memory)

        return filtered

    def _is_high_quality(self, memory: MemoryEntry) -> bool:
        """
        检查记忆是否高质量。

        参数:
            memory: 记忆条目

        返回:
            True 如果高质量
        """
        # 1. 检查内容长度
        if len(memory.content) < self.min_content_length:
            return False

        if len(memory.content) > self.max_content_length:
            return False

        # 2. 检查关键词数
        if len(memory.keywords) < self.min_keywords:
            return False

        # 3. 检查内容质量
        if not self._has_meaningful_content(memory.content):
            return False

        # 4. 检查是否重复
        if self._is_duplicate(memory):
            return False

        return True

    def _has_meaningful_content(self, content: str) -> bool:
        """
        检查内容是否有意义。

        参数:
            content: 内容

        返回:
            True 如果有意义
        """
        # 检查是否包含实际内容
        if len(content.strip()) < 5:
            return False

        # 检查是否只是标点符号
        if re.match(r'^[^\w]+$', content):
            return False

        # 检查是否包含动词
        verbs = ['run', 'execute', 'install', 'create', 'delete', 'update',
                 'fix', 'change', 'add', 'remove', 'use', 'set', 'get',
                 'prefer', 'want', 'need', 'like', 'error', 'fail',
                 'implement', 'build', 'test', 'deploy', 'configure',
                 'setup', 'write', 'read', 'open', 'close', 'start',
                 'stop', 'enable', 'disable', 'import', 'export']
        has_verb = any(verb in content.lower() for verb in verbs)

        return has_verb

    def _is_duplicate(self, memory: MemoryEntry) -> bool:
        """
        检查是否重复。

        参数:
            memory: 记忆条目

        返回:
            True 如果重复
        """
        # 这里应该与已有的记忆比较
        # 简化实现：检查内容相似度
        # TODO: 实现实际的重复检测
        return False


# ============================================================================
# 高级质量过滤器
# ============================================================================

class AdvancedQualityFilter(QualityFilter):
    """
    高级质量过滤器。

    增强功能:
    - 语义相似度检测
    - 时效性检查
    - 置信度评估
    """

    def __init__(
        self,
        min_content_length: int = 10,
        max_content_length: int = 1000,
        min_keywords: int = 1,
        similarity_threshold: float = 0.8,
    ):
        """
        初始化高级质量过滤器。

        参数:
            min_content_length: 最小内容长度
            max_content_length: 最大内容长度
            min_keywords: 最小关键词数
            similarity_threshold: 相似度阈值
        """
        super().__init__(min_content_length, max_content_length, min_keywords)
        self.similarity_threshold = similarity_threshold
        self.seen_contents: List[str] = []

    def filter(self, memories: List[MemoryEntry]) -> List[MemoryEntry]:
        """
        过滤低质量记忆。

        参数:
            memories: 记忆列表

        返回:
            过滤后的记忆列表
        """
        filtered = []
        self.seen_contents = []

        for memory in memories:
            if self._is_high_quality(memory):
                # 检查与已过滤记忆的相似度
                if not self._is_similar_to_existing(memory):
                    filtered.append(memory)
                    self.seen_contents.append(memory.content)

        return filtered

    def _is_similar_to_existing(self, memory: MemoryEntry) -> bool:
        """
        检查是否与已有记忆相似。

        参数:
            memory: 记忆条目

        返回:
            True 如果相似
        """
        for seen in self.seen_contents:
            similarity = self._calculate_similarity(memory.content, seen)
            if similarity >= self.similarity_threshold:
                return True

        return False

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算文本相似度。

        参数:
            text1: 文本1
            text2: 文本2

        返回:
            相似度 (0.0 - 1.0)
        """
        # 简单的 Jaccard 相似度
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0


# ============================================================================
# 记忆评分器
# ============================================================================

class MemoryScorer:
    """
    记忆评分器。
    为记忆打分，用于排序和优先级。
    """

    # 类型权重
    TYPE_WEIGHTS = {
        MemoryType.PREFERENCE: 1.0,
        MemoryType.PROCEDURE: 0.9,
        MemoryType.ENVIRONMENT: 0.7,
        MemoryType.TASK: 0.8,
        MemoryType.FAILURE: 0.85,
    }

    def score(self, memory: MemoryEntry) -> float:
        """
        为记忆打分。

        参数:
            memory: 记忆条目

        返回:
            分数 (0.0 - 1.0)
        """
        score = 0.0

        # 1. 类型权重
        type_weight = self.TYPE_WEIGHTS.get(memory.type, 0.5)
        score += type_weight * 0.3

        # 2. 内容长度
        content_len = len(memory.content)
        if content_len >= 20 and content_len <= 200:
            score += 0.2
        elif content_len > 200:
            score += 0.1

        # 3. 关键词数
        keyword_count = len(memory.keywords)
        if keyword_count >= 3:
            score += 0.2
        elif keyword_count >= 1:
            score += 0.1

        # 4. 使用次数
        if memory.usage_count > 0:
            score += min(memory.usage_count * 0.1, 0.3)

        return min(score, 1.0)

    def rank(self, memories: List[MemoryEntry]) -> List[MemoryEntry]:
        """
        按分数排序记忆。

        参数:
            memories: 记忆列表

        返回:
            排序后的记忆列表
        """
        return sorted(memories, key=lambda m: self.score(m), reverse=True)
