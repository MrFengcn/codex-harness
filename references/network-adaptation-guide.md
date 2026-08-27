# 中国网络适配指南 / China Network Adaptation Guide

> Author / 作者: Walter
> Source / 源码: https://github.com/MrFengcn/codex-harness

---

## 📖 Overview / 概述

Codex Harness automatically detects China network and switches services to provide the best experience for Chinese users.

Codex Harness 自动检测中国网络并切换服务，为中国用户提供最佳体验。

---

## 🔍 How It Works / 工作原理

### Network Detection / 网络检测

Codex Harness uses multiple methods to detect network type:

Codex Harness 使用多种方法检测网络类型：

1. **DNS Detection / DNS 检测**: Tests DNS resolution for Chinese and international domains
2. **HTTP Detection / HTTP 检测**: Tests accessibility to Chinese and international websites
3. **IP Geolocation / IP 地理位置**: Uses IP geolocation API to determine location

### Service Replacement / 服务替换

Based on network type, Codex Harness automatically selects the best service:

根据网络类型，Codex Harness 自动选择最佳服务：

| Service Type | International | China |
|--------------|---------------|-------|
| LLM | OpenAI | DeepSeek / 通义千问 / 文心一言 |
| Code Hosting | GitHub | Gitee |
| Model Repo | HuggingFace | 魔搭社区 |
| Package Manager | PyPI | 清华镜像 / 阿里镜像 |
| Search | Google | 百度 |

---

## 🚀 Usage / 使用

### Auto Detection / 自动检测

```python
from network_detector import is_china_network, get_global_network_detector

# Check if China network / 检查是否是中国网络
if is_china_network():
    print("Using China network")
else:
    print("Using international network")

# Get detailed info / 获取详细信息
detector = get_global_network_detector()
info = detector.get_network_info()
print(f"Network type: {info['type']}")
```

### Manual Override / 手动覆盖

```python
from network_detector import NetworkConfig

# Force China network / 强制使用中国网络
config = NetworkConfig(force_china=True)

# Force international network / 强制使用国际网络
config = NetworkConfig(force_international=True)
```

### Service Selection / 服务选择

```python
from service_registry import ServiceAdapter, ServiceType

adapter = ServiceAdapter()

# Get best LLM service / 获取最佳 LLM 服务
llm = adapter.get_llm_service()
print(f"LLM: {llm.name}")  # DeepSeek (China) or OpenAI (International)

# Get best code hosting / 获取最佳代码托管
code = adapter.get_code_hosting_service()
print(f"Code: {code.name}")  # Gitee (China) or GitHub (International)
```

---

## 🇨🇳 China-Specific Services / 中国特有服务

### LLM Services / LLM 服务

| Service | API | Key |
|---------|-----|-----|
| DeepSeek | https://api.deepseek.com/v1 | DEEPSEEK_API_KEY |
| 通义千问 | https://dashscope.aliyuncs.com/api/v1 | DASHSCOPE_API_KEY |
| 文心一言 | https://aip.baidubce.com/rpc/2.0/ai_custom/v1 | ERNIE_API_KEY |

### Code Hosting / 代码托管

| Service | API | Key |
|---------|-----|-----|
| Gitee | https://gitee.com/api/v5 | GITEE_TOKEN |

### Model Repository / 模型仓库

| Service | API | Key |
|---------|-----|-----|
| 魔搭社区 | https://modelscope.cn/api/v1 | MODELSCOPE_TOKEN |

### Package Manager / 包管理

| Service | URL |
|---------|-----|
| 清华镜像 | https://pypi.tuna.tsinghua.edu.cn/simple |
| 阿里镜像 | https://mirrors.aliyun.com/pypi/simple |

### Search / 搜索

| Service | URL |
|---------|-----|
| 百度 | https://www.baidu.com/s |
| Bing | https://www.bing.com/search |

---

## ⚙️ Configuration / 配置

### Environment Variables / 环境变量

```bash
# China LLM services / 中国 LLM 服务
export DEEPSEEK_API_KEY="your-key"
export DASHSCOPE_API_KEY="your-key"
export ERNIE_API_KEY="your-key"

# China code hosting / 中国代码托管
export GITEE_TOKEN="your-token"

# China model repo / 中国模型仓库
export MODELSCOPE_TOKEN="your-token"
```

### Force Network Type / 强制网络类型

```python
from network_detector import NetworkConfig

# Force China / 强制中国
config = NetworkConfig(force_china=True)

# Force International / 强制国际
config = NetworkConfig(force_international=True)
```

---

## 🔧 Troubleshooting / 故障排除

### Problem: Wrong network detected / 问题：检测到错误的网络

**Solution / 解决方案**:

```python
from network_detector import NetworkConfig

# Force correct network / 强制正确的网络
config = NetworkConfig(force_china=True)  # or force_international=True
```

### Problem: Service not available / 问题：服务不可用

**Solution / 解决方案**:

```python
from service_registry import ServiceAdapter, ServiceType

adapter = ServiceAdapter()

# Switch to different service / 切换到不同服务
adapter.switch_service(ServiceType.LLM, "qwen")  # Use 通义千问
```

---

## 📊 Statistics / 统计

| Metric | Value |
|--------|-------|
| China Services | 8 |
| International Services | 5 |
| Global Services | 1 |
| Total Services | 14 |

---

*Last Updated / 最后更新: 2026-08-24*
