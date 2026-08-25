#!/usr/bin/env python3
"""
Codex Harness — 技能系统

提供技能加载和执行能力。
对应 Codex 的 skills 模块。

Python 兼容性: 3.6+
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional
import time


class SkillType(Enum):
    """技能类型"""
    BUILTIN = "builtin"
    CUSTOM = "custom"
    PLUGIN = "plugin"


class SkillStatus(Enum):
    """技能状态"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    ERROR = "error"


class SkillDefinition:
    """
    技能定义。

    属性:
        name: 技能名称
        description: 技能描述
        type: 技能类型
        version: 版本
        capabilities: 能力列表
    """
    def __init__(
        self,
        name: str,
        description: str = "",
        type: SkillType = SkillType.CUSTOM,
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
    ):
        self.name = name
        self.description = description
        self.type = type
        self.version = version
        self.capabilities = capabilities or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "version": self.version,
            "capabilities": self.capabilities,
        }


class Skill(ABC):
    """
    技能基类。
    对应 Codex 的 Skill 接口。
    """

    @abstractmethod
    def get_definition(self) -> SkillDefinition:
        pass

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def get_status(self) -> SkillStatus:
        return SkillStatus.ACTIVE


class SkillRegistry:
    """
    技能注册表。
    管理所有技能。
    """

    def __init__(self):
        self.skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> bool:
        definition = skill.get_definition()
        self.skills[definition.name] = skill
        return True

    def unregister(self, name: str) -> bool:
        if name in self.skills:
            del self.skills[name]
            return True
        return False

    def get(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)

    def list_skills(self) -> List[str]:
        return list(self.skills.keys())

    def get_definitions(self) -> List[SkillDefinition]:
        return [skill.get_definition() for skill in self.skills.values()]

    def execute(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        skill = self.skills.get(name)
        if not skill:
            return {"success": False, "error": f"Skill not found: {name}"}
        try:
            return skill.execute(params)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total": len(self.skills),
            "skills": list(self.skills.keys()),
        }


class SkillManager:
    """
    技能管理器。
    统一管理技能注册和执行。
    """

    def __init__(self):
        self.registry = SkillRegistry()

    def register(self, skill: Skill) -> bool:
        return self.registry.register(skill)

    def execute(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self.registry.execute(name, params)

    def list_skills(self) -> List[str]:
        return self.registry.list_skills()

    def get_stats(self) -> Dict[str, Any]:
        return self.registry.get_stats()


_global_manager = None

def get_global_skill_manager() -> SkillManager:
    global _global_manager
    if _global_manager is None:
        _global_manager = SkillManager()
    return _global_manager
