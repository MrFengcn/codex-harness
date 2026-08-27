# Codex Harness — 超级 AI 智能体增强技能

> 🚀 Super Skill for AI Agents — 用 OpenAI Codex 能力增强 AI 智能体
>
> 支持 15 种主流 Agent 框架 | 中国网络智能适配 | 25+ 功能模块

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Agents](https://img.shields.io/badge/Agents-15-green.svg)](#支持的智能体)
[![Modules](https://img.shields.io/badge/Modules-25+-orange.svg)](#模块列表)

**作者**: Walter | **许可证**: MIT (仅限个人使用) | **项目地址**: https://github.com/MrFengcn/codex-harness

---

## 📖 项目介绍

Codex Harness 是一个**超级 AI 智能体增强技能**，它将 OpenAI Codex 的核心能力抽象为可复用的模块，让任何 AI 智能体都能获得强大的编码能力。

### ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🤖 **15 种 Agent 支持** | 支持 Hermes、Cursor、Claude Code、Trae、Qoder、CodeBuddy、Comate、DeepSeek 等国内外主流 AI 开发工具 |
| 🇨🇳 **中国网络智能适配** | 自动检测中国网络，将 OpenAI/Google/GitHub 等服务替换为 DeepSeek/百度/Gitee 等国内服务 |
| 🛡️ **安全防护** | 命令验证、路径遍历防护、敏感文件检测、Shell 注入防护 |
| 📦 **25+ 功能模块** | 压缩、补丁、安全检查、记忆提取、Agent 通信、MCP 协议等 |
| 🔧 **易于集成** | 简单 API，无需修改核心代码，即插即用 |

### 🎯 适用场景

- ✅ 代码编辑和补丁应用
- ✅ 安全检查和风险评估
- ✅ 上下文管理和压缩
- ✅ 记忆提取和管理
- ✅ 多 Agent 协作
- ✅ 中国网络环境下的 AI 开发

---

## 🤖 支持的智能体

### 国际工具

| Agent | 版本 | 开发商 | 说明 |
|-------|------|--------|------|
| [Hermes](https://hermes-agent.nousresearch.com) | 0.20.0+ | Nous Research | 开源 AI Agent 框架 |
| [Cursor](https://cursor.sh) | 0.1.0+ | Cursor Inc | AI 代码编辑器 (VS Code fork) |
| [Claude Code](https://docs.anthropic.com) | 0.1.0+ | Anthropic | CLI AI 编程工具 |
| [LangChain](https://langchain.com) | 0.1.0+ | LangChain | LLM 应用开发框架 |
| [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) | 0.1.0+ | 开源 | 自主 AI Agent |
| [MetaGPT](https://github.com/geekan/MetaGPT) | 0.1.0+ | 开源 | 多 Agent 协作框架 |
| [CrewAI](https://github.com/joaomdmoura/crewai) | 0.1.0+ | 开源 | Agent 团队协作框架 |
| [BabyAGI](https://github.com/yoheinakajima/babyagi) | 0.1.0+ | 开源 | 任务驱动 AI Agent |
| [AgentGPT](https://github.com/reworkd/AgentGPT) | 0.1.0+ | 开源 | 自主 AI Agent |

### 国内工具

| Agent | 版本 | 开发商 | 说明 |
|-------|------|--------|------|
| [Trae](https://www.trae.ai) | 0.1.0+ | 字节跳动 | AI IDE |
| [Qoder](https://qoder.aliyun.com) | 0.1.0+ | 阿里巴巴 | AI 编程助手 |
| [CodeBuddy](https://cloud.tencent.com/product/codebuddy) | 0.1.0+ | 腾讯 | AI 编程助手 |
| [Comate](https://comate.baidu.com) | 0.1.0+ | 百度 | AI 编程助手 |
| [DeepSeek](https://www.deepseek.com) | 0.1.0+ | DeepSeek | AI 大模型 |
| [OpenClaw](https://github.com/openclaw) | 1.0.0+ | 开源 | AI Agent 框架 |

---

## 🇨🇳 中国网络智能适配

Codex Harness 会自动检测用户网络环境，如果是**中国大陆网络**，会自动将受限服务替换为国内可用服务：

| 服务类型 | 国际版 | 中国替代 |
|----------|--------|----------|
| **LLM API** | OpenAI GPT | DeepSeek / 通义千问 / 文心一言 |
| **代码托管** | GitHub | Gitee |
| **模型仓库** | HuggingFace | 魔搭社区 (ModelScope) |
| **包管理** | PyPI | 清华镜像 / 阿里镜像 |
| **搜索引擎** | Google | 百度 / Bing |

### 网络检测方式

1. **DNS 检测** — 通过 DNS 解析判断网络类型
2. **HTTP 检测** — 通过访问特定网站判断
3. **IP 地理位置** — 通过 IP 地址判断地理位置

三种方式综合投票，确保检测准确。

---

## 📦 安装方法

### 方法一：Git 克隆（推荐）

```bash
# 克隆仓库
git clone https://github.com/MrFengcn/codex-harness.git

# 复制到技能目录
cp -r codex-harness ~/.hermes/skills/
```

### 方法二：下载 ZIP

1. 访问 https://github.com/MrFengcn/codex-harness
2. 点击绿色 "Code" 按钮
3. 选择 "Download ZIP"
4. 解压到 `~/.hermes/skills/codex-harness/`

### 方法三：一句话安装（让 AI 自动安装）

将以下命令发送给你的 AI 智能体：

**Hermes Agent:**
```
查看 https://github.com/MrFengcn/codex-harness 页面项目，帮我以 README 说明里的方式安装 codex-harness skill，这个 skill 是用来增强 AI 智能体的编码能力的，在需要进行代码编辑、安全检查或多智能体协作时切换或使用
```

**Cursor:**
```
查看 https://github.com/MrFengcn/codex-harness 页面项目，帮我集成 codex-harness，这个工具是用来增强 Cursor 编辑器能力的，在需要进行代码编辑时使用
```

**Claude Code:**
```
查看 https://github.com/MrFengcn/codex-harness 页面项目，帮我安装 codex-harness skill，这个 skill 是用来增强 Claude Code 能力的，在需要进行复杂编码任务时使用
```

**Trae:**
```
查看 https://github.com/MrFengcn/codex-harness 页面项目，帮我集成 codex-harness，这个工具是用来增强 Trae IDE 能力的，在需要进行代码编辑时使用
```

**Qoder:**
```
查看 https://github.com/MrFengcn/codex-harness 页面项目，帮我安装 codex-harness skill，这个 skill 是用来增强 Qoder 编程助手能力的，在需要进行代码编辑时使用
```

**CodeBuddy:**
```
查看 https://github.com/MrFengcn/codex-harness 页面项目，帮我集成 codex-harness，这个工具是用来增强 CodeBuddy 编程助手能力的，在需要进行代码编辑时使用
```

**Comate:**
```
查看 https://github.com/MrFengcn/codex-harness 页面项目，帮我安装 codex-harness skill，这个 skill 是用来增强 Comate 编程助手能力的，在需要进行代码编辑时使用
```

**DeepSeek:**
```
查看 https://github.com/MrFengcn/codex-harness 页面项目，帮我集成 codex-harness，这个工具是用来增强 DeepSeek 能力的，在需要进行复杂编码任务时使用
```

---

## 🚀 快速开始

### 基本使用

```python
# 导入模块
from compression import CompressionManager
from safety import SafetyManager
from rollout import RolloutExtractor

# 创建实例
compression = CompressionManager()
safety = SafetyManager()
memory = RolloutExtractor()

# 安全检查
result = safety.check_operation('terminal', {'command': 'ls -la'})
print(f'安全检查: {result.is_safe}')  # True
```

### 网络检测

```python
from network_detector import is_china_network, get_global_network_detector

# 检查是否是中国网络
if is_china_network():
    print("当前是中国网络，将使用国内服务")
else:
    print("当前是国际网络")

# 获取详细网络信息
detector = get_global_network_detector()
info = detector.get_network_info()
print(f"网络类型: {info['type']}")
```

### 服务自动切换

```python
from service_registry import ServiceAdapter, ServiceType

# 创建适配器
adapter = ServiceAdapter()

# 获取最佳 LLM 服务（自动根据网络选择）
llm = adapter.get_llm_service()
print(f"使用 LLM: {llm.name}")
# 中国网络: DeepSeek
# 国际网络: OpenAI

# 获取最佳代码托管服务
code = adapter.get_code_hosting_service()
print(f"代码托管: {code.name}")
# 中国网络: Gitee
# 国际网络: GitHub
```

### 多 Agent 支持

```python
from agent_adapter import get_global_adapter_manager

# 获取适配器管理器
manager = get_global_adapter_manager()

# 列出所有可用适配器
adapters = manager.list_adapters()
print(f"可用适配器: {adapters}")

# 获取特定适配器
hermes = manager.get_adapter('hermes')
cursor = manager.get_adapter('cursor')
deepseek = manager.get_adapter('deepseek')

# 使用适配器接口
memory = hermes.get_memory()
memory.store('key', 'value')
value = memory.retrieve('key')
```

---

## 📚 模块列表

### 核心模块

| 模块 | 说明 | 用法 |
|------|------|------|
| `compression/` | 上下文压缩系统 | 管理对话上下文窗口 |
| `patch/` | 代码补丁系统 | 安全地应用代码补丁 |
| `safety/` | 安全检查系统 | 评估操作安全性 |
| `canonicalization/` | 命令规范化 | 标准化命令用于审批缓存 |
| `rollout/` | 记忆提取 | 从会话历史提取结构化记忆 |

### 网络和服务

| 模块 | 说明 | 用法 |
|------|------|------|
| `network_detector/` | 网络检测系统 | 检测中国/国际网络 |
| `service_registry/` | 服务替换系统 | 根据网络自动切换服务 |

### 通信模块

| 模块 | 说明 | 用法 |
|------|------|------|
| `communication/` | Agent 通信 | 代理间消息传递 |
| `agents_md/` | AGENTS.md 配置 | 解析和管理项目配置 |
| `connectors/` | 外部连接器 | 外部应用连接器 |
| `event_mapping/` | 事件映射 | 事件类型和映射规则 |

### 工具模块

| 模块 | 说明 | 用法 |
|------|------|------|
| `function_tool/` | 函数工具 | 函数工具定义和管理 |
| `hook_runtime/` | Hook 运行时 | Hook 生命周期管理 |
| `mcp/` | MCP 协议 | Model Context Protocol |
| `shell/` | Shell 集成 | Shell 命令执行 |
| `skills/` | 技能系统 | 技能加载和执行 |

### 管理模块

| 模块 | 说明 | 用法 |
|------|------|------|
| `thread_manager/` | 线程管理器 | 并发线程管理 |
| `elicitation/` | 引导系统 | 用户交互引导 |
| `realtime/` | 实时系统 | 实时事件流 |
| `responses/` | 响应系统 | 响应格式化 |
| `turn/` | Turn 管理 | 对话 Turn 管理 |
| `web_search/` | Web 搜索 | Web 搜索能力 |

### Agent 适配器

| 模块 | 说明 | 用法 |
|------|------|------|
| `agent_adapter/` | 多 Agent 支持 | 支持 15 种 Agent 框架 |

---

## 🛡️ 安全特性

| 特性 | 说明 |
|------|------|
| ✅ 命令验证 | 检查危险命令模式 |
| ✅ 路径遍历防护 | 阻止 `..` 路径攻击 |
| ✅ 敏感文件检测 | 检测 `.env`, `id_rsa` 等 |
| ✅ Shell 注入防护 | 防止命令注入攻击 |
| ✅ 危险命令阻止 | 阻止 `rm -rf /` 等危险命令 |

---

## 📊 项目统计

| 指标 | 数值 |
|------|------|
| Python 文件 | 108 |
| 总代码行数 | 25,538 |
| 功能模块 | 25+ |
| 支持 Agent | 15 |
| 测试通过率 | 100% |

---

## 🔧 配置

### 环境变量（可选）

```bash
# 中国 LLM 服务 API Key
export DEEPSEEK_API_KEY="your-key"
export DASHSCOPE_API_KEY="your-key"      # 通义千问
export ERNIE_API_KEY="your-key"          # 文心一言

# 中国代码托管
export GITEE_TOKEN="your-token"

# 中国模型仓库
export MODELSCOPE_TOKEN="your-token"

# 国际服务（如果不使用中国网络）
export OPENAI_API_KEY="your-key"
export GITHUB_TOKEN="your-token"
```

### 强制网络类型

```python
from network_detector import NetworkConfig

# 强制使用中国网络
config = NetworkConfig(force_china=True)

# 强制使用国际网络
config = NetworkConfig(force_international=True)
```

---

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'Add your feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 创建 Pull Request

### 标注要求

修改或再分发本软件时，**必须**包含以下标注：

```markdown
Based on Codex Harness by Walter
Source: https://github.com/MrFengcn/codex-harness
```

---

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)，但有以下限制：

| 使用场景 | 是否允许 |
|----------|----------|
| ✅ 个人使用 | 免费 |
| ❌ 商业使用 | 禁止 |
| ✅ 修改 | 需标注来源 |
| ✅ 再分发 | 需标注来源 |
| ✅ 私人使用 | 允许 |

---

## 🙏 致谢

- [OpenAI Codex](https://github.com/openai/codex) — 灵感来源
- [Hermes Agent](https://hermes-agent.nousresearch.com) — 运行平台
- 所有支持的 Agent 框架

---

## 📞 联系方式

- **作者**: Walter
- **GitHub**: [MrFengcn](https://github.com/MrFengcn)
- **项目**: [codex-harness](https://github.com/MrFengcn/codex-harness)
- **问题反馈**: [Issues](https://github.com/MrFengcn/codex-harness/issues)

---

## ⭐ Star History

如果这个项目对你有帮助，请给个 Star ⭐ 支持一下！

---

*最后更新: 2026-08-24*
