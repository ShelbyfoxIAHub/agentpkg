import unittest
import json
from pathlib import Path
import tempfile
import shutil
from agentpkg.builder import create_package
from agentpkg.server import MCPServer
from agentpkg.skills import load_skills_from_package

class TestMCPAndSkills(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.pkg_path = self.test_dir / "test_mcp.agentpkg"
        
        # Crear estructura con skills
        skills_dir = self.test_dir / "src" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        
        skills_data = {
            "skills": [
                {
                    "name": "calculator",
                    "description": "Realiza operaciones matemáticas",
                    "parameters": {"expression": "str"},
                    "requires_permission": False
                },
                {
                    "name": "delete_file",
                    "description": "Elimina un archivo del sistema",
                    "parameters": {"path": "str"},
                    "requires_permission": True
                }
            ]
        }
        with open(skills_dir / "skills.json", "w", encoding="utf8") as f:
            json.dump(skills_data, f)
            
        create_package(self.test_dir / "src", self.pkg_path, title="MCP Test")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_mcp_server_resources_and_tools(self):
        server = MCPServer(self.pkg_path)
        resources = server.list_resources()
        tools = server.list_tools()

        self.assertIn("manifest", resources)
        self.assertEqual(len(tools["tools"]), 2)

    def test_mcp_tool_execution_permissions(self):
        server = MCPServer(self.pkg_path)
        
        # Tool sin permisos requeridos
        res_calc = server.execute_tool("calculator", {"expression": "2+2"})
        self.assertEqual(res_calc.get("status"), "success")

        # Tool con permisos requeridos (sin aprobación)
        res_del_unapproved = server.execute_tool("delete_file", {"path": "/tmp/a.txt"}, approved=False)
        self.assertIn("error", res_del_unapproved)

        # Tool con permisos requeridos (con aprobación)
        res_del_approved = server.execute_tool("delete_file", {"path": "/tmp/a.txt"}, approved=True)
        self.assertEqual(res_del_approved.get("status"), "success")

if __name__ == "__main__":
    unittest.main()
