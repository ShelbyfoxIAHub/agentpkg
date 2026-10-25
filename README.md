# agentpkg

Formato y herramientas portatiles para empaquetar, indexar y consultar conocimientos estructurados mediante IA local y MCP.

## Caracteristicas

- Manifiesto e Integridad SHA-256 (verify)
- Conectores LLM Locales (Ollama: llama3.2, nomic-embed-text)
- Busqueda Vectorial y RAG (index, search, ask)
- Servidor MCP Integrado (serve con herramientas search_package y ask_package)
- Analizadores Avanzados (PDF, DOCX, XLSX, HTML y CSV)
- Empaquetado Inteligente y .agentpkgignore

## Comandos CLI

### 1. Empaquetar y Verificar
python -m agentpkg.cli pack ./mi_carpeta -o mi_paquete.agentpkg --name "Mi Coleccion"
python -m agentpkg.cli inspect mi_paquete.agentpkg
python -m agentpkg.cli verify mi_paquete.agentpkg

### 2. Indexacion Vectorial y Consultas RAG
python -m agentpkg.cli index mi_paquete.agentpkg --model ollama:nomic-embed-text
python -m agentpkg.cli search mi_paquete.agentpkg "consulta"
python -m agentpkg.cli ask mi_paquete.agentpkg "pregunta"

### 3. Servidor MCP
python -m agentpkg.cli serve mi_paquete.agentpkg
