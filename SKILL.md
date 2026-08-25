---
name: codex-harness
description: "Use when you need enhanced coding capabilities including compression, patching, safety checks, memory extraction, agent communication, and multi-agent support. Provides OpenAI Codex-like superpowers to AI Agents."
triggers:
  - "code editing"
  - "patch application"
  - "safety check"
  - "memory management"
  - "agent communication"
  - "multi-agent"
  - "tool orchestration"
---

# Codex Harness — Super Skill

> 🚀 Enhance AI Agents with OpenAI Codex capabilities
> 
> 🚀 用 OpenAI Codex 能力增强 AI 智能体

**Author / 作者**: Walter
**Source / 源码**: https://github.com/MrFengcn/codex-harness
**License / 许可证**: MIT (Personal Use Only / 仅限个人使用)

---

## 📖 Overview / 概述

Codex Harness is a super skill that enhances AI Agents with OpenAI Codex capabilities. It provides 20+ modules covering compression, patching, safety checks, memory extraction, agent communication, and multi-agent support.

Codex Harness 是一个超级技能，用 OpenAI Codex 能力增强 AI 智能体。它提供 20+ 个模块，涵盖压缩、补丁、安全检查、记忆提取、智能体通信和多智能体支持。

### Supported Agents / 支持的智能体

| Agent | Version | Status |
|-------|---------|--------|
| Hermes | 0.20.0+ | ✅ Fully Supported |
| OpenClaw | 1.0.0+ | ✅ Fully Supported |
| LangChain | 0.1.0+ | ✅ Supported |
| AutoGPT | 0.1.0+ | ✅ Supported |
| MetaGPT | 0.1.0+ | ✅ Supported |
| CrewAI | 0.1.0+ | ✅ Supported |
| BabyAGI | 0.1.0+ | ✅ Supported |
| AgentGPT | 0.1.0+ | ✅ Supported |

---

## 🎯 One-Line Deployment / 一句话部署

### For Hermes Agent / 对于 Hermes 智能体

```
查看 https://github.com/MrFengcn/codex-harness 页面项目，帮我以 README 说明里的方式安装 codex-harness skill，这个 skill 是用来增强 AI 智能体的编码能力的，提供压缩、补丁、安全检查、记忆提取等功能，在需要进行代码编辑、安全检查或多智能体协作时切换或使用
```

### For OpenClaw / 对于 OpenClaw

```
查看 https://github.com/MrFengcn/codex-harness 页面项目，帮我安装 codex-harness skill，这个 skill 是用来增强智能体能力的，提供工具调用、记忆管理、安全检查等功能，在需要进行复杂编码任务时使用
```

### For LangChain / 对于 LangChain

```
查看 https://github.com/MrFengcn/codex-harness 页面项目，帮我集成 codex-harness，这个工具是用来增强 LangChain Agent 能力的，提供压缩、补丁、安全检查等功能，在需要进行代码编辑时使用
```

---

## 📦 Installation / 安装

### Method 1: Clone Repository / 方法一：克隆仓库

```bash
# Clone the repository / 克隆仓库
git clone https://github.com/MrFengcn/codex-harness.git

# Copy to skills directory / 复制到技能目录
cp -r codex-harness ~/.hermes/skills/
```

### Method 2: Download ZIP / 方法二：下载 ZIP

1. Visit https://github.com/MrFengcn/codex-harness
2. Click "Code" → "Download ZIP"
3. Extract to `~/.hermes/skills/codex-harness/`

### Method 3: Using Git Sparse Checkout / 方法三：使用 Git 稀疏检出

```bash
# For minimal install / 最小化安装
git clone --depth 1 https://github.com/MrFengcn/codex-harness.git
cp -r codex-harness ~/.hermes/skills/
```

---

## 🚀 Quick Start / 快速开始

### Basic Usage / 基本使用

```python
# Import the modules you need / 导入需要的模块
from compression import CompressionManager
from safety import SafetyManager
from rollout import RolloutExtractor
from communication import CommunicationManager

# Create instances / 创建实例
compression = CompressionManager()
safety = SafetyManager()
memory = RolloutExtractor()
communication = CommunicationManager()

# Use the modules / 使用模块
result = safety.check_operation('terminal', {'command': 'ls -la'})
print(f'Safety check: {result.is_safe}')
```

### Multi-Agent Support / 多智能体支持

```python
# Import agent adapter / 导入智能体适配器
from agent_adapter import get_global_adapter_manager

# Get adapter manager / 获取适配器管理器
manager = get_global_adapter_manager()

# List available adapters / 列出可用适配器
adapters = manager.list_adapters()
print(f'Available adapters: {adapters}')

# Get specific adapter / 获取特定适配器
hermes = manager.get_adapter('hermes')
openclaw = manager.get_adapter('openclaw')

# Use adapter interfaces / 使用适配器接口
memory = hermes.get_memory()
memory.store('key', 'value')
value = memory.retrieve('key')
```

---

## 📚 Module Reference / 模块参考

### Core Modules / 核心模块

| Module | Description | 说明 |
|--------|-------------|------|
| compression/ | Context compression system | 上下文压缩系统 |
| patch/ | Code patching system | 代码补丁系统 |
| safety/ | Security check system | 安全检查系统 |
| canonicalization/ | Command normalization | 命令规范化 |
| rollout/ | Memory extraction | 记忆提取 |

### Communication Modules / 通信模块

| Module | Description | 说明 |
|--------|-------------|------|
| communication/ | Agent communication | 智能体通信 |
| agents_md/ | AGENTS.md configuration | AGENTS.md 配置 |
| connectors/ | External connectors | 外部连接器 |
| event_mapping/ | Event mapping | 事件映射 |

### Tool Modules / 工具模块

| Module | Description | 说明 |
|--------|-------------|------|
| function_tool/ | Function tools | 函数工具 |
| hook_runtime/ | Hook runtime | Hook 运行时 |
| mcp/ | MCP protocol | MCP 协议 |
| shell/ | Shell integration | Shell 集成 |
| skills/ | Skill system | 技能系统 |

### Management Modules / 管理模块

| Module | Description | 说明 |
|--------|-------------|------|
| thread_manager/ | Thread management | 线程管理器 |
| elicitation/ | User interaction | 用户交互引导 |
| realtime/ | Real-time events | 实时事件 |
| responses/ | Response formatting | 响应格式化 |
| turn/ | Turn management | Turn 管理 |
| web_search/ | Web search | Web 搜索 |

### Agent Adapter / 智能体适配器

| Module | Description | 说明 |
|--------|-------------|------|
| agent_adapter/ | Multi-agent support | 多智能体支持 |

---

## 🔧 Configuration / 配置

### Environment Variables / 环境变量

```bash
# Optional: Set API key for remote compression / 可选：设置远程压缩 API 密钥
export CODEX_HARNESS_API_KEY="your-api-key"

# Optional: Set working directory / 可选：设置工作目录
export CODEX_HARNESS_WORKDIR="/path/to/project"
```

### Configuration File / 配置文件

Create `~/.hermes/skills/codex-harness/config.json`:

```json
{
  "compression": {
    "enable_remote": false,
    "target_tokens": 1000
  },
  "safety": {
    "check_commands": true,
    "check_files": true
  },
  "memory": {
    "enable_extraction": true,
    "max_memories": 1000
  }
}
```

---

## 🛡️ Security / 安全性

### Security Features / 安全特性

- ✅ Command validation / 命令验证
- ✅ Path traversal protection / 路径遍历防护
- ✅ Sensitive file detection / 敏感文件检测
- ✅ Dangerous command blocking / 危险命令阻止
- ✅ Shell injection prevention / Shell 注入防护

### Security Checks / 安全检查

```python
from safety import SafetyManager

safety = SafetyManager()

# Check command safety / 检查命令安全性
result = safety.check_operation('terminal', {'command': 'ls -la'})
print(f'Safe: {result.is_safe}')

# Check file safety / 检查文件安全性
result = safety.check_operation('read_file', {'path': './config.py'})
print(f'Safe: {result.is_safe}')
```

---

## 📊 Statistics / 统计信息

| Metric | Value |
|--------|-------|
| Python Files | 95 |
| Total Lines | 23,329 |
| Modules | 23 |
| Supported Agents | 8 |
| Test Pass Rate | 100% |

---

## 🤝 Contributing / 贡献

1. Fork the repository / Fork 仓库
2. Create your feature branch / 创建功能分支
3. Commit your changes / 提交更改
4. Push to the branch / 推送到分支
5. Open a Pull Request / 创建 Pull Request

### Attribution Requirements / 标注要求

When modifying or redistributing this software, you MUST include:

修改或再分发本软件时，您必须包含：

```markdown
Based on Codex Harness by Walter
Source: https://github.com/MrFengcn/codex-harness
```

---

## 📄 License / 许可证

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

**Important / 重要**:
- ✅ Free for personal use / 个人免费使用
- ❌ Commercial use prohibited / 禁止商用
- 📝 Attribution required for modifications / 改编需要标注来源

---

## 🙏 Acknowledgments / 致谢

- OpenAI Codex — Inspiration / 灵感来源
- Hermes Agent — Platform / 运行平台
- All supported Agent frameworks / 所有支持的智能体框架

---

## 📞 Contact / 联系方式

- Author / 作者: Walter
- GitHub: https://github.com/MrFengcn
- Project / 项目: https://github.com/MrFengcn/codex-harness

---

*Last Updated / 最后更新: 2026-08-24*
