#!/usr/bin/env python3
"""
Codex Harness — 远程压缩策略 V2

支持流式响应和更好的错误处理。
对应 Codex 的 compact_remote_v2.rs。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from typing import List, Dict, Any, Optional
from compression.base import CompressionResult
from compression.remote import RemoteCompression
from core import estimate_tokens


# ============================================================================
# 远程压缩策略 V2
# ============================================================================

class RemoteCompressionV2(RemoteCompression):
    """
    远程压缩策略 V2。
    对应 Codex 的 compact_remote_v2.rs。

    在 V1 基础上增加:
    - 流式响应支持
    - 更好的错误处理
    - Token 预算管理
    - 重试状态跟踪
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        max_retries: int = 3,
        timeout: int = 60,
        max_summary_tokens: int = 2000,
        min_history_length: int = 3,
        retained_message_token_budget: int = 64000,
        max_retained_agent_message_tokens: int = 10000,
        max_stream_retries: int = 2,
        enable_streaming: bool = True,
    ):
        """
        初始化远程压缩策略 V2。

        参数:
            api_url: API URL
            api_key: API 密钥
            model: 使用的模型
            max_retries: 最大重试次数
            timeout: 超时时间 (秒)
            max_summary_tokens: 摘要最大 Token 数
            min_history_length: 最小历史消息数
            retained_message_token_budget: 保留消息 Token 预算
            max_retained_agent_message_tokens: 最大保留代理消息 Token 数
            max_stream_retries: 最大流式重试次数
            enable_streaming: 启用流式响应
        """
        super().__init__(
            api_url=api_url,
            api_key=api_key,
            model=model,
            max_retries=max_retries,
            timeout=timeout,
            max_summary_tokens=max_summary_tokens,
            min_history_length=min_history_length,
        )
        self.retained_message_token_budget = retained_message_token_budget
        self.max_retained_agent_message_tokens = max_retained_agent_message_tokens
        self.max_stream_retries = max_stream_retries
        self.enable_streaming = enable_streaming

    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return "remote_v2"

    def get_priority(self) -> int:
        """获取优先级 (V2 优先级更高)"""
        return 70

    def get_description(self) -> str:
        """获取策略描述"""
        return f"远程 API 压缩 V2 - 流式响应，Token 预算管理"

    def compress(
        self,
        messages: List[Dict[str, Any]],
        target_tokens: int,
        keep_recent: int = 10,
    ) -> CompressionResult:
        """
        执行远程压缩 V2。

        流程:
        1. 提取消息
        2. 计算 Token 预算
        3. 调用远程 API (流式或非流式)
        4. 处理响应
        5. 组装结果

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

        # 2. 计算 Token 预算
        token_budget = self._calculate_token_budget(
            target_tokens,
            len(system_messages),
            len(recent_messages),
        )

        # 3. 调用远程 API
        if self.enable_streaming:
            summary, api_metadata = self._call_remote_api_streaming(history_messages, token_budget)
        else:
            summary, api_metadata = self._call_remote_api(history_messages)

        # 计算摘要 Token 数
        summary_tokens = estimate_tokens(summary) if summary else 0

        # 4. 组装压缩后的消息
        compressed_messages = []

        # 添加系统消息
        compressed_messages.extend(system_messages)

        # 添加摘要消息
        if summary:
            compressed_messages.append({
                'role': 'assistant',
                'content': summary,
            })

        # 添加最近消息 (检查 Token 预算)
        recent_tokens = estimate_tokens(str(recent_messages))
        if recent_tokens > self.max_retained_agent_message_tokens:
            # 截断最近消息
            recent_messages = self._truncate_messages(
                recent_messages,
                self.max_retained_agent_message_tokens,
            )

        compressed_messages.extend(recent_messages)

        # 计算压缩后 Token 数
        compressed_tokens = estimate_tokens(str(compressed_messages))

        # 5. 检查是否达到目标
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
                "token_budget": token_budget,
                "api_metadata": api_metadata,
                "streaming": self.enable_streaming,
            },
        )

    def _calculate_token_budget(
        self,
        target_tokens: int,
        system_count: int,
        recent_count: int,
    ) -> int:
        """
        计算 Token 预算。

        参数:
            target_tokens: 目标 Token 数
            system_count: 系统消息数
            recent_count: 最近消息数

        返回:
            Token 预算
        """
        # 估算系统消息和最近消息的 Token 数
        estimated_system_tokens = system_count * 500  # 估算每条系统消息 500 Token
        estimated_recent_tokens = recent_count * 1000  # 估算每条最近消息 1000 Token

        # 计算可用于摘要的 Token 数
        available_tokens = target_tokens - estimated_system_tokens - estimated_recent_tokens

        # 限制在合理范围内
        available_tokens = max(1000, min(available_tokens, self.max_summary_tokens))

        return available_tokens

    def _call_remote_api_streaming(
        self,
        history_messages: List[Dict[str, Any]],
        token_budget: int,
    ) -> tuple:
        """
        调用远程 API (流式响应)。

        参数:
            history_messages: 历史消息列表
            token_budget: Token 预算

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
            "max_tokens": token_budget,
            "temperature": 0.3,
            "stream": True,
        }

        # 调用 API (带重试)
        for attempt in range(self.max_stream_retries):
            try:
                response = self._make_api_request_streaming(request_body)
                if response:
                    summary = response.get('summary', '')
                    metadata = {
                        "attempt": attempt + 1,
                        "model": self.model,
                        "streaming": True,
                        "usage": response.get('usage', {}),
                    }
                    return summary, metadata
            except Exception as e:
                if attempt == self.max_stream_retries - 1:
                    return "", {"error": str(e), "attempt": attempt + 1, "streaming": True}
                time.sleep(1 * (attempt + 1))

        return "", {"error": "Max stream retries exceeded", "streaming": True}

    def _make_api_request_streaming(self, request_body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        发送 API 请求 (流式响应)。

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

            # 发送请求并处理流式响应
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                full_content = ""
                usage = {}

                for line in response:
                    line = line.decode('utf-8').strip()
                    if not line:
                        continue

                    # 解析 SSE 格式
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break

                        try:
                            data = json.loads(data_str)
                            choices = data.get('choices', [])
                            if choices:
                                delta = choices[0].get('delta', {})
                                content = delta.get('content', '')
                                full_content += content

                                # 检查是否有 usage 信息
                                if 'usage' in data:
                                    usage = data['usage']
                        except json.JSONDecodeError:
                            continue

                return {
                    "summary": full_content,
                    "usage": usage,
                }

        except urllib.error.HTTPError as e:
            raise Exception(f"HTTP Error: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            raise Exception(f"URL Error: {e.reason}")
        except Exception as e:
            raise Exception(f"Request Error: {str(e)}")

    def _truncate_messages(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int,
    ) -> List[Dict[str, Any]]:
        """
        截断消息到指定 Token 数。

        参数:
            messages: 消息列表
            max_tokens: 最大 Token 数

        返回:
            截断后的消息列表
        """
        truncated = []
        current_tokens = 0

        for msg in messages:
            msg_tokens = estimate_tokens(str(msg))
            if current_tokens + msg_tokens > max_tokens:
                # 截断这条消息
                content = msg.get('content', '')
                if content:
                    # 估算可以保留多少字符
                    chars_per_token = 4
                    max_chars = (max_tokens - current_tokens) * chars_per_token
                    if max_chars > 0:
                        truncated_content = content[:max_chars] + "...[truncated]"
                        truncated_msg = msg.copy()
                        truncated_msg['content'] = truncated_content
                        truncated.append(truncated_msg)
                break

            truncated.append(msg)
            current_tokens += msg_tokens

        return truncated
