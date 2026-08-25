#!/usr/bin/env python3
"""
Codex Harness — 远程压缩策略

调用远程 API 进行对话压缩。
对应 Codex 的 compact_remote.rs。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from typing import List, Dict, Any, Optional
from compression.base import CompressionStrategy, CompressionResult
from core import estimate_tokens


# ============================================================================
# 远程压缩策略
# ============================================================================

class RemoteCompression(CompressionStrategy):
    """
    远程压缩策略。
    对应 Codex 的 compact_remote.rs。

    调用远程 API 进行对话压缩。
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        max_retries: int = 3,
        timeout: int = 30,
        max_summary_tokens: int = 2000,
        min_history_length: int = 3,
    ):
        """
        初始化远程压缩策略。

        参数:
            api_url: API URL (None 使用默认)
            api_key: API 密钥 (None 使用环境变量)
            model: 使用的模型
            max_retries: 最大重试次数
            timeout: 超时时间 (秒)
            max_summary_tokens: 摘要最大 Token 数
            min_history_length: 最小历史消息数
        """
        self.api_url = api_url or os.environ.get('OPENAI_API_URL', 'https://api.openai.com/v1/chat/completions')
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY', '')
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.max_summary_tokens = max_summary_tokens
        self.min_history_length = min_history_length

    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return "remote"

    def get_priority(self) -> int:
        """获取优先级 (远程压缩优先级中等)"""
        return 75

    def get_description(self) -> str:
        """获取策略描述"""
        return f"远程 API 压缩 - 使用 {self.model} 生成摘要"

    def can_compress(self, messages: List[Dict[str, Any]], token_count: int) -> bool:
        """
        检查是否可以使用远程压缩。

        条件:
        1. 消息格式有效
        2. 历史消息数 >= min_history_length
        3. API 配置有效

        参数:
            messages: 当前消息列表
            token_count: 当前 Token 数

        返回:
            True 如果可以压缩
        """
        if not self.validate_messages(messages):
            return False

        # 统计非系统消息
        non_system = [m for m in messages if m.get('role') != 'system']

        # 检查历史消息数
        if len(non_system) < self.min_history_length:
            return False

        # 检查 API 配置
        if not self.api_key:
            return False

        return True

    def compress(
        self,
        messages: List[Dict[str, Any]],
        target_tokens: int,
        keep_recent: int = 10,
    ) -> CompressionResult:
        """
        执行远程压缩。

        流程:
        1. 提取系统消息
        2. 提取历史消息
        3. 提取最近消息
        4. 调用远程 API 生成摘要
        5. 组装压缩后的消息

        参数:
            messages: 当前消息列表
            target_tokens: 目标 Token 数
            keep_recent: 保留最近的消息数

        返回:
            CompressionResult 压缩结果
        """
        if not self.validate_messages(messages):
            return CompressionResult(
                success=False,
                compressed_messages=messages,
                original_tokens=estimate_tokens(str(messages)),
                compressed_tokens=estimate_tokens(str(messages)),
                strategy_name=self.get_strategy_name(),
                metadata={"error": "Invalid message format"},
            )

        # 1. 提取消息
        system_messages = self.extract_system_messages(messages)
        history_messages = self.extract_history_messages(messages, keep_recent)
        recent_messages = self.extract_recent_messages(messages, keep_recent)

        # 计算原始 Token 数
        original_tokens = estimate_tokens(str(messages))

        # 2. 调用远程 API 生成摘要
        summary, api_metadata = self._call_remote_api(history_messages)

        # 计算摘要 Token 数
        summary_tokens = estimate_tokens(summary) if summary else 0

        # 3. 组装压缩后的消息
        compressed_messages = []

        # 添加系统消息
        compressed_messages.extend(system_messages)

        # 添加摘要消息
        if summary:
            compressed_messages.append({
                'role': 'assistant',
                'content': summary,
            })

        # 添加最近消息
        compressed_messages.extend(recent_messages)

        # 计算压缩后 Token 数
        compressed_tokens = estimate_tokens(str(compressed_messages))

        # 4. 检查是否达到目标
        success = compressed_tokens <= target_tokens or compressed_tokens < original_tokens

        return CompressionResult(
            success=success,
            compressed_messages=compressed_messages,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            strategy_name=self.get_strategy_name(),
            metadata={
                "summary_tokens": summary_tokens,
                "history_messages": len(history_messages),
                "recent_messages": len(recent_messages),
                "keep_recent": keep_recent,
                "api_metadata": api_metadata,
            },
        )

    def _call_remote_api(
        self,
        history_messages: List[Dict[str, Any]],
    ) -> tuple:
        """
        调用远程 API 生成摘要。

        参数:
            history_messages: 历史消息列表

        返回:
            (摘要文本, API 元数据)
        """
        if not history_messages:
            return "", {}

        # 构建历史文本
        history_text = self._format_history(history_messages)

        # 构建请求
        request_body = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "请将以下对话历史压缩成简洁的摘要，保留关键信息。"
                },
                {
                    "role": "user",
                    "content": history_text
                }
            ],
            "max_tokens": self.max_summary_tokens,
            "temperature": 0.3,
        }

        # 调用 API (带重试)
        for attempt in range(self.max_retries):
            try:
                response = self._make_api_request(request_body)
                if response:
                    summary = response.get('choices', [{}])[0].get('message', {}).get('content', '')
                    metadata = {
                        "attempt": attempt + 1,
                        "model": self.model,
                        "usage": response.get('usage', {}),
                    }
                    return summary, metadata
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return "", {"error": str(e), "attempt": attempt + 1}
                time.sleep(1 * (attempt + 1))  # 指数退避

        return "", {"error": "Max retries exceeded"}

    def _format_history(self, history_messages: List[Dict[str, Any]]) -> str:
        """
        格式化历史消息。

        参数:
            history_messages: 历史消息列表

        返回:
            格式化的历史文本
        """
        parts = []
        for msg in history_messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            if content:
                parts.append(f"[{role}]: {content[:500]}")
        return "\n".join(parts)

    def _make_api_request(self, request_body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        发送 API 请求。

        参数:
            request_body: 请求体

        返回:
            响应字典，如果失败返回 None
        """
        try:
            import urllib.request
            import urllib.error

            # 准备请求
            data = json.dumps(request_body).encode('utf-8')
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}',
            }

            # 创建请求
            req = urllib.request.Request(
                self.api_url,
                data=data,
                headers=headers,
                method='POST',
            )

            # 发送请求
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)

        except urllib.error.HTTPError as e:
            raise Exception(f"HTTP Error: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            raise Exception(f"URL Error: {e.reason}")
        except Exception as e:
            raise Exception(f"Request Error: {str(e)}")
