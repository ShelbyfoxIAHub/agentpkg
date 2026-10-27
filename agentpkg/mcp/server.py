import json
import sys
import zipfile
from pathlib import Path
from typing import Dict, Any, List

class MCPServer:
    """Servidor MCP sobre STDIO (JSON-RPC) para exponer recursos y habilidades de paquetes .agentpkg."""

    def __init__(self, package_path: Path, allow_execution: bool = False):
        self.package_path = package_path
        self.allow_execution = allow_execution

    def list_resources(self) -> List[Dict[str, Any]]:
        resources = []
        with zipfile.ZipFile(self.package_path, "r") as z:
            for name in z.namelist():
                if not name.endswith("/"):
                    resources.append({
                        "uri": f"agentpkg://{name}",
                        "name": name,
                        "mimeType": "text/plain" if name.endswith((".json", ".txt", ".md", ".py")) else "application/octet-stream"
                    })
        return resources

    def read_resource(self, uri: str) -> str:
        file_path = uri.replace("agentpkg://", "")
        with zipfile.ZipFile(self.package_path, "r") as z:
            if file_path in z.namelist():
                return z.read(file_path).decode("utf-8", errors="ignore")
            raise FileNotFoundError(f"Recurso {file_path} no encontrado.")

    def list_tools(self) -> List[Dict[str, Any]]:
        with zipfile.ZipFile(self.package_path, "r") as z:
            if "manifest.json" in z.namelist():
                manifest = json.loads(z.read("manifest.json").decode("utf-8"))
                return manifest.get("capabilities", {}).get("tools", [])
        return []

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        if not self.allow_execution:
            raise PermissionError("Ejecución bloqueada. Se requiere autorización explícita (--allow-execution).")
        return f"Herramienta '{name}' ejecutada con argumentos: {json.dumps(arguments)}"

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        req_id = request.get("id")
        method = request.get("method")

        try:
            if method == "resources/list":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"resources": self.list_resources()}}
            elif method == "resources/read":
                uri = request.get("params", {}).get("uri", "")
                content = self.read_resource(uri)
                return {"jsonrpc": "2.0", "id": req_id, "result": {"contents": [{"uri": uri, "text": content}]}}
            elif method == "tools/list":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": self.list_tools()}}
            elif method == "tools/call":
                params = request.get("params", {})
                result = self.call_tool(params.get("name"), params.get("arguments", {}))
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": result}]}}
            else:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Metodo '{method}' no soportado"}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(e)}}

    def run_stdio(self):
        """Bucle principal de escucha STDIO para protocolo JSON-RPC MCP."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except Exception as e:
                err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"Error de JSON: {e}"}}
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
