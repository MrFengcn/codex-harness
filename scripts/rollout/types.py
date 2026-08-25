#!/usr/bin/env python3
"""
Codex Harness — Rollout 类型定义

定义记忆类型和记忆条目。
对应 Codex 的 SessionMeta 和 MemoryType。

Python 兼容性: 3.6+
"""

from enum import Enum
from typing import List, Dict, Any, Optional
import time


class MemoryType(Enum):
    """
    记忆类型。
    对应 Codex 的记忆分类。

    属性:
        PREFERENCE: 用户偏好 (代码风格、工具选择)
        PROCEDURE: 可复用知识 (命令、配置、模式)
        ENVIRONMENT: 环境信息 (OS、工具版本、路径)
        TASK: 任务结果 (成功完成的任务)
        FAILURE: 失败教训 (错误原因、避免方法)
    """
    PREFERENCE = "preference"
    PROCEDURE = "procedure"
    ENVIRONMENT = "environment"
    TASK = "task"
    FAILURE = "failure"


class MemoryEntry:
    """
    记忆条目。
    对应 Codex 的 SessionMeta。

    属性:
        id: 唯一标识
        type: 记忆类型
        content: 记忆内容
        task: 关联任务
        task_group: 任务分组
        outcome: 任务结果
        keywords: 关键词列表
        usage_count: 使用次数
        last_usage: 最后使用时间
        created_at: 创建时间
        source_session: 来源会话
        source_files: 来源文件列表
    """
    def __init__(
        self,
        type: MemoryType,
        content: str,
        task: str = "",
        task_group: str = "",
        outcome: str = "",
        keywords: Optional[List[str]] = None,
        usage_count: int = 0,
        last_usage: Optional[float] = None,
        created_at: Optional[float] = None,
        source_session: str = "",
        source_files: Optional[List[str]] = None,
    ):
        """
        初始化记忆条目。

        参数:
            type: 记忆类型
            content: 记忆内容
            task: 关联任务
            task_group: 任务分组
            outcome: 任务结果
            keywords: 关键词列表
            usage_count: 使用次数
            last_usage: 最后使用时间
            created_at: 创建时间
            source_session: 来源会话
            source_files: 来源文件列表
        """
        self.id = self._generate_id()
        self.type = type
        self.content = content
        self.task = task
        self.task_group = task_group
        self.outcome = outcome
        self.keywords = keywords or []
        self.usage_count = usage_count
        self.last_usage = last_usage or time.time()
        self.created_at = created_at or time.time()
        self.source_session = source_session
        self.source_files = source_files or []

    def _generate_id(self) -> str:
        """生成唯一标识"""
        import uuid
        return str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "task": self.task,
            "task_group": self.task_group,
            "outcome": self.outcome,
            "keywords": self.keywords,
            "usage_count": self.usage_count,
            "last_usage": self.last_usage,
            "created_at": self.created_at,
            "source_session": self.source_session,
            "source_files": self.source_files,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """从字典创建记忆条目"""
        return cls(
            type=MemoryType(data.get('type', 'task')),
            content=data.get('content', ''),
            task=data.get('task', ''),
            task_group=data.get('task_group', ''),
            outcome=data.get('outcome', ''),
            keywords=data.get('keywords', []),
            usage_count=data.get('usage_count', 0),
            last_usage=data.get('last_usage'),
            created_at=data.get('created_at'),
            source_session=data.get('source_session', ''),
            source_files=data.get('source_files', []),
        )

    def update_usage(self):
        """更新使用记录"""
        self.usage_count += 1
        self.last_usage = time.time()

    def to_frontmatter(self) -> str:
        """
        转换为 Markdown frontmatter 格式。

        返回:
            frontmatter 字符串
        """
        lines = [
            "---",
            f'description: "{self.content[:100]}"',
            f'task: "{self.task}"',
            f'task_group: "{self.task_group}"',
            f'outcome: "{self.outcome}"',
            f'keywords: {self.keywords}',
            "---",
        ]
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"MemoryEntry(type={self.type.value}, "
            f"content={self.content[:30]}...)"
        )


class ExtractionResult:
    """
    提取结果。

    属性:
        memories: 提取的记忆列表
        source_tokens: 源 Token 数
        extracted_tokens: 提取后 Token 数
        extraction_ratio: 提取率
    """
    def __init__(
        self,
        memories: List[MemoryEntry],
        source_tokens: int = 0,
        extracted_tokens: int = 0,
    ):
        """
        初始化提取结果。

        参数:
            memories: 提取的记忆列表
            source_tokens: 源 Token 数
            extracted_tokens: 提取后 Token 数
        """
        self.memories = memories
        self.source_tokens = source_tokens
        self.extracted_tokens = extracted_tokens

    @property
    def count(self) -> int:
        """记忆数量"""
        return len(self.memories)

    @property
    def extraction_ratio(self) -> float:
        """提取率"""
        if self.source_tokens == 0:
            return 0.0
        return self.extracted_tokens / self.source_tokens

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "count": self.count,
            "source_tokens": self.source_tokens,
            "extracted_tokens": self.extracted_tokens,
            "extraction_ratio": round(self.extraction_ratio, 3),
            "memories": [m.to_dict() for m in self.memories],
        }
