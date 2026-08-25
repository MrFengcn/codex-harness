# 安全检查系统深度文档

> 对应 Codex: codex-rs/core/src/safety.rs
> 实现: scripts/safety/

## 概述

安全检查系统负责评估各种操作的安全性，包括补丁、命令、文件和网络操作。提供统一的安全评估接口。

## 核心概念

### 1. 安全级别 (SafetyLevel)

```python
class SafetyLevel(Enum):
    LOW = "low"           # 低风险 (读取文件、查看状态)
    MEDIUM = "medium"     # 中风险 (写入文件、执行命令)
    HIGH = "high"         # 高风险 (删除文件、修改系统)
    CRITICAL = "critical" # 极高风险 (sudo、rm -rf)
```

### 2. 安全检查结果 (SafetyCheck)

```python
class SafetyCheck(Enum):
    AUTO_APPROVE = "auto_approve"  # 自动批准
    ASK_USER = "ask_user"          # 需要用户确认
    REJECT = "reject"              # 拒绝
```

### 3. 安全结果详情 (SafetyResult)

```python
class SafetyResult:
    check: SafetyCheck      # 安全检查结果
    level: SafetyLevel      # 安全级别
    reason: Optional[str]   # 原因
    details: Dict           # 详细信息
    path: Optional[str]     # 检查的路径
    operation: Optional[str] # 检查的操作
```

### 4. 安全策略 (SafetyPolicy)

```python
class SafetyPolicy:
    allowed_dirs: List[str]      # 允许的目录列表
    denied_paths: List[str]      # 禁止的路径列表
    denied_commands: List[str]   # 禁止的命令列表
    sensitive_files: List[str]   # 敏感文件列表
    max_file_size: int           # 最大文件大小 (字节)
```

## 模块结构

### types.py (安全类型)

定义安全级别、安全检查结果和安全策略。

### command.py (命令安全检查)

检查命令安全性：

```python
from safety import CommandSafetyChecker, CommandClassifier

checker = CommandSafetyChecker()
result = checker.check('ls -la')
# result.check = SafetyCheck.AUTO_APPROVE
# result.level = SafetyLevel.LOW

classifier = CommandClassifier()
category = classifier.classify('ls -la')
# category = 'safe'
```

**检查项目:**
1. 禁止命令 (rm -rf /, mkfs 等)
2. 危险模式 (wget http://, curl http://)
3. shell 注入 (; rm, | rm)
4. 命令复杂度 (管道、重定向、子shell)

### file.py (文件安全检查)

检查文件操作安全性：

```python
from safety import FileSafetyChecker, FileClassifier

checker = FileSafetyChecker()
result = checker.check_read('./src/main.py')
# result.check = SafetyCheck.AUTO_APPROVE

result = checker.check_write('/etc/passwd')
# result.check = SafetyCheck.REJECT
```

**检查项目:**
1. 路径遍历 (..)
2. 禁止路径 (/etc, /proc 等)
3. 敏感文件 (.env, id_rsa)
4. 文件大小 (> 10MB)
5. 路径白名单

### network.py (网络安全检查)

检查网络操作安全性：

```python
from safety import NetworkSafetyChecker, URLClassifier

checker = NetworkSafetyChecker()
result = checker.check_url('https://github.com')
# result.check = SafetyCheck.AUTO_APPROVE

result = checker.check_url('https://malware.com')
# result.check = SafetyCheck.REJECT
```

**检查项目:**
1. 协议安全 (http, https, ftp)
2. 危险域名 (malware.com 等)
3. 域名白名单
4. 危险端口 (21, 23, 25 等)

### patch.py (补丁安全检查)

检查补丁操作安全性：

```python
from safety import PatchSafetyChecker, PatchRiskAssessor

checker = PatchSafetyChecker()
changes = [{'path': './test.py', 'action': 'add', 'content': 'test'}]
result = checker.check(changes)
# result.check = SafetyCheck.AUTO_APPROVE
```

**检查项目:**
1. 路径遍历 (..)
2. 禁止路径 (/etc, /proc 等)
3. 敏感文件 (.env, id_rsa)
4. 路径白名单
5. 审批策略

### manager.py (安全管理器)

统一管理所有安全检查器：

```python
from safety import SafetyManager, check_operation

manager = SafetyManager()

# 统一接口
result = manager.check_operation('terminal', {'command': 'ls -la'})

# 分类功能
command_category = manager.classify_command('ls -la')
file_category = manager.classify_file('main.py')
url_category = manager.classify_url('https://github.com')

# 风险评估
risk = manager.assess_patch_risk(changes)

# 统计
stats = manager.get_stats()
```

## 安全检查流程

```
1. 接收操作请求
2. 选择检查器 (根据操作类型)
3. 执行安全检查
4. 返回安全结果
5. 记录安全事件
```

## 使用方式

### 基本使用

```python
from safety import SafetyManager

manager = SafetyManager()

# 检查命令
result = manager.check_command('ls -la')
if result.is_auto_approve:
    print("安全")
elif result.is_ask_user:
    print("需要确认")
elif result.is_reject:
    print("被拒绝")
```

### 统一接口

```python
from safety import check_operation

result = check_operation('terminal', {'command': 'ls -la'})
if result.is_safe:
    print("安全")
```

### Guardian 集成

```python
from guardian import GuardianSafetyIntegration

integration = GuardianSafetyIntegration()
result = integration.review_with_safety('terminal', {'command': 'ls -la'})
if result['allowed']:
    print("允许执行")
```

## 检查器功能

### CommandSafetyChecker

| 检查 | 说明 | 结果 |
|------|------|------|
| 禁止命令 | rm -rf /, mkfs | Reject |
| 危险模式 | wget http://, curl http:// | Reject |
| shell 注入 | ; rm, \| rm | AskUser |
| 命令复杂度 | 管道、重定向、子shell | AskUser |

### FileSafetyChecker

| 检查 | 说明 | 结果 |
|------|------|------|
| 路径遍历 | .. 路径 | Reject |
| 禁止路径 | /etc, /proc | Reject |
| 敏感文件 | .env, id_rsa | Reject |
| 文件大小 | > 10MB | AskUser |
| 路径白名单 | 不在允许目录 | AskUser |

### NetworkSafetyChecker

| 检查 | 说明 | 结果 |
|------|------|------|
| 协议安全 | 非 http/https/ftp | Reject |
| 危险域名 | malware.com | Reject |
| 域名白名单 | 不在白名单 | AskUser |
| 危险端口 | 21, 23, 25 | AskUser |

### PatchSafetyChecker

| 检查 | 说明 | 结果 |
|------|------|------|
| 路径遍历 | .. 路径 | Reject |
| 禁止路径 | /etc, /proc | Reject |
| 敏感文件 | .env, id_rsa | Reject |
| 路径白名单 | 不在允许目录 | AskUser |
| 审批策略 | never 策略 | Reject |

## 与 Codex 的对应关系

| Codex 模块 | 我们的实现 | 说明 |
|-----------|-----------|------|
| SafetyCheck | SafetyCheck | 安全检查结果枚举 |
| assess_patch_safety | PatchSafetyChecker | 补丁安全检查 |
| CommandSafetyChecker | CommandSafetyChecker | 命令安全检查 |
| FileSafetyChecker | FileSafetyChecker | 文件安全检查 |
| NetworkSafetyChecker | NetworkSafetyChecker | 网络安全检查 |
| SafetyManager | SafetyManager | 安全管理器 |

## 安全特性

| 特性 | 说明 |
|------|------|
| 路径遍历防护 | 检查 `..` 路径 |
| 禁止路径 | /etc, /proc, /sys 等 |
| 敏感文件 | .env, id_rsa 等 |
| 危险命令 | rm -rf /, mkfs 等 |
| shell 注入 | ; rm, \| rm 等 |
| 危险域名 | malware.com 等 |
| 危险端口 | 21, 23, 25 等 |
| 协议安全 | 仅允许 http/https/ftp |

## 故障排除

### 问题: 安全检查失败

**原因**: 操作被安全策略拒绝

**解决**: 检查安全策略配置，或使用相对路径

### 问题: 命令被拒绝

**原因**: 命令包含危险模式

**解决**: 使用更安全的命令形式

## 文件结构

```
scripts/safety/
├── __init__.py           # 模块初始化
├── types.py              # SafetyLevel, SafetyCheck, SafetyResult, SafetyPolicy
├── command.py            # CommandSafetyChecker, CommandClassifier
├── file.py               # FileSafetyChecker, FileClassifier
├── network.py            # NetworkSafetyChecker, URLClassifier
├── patch.py              # PatchSafetyChecker, PatchRiskAssessor
└── manager.py            # SafetyManager, get_global_safety_manager, check_operation
```
