#!/usr/bin/env python3
"""
Codex Harness — AGENTS.md 解析器

解析 AGENTS.md 配置文件。
对应 Codex 的 agents_md 模块。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from typing import List, Dict, Any, Optional


# ============================================================================
# AGENTS.md 解析器
# ============================================================================

class AgentsMdParser:
    """
    AGENTS.md 解析器。
    对应 Codex 的 agents_md 模块。

    功能:
    - 发现 AGENTS.md 文件
    - 解析配置内容
    - 合并多个配置
    """

    # 默认文件名
    DEFAULT_FILENAME = "AGENTS.md"
    LOCAL_FILENAME = "AGENTS.override.md"

    # 项目根标记
    ROOT_MARKERS = ['.git', '.hg', '.svn', 'package.json', 'Cargo.toml', 'pyproject.toml']

    def __init__(
        self,
        filename: str = "AGENTS.md",
        root_markers: Optional[List[str]] = None,
    ):
        """
        初始化解析器。

        参数:
            filename: AGENTS.md 文件名
            root_markers: 项目根标记列表
        """
        self.filename = filename
        self.root_markers = root_markers or self.ROOT_MARKERS

    def discover(self, start_path: str = ".") -> List[str]:
        """
        发现 AGENTS.md 文件。

        参数:
            start_path: 起始路径

        返回:
            AGENTS.md 文件路径列表
        """
        # 查找项目根
        project_root = self._find_project_root(start_path)

        # 收集 AGENTS.md 文件
        files = []
        for root, dirs, filenames in os.walk(project_root):
            for fn in filenames:
                if fn == self.filename or fn == self.LOCAL_FILENAME:
                    files.append(os.path.join(root, fn))

        # 按路径深度排序
        files.sort(key=lambda f: f.count(os.sep))

        return files

    def parse(self, filepath: str) -> Dict[str, Any]:
        """
        解析单个 AGENTS.md 文件。

        参数:
            filepath: 文件路径

        返回:
            解析后的配置字典
        """
        if not os.path.exists(filepath):
            return {}

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        return self._parse_content(content)

    def parse_all(self, start_path: str = ".") -> Dict[str, Any]:
        """
        解析所有 AGENTS.md 文件并合并。

        参数:
            start_path: 起始路径

        返回:
            合并后的配置字典
        """
        files = self.discover(start_path)
        configs = []

        for filepath in files:
            config = self.parse(filepath)
            if config:
                configs.append(config)

        return self._merge_configs(configs)

    def _find_project_root(self, start_path: str) -> str:
        """
        查找项目根目录。

        参数:
            start_path: 起始路径

        返回:
            项目根目录路径
        """
        current = os.path.abspath(start_path)

        while True:
            # 检查是否有根标记
            for marker in self.root_markers:
                if os.path.exists(os.path.join(current, marker)):
                    return current

            # 向上遍历
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent

        # 如果没有找到标记，返回起始路径
        return os.path.abspath(start_path)

    def _parse_content(self, content: str) -> Dict[str, Any]:
        """
        解析 AGENTS.md 内容。

        参数:
            content: 文件内容

        返回:
            解析后的配置字典
        """
        config = {
            "rules": [],
            "sections": {},
        }

        # 解析规则
        rules = self._extract_rules(content)
        config["rules"] = rules

        # 解析章节
        sections = self._extract_sections(content)
        config["sections"] = sections

        return config

    def _extract_rules(self, content: str) -> List[str]:
        """
        提取规则。

        参数:
            content: 文件内容

        返回:
            规则列表
        """
        rules = []

        # 匹配列表项
        pattern = r'^[\-\*]\s+(.+)$'
        for match in re.finditer(pattern, content, re.MULTILINE):
            rule = match.group(1).strip()
            if rule:
                rules.append(rule)

        return rules

    def _extract_sections(self, content: str) -> Dict[str, str]:
        """
        提取章节。

        参数:
            content: 文件内容

        返回:
            章节字典
        """
        sections = {}
        current_section = None
        current_content = []

        for line in content.split('\n'):
            # 检查是否是标题
            if line.startswith('#'):
                # 保存上一个章节
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()

                # 开始新章节
                current_section = line.lstrip('#').strip()
                current_content = []
            else:
                current_content.append(line)

        # 保存最后一个章节
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    def _merge_configs(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        合并多个配置。

        参数:
            configs: 配置列表

        返回:
            合并后的配置
        """
        if not configs:
            return {"rules": [], "sections": {}}

        if len(configs) == 1:
            return configs[0]

        merged = {
            "rules": [],
            "sections": {},
        }

        for config in configs:
            merged["rules"].extend(config.get("rules", []))
            merged["sections"].update(config.get("sections", {}))

        # 去重规则
        merged["rules"] = list(dict.fromkeys(merged["rules"]))

        return merged


# ============================================================================
# AGENTS.md 管理器
# ============================================================================

class AgentsMdManager:
    """
    AGENTS.md 管理器。
    管理 AGENTS.md 配置。

    功能:
    - 加载配置
    - 缓存配置
    - 提供配置查询
    """

    def __init__(self, start_path: str = "."):
        """
        初始化管理器。

        参数:
            start_path: 起始路径
        """
        self.start_path = start_path
        self.parser = AgentsMdParser()
        self._config: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        """
        加载配置。

        返回:
            配置字典
        """
        if self._config is None:
            self._config = self.parser.parse_all(self.start_path)
        return self._config

    def reload(self) -> Dict[str, Any]:
        """
        重新加载配置。

        返回:
            配置字典
        """
        self._config = None
        return self.load()

    def get_rules(self) -> List[str]:
        """
        获取规则列表。

        返回:
            规则列表
        """
        config = self.load()
        return config.get("rules", [])

    def get_sections(self) -> Dict[str, str]:
        """
        获取章节字典。

        返回:
            章节字典
        """
        config = self.load()
        return config.get("sections", {})

    def get_section(self, name: str) -> Optional[str]:
        """
        获取指定章节。

        参数:
            name: 章节名称

        返回:
            章节内容，如果不存在返回 None
        """
        sections = self.get_sections()
        return sections.get(name)

    def get_files(self) -> List[str]:
        """
        获取 AGENTS.md 文件列表。

        返回:
            文件路径列表
        """
        return self.parser.discover(self.start_path)


# ============================================================================
# 全局管理器
# ============================================================================

_global_manager: Optional[AgentsMdManager] = None


def get_global_agents_md_manager() -> AgentsMdManager:
    """
    获取全局 AGENTS.md 管理器。

    返回:
        全局管理器实例
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = AgentsMdManager()
    return _global_manager
