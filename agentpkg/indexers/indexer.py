import json
import zipfile
import urllib.error
from pathlib import Path
from typing import List, Tuple, Dict, Any
from agentpkg.indexers.chunker import chunk_text
from agentpkg.indexers.vector import VectorIndex
from agentpkg.connectors.base import ModelConnector

TEXT_EXTENSIONS = {".txt", ".md", ".py", ".js", ".ts", ".json", ".yaml", ".yml", ".html", ".css"}
MAX_CHUNKS_PER_FILE = 2000

def build_package_index(package_path: Path, connector: ModelConnector) -> int:
    vector_index = VectorIndex()
    total_chunks = 0

    with zipfile.ZipFile(package_path, "r") as z:
        text_files = [
            f for f in z.infolist()
            if f.filename.startswith("data/") and not f.is_dir() and Path(f.filename).suffix.lower() in TEXT_EXTENSIONS
        ]
        
        total_files = len(text_files)
        print(f"Archivos elegibles para indizacion: {total_files}")

        for idx, file_info in enumerate(text_files, 1):
            try:
                content = z.read(file_info.filename).decode("utf-8", errors="ignore")
                chunks = chunk_text(content, chunk_size=500, overlap=100)
                
                valid_chunks = []
                for chunk_item in chunks:
                    text_content = chunk_item.get("text", "") if isinstance(chunk_item, dict) else str(chunk_item)
                    cleaned = text_content.strip()
                    if cleaned:
                        valid_chunks.append(cleaned)
                
                if not valid_chunks:
                    continue

                if len(valid_chunks) > MAX_CHUNKS_PER_FILE:
                    print(f"[{idx}/{total_files}] Omitiendo {file_info.filename}: excede el limite de fragmentos ({len(valid_chunks)} > {MAX_CHUNKS_PER_FILE}).")
                    continue

                print(f"[{idx}/{total_files}] Indizando {file_info.filename} ({len(valid_chunks)} fragmentos en lotes)...")
                
                embeddings = connector.embed(valid_chunks)
                for chunk_text_val, emb in zip(valid_chunks, embeddings):
                    if emb:
                        vector_index.add_entry(
                            chunk_text=chunk_text_val,
                            source_file=file_info.filename,
                            embedding=emb
                        )
                        total_chunks += 1

            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8', errors='ignore')
                print(f"Error API ({e.code}) en {file_info.filename}: {error_body}")
            except Exception as e:
                print(f"Error al procesar {file_info.filename}: {e}")

    temp_zip = package_path.with_suffix(".tmp.agentpkg")
    with zipfile.ZipFile(package_path, "r") as src_zip:
        with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as dst_zip:
            for item in src_zip.infolist():
                if item.filename != "index/vector_index.json":
                    dst_zip.writestr(item, src_zip.read(item.filename))
            dst_zip.writestr("index/vector_index.json", vector_index.to_json())

    temp_zip.replace(package_path)
    return total_chunks

def search_package_index(package_path: Path, query: str, connector: ModelConnector, top_k: int = 3) -> List[Tuple[float, Dict[str, Any]]]:
    with zipfile.ZipFile(package_path, "r") as z:
        if "index/vector_index.json" not in z.namelist():
            raise FileNotFoundError("El paquete no contiene un indice vectorial en 'index/vector_index.json'. Ejecuta 'agentpkg index' primero.")
        index_data = z.read("index/vector_index.json").decode("utf-8")
        vector_index = VectorIndex.from_json(index_data)

    embeddings = connector.embed([query])
    if not embeddings or not embeddings[0]:
        return []
    return vector_index.search(embeddings[0], top_k=top_k)
