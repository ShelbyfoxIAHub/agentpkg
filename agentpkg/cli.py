"""Command-line interface for agentpkg."""

import argparse
import json
import sys
from pathlib import Path

from agentpkg.builder import create_package
from agentpkg.loader import inspect_package, unpack_package
from agentpkg.reader import read_package


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentpkg",
        description="Create and manage portable semantic packages for AI agents.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    pack = commands.add_parser("pack", help="Package a directory.")
    pack.add_argument("source", type=Path, help="Directory containing source files.")
    pack.add_argument("-o", "--output", required=True, type=Path, help="Output archive.")
    pack.add_argument("--title", help="Package name (defaults to the directory name).")
    pack.add_argument("--description", default="", help="Package description.")
    pack.add_argument("--author", default="", help="Package author.")

    inspect = commands.add_parser("inspect", help="Show package metadata and files.")
    inspect.add_argument("package", type=Path, help="Package to inspect.")

    read = commands.add_parser(
        "read",
        help="Read package contents as provider-neutral JSON for AI integrations.",
    )
    read.add_argument("package", type=Path, help="Package to read.")
    read.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write JSON to a file instead of standard output.",
    )

    unpack = commands.add_parser("unpack", help="Extract a package.")
    unpack.add_argument("package", type=Path, help="Package to extract.")
    unpack.add_argument("-d", "--destination", required=True, type=Path)

    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "pack":
            manifest = create_package(
                args.source,
                args.output,
                title=args.title,
                description=args.description,
                author=args.author,
            )
            print(
                "Created {} ({} files)".format(
                    args.output, manifest["data_summary"]["file_count"]
                )
            )
        elif args.command == "inspect":
            print(
                json.dumps(
                    inspect_package(args.package),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        elif args.command == "read":
            output = json.dumps(
                read_package(args.package),
                ensure_ascii=False,
                indent=2,
            )
            if args.output:
                args.output.write_text(output + "\n", encoding="utf-8")
                print("Wrote AI-readable context to {}".format(args.output))
            else:
                print(output)
        else:
            paths = unpack_package(args.package, args.destination)
            print("Extracted {} files to {}".format(len(paths), args.destination))
    except (OSError, RuntimeError, ValueError) as error:
        print("agentpkg: error: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
