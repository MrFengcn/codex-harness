# 补丁系统深度文档

> 对应 Codex: codex-rs/core/src/apply_patch*.rs
> 实现: scripts/patch/

## 概述

补丁系统负责安全地应用代码补丁到文件系统。支持 unified diff 格式，包含安全检查和审批流程。

## 核心概念

### 1. 补丁动作 (PatchAction)

```python
class PatchAction(Enum):
    ADD = "add"          # 添加文件
    DELETE = "delete"    # 删除文件
    UPDATE = "update"    # 更新文件
```

### 2. 文件变更 (FileChange)

```python
class FileChange:
    path: str                    # 文件路径
    action: PatchAction          # 补丁动作
    content: Optional[str]       # 文件内容 (Add/Delete)
    unified_diff: Optional[str]  # unified diff (Update)
    move_path: Optional[str]     # 移动目标路径
```

### 3. 安全检查 (SafetyCheck)

```python
class SafetyCheck(Enum):
    AUTO_APPROVE = "auto_approve"  # 自动批准
    ASK_USER = "ask_user"          # 需要用户确认
    REJECT = "reject"              # 拒绝
```

### 4. 补丁管理器 (PatchManager)

```python
class PatchManager:
    def apply_patch(patch_text) -> PatchResult
    def dry_run(patch_text) -> PatchResult
    def rollback(backup_path) -> PatchResult
    def validate_patch(patch_text) -> Dict
    def check_safety(patch_text) -> Dict
```

## 模块结构

### PatchParser (补丁解析器)

解析 unified diff 格式的补丁：

```python
from patch import PatchParser

parser = PatchParser()
changes = parser.parse(patch_text)

# changes = [
#     FileChange(path='test.py', action=PatchAction.ADD, content='...'),
#     FileChange(path='old.py', action=PatchAction.DELETE, content='...'),
# ]
```

**支持的格式:**
- 添加文件: `--- /dev/null` → `+++ b/file.py`
- 删除文件: `--- a/file.py` → `+++ /dev/null`
- 更新文件: `--- a/file.py` → `+++ b/file.py`

### PatchSafetyChecker (安全检查器)

验证补丁安全性：

```python
from patch import PatchSafetyChecker, FileChange, PatchAction

checker = PatchSafetyChecker(allowed_dirs=['.'])
changes = [FileChange(path='./test.py', action=PatchAction.ADD, content='test')]
result = checker.check(changes)

# result.is_auto_approve: True
# result.is_reject: False
```

**检查项目:**
1. 路径遍历 (`..`)
2. 禁止路径 (`/etc`, `/proc`, `/sys` 等)
3. 敏感文件 (`.env`, `id_rsa` 等)
4. 禁止扩展名 (`.exe`, `.dll` 等)
5. 路径白名单 (当前目录)

### PatchApplicator (补丁应用器)

应用补丁到文件系统：

```python
from patch import PatchApplicator

applicator = PatchApplicator(create_backup=True)
result = applicator.apply(changes)

# result.success: True
# result.changes_applied: 1
# result.backup_path: '.patch_backups/backup_123456'
```

**特性:**
- 自动创建备份
- 支持回滚
- 干运行模式

### PatchManager (补丁管理器)

统一管理补丁操作：

```python
from patch import PatchManager, PatchConfig

config = PatchConfig(
    allowed_dirs=['.'],
    create_backup=True,
    check_safety=True,
)
manager = PatchManager(config)

# 应用补丁
result = manager.apply_patch(patch_text)

# 干运行
result = manager.dry_run(patch_text)

# 验证补丁
validation = manager.validate_patch(patch_text)

# 安全检查
safety = manager.check_safety(patch_text)
```

## 安全检查流程

```
1. 解析补丁
2. 检查路径遍历 (..)
3. 检查禁止路径 (/etc, /proc 等)
4. 检查敏感文件 (.env, id_rsa 等)
5. 检查禁止扩展名 (.exe, .dll 等)
6. 检查路径白名单 (当前目录)
7. 返回结果:
   - AUTO_APPROVE: 自动批准
   - ASK_USER: 需要用户确认
   - REJECT: 拒绝
```

## 补丁应用流程

```
1. 验证补丁格式
2. 解析补丁
3. 安全检查
4. 创建备份
5. 应用变更
6. 记录历史
```

## 与 orchestrator.py 的集成

### PatchApprovalHandler

```python
from orchestrator import PatchApprovalHandler

handler = PatchApprovalHandler()

# 获取审批需求
approval = handler.handle_patch_request(patch_text)

# 带审批的补丁应用
result = handler.apply_patch_with_approval(
    patch_text,
    approval_policy="auto",
    strict_auto_review=False,
    guardian_review_fn=None,
)
```

### apply_patch 工具

```python
from orchestrator import apply_patch_tool

result = apply_patch_tool(patch_text)
if result['success']:
    print(f"成功应用 {result['changes_applied']} 个变更")
```

## 配置

### PatchConfig

```python
from patch import PatchConfig

config = PatchConfig(
    allowed_dirs=['.'],      # 允许的目录列表
    create_backup=True,      # 是否创建备份
    dry_run=False,           # 是否为干运行模式
    check_safety=True,       # 是否检查安全性
)
```

### PatchSecurityPolicy

```python
from patch import PatchSecurityPolicy

policy = PatchSecurityPolicy()

# 禁止的路径
policy.DENY_PATHS = {'/etc', '/proc', '/sys', '/dev', '/boot', '/usr', '/var', '/tmp'}

# 禁止的扩展名
policy.DENY_EXTENSIONS = {'.exe', '.dll', '.so', '.dylib', '.bin', '.sh', '.bash'}

# 敏感文件
policy.SENSITIVE_FILES = {'.env', '.env.local', '.env.production', 'id_rsa', 'id_ed25519'}
```

## 使用方式

### 基本使用

```python
from patch import PatchManager

manager = PatchManager()

# 应用补丁
patch_text = '''--- /dev/null
+++ b/hello.py
@@ -0,0 +1,2 @@
+print('Hello')
+'''

result = manager.apply_patch(patch_text)
print(f"成功: {result.success}")
print(f"应用: {result.changes_applied}")
```

### 干运行

```python
from patch import PatchManager

manager = PatchManager()

# 干运行
result = manager.dry_run(patch_text)
print(f"可以应用: {result.success}")
print(f"变更数: {result.changes_applied}")
```

### 回滚

```python
from patch import PatchManager

manager = PatchManager()

# 应用补丁
result = manager.apply_patch(patch_text)

# 回滚
if result.backup_path:
    rollback_result = manager.rollback(result.backup_path)
    print(f"回滚成功: {rollback_result.success}")
```

### 安全检查

```python
from patch import PatchManager

manager = PatchManager()

# 检查安全性
safety = manager.check_safety(patch_text)
print(f"安全: {safety['safe']}")
print(f"需要审批: {safety['needs_approval']}")
print(f"被拒绝: {safety['rejected']}")
```

## 与 Codex 的对应关系

| Codex 模块 | 我们的实现 | 说明 |
|-----------|-----------|------|
| ApplyPatchAction | PatchAction | 补丁动作类型 |
| ApplyPatchFileChange | FileChange | 文件变更 |
| StreamingPatchParser | PatchParser | 补丁解析器 |
| SafetyCheck | PatchSafetyChecker | 安全检查 |
| ApplyPatchHandler | PatchApplicator | 补丁应用器 |
| PatchManager | PatchManager | 补丁管理器 |

## 安全特性

| 特性 | 说明 |
|------|------|
| 路径遍历防护 | 检查 `..` 路径 |
| 禁止路径 | /etc, /proc, /sys 等 |
| 敏感文件 | .env, id_rsa 等 |
| 禁止扩展名 | .exe, .dll 等 |
| 路径白名单 | 限制在当前目录 |
| 备份支持 | 自动创建备份 |
| 回滚支持 | 从备份恢复 |

## 故障排除

### 问题: 补丁解析失败

**原因**: 补丁格式不正确

**解决**: 检查是否包含 `---` 和 `+++` 头，以及 `@@` hunk 头

### 问题: 安全检查失败

**原因**: 路径不在允许的目录下

**解决**: 使用相对路径或修改 `allowed_dirs` 配置

### 问题: 补丁应用失败

**原因**: 文件不存在或没有写权限

**解决**: 检查文件路径和权限

## 文件结构

```
scripts/patch/
├── __init__.py           # 模块初始化
├── action.py             # PatchAction, FileChange, PatchResult
├── parser.py             # PatchParser, PatchValidator
├── safety.py             # PatchSafetyChecker, PatchSecurityPolicy
├── applicator.py         # PatchApplicator, DryRunApplicator
└── manager.py            # PatchManager, PatchConfig
```
