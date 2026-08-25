# 压缩系统深度文档

> 对应 Codex: codex-rs/core/src/compact*.rs
> 实现: scripts/compression/

## 概述

压缩系统负责管理对话上下文窗口，当上下文超过 Token 预算时自动触发压缩。支持多种压缩策略，可根据配置自动选择最佳策略。

## 核心概念

### 1. 压缩策略 (CompressionStrategy)

所有压缩策略的抽象基类，定义统一接口：

```python
class CompressionStrategy(ABC):
    def can_compress(messages, token_count) -> bool
    def compress(messages, target_tokens, keep_recent) -> CompressionResult
    def get_strategy_name() -> str
    def get_priority() -> int
```

### 2. 压缩结果 (CompressionResult)

```python
class CompressionResult:
    success: bool                    # 是否成功
    compressed_messages: List[Dict]  # 压缩后的消息
    original_tokens: int             # 原始 Token 数
    compressed_tokens: int           # 压缩后 Token 数
    strategy_name: str               # 使用的策略
    compression_ratio: float         # 压缩率 (0.0-1.0)
    tokens_saved: int                # 节省的 Token 数
```

### 3. 压缩管理器 (CompressionManager)

统一管理所有压缩策略：

```python
class CompressionManager:
    def register_strategy(strategy)
    def should_compress(token_count, max_tokens) -> bool
    def compress(messages, target_tokens, keep_recent) -> CompressionResult
    def get_compression_stats() -> Dict
```

## 压缩策略

### 1. TokenBudgetCompression (Token 预算压缩)

**优先级**: 10 (最高)

**特点**:
- 不调用 LLM 生成摘要
- 直接截断历史消息
- 保留最近的 N 条消息
- 速度最快

**适用场景**:
- 需要快速压缩
- 不需要高质量摘要
- Token 预算紧张

```python
from compression import TokenBudgetCompression

strategy = TokenBudgetCompression()
result = strategy.compress(messages, target_tokens=1000, keep_recent=10)
```

### 2. LocalCompression (本地压缩)

**优先级**: 50

**特点**:
- 使用本地 LLM 生成摘要
- 保留关键信息
- 质量较高

**适用场景**:
- 需要高质量摘要
- 有本地 LLM 可用
- 对压缩质量要求高

```python
from compression import LocalCompression

strategy = LocalCompression(max_summary_tokens=2000)
result = strategy.compress(messages, target_tokens=1000, keep_recent=10)
```

### 3. RemoteCompressionV2 (远程压缩 V2)

**优先级**: 70

**特点**:
- 调用远程 API 进行压缩
- 支持流式响应
- Token 预算管理
- 质量最高

**适用场景**:
- 需要最高质量摘要
- 有远程 API 可用
- 网络稳定

```python
from compression import RemoteCompressionV2

strategy = RemoteCompressionV2(
    api_url="https://api.openai.com/v1/chat/completions",
    api_key="your-api-key",
    model="gpt-4",
)
result = strategy.compress(messages, target_tokens=1000, keep_recent=10)
```

### 4. RemoteCompression (远程压缩)

**优先级**: 75

**特点**:
- 调用远程 API 进行压缩
- 支持重试机制
- 质量较高

**适用场景**:
- 需要高质量摘要
- 有远程 API 可用
- 网络稳定

```python
from compression import RemoteCompression

strategy = RemoteCompression(
    api_url="https://api.openai.com/v1/chat/completions",
    api_key="your-api-key",
    model="gpt-4",
)
result = strategy.compress(messages, target_tokens=1000, keep_recent=10)
```

### 5. ModelFallbackCompression (模型回退压缩)

**优先级**: 200 (最低)

**特点**:
- 当主策略失败时回退到备用策略
- 支持多级回退
- 记录回退事件

**适用场景**:
- 需要高可用性
- 多种压缩策略可用
- 需要容错机制

```python
from compression import ModelFallbackCompression, LocalCompression, TokenBudgetCompression

primary = LocalCompression()
fallback = TokenBudgetCompression()

strategy = ModelFallbackCompression(
    primary_strategy=primary,
    fallback_strategies=[fallback],
)
result = strategy.compress(messages, target_tokens=1000, keep_recent=10)
```

## 配置

### CompressionConfig

```python
from compression import CompressionConfig

config = CompressionConfig(
    compression_threshold=0.8,  # 触发压缩的 Token 比例
    keep_recent=10,             # 保留最近的消息数
    max_summary_tokens=2000,    # 摘要最大 Token 数
    enable_local=True,          # 启用本地压缩
    enable_remote=False,        # 启用远程压缩
    enable_remote_v2=False,     # 启用远程压缩 V2
    enable_fallback=True,       # 启用回退压缩
    remote_api_url=None,        # 远程 API URL
    remote_api_key=None,        # 远程 API 密钥
    remote_model="gpt-4",       # 远程模型
    enable_hooks=True,          # 启用 Hook
)
```

## 使用方式

### 基本使用

```python
from compression import CompressionManager, CompressionConfig

# 创建配置
config = CompressionConfig(
    compression_threshold=0.8,
    keep_recent=10,
)

# 创建管理器
manager = CompressionManager(config)

# 检查是否需要压缩
if manager.should_compress(current_tokens, max_tokens):
    # 执行压缩
    result = manager.compress(messages, target_tokens, keep_recent)
    if result.success:
        print(f"压缩率: {result.compression_ratio:.1%}")
        print(f"节省: {result.tokens_saved} tokens")
```

### 集成到 context_manager.py

```python
from context_manager import ContextCompressionManager

# 创建管理器
manager = ContextCompressionManager(
    max_tokens=128000,
    compression_threshold=0.8,
    keep_recent=10,
)

# 检查并压缩
result = manager.check_and_compress(messages, current_tokens=100000)
if result:
    print(f"压缩率: {result.savings_pct:.1f}%")
```

### 集成 Hook

```python
from compression import CompressionManager, CompressionConfig
from hook_engine import HookEngine, HookDef

# 创建 Hook 引擎
hook_engine = HookEngine()
hook_engine.add_hook(HookDef(
    name='log_compact',
    event='PreCompact',
    command='echo "Compacting..."',
))

# 创建压缩管理器
config = CompressionConfig(enable_hooks=True)
manager = CompressionManager(config)
manager.set_hook_engine(hook_engine)

# 压缩时自动触发 Hook
result = manager.compress(messages, target_tokens=1000)
```

## 压缩流程

```
1. 检查是否需要压缩 (should_compress)
   ↓ 是
2. 触发 PreCompact Hook
   ↓
3. 选择策略 (按优先级)
   ↓
4. 执行压缩
   ↓
5. 记录历史
   ↓
6. 触发 PostCompact Hook
   ↓
7. 返回结果
```

## 策略选择逻辑

```
1. TokenBudgetCompression (优先级 10)
   - 最快，无 LLM 调用
   ↓
2. LocalCompression (优先级 50)
   - 本地 LLM 摘要
   ↓
3. RemoteCompressionV2 (优先级 70)
   - 远程 API 流式压缩
   ↓
4. RemoteCompression (优先级 75)
   - 远程 API 压缩
   ↓
5. ModelFallbackCompression (优先级 200)
   - 回退策略
```

## 与 Codex 的对应关系

| Codex 模块 | 我们的实现 | 说明 |
|-----------|-----------|------|
| compact.rs | local.py | 本地 LLM 压缩 |
| compact_remote.rs | remote.py | 远程 API 压缩 |
| compact_remote_v2.rs | remote_v2.py | 远程压缩 V2 |
| compact_token_budget.rs | token_budget.py | Token 预算压缩 |
| compact_model_fallback.rs | fallback.py | 模型回退压缩 |
| CompressionManager | manager.py | 压缩管理器 |
| PreCompact/PostCompact Hook | hook_engine.py | Hook 集成 |

## 性能指标

| 策略 | 速度 | 质量 | 依赖 |
|------|------|------|------|
| TokenBudgetCompression | ⚡ 最快 | ⭐⭐ 低 | 无 |
| LocalCompression | 🐢 慢 | ⭐⭐⭐⭐ 高 | 本地 LLM |
| RemoteCompression | 🐢 慢 | ⭐⭐⭐⭐⭐ 最高 | 远程 API |
| RemoteCompressionV2 | 🐢 慢 | ⭐⭐⭐⭐⭐ 最高 | 远程 API |
| ModelFallbackCompression | ⚡ 快 | ⭐⭐⭐ 中 | 依赖主策略 |

## 故障排除

### 问题: 压缩率过低

**原因**: 消息太小，压缩无意义

**解决**: 增加消息数量或减少目标 Token 数

### 问题: 压缩失败

**原因**: 所有策略都失败

**解决**: 检查 API 配置，确保至少有一个可用策略

### 问题: 压缩质量低

**原因**: 使用了 TokenBudgetCompression

**解决**: 启用 LocalCompression 或 RemoteCompression

## 文件结构

```
scripts/compression/
├── __init__.py           # 模块初始化
├── base.py               # 基类和结果类
├── local.py              # 本地压缩策略
├── remote.py             # 远程压缩策略
├── remote_v2.py          # 远程压缩策略 V2
├── fallback.py           # 模型回退压缩策略
├── token_budget.py       # Token 预算压缩策略
└── manager.py            # 压缩管理器
```
