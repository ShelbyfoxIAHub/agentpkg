import json
import zipfile
from pathlib import Path
from agentpkg.builder import create_package, load_ignore_patterns, is_ignored
from agentpkg.parsers import parse_file
from agentpkg.mcp import MCPServer

def test_ignore_patterns(tmp_path):
    # Crear estructura de prueba con archivo ignorado
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "valid.txt").write_text("Texto valido", encoding="utf-8")
    (src_dir / "temp.tmp").write_text("Temporal", encoding="utf-8")
    
    pkg_file = tmp_path / "test.agentpkg"
    create_package(src_dir, pkg_file)
    
    with zipfile.ZipFile(pkg_file, "r") as z:
        names = z.namelist()
        assert "data/valid.txt" in names
        assert "data/temp.tmp" not in names

def test_parsers(tmp_path):
    html_file = tmp_path / "doc.html"
    html_file.write_text("<html><body><h1>Titulo</h1><script>var x=1;</script><p>Contenido</p></body></html>", encoding="utf-8")
    text = parse_file(html_file)
    assert "Titulo" in text
    assert "Contenido" in text
    assert "var x=1" not in text

def test_mcp_security(tmp_path):
    pkg_file = tmp_path / "empty.agentpkg"
    src_dir = tmp_path / "empty_src"
    src_dir.mkdir()
    (src_dir / "data.txt").write_text("hello", encoding="utf-8")
    create_package(src_dir, pkg_file)
    
    server = MCPServer(pkg_file, allow_execution=False)
    resp = server.handle_request({"id": 1, "method": "tools/call", "params": {"name": "test_tool"}})
    assert "error" in resp
