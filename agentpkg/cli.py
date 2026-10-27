import argparse
import json
import sys
from pathlib import Path
from agentpkg.builder import create_package
from agentpkg.inspector import inspect_package
from agentpkg.reader import read_package
from agentpkg.indexers.indexer import build_package_index, search_package_index
from agentpkg.connectors.ollama import OllamaConnector
from agentpkg.connectors.openai import OpenAIConnector
from agentpkg.server.mcp_server import MCPServer

def parse_connector(model_str: str):
    if ":" in model_str:
        provider, model_name = model_str.split(":", 1)
    else:
        provider, model_name = "ollama", model_str

    if provider.lower() == "ollama":
        return OllamaConnector(model=model_name)
    elif provider.lower() in ("openai", "gpt"):
        return OpenAIConnector(model=model_name)
    else:
        raise ValueError(f"Proveedor de modelo no soportado: {provider}")

def main():
    parser = argparse.ArgumentParser(prog="agentpkg", description="Herramienta CLI para paquetes AgentPKG")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # pack
    pack_p = subparsers.add_parser("pack", help="Empaquetar directorio")
    pack_p.add_argument("source", type=Path)
    pack_p.add_argument("output", type=Path)
    pack_p.add_argument("--title", type=str, default="")

    # inspect
    inspect_p = subparsers.add_parser("inspect", help="Inspeccionar paquete")
    inspect_p.add_argument("package", type=Path)

    # index
    index_p = subparsers.add_parser("index", help="Generar indice vectorial")
    index_p.add_argument("package", type=Path)
    index_p.add_argument("--model", type=str, default="ollama:nomic-embed-text:latest")

    # search
    search_p = subparsers.add_parser("search", help="Buscar en el indice vectorial")
    search_p.add_argument("package", type=Path)
    search_p.add_argument("query", type=str)
    search_p.add_argument("--model", type=str, default="ollama:nomic-embed-text:latest")
    search_p.add_argument("--top-k", type=int, default=3)

    # serve
    serve_p = subparsers.add_parser("serve", help="Iniciar servidor MCP")
    serve_p.add_argument("package", type=Path)

    # run-skill
    run_p = subparsers.add_parser("run-skill", help="Ejecutar una habilidad del paquete")
    run_p.add_argument("package", type=Path)
    run_p.add_argument("skill_name", type=str)
    run_p.add_argument("--params", type=str, default="{}")
    run_p.add_argument("--approve", action="store_true", help="Otorgar autorizacion de ejecucion")

    args = parser.parse_args()

    if args.command == "pack":
        create_package(args.source, args.output, title=args.title)
        print(f"Paquete creado exitosamente: {args.output.resolve()}")
    elif args.command == "inspect":
        info = inspect_package(args.package)
        print(json.dumps(info, indent=2, ensure_ascii=False))
    elif args.command == "index":
        connector = parse_connector(args.model)
        total = build_package_index(args.package, connector)
        print(f"Indice vectorial creado exitosamente con {total} fragmentos.")
    elif args.command == "search":
        connector = parse_connector(args.model)
        results = search_package_index(args.package, args.query, connector, top_k=args.top_k)
        print(f"\nResultados para: '{args.query}' (Top {args.top_k})\n" + "="*50)
        for score, entry in results:
            source = entry.get("source", "Desconocido")
            text = entry.get("text", "")
            print(f"Puntaje de similitud: {score:.4f} | Archivo: {source}")
            print(f"Texto: {text}\n" + "-"*50)
    elif args.command == "serve":
        server = MCPServer(args.package)
        print(f"Servidor MCP iniciado para el paquete: {args.package.resolve()}\n")
        print("Recursos expuestos:")
        print(json.dumps(server.list_resources(), indent=2, ensure_ascii=False))
        print("\nHerramientas (skills) disponibles:")
        print(json.dumps(server.list_tools(), indent=2, ensure_ascii=False))
    elif args.command == "run-skill":
        server = MCPServer(args.package)
        try:
            params_dict = json.loads(args.params)
        except json.JSONDecodeError:
            print("Error: El argumento --params debe ser un JSON valido.")
            return
        
        res = server.execute_tool(args.skill_name, params_dict, approved=args.approve)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
