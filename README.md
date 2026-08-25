# Codex Harness — Super Skill for AI Agents

> 🚀 Enhance AI Agents with OpenAI Codex capabilities
>
> 🚀 用 OpenAI Codex 能力增强 AI 智能体

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

**Author / 作者**: Walter
**License / 许可证**: MIT (Personal Use Only / 仅限个人使用)

---

## 🌟 Features / 特性

- ✅ **20+ Modules** — Compression, patching, safety, memory, and more
- ✅ **8 Agent Support** — Hermes, OpenClaw, LangChain, AutoGPT, MetaGPT, CrewAI, BabyAGI, AgentGPT
- ✅ **Security First** — Command validation, path protection, injection prevention
- ✅ **Easy Integration** — Simple API, no core modifications required
- ✅ **Python 3.6+** — Compatible with all Python 3.6+ environments

---

## 🎯 One-Line Deployment / 一句话部署

### For AI Agents / 对于 AI 智能体

Copy and paste this command to your AI agent:

复制并粘贴此命令给您的 AI 智能体：

**Hermes Agent:**
```
查看 https://github.com/MrFengcn/codex-harness 页面项目，帮我以 README 说明里的方式安装 codex-harness skill，这个 skill 是用来增强 AI 智能体的编码能力的，提供压缩、补丁、安全检查、记忆提取等功能，在需要进行代码编辑、安全检查或多智能体协作时切换或使用
```

**OpenClaw:**
```
查看 https://github.com/MrFengcn/codex-harness 页面项目，帮我安装 codex-harness skill，这个 skill 是用来增强智能体能力的，在需要进行复杂编码任务时使用
```

**LangChain:**
```
查看 https://github.com/MrFengcn/codex-harness 页面项目，帮我集成 codex-harness，这个工具是用来增强 LangChain Agent 能力的，在需要进行代码编辑时使用
```

---

## 📦 Installation / 安装

### Quick Install / 快速安装

```bash
# Clone and install / 克隆并安装
git clone https://github.com/MrFengcn/codex-harness.git
cp -r codex-harness ~/.hermes/skills/
```

### Manual Install / 手动安装

1. Download the repository / 下载仓库
2. Extract to `~/.hermes/skills/codex-harness/`
3. Restart your AI Agent / 重启您的 AI 智能体

---

## 🚀 Quick Start / 快速开始

### Basic Usage / 基本使用

```python
# Import modules / 导入模块
from compression import CompressionManager
from safety import SafetyManager
from rollout import RolloutExtractor

# Create instances / 创建实例
compression = CompressionManager()
safety = SafetyManager()
memory = RolloutExtractor()

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
print(f'Available: {adapters}')

# Get specific adapter / 获取特定适配器
hermes = manager.get_adapter('hermes')
openclaw = manager.get_adapter('openclaw')

# Use adapter interfaces / 使用适配器接口
memory = hermes.get_memory()
memory.store('key', 'value')
```

---

## 📚 Module List / 模块列表

| Module | Description | 说明 |
|--------|-------------|------|
| compression/ | Context compression | 上下文压缩 |
| patch/ | Code patching | 代码补丁 |
| safety/ | Security checks | 安全检查 |
| canonicalization/ | Command normalization | 命令规范化 |
| rollout/ | Memory extraction | 记忆提取 |
| communication/ | Agent communication | 智能体通信 |
| agents_md/ | AGENTS.md config | AGENTS.md 配置 |
| connectors/ | External connectors | 外部连接器 |
| event_mapping/ | Event mapping | 事件映射 |
| function_tool/ | Function tools | 函数工具 |
| hook_runtime/ | Hook runtime | Hook 运行时 |
| mcp/ | MCP protocol | MCP 协议 |
| shell/ | Shell integration | Shell 集成 |
| skills/ | Skill system | 技能系统 |
| thread_manager/ | Thread management | 线程管理器 |
| elicitation/ | User interaction | 用户交互 |
| realtime/ | Real-time events | 实时事件 |
| responses/ | Response formatting | 响应格式化 |
| turn/ | Turn management | Turn 管理 |
| web_search/ | Web search | Web 搜索 |
| agent_adapter/ | Multi-agent support | 多智能体支持 |

---

## 🛡️ Security / 安全性

- ✅ Command validation / 命令验证
- ✅ Path traversal protection / 路径遍历防护
- ✅ Sensitive file detection / 敏感文件检测
- ✅ Dangerous command blocking / 危险命令阻止
- ✅ Shell injection prevention / Shell 注入防护

---

## 📊 Statistics / 统计

| Metric | Value |
|--------|-------|
| Python Files | 95 |
| Total Lines | 23,329 |
| Modules | 23 |
| Supported Agents | 8 |
| Test Pass Rate | 100% |

---

## 🤝 Contributing / 贡献

We welcome contributions! Please follow these steps:

欢迎贡献！请按照以下步骤操作：

1. Fork this repository / Fork 本仓库
2. Create your feature branch / 创建功能分支
3. Commit your changes / 提交更改
4. Push to the branch / 推送到分支
5. Open a Pull Request / 创建 Pull Request

### Attribution / 标注要求

When modifying or redistributing, you MUST include:

修改或再分发时，您必须包含：

```markdown
Based on Codex Harness by Walter
Source: https://github.com/MrFengcn/codex-harness
```

---

## 📄 License / 许可证

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

### License Summary / 许可证摘要

| Use Case | Allowed | 说明 |
|----------|---------|------|
| Personal Use | ✅ Yes | 个人使用 ✅ |
| Commercial Use | ❌ No | 商用 ❌ |
| Modification | ✅ Yes (with attribution) | 修改 ✅ (需标注) |
| Redistribution | ✅ Yes (with attribution) | 再分发 ✅ (需标注) |
| Private Use | ✅ Yes | 私人使用 ✅ |

---

## 🙏 Acknowledgments / 致谢

- [OpenAI Codex](https://github.com/openai/codex) — Inspiration / 灵感来源
- [Hermes Agent](https://hermes-agent.nousresearch.com) — Platform / 运行平台
- All supported Agent frameworks / 所有支持的智能体框架

---

## 📞 Contact / 联系方式

- **Author / 作者**: Walter
- **GitHub**: [MrFengcn](https://github.com/MrFengcn)
- **Project / 项目**: [codex-harness](https://github.com/MrFengcn/codex-harness)
- **Issues**: [Report Issues](https://github.com/MrFengcn/codex-harness/issues)

---

## 🌐 中文说明

### 这是什么？

Codex Harness 是一个超级技能，用 OpenAI Codex 能力增强 AI 智能体。

### 有什么用？

- 压缩系统：自动管理对话上下文
- 补丁系统：安全地应用代码补丁
- 安全检查：评估操作安全性
- 记忆提取：从会话历史提取记忆
- 智能体通信：代理间消息传递
- 多智能体支持：支持 8 种主流框架

### 怎么用？

1. 克隆仓库到 `~/.hermes/skills/` 目录
2. 重启您的 AI 智能体
3. 使用提供的 API 进行开发

### 有什么限制？

- ✅ 个人免费使用
- ❌ 禁止商用
- 📝 改编需要标注来源

---

*Last Updated / 最后更新: 2026-08-24*
