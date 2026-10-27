import json
from pathlib import Path
import pytest
from agentpkg.inspector import inspect_package

def test_package_conformance():
    package_path = Path("ecc.agentpkg")
    assert package_path.exists(), "El paquete ecc.agentpkg debe existir para ejecutar las pruebas."
    
    info = inspect_package(package_path)
    
    # 📋 Validar campos obligatorios del manifiesto
    assert "manifest" in info, "El paquete debe contener un manifiesto."
    manifest = info["manifest"]
    assert "title" in manifest, "El manifiesto debe incluir un título."
    assert "spec_version" in manifest, "El manifiesto debe especificar la versión del estándar."
    assert "categories" in manifest, "El manifiesto debe declarar categorías."
    assert "primary_languages" in manifest, "El manifiesto debe declarar lenguajes principales."
    
    # 🛡️ Validar lista de archivos
    assert "files" in info, "El paquete debe listar sus archivos."
    assert isinstance(info["files"], list), "La lista de archivos debe ser una lista."
    assert len(info["files"]) > 0, "El paquete debe contener archivos."
