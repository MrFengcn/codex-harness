#!/usr/bin/env python3
"""
Codex Harness — AGENTS.md 配置提取和应用

从 AGENTS.md 提取配置并应用到系统。
对应 Codex 的 agents_md 配置逻辑。

Python 兼容性: 3.6+
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from typing import List, Dict, Any, Optional
from agents_md.parser import AgentsMdManager


# ============================================================================
# 配置提取器
# ============================================================================

class ConfigExtractor:
    """
    配置提取器。
    从 AGENTS.md 提取结构化配置。

    功能:
    - 提取规则
    - 提取约束
    - 提取偏好
    - 提取工具配置
    """

    # 配置模式
    CONFIG_PATTERNS = {
        'rules': r'(?:^|\n)[\-\*]\s+(.+)',
        'constraints': r'(?:must|should|never|always)\s+(.+)',
        'preferences': r'(?:prefer|like|want)\s+(.+)',
        'tools': r'(?:use|run|execute)\s+(\w+)',
    }

    def extract(self, content: str) -> Dict[str, Any]:
        """
        提取配置。

        参数:
            content: AGENTS.md 内容

        返回:
            配置字典
        """
        config = {
            "rules": self._extract_rules(content),
            "constraints": self._extract_constraints(content),
            "preferences": self._extract_preferences(content),
            "tools": self._extract_tools(content),
            "settings": self._extract_settings(content),
        }

        return config

    def _extract_rules(self, content: str) -> List[str]:
        """
        提取规则。

        参数:
            content: 内容

        返回:
            规则列表
        """
        rules = []
        pattern = r'^[\-\*]\s+(.+)$'

        for match in re.finditer(pattern, content, re.MULTILINE):
            rule = match.group(1).strip()
            if rule:
                rules.append(rule)

        return rules

    def _extract_constraints(self, content: str) -> List[str]:
        """
        提取约束。

        参数:
            content: 内容

        返回:
            约束列表
        """
        constraints = []
        pattern = r'(?:must|should|never|always)\s+(.+?)(?:\.|$)'

        for match in re.finditer(pattern, content, re.IGNORECASE):
            constraint = match.group(1).strip()
            if constraint:
                constraints.append(constraint)

        return constraints

    def _extract_preferences(self, content: str) -> List[str]:
        """
        提取偏好。

        参数:
            content: 内容

        返回:
            偏好列表
        """
        preferences = []
        pattern = r'(?:prefer|like|want)\s+(.+?)(?:\.|$)'

        for match in re.finditer(pattern, content, re.IGNORECASE):
            preference = match.group(1).strip()
            if preference:
                preferences.append(preference)

        return preferences

    def _extract_tools(self, content: str) -> List[str]:
        """
        提取工具。

        参数:
            content: 内容

        返回:
            工具列表
        """
        tools = []
        pattern = r'(?:use|run|execute)\s+(\w+)'

        for match in re.finditer(pattern, content, re.IGNORECASE):
            tool = match.group(1).strip()
            if tool:
                tools.append(tool)

        return list(set(tools))

    def _extract_settings(self, content: str) -> Dict[str, str]:
        """
        提取设置。

        参数:
            content: 内容

        返回:
            设置字典
        """
        settings = {}
        pattern = r'(\w+)\s*[:=]\s*(.+?)(?:\n|$)'

        for match in re.finditer(pattern, content):
            key = match.group(1).strip()
            value = match.group(2).strip()
            if key and value:
                settings[key] = value

        return settings


# ============================================================================
# 配置应用器
# ============================================================================

class ConfigApplicator:
    """
    配置应用器。
    将提取的配置应用到系统。

    功能:
    - 应用规则
    - 应用约束
    - 应用偏好
    - 验证配置
    """

    def apply(
        self,
        config: Dict[str, Any],
        system_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        应用配置。

        参数:
            config: 提取的配置
            system_config: 系统配置

        返回:
            应用后的配置
        """
        if system_config is None:
            system_config = {}

        # 合并配置
        merged = self._merge_configs(system_config, config)

        # 验证配置
        validated = self._validate_config(merged)

        return validated

    def _merge_configs(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        合并配置。

        参数:
            base: 基础配置
            override: 覆盖配置

        返回:
            合并后的配置
        """
        merged = base.copy()

        for key, value in override.items():
            if key in merged:
                # 合并列表
                if isinstance(merged[key], list) and isinstance(value, list):
                    merged[key] = list(set(merged[key] + value))
                # 合并字典
                elif isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key].update(value)
                # 覆盖标量
                else:
                    merged[key] = value
            else:
                merged[key] = value

        return merged

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证配置。

        参数:
            config: 配置

        返回:
            验证后的配置
        """
        validated = {}

        # 验证规则
        if "rules" in config:
            validated["rules"] = [
                rule for rule in config["rules"]
                if isinstance(rule, str) and len(rule) > 0
            ]

        # 验证约束
        if "constraints" in config:
            validated["constraints"] = [
                c for c in config["constraints"]
                if isinstance(c, str) and len(c) > 0
            ]

        # 验证偏好
        if "preferences" in config:
            validated["preferences"] = [
                p for p in config["preferences"]
                if isinstance(p, str) and len(p) > 0
            ]

        # 验证工具
        if "tools" in config:
            validated["tools"] = [
                t for t in config["tools"]
                if isinstance(t, str) and len(t) > 0
            ]

        # 验证设置
        if "settings" in config:
            validated["settings"] = {
                k: v for k, v in config["settings"].items()
                if isinstance(k, str) and isinstance(v, str)
            }

        return validated

    def format_for_prompt(self, config: Dict[str, Any]) -> str:
        """
        格式化配置为提示词。

        参数:
            config: 配置

        返回:
            格式化的提示词
        """
        lines = []

        # 添加规则
        if "rules" in config and config["rules"]:
            lines.append("## Rules")
            for rule in config["rules"]:
                lines.append(f"- {rule}")
            lines.append("")

        # 添加约束
        if "constraints" in config and config["constraints"]:
            lines.append("## Constraints")
            for constraint in config["constraints"]:
                lines.append(f"- {constraint}")
            lines.append("")

        # 添加偏好
        if "preferences" in config and config["preferences"]:
            lines.append("## Preferences")
            for pref in config["preferences"]:
                lines.append(f"- {pref}")
            lines.append("")

        return "\n".join(lines)


# ============================================================================
# AGENTS.md 配置管理器
# ============================================================================

class AgentsMdConfigManager:
    """
    AGENTS.md 配置管理器。
    统一管理 AGENTS.md 配置的提取和应用。

    功能:
    - 加载配置
    - 提取配置
    - 应用配置
    - 格式化配置
    """

    def __init__(self, start_path: str = "."):
        """
        初始化配置管理器。

        参数:
            start_path: 起始路径
        """
        self.start_path = start_path
        self.manager = AgentsMdManager(start_path)
        self.extractor = ConfigExtractor()
        self.applicator = ConfigApplicator()
        self._config: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        """
        加载配置。

        返回:
            配置字典
        """
        if self._config is None:
            # 获取 AGENTS.md 内容
            files = self.manager.get_files()
            contents = []

            for filepath in files:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        contents.append(f.read())
                except Exception:
                    pass

            # 合并内容
            combined = "\n\n---\n\n".join(contents)

            # 提取配置
            self._config = self.extractor.extract(combined)

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

    def get_constraints(self) -> List[str]:
        """
        获取约束列表。

        返回:
            约束列表
        """
        config = self.load()
        return config.get("constraints", [])

    def get_preferences(self) -> List[str]:
        """
        获取偏好列表。

        返回:
            偏好列表
        """
        config = self.load()
        return config.get("preferences", [])

    def get_tools(self) -> List[str]:
        """
        获取工具列表。

        返回:
            工具列表
        """
        config = self.load()
        return config.get("tools", [])

    def get_settings(self) -> Dict[str, str]:
        """
        获取设置字典。

        返回:
            设置字典
        """
        config = self.load()
        return config.get("settings", {})

    def apply_to_system(
        self,
        system_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        应用配置到系统。

        参数:
            system_config: 系统配置

        返回:
            应用后的配置
        """
        config = self.load()
        return self.applicator.apply(config, system_config)

    def format_for_prompt(self) -> str:
        """
        格式化配置为提示词。

        返回:
            格式化的提示词
        """
        config = self.load()
        return self.applicator.format_for_prompt(config)


# ============================================================================
# 全局配置管理器
# ============================================================================

_global_config_manager: Optional[AgentsMdConfigManager] = None


def get_global_config_manager() -> AgentsMdConfigManager:
    """
    获取全局配置管理器。

    返回:
        全局配置管理器实例
    """
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = AgentsMdConfigManager()
    return _global_config_manager
