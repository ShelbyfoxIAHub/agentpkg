import json
from typing import List, Dict, Any, Optional

class Skill:
    def __init__(self, name: str, description: str, parameters: Dict[str, Any], requires_permission: bool = True):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.requires_permission = requires_permission

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "requires_permission": self.requires_permission
        }

class SkillRegistry:
    def __init__(self):
        self.skills: Dict[str, Skill] = {}

    def register(self, skill: Skill):
        self.skills[skill.name] = skill

    def get_skill(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)

    def list_skills(self) -> List[Dict[str, Any]]:
        return [skill.to_dict() for skill in self.skills.values()]

def load_skills_from_package(package_data: Dict[str, Any]) -> SkillRegistry:
    """Extrae las definiciones de habilidades desde la lista de archivos del paquete."""
    registry = SkillRegistry()
    files = package_data.get("files", [])

    skills_config = None
    for file_info in files:
        path = file_info.get("path", "")
        if path.endswith("skills/skills.json") or path.endswith("skills.json"):
            content = file_info.get("content", "")
            if isinstance(content, str):
                skills_config = json.loads(content.lstrip('\ufeff'))
            elif isinstance(content, dict):
                skills_config = content
            break

    if isinstance(skills_config, dict) and "skills" in skills_config:
        for skill_data in skills_config.get("skills", []):
            skill = Skill(
                name=skill_data.get("name", "unnamed_skill"),
                description=skill_data.get("description", ""),
                parameters=skill_data.get("parameters", {}),
                requires_permission=skill_data.get("requires_permission", True)
            )
            registry.register(skill)

    return registry
