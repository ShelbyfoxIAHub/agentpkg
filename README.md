# agentpkg

[English](#english) | [Español](#español)

## English

`agentpkg` is an open, ZIP-based package format and Python CLI for collecting
files with a semantic manifest for AI applications. It works offline and does
not upload package contents.

### Requirements

- Python 3.9 or newer
- Git to clone the repository

### Install

After this project is published, clone it from
[https://github.com/ShelbyfoxIAHub/agentpkg.git](https://github.com/ShelbyfoxIAHub/agentpkg.git):

```bash
git clone https://github.com/ShelbyfoxIAHub/agentpkg.git
cd agentpkg
python -m pip install .
```

For PDF, DOCX, and XLSX text extraction, install the optional document parsers:

```bash
python -m pip install ".[documents]"
```

Or install directly from the published GitHub repository:

```bash
python -m pip install "agentpkg[documents] @ git+https://github.com/ShelbyfoxIAHub/agentpkg.git"
```

For development:

```bash
python -m pip install -e ".[documents]"
python -m unittest discover -s tests -v
```

#### Windows PowerShell

From the project directory, create and install into a virtual environment, then
run the tests:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install ".[documents]"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

To use the `agentpkg` command directly, activate the environment with
`.\.venv\Scripts\Activate.ps1`. If you do not activate it, run commands with
`.\.venv\Scripts\python.exe -m agentpkg.cli`, for example:

```powershell
.\.venv\Scripts\python.exe -m agentpkg.cli --help
```

### Quick start

Package a directory with one command:

```bash
agentpkg pack ./my_documents -o my_knowledge.agentpkg --title "My Knowledge"
```

Inspect the package:

```bash
agentpkg inspect my_knowledge.agentpkg
```

Read it as provider-neutral JSON for an AI application:

```bash
agentpkg read my_knowledge.agentpkg -o ai_context.json
```

Extract the package:

```bash
agentpkg unpack my_knowledge.agentpkg -d ./extracted
```

### Package format and supported files

An `.agentpkg` file is a DEFLATE-compressed ZIP archive:

```text
my_knowledge.agentpkg
├── manifest.json
├── data/                  # Required; original files and folder structure
└── index/                 # Optional; precomputed indexes
```

Every regular file in the source directory is included recursively, regardless
of extension or content type. File bytes are preserved, including skills, MCP
configurations, vectors, graphs, databases, source code, documents, and other
binary or text files. Nested and empty directories are preserved. The current
CLI stores source files under `data/`; `index/` is reserved for optional
precomputed indexes.
Symbolic links are rejected rather than followed.

The manifest records the specification version, package name and description,
author, creation time, file count, and entry points. Extraction validates
archive paths and refuses to overwrite existing files.

### Reading packages in AI applications

The CLI `read` command and the Python `read_package(path)` API return the same
JSON-serializable structure: the manifest and each file's package path, media
type, size, and content. UTF-8 text is returned as text; other files are
base64-encoded so their original bytes can be recovered. PDF, DOCX, and XLSX
also include extracted text when the optional document parsers are installed.
PDF extraction reads selectable text; scanned pages require OCR by a separate
tool.

```python
import json
from agentpkg import read_package

context = read_package("my_knowledge.agentpkg")
provider_payload = json.dumps(context, ensure_ascii=False)
# Pass provider_payload to the model/API client you choose.
```

This interface is provider-neutral: it can be used with local models or cloud
APIs, but it does not connect to a model, require credentials, or send data
anywhere. Your application decides what to transmit. Base64 preserves binary
files losslessly; a text-only model cannot interpret arbitrary binary data
directly, so use extracted text or a format- and model-specific integration
when required. This is a package reader, not a REST server, embedding engine,
or RAG retriever. JSON output can be large; select or chunk content in your
application before sending it to a model.

## Español

`agentpkg` es un formato abierto basado en ZIP y una CLI de Python para reunir
archivos junto con un manifiesto semántico para aplicaciones de IA. Funciona
sin conexión y no sube el contenido de los paquetes.

### Requisitos

- Python 3.9 o posterior
- Git para clonar el repositorio

### Instalación

Cuando el proyecto esté publicado, clónalo desde
[https://github.com/ShelbyfoxIAHub/agentpkg.git](https://github.com/ShelbyfoxIAHub/agentpkg.git):

```bash
git clone https://github.com/ShelbyfoxIAHub/agentpkg.git
cd agentpkg
python -m pip install .
```

Para extraer texto de archivos PDF, DOCX y XLSX, instala los analizadores
opcionales:

```bash
python -m pip install ".[documents]"
```

También puedes instalar directamente desde el repositorio publicado en GitHub:

```bash
python -m pip install "agentpkg[documents] @ git+https://github.com/ShelbyfoxIAHub/agentpkg.git"
```

Para desarrollo:

```bash
python -m pip install -e ".[documents]"
python -m unittest discover -s tests -v
```

#### Windows PowerShell

Desde la carpeta del proyecto, crea e instala el entorno virtual y ejecuta las
pruebas:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install ".[documents]"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Para usar directamente el comando `agentpkg`, activa el entorno con
`.\.venv\Scripts\Activate.ps1`. Si no lo activas, ejecuta los comandos mediante
`.\.venv\Scripts\python.exe -m agentpkg.cli`, por ejemplo:

```powershell
.\.venv\Scripts\python.exe -m agentpkg.cli --help
```

### Inicio rápido

Empaqueta una carpeta con un solo comando:

```bash
agentpkg pack ./mis_documentos -o mi_conocimiento.agentpkg --title "Mi Conocimiento"
```

Inspecciona el paquete:

```bash
agentpkg inspect mi_conocimiento.agentpkg
```

Léelo como JSON neutral para integrarlo con una aplicación de IA:

```bash
agentpkg read mi_conocimiento.agentpkg -o contexto_ia.json
```

Extrae los archivos del paquete:

```bash
agentpkg unpack mi_conocimiento.agentpkg -d ./extraidos
```

### Formato del paquete y archivos compatibles

Un archivo `.agentpkg` es un ZIP comprimido con DEFLATE:

```text
mi_conocimiento.agentpkg
├── manifest.json
├── data/                  # Obligatorio; archivos originales y su estructura
└── index/                 # Opcional; índices preprocesados
```

Se incluye recursivamente cada archivo normal de la carpeta de origen, sin
importar su extensión ni tipo de contenido. Se preservan los bytes originales,
incluidos skills, configuraciones MCP, vectores, grafos, bases de datos, código
fuente, documentos y otros archivos binarios o de texto. También se conserva la
estructura de subcarpetas, incluidas las vacías. Actualmente, la CLI guarda los
archivos de origen bajo `data/`; `index/` queda reservado para índices
preprocesados opcionales.
Los enlaces simbólicos se rechazan, no se siguen.

El manifiesto registra la versión de la especificación, el nombre y descripción
del paquete, autor, fecha de creación, cantidad de archivos y puntos de entrada.
La extracción valida las rutas del archivo y no sobrescribe archivos existentes.

### Lectura desde aplicaciones de IA

El comando `read` y la API Python `read_package(path)` devuelven la misma
estructura serializable como JSON: el manifiesto y, para cada archivo, su ruta
dentro del paquete, tipo MIME, tamaño y contenido. El texto UTF-8 se devuelve
como texto; los demás archivos se codifican en base64 para recuperar sus bytes
originales. PDF, DOCX y XLSX también incluyen texto extraído si se instalaron
los analizadores opcionales.
La extracción de PDF lee texto seleccionable; las páginas escaneadas requieren
OCR mediante otra herramienta.

```python
import json
from agentpkg import read_package

contexto = read_package("mi_conocimiento.agentpkg")
datos_para_el_proveedor = json.dumps(contexto, ensure_ascii=False)
# Envía datos_para_el_proveedor al cliente del modelo o API que elijas.
```

Esta interfaz es neutral: puede usarse con modelos locales o APIs en la nube,
pero no se conecta por sí sola a un modelo, no requiere credenciales y no envía
datos a ningún servicio. Tu aplicación decide qué transmitir. Base64 conserva
los archivos binarios sin pérdida; un modelo que solo procesa texto no puede
interpretar directamente cualquier archivo binario. Cuando haga falta, usa el
texto extraído o una integración específica para el formato y el modelo.
Esta herramienta lee paquetes, pero no es un servidor REST, motor de embeddings
ni recuperador RAG. El JSON puede ser grande; selecciona o divide el contenido
en tu aplicación antes de enviarlo al modelo.

## License / Licencia

MIT. See [LICENSE](LICENSE) / Consulta [LICENSE](LICENSE).
