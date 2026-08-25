#!/usr/bin/env python3
"""
Codex Harness — Rollout 提取器

从会话历史中提取结构化记忆。
对应 Codex 的 RolloutRecorder。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from typing import List, Dict, Any, Optional
from rollout.types import MemoryType, MemoryEntry, ExtractionResult


# ============================================================================
# Rollout 提取器
# ============================================================================

class RolloutExtractor:
    """
    Rollout 提取器。
    对应 Codex 的 RolloutRecorder。

    从会话历史中提取结构化记忆。

    功能:
    - 提取用户偏好
    - 提取可复用知识
    - 提取环境信息
    - 提取任务结果
    - 提取失败教训
    """

    # 关键词模式
    PREFERENCE_PATTERNS = [
        r'prefer|like|want|need|use\s+\w+\s+instead',
        r'always\s+\w+|never\s+\w+',
        r'style|format|convention',
    ]

    PROCEDURE_PATTERNS = [
        r'run|execute|command|install|configure',
        r'step\s+\d+|first.*then|how\s+to',
        r'setup|deploy|build|test',
    ]

    ENVIRONMENT_PATTERNS = [
        r'os|platform|version|path|directory',
        r'python|node|java|docker|kubernetes',
        r'linux|macos|windows|ubuntu|centos',
    ]

    TASK_PATTERNS = [
        r'completed|finished|done|success|created|built',
        r'implemented|added|fixed|updated|changed',
        r'deployed|migrated|integrated',
    ]

    FAILURE_PATTERNS = [
        r'error|fail|crash|bug|issue|problem',
        r'wrong|incorrect|invalid|broken',
        r'fix|solution|workaround|avoid',
    ]

    def extract(self, session_history: List[Dict[str, Any]]) -> ExtractionResult:
        """
        从会话历史提取记忆。

        参数:
            session_history: 会话历史列表

        返回:
            ExtractionResult 提取结果
        """
        memories = []

        for msg in session_history:
            role = msg.get('role', '')
            content = msg.get('content', '')

            if not content:
                continue

            # 提取记忆
            extracted = self._extract_from_message(role, content)
            memories.extend(extracted)

        # 计算 Token 数
        source_tokens = sum(len(str(msg)) for msg in session_history)
        extracted_tokens = sum(len(m.content) for m in memories)

        return ExtractionResult(
            memories=memories,
            source_tokens=source_tokens,
            extracted_tokens=extracted_tokens,
        )

    def _extract_from_message(
        self,
        role: str,
        content: str,
    ) -> List[MemoryEntry]:
        """
        从单条消息提取记忆。

        参数:
            role: 消息角色
            content: 消息内容

        返回:
            记忆列表
        """
        memories = []

        # 只从用户和助手消息提取
        if role not in ('user', 'assistant'):
            return memories

        # 提取用户偏好
        preferences = self._extract_patterns(content, self.PREFERENCE_PATTERNS)
        for pref in preferences:
            memories.append(MemoryEntry(
                type=MemoryType.PREFERENCE,
                content=pref,
                keywords=self._extract_keywords(pref),
            ))

        # 提取可复用知识
        procedures = self._extract_patterns(content, self.PROCEDURE_PATTERNS)
        for proc in procedures:
            memories.append(MemoryEntry(
                type=MemoryType.PROCEDURE,
                content=proc,
                keywords=self._extract_keywords(proc),
            ))

        # 提取环境信息
        environments = self._extract_patterns(content, self.ENVIRONMENT_PATTERNS)
        for env in environments:
            memories.append(MemoryEntry(
                type=MemoryType.ENVIRONMENT,
                content=env,
                keywords=self._extract_keywords(env),
            ))

        # 提取任务结果
        tasks = self._extract_patterns(content, self.TASK_PATTERNS)
        for task in tasks:
            memories.append(MemoryEntry(
                type=MemoryType.TASK,
                content=task,
                keywords=self._extract_keywords(task),
            ))

        # 提取失败教训
        failures = self._extract_patterns(content, self.FAILURE_PATTERNS)
        for fail in failures:
            memories.append(MemoryEntry(
                type=MemoryType.FAILURE,
                content=fail,
                keywords=self._extract_keywords(fail),
            ))

        return memories

    def _extract_patterns(
        self,
        content: str,
        patterns: List[str],
    ) -> List[str]:
        """
        使用正则模式提取内容。

        参数:
            content: 文本内容
            patterns: 正则模式列表

        返回:
            匹配的句子列表
        """
        matches = []
        sentences = self._split_sentences(content)

        for sentence in sentences:
            for pattern in patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    matches.append(sentence.strip())
                    break

        return matches

    def _split_sentences(self, text: str) -> List[str]:
        """
        拆分文本为句子。

        参数:
            text: 文本

        返回:
            句子列表
        """
        # 使用标点符号拆分
        sentences = re.split(r'[.!?;]', text)
        return [s.strip() for s in sentences if s.strip()]

    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词。

        参数:
            text: 文本

        返回:
            关键词列表
        """
        # 移除标点符号
        text = re.sub(r'[^\w\s]', '', text)

        # 拆分为单词
        words = text.lower().split()

        # 过滤停用词
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were',
            'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'shall',
            'to', 'of', 'in', 'for', 'on', 'with', 'at',
            'by', 'from', 'as', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between',
            'and', 'but', 'or', 'nor', 'not', 'so',
            'i', 'you', 'he', 'she', 'it', 'we', 'they',
        }

        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        # 去重
        return list(set(keywords))


# ============================================================================
# 高级提取器
# ============================================================================

class AdvancedRolloutExtractor(RolloutExtractor):
    """
    高级 Rollout 提取器。

    增强功能:
    - 上下文感知提取
    - 多轮对话分析
    - 关键信息提取
    """

    def extract_with_context(
        self,
        session_history: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> ExtractionResult:
        """
        带上下文的提取。

        参数:
            session_history: 会话历史
            context: 上下文信息

        返回:
            ExtractionResult 提取结果
        """
        # 基础提取
        result = self.extract(session_history)

        # 上下文增强
        if context:
            self._enhance_with_context(result.memories, context)

        return result

    def _enhance_with_context(
        self,
        memories: List[MemoryEntry],
        context: Dict[str, Any],
    ):
        """
        使用上下文增强记忆。

        参数:
            memories: 记忆列表
            context: 上下文信息
        """
        # 添加任务信息
        task = context.get('task', '')
        task_group = context.get('task_group', '')

        for memory in memories:
            if not memory.task:
                memory.task = task
            if not memory.task_group:
                memory.task_group = task_group

    def extract_from_conversation(
        self,
        messages: List[Dict[str, Any]],
    ) -> ExtractionResult:
        """
        从对话中提取记忆。

        参数:
            messages: 消息列表

        返回:
            ExtractionResult 提取结果
        """
        memories = []

        # 分析多轮对话
        for i in range(len(messages) - 1):
            current = messages[i]
            next_msg = messages[i + 1]

            # 提取问答对
            if current.get('role') == 'user' and next_msg.get('role') == 'assistant':
                question = current.get('content', '')
                answer = next_msg.get('content', '')

                # 从问题中提取需求
                needs = self._extract_needs(question)
                for need in needs:
                    memories.append(MemoryEntry(
                        type=MemoryType.PREFERENCE,
                        content=need,
                        keywords=self._extract_keywords(need),
                    ))

                # 从答案中提取知识
                knowledge = self._extract_knowledge(answer)
                for know in knowledge:
                    memories.append(MemoryEntry(
                        type=MemoryType.PROCEDURE,
                        content=know,
                        keywords=self._extract_keywords(know),
                    ))

        # 计算 Token 数
        source_tokens = sum(len(str(msg)) for msg in messages)
        extracted_tokens = sum(len(m.content) for m in memories)

        return ExtractionResult(
            memories=memories,
            source_tokens=source_tokens,
            extracted_tokens=extracted_tokens,
        )

    def _extract_needs(self, question: str) -> List[str]:
        """
        从问题中提取需求。

        参数:
            question: 问题

        返回:
            需求列表
        """
        needs = []
        patterns = [
            r'I\s+want\s+to\s+\w+',
            r'I\s+need\s+\w+',
            r'How\s+to\s+\w+',
            r'Can\s+you\s+\w+',
            r'Please\s+\w+',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, question, re.IGNORECASE)
            needs.extend(matches)

        return needs

    def _extract_knowledge(self, answer: str) -> List[str]:
        """
        从答案中提取知识。

        参数:
            answer: 答案

        返回:
            知识列表
        """
        knowledge = []

        # 提取代码块
        code_blocks = re.findall(r'```[\w]*\n(.*?)```', answer, re.DOTALL)
        for block in code_blocks:
            if len(block.strip()) > 10:
                knowledge.append(f"Code: {block.strip()[:100]}")

        # 提取步骤
        steps = re.findall(r'\d+\.\s+(.*?)(?=\d+\.|$)', answer, re.DOTALL)
        for step in steps:
            if len(step.strip()) > 10:
                knowledge.append(f"Step: {step.strip()[:100]}")

        return knowledge
