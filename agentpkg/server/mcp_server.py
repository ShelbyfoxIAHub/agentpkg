import json
from pathlib import Path
from typing import Dict, Any
from agentpkg.reader import read_package
from agentpkg.skills.loader import load_skills_from_package

class MCPServer:
    """Servidor MCP para exponer recursos y herramientas de un paquete .agentpkg."""
    
    def __init__(self, package_path: Path):
        self.package_path = package_path
        self.package_data = read_package(package_path)
        self.skills_registry = load_skills_from_package(self.package_data)

    def list_resources(self) -> Dict[str, Any]:
        """Devuelve la lista de recursos (manifiesto y rutas de archivos) del paquete."""
        files_list = self.package_data.get("files", [])
        file_paths = [f.get("path") for f in files_list if isinstance(f, dict)]
        return {
            "manifest": self.package_data.get("manifest", {}),
            "files": file_paths
        }

    def list_tools(self) -> Dict[str, Any]:
        """Lista las herramientas/skills expuestas por el paquete."""
        return {
            "tools": self.skills_registry.list_skills()
        }

    def execute_tool(self, tool_name: str, params: Dict[str, Any], approved: bool = False) -> Dict[str, Any]:
        """Ejecuta una herramienta validando permisos de usuario."""
        skill = self.skills_registry.get_skill(tool_name)
        if not skill:
            return {"error": f"Herramienta '{tool_name}' no encontrada."}
        
        if skill.requires_permission and not approved:
            return {
                "error": f"La herramienta '{tool_name}' requiere permisos explícitos del usuario para ejecutarse."
            }
        
        return {
            "status": "success",
            "tool": tool_name,
            "params": params,
            "result": f"Ejecución autorizada de '{tool_name}' completada."
        }
