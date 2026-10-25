import argparse
import sys
from pathlib import Path
from agentpkg.builder import create_package
from agentpkg.verifier import verify_package_integrity
from agentpkg.repo import clone_and_pack_repo

def main():
    parser = argparse.ArgumentParser(prog="agentpkg", description="Herramientas para empaquetar e indexar conocimiento para IA.")
    subparsers = parser.add_subparsers(dest="command", help="Subcomandos disponibles")

    # pack
    pack_p = subparsers.add_parser("pack", help="Empaquetar un directorio local")
    pack_p.add_argument("source", help="Directorio origen")
    pack_p.add_argument("-o", "--output", required=True, help="Archivo .agentpkg de salida")
    pack_p.add_argument("--name", help="Nombre del paquete")

    # pack-repo
    repo_p = subparsers.add_parser("pack-repo", help="Clonar y empaquetar un repositorio Git")
    repo_p.add_argument("url", help="URL del repositorio Git (ej. https://github.com/user/repo.git)")
    repo_p.add_argument("-o", "--output", required=True, help="Archivo .agentpkg de salida")
    repo_p.add_argument("--name", help="Nombre personalizado para el paquete")

    # verify
    verify_p = subparsers.add_parser("verify", help="Verificar la integridad SHA-256 de un paquete")
    verify_p.add_argument("package", help="Ruta al archivo .agentpkg")

    args = parser.parse_args()

    if args.command == "pack":
        out = create_package(source=Path(args.source), destination=Path(args.output), title=args.name)
        print(f"Paquete creado con exito: {args.output}")
    elif args.command == "pack-repo":
        print(f"Clonando y empaquetando repositorio desde {args.url}...")
        out = clone_and_pack_repo(args.url, args.output, name=args.name)
        print(f"Repositorio empaquetado con exito en: {args.output}")
    elif args.command == "verify":
        valid, msgs = verify_package_integrity(args.package)
        status = "OK" if valid else "FALLO"
        print(f"Estado de verificacion: {status}")
        for m in msgs:
            print(f"  - {m}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
