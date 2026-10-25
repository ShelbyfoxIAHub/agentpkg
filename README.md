# agentpkg

Formato y conjunto de herramientas portatiles para empaquetar, indexar y consultar repositorios, habilidades e indices estructurados para IA local y MCP.

![agentpkg Architecture](https://raw.githubusercontent.com/ShelbyfoxIAHub/agentpkg/main/docs/architecture.png)

## Caracteristicas
- 📜 Manifiesto Semantico e Integridad SHA-256 (`verify`)
- 🤖 Conectores LLM Locales (Ollama: `llama3.2`, `nomic-embed-text`)
- 🔍 Busqueda Vectorial y RAG (`index`, `search`, `ask`)
- 🔌 Servidor MCP Integrado (`serve`)
- 📄 Analizadores Avanzados (PDF, DOCX, XLSX, HTML, CSV)
- 📦 Clonado y Empaquetado Directo de Repositorios Git (`pack-repo`)

## Comandos CLI

### Clonar y Empaquetar Repositorios Git
python -m agentpkg.cli pack-repo https://github.com/usuario/repositorio.git -o repo.agentpkg

### Inspeccionar e Indexar
python -m agentpkg.cli inspect repo.agentpkg
python -m agentpkg.cli index repo.agentpkg --model ollama:nomic-embed-text
