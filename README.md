# 📦 agentpkg

**agentpkg** es un estándar abierto, portátil y seguro para empaquetar contexto, datos, herramientas e índices de conocimiento destinados a Agentes de IA.

---

## 🚀 Características Principales

* 📦 **Empaque{Zvo Estructurado:** Genera paquetes portátiles `.agentpkg` con `data/` y `manifest.json`.
* 🏷️ **Detección Semántica:** Categoriza automáticamente contenido (`skill`, `config_mcp`, `vector`, `graph`, `database`, `dataset`, `code`, `document`).
* 🛡️ **Integridad SHA-256:** Firma por archivo y hash criptográfico global.
* 🔒 **Seguridad Estricta:** Aislamiento de rutas y bloqueo de symlinks no seguros.
* ښ�️ **Filtros Flexibles:** Soporte para `.agentpkgignore`, `--include` y `--exclude`.
* 📄 **Parsers de Documentos:** Extracción nativa de texto de `.pdf`, `.docx` y `.xlsx`.

---

## 🛠️ Estructura del Manifiesto (`manifest.json`)

```json
{
  "spec_version": "1.0",
  "name": "mi_paquete",
  "categories": ["code", "document"],
  "primary_languages": ["Python"],
  "integrity": {
    "algorithm": "sha256",
    "hash": "..."
  }
}
```

---

## 🗺️ Hoja de Ruta (Roadmap)

- [x] **Fase 1: Manifiesto Semántico e Integridad**
- [x] **Fase 2: Conectores a Modelos (`agentpkg ask`)**
- [x] **Fase 3: Índices y Búsqueda Portátil (`agentpkg search`)**
- [x] **Fase 4: Servidor MCP y Habilidades (`agentpkg serve`)**
- [x] **Fase 5: Ecosistema y Parsers Extendidos**

---

## 📄 Licencia

MIT License

