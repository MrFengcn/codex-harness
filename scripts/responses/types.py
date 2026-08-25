#!/usr/bin/env python3
"""
Codex Harness — 响应系统

提供响应格式化能力。
对应 Codex 的 responses 模块。

Python 兼容性: 3.6+
"""

from enum import Enum
from typing import List, Dict, Any, Optional


class ResponseType(Enum):
    """响应类型"""
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


class Response:
    """响应"""
    def __init__(self, type: ResponseType = ResponseType.TEXT, content: str = "", metadata: Optional[Dict] = None):
        self.type = type
        self.content = content
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type.value, "content": self.content, "metadata": self.metadata}


class ResponseBuilder:
    """响应构建器"""
    def __init__(self):
        self.responses: List[Response] = []

    def text(self, content: str) -> 'ResponseBuilder':
        self.responses.append(Response(type=ResponseType.TEXT, content=content))
        return self

    def json(self, data: Dict[str, Any]) -> 'ResponseBuilder':
        import json
        self.responses.append(Response(type=ResponseType.JSON, content=json.dumps(data)))
        return self

    def markdown(self, content: str) -> 'ResponseBuilder':
        self.responses.append(Response(type=ResponseType.MARKDOWN, content=content))
        return self

    def build(self) -> List[Response]:
        return self.responses


class ResponseManager:
    """响应管理器"""
    def __init__(self):
        self.history: List[Response] = []

    def create_builder(self) -> ResponseBuilder:
        return ResponseBuilder()

    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self.history)}
