"""Command line interface for agentpkg."""

import argparse
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

from agentpkg.builder import create_package
from agentpkg.connectors import get_connector
from agentpkg.indexers import SimpleVectorIndex
from agentpkg.parsers import parse_bytes
from agentpkg.reader import read_package
from agentpkg.verifier import verify_package_integrity


def cmd_pack(args):
    """Handler for 'agentpkg pack'."""
    create_package(
        source=Path(args.source),
        destination=Path(args.output),
        title=args.name,
        description=args.description,
    )
    print(f"Successfully created package: {args.output}")


def cmd_inspect(args):
    """Handler for 'agentpkg inspect'."""
    data = read_package(args.package)
    manifest = data.get("manifest", {})
    files = data.get("files", [])

    print(f"Package Name: {manifest.get('name')}")
    print(f"Version:      {manifest.get('version', 'N/A')}")
    print(f"Description:  {manifest.get('description')}")
    print(f"Spec Version: {manifest.get('spec_version')}")
    print(f"Files count:  {len(files)}")
    print("\nFile contents overview:")
    for file_info in files:
        print(f"  - {file_info.get('path')}")


def cmd_read(args):
    """Handler for 'agentpkg read'."""
    data = read_package(args.package)
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_unpack(args):
    """Handler for 'agentpkg unpack'."""
    os.makedirs(args.output, exist_ok=True)
    with zipfile.ZipFile(args.package, "r") as zip_ref:
        zip_ref.extractall(args.output)
    print(f"Extracted '{args.package}' to '{args.output}'")


def cmd_verify(args):
    """Handler for 'agentpkg verify'."""
    print(f"Verificando integridad SHA-256 del paquete '{args.package}'...\n")
    is_valid, errors = verify_package_integrity(args.package)
    if is_valid:
        print(" INTEGRIDAD CONFIRMADA: Todos los hashes SHA-256 coinciden correctamente.")
    else:
        print(" FALLO DE INTEGRIDAD: Se detectaron los siguientes problemas:")
        for err in errors:
            print(f"  - {err}")


def cmd_serve(args):
    """Handler for 'agentpkg serve' (MCP Server mode)."""
    from agentpkg.mcp_server import run_mcp_server
    run_mcp_server(
        package_path=args.package,
        model_spec=args.model,
        embed_model_spec=args.embed_model,
    )


def cmd_index(args):
    """Handler for 'agentpkg index'."""
    print(f"Indexing package '{args.package}' using model spec '{args.model}'...")
    connector = get_connector(args.model)

    documents = []
    with zipfile.ZipFile(args.package, "r") as zip_ref:
        for name in zip_ref.namelist():
            if name.startswith("data/") and not name.endswith("/"):
                content_bytes = zip_ref.read(name)
                text = parse_bytes(content_bytes, name)
                if text.strip():
                    documents.append({"file_path": name, "content": text})

    if not documents:
        print("No indexable documents found in 'data/'.")
        return

    print(f"Extracted text from {len(documents)} document(s). Generating vector index...")
    index = SimpleVectorIndex()
    index.build_from_documents(documents, connector, chunk_size=args.chunk_size)

    temp_dir = tempfile.mkdtemp(dir=Path(args.package).parent)
    temp_pkg = os.path.join(temp_dir, "updated.agentpkg")

    with zipfile.ZipFile(args.package, "r") as src_zip:
        with zipfile.ZipFile(temp_pkg, "w", zipfile.ZIP_DEFLATED) as dst_zip:
            for item in src_zip.infolist():
                if not item.filename.startswith("index/"):
                    dst_zip.writestr(item, src_zip.read(item.filename))

            index_json = json.dumps(index.to_dict(), indent=2, ensure_ascii=False)
            dst_zip.writestr("index/index.json", index_json)

    os.replace(temp_pkg, args.package)
    print(f"Successfully built index with {len(index.entries)} entries and saved to '{args.package}'.")


def cmd_search(args):
    """Handler for 'agentpkg search'."""
    connector = get_connector(args.model)

    with zipfile.ZipFile(args.package, "r") as zip_ref:
        if "index/index.json" not in zip_ref.namelist():
            print("Error: Package does not contain an index. Run 'agentpkg index' first.")
            return

        index_data = json.loads(zip_ref.read("index/index.json").decode("utf-8"))

    index = SimpleVectorIndex.from_dict(index_data)
    query_vector = connector.embed([args.query])[0]
    results = index.search(query_vector, top_k=args.top_k)

    print(f"\nTop {len(results)} search results for query: '{args.query}'\n" + "-" * 50)
    for i, res in enumerate(results, 1):
        print(f"[{i}] Score: {res['score']:.4f} | File: {res['file_path']}")
        print(f"    Text: {res['text'].strip()}\n")


def cmd_ask(args):
    """Handler for 'agentpkg ask' (RAG Query)."""
    embed_connector = get_connector(args.embed_model)
    llm_connector = get_connector(args.model)

    with zipfile.ZipFile(args.package, "r") as zip_ref:
        if "index/index.json" not in zip_ref.namelist():
            print("Error: Package does not contain an index. Run 'agentpkg index' first.")
            return

        index_data = json.loads(zip_ref.read("index/index.json").decode("utf-8"))

    index = SimpleVectorIndex.from_dict(index_data)
    query_vector = embed_connector.embed([args.question])[0]
    results = index.search(query_vector, top_k=args.top_k)

    context_str = "\n---\n".join([r["text"].strip() for r in results])
    
    prompt = (
        f"Responde a la siguiente pregunta utilizando ÚNICAMENTE la información del contexto proporcionado.\n"
        f"Si la información no está en el contexto, indica amablemente que no dispones de esos datos.\n\n"
        f"Contexto del paquete '{args.package}':\n{context_str}\n\n"
        f"Pregunta: {args.question}"
    )

    messages = [{"role": "user", "content": prompt}]
    print(f"Consultando a {args.model} con el contexto recuperado...\n")
    response = llm_connector.chat(messages)
    print("Respuesta:")
    print(response)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="agentpkg", description="CLI tool for .agentpkg files")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # pack
    p_pack = subparsers.add_parser("pack", help="Build a .agentpkg package from a folder")
    p_pack.add_argument("source", help="Source directory")
    p_pack.add_argument("-o", "--output", required=True, help="Output .agentpkg path")
    p_pack.add_argument("--name", help="Package name")
    p_pack.add_argument("--description", default="", help="Package description")
    p_pack.add_argument("--version", default="0.1.0", help="Package version")
    p_pack.set_defaults(func=cmd_pack)

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect .agentpkg manifest and files")
    p_inspect.add_argument("package", help="Path to .agentpkg file")
    p_inspect.set_defaults(func=cmd_inspect)

    # verify
    p_verify = subparsers.add_parser("verify", help="Verify SHA-256 integrity of files in package")
    p_verify.add_argument("package", help="Path to .agentpkg file")
    p_verify.set_defaults(func=cmd_verify)

    # serve (MCP)
    p_serve = subparsers.add_parser("serve", help="Expose package content via MCP over stdio")
    p_serve.add_argument("package", help="Path to .agentpkg file")
    p_serve.add_argument("--model", default="ollama:llama3.2", help="LLM model spec")
    p_serve.add_argument("--embed-model", default="ollama:nomic-embed-text", help="Embedding model spec")
    p_serve.set_defaults(func=cmd_serve)

    # read
    p_read = subparsers.add_parser("read", help="Read package as JSON")
    p_read.add_argument("package", help="Path to .agentpkg file")
    p_read.set_defaults(func=cmd_read)

    # unpack
    p_unpack = subparsers.add_parser("unpack", help="Unpack .agentpkg to directory")
    p_unpack.add_argument("package", help="Path to .agentpkg file")
    p_unpack.add_argument("-o", "--output", required=True, help="Destination directory")
    p_unpack.set_defaults(func=cmd_unpack)

    # index
    p_index = subparsers.add_parser("index", help="Index document contents in package")
    p_index.add_argument("package", help="Path to .agentpkg file")
    p_index.add_argument("--model", default="ollama:nomic-embed-text", help="Embedding model spec")
    p_index.add_argument("--chunk-size", type=int, default=500, help="Chunk size in characters")
    p_index.set_defaults(func=cmd_index)

    # search
    p_search = subparsers.add_parser("search", help="Search indexed content in package")
    p_search.add_argument("package", help="Path to .agentpkg file")
    p_search.add_argument("query", help="Search query string")
    p_search.add_argument("--model", default="ollama:nomic-embed-text", help="Embedding model spec")
    p_search.add_argument("--top-k", type=int, default=3, help="Number of top results")
    p_search.set_defaults(func=cmd_search)

    # ask
    p_ask = subparsers.add_parser("ask", help="Ask a question about the package content (RAG)")
    p_ask.add_argument("package", help="Path to .agentpkg file")
    p_ask.add_argument("question", help="Question string")
    p_ask.add_argument("--model", default="ollama:llama3.2", help="LLM model spec for generation")
    p_ask.add_argument("--embed-model", default="ollama:nomic-embed-text", help="Embedding model spec for retrieval")
    p_ask.add_argument("--top-k", type=int, default=3, help="Number of context chunks to retrieve")
    p_ask.set_defaults(func=cmd_ask)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
