import os
import shutil
import subprocess
import tempfile
import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Tuple
from agentpkg.builder import create_package

LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "React/JavaScript",
    ".tsx": "React/TypeScript",
    ".rs": "Rust",
    ".go": "Go",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".java": "Java",
    ".html": "HTML",
    ".css": "CSS",
    ".md": "Markdown",
    ".sql": "SQL",
    ".sh": "Shell",
    ".ps1": "PowerShell"
}

def analyze_repo_languages(repo_dir: Path) -> List[str]:
    """Analiza los lenguajes principales segun el tamaño total ocupado por extension."""
    stats: Dict[str, int] = {}
    
    for root, _, files in os.walk(repo_dir):
        if ".git" in root or "__pycache__" in root:
            continue
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in LANGUAGE_EXTENSIONS:
                lang = LANGUAGE_EXTENSIONS[ext]
                filepath = Path(root) / file
                try:
                    stats[lang] = stats.get(lang, 0) + filepath.stat().st_size
                except OSError:
                    pass
                    
    sorted_langs = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    return [lang for lang, _ in sorted_langs[:3]]

def clone_and_pack_repo(repo_url: str, output_path: str, name: str = None) -> dict:
    """Clona un repositorio remoto y lo empaqueta como .agentpkg."""
    with tempfile.TemporaryDirectory() as temp_dir:
        target_dir = Path(temp_dir) / "repo"
        
        # 1. Clonado ligero (--depth 1)
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 2. Deteccion de metadatos
        languages = analyze_repo_languages(target_dir)
        repo_name = name or Path(repo_url.rstrip("/")).stem.replace(".git", "")
        
        # 3. Empaquetado usando la firma exacta de create_package
        out_pkg = create_package(
            source=target_dir,
            destination=Path(output_path),
            title=repo_name,
            description=f"Empaquetado automatico del repositorio {repo_url}"
        )
        
        return out_pkg

def search_github_repos(query: str, limit: int = 5) -> List[dict]:
    """Busca repositorios publicos en GitHub por termino de busqueda."""
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.github.com/search/repositories?q={encoded_query}&per_page={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "agentpkg-cli"})
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            items = data.get("items", [])
            results = []
            for item in items:
                results.append({
                    "full_name": item.get("full_name"),
                    "description": item.get("description"),
                    "stars": item.get("stargazers_count"),
                    "clone_url": item.get("clone_url")
                })
            return results
    except Exception as e:
        print(f"Error al consultar la API de GitHub: {e}")
        return []
