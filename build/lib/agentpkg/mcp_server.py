"""Model Context Protocol (MCP) server for agentpkg using stdio."""

import json
import sys
import zipfile
from agentpkg.connectors import get_connector
from agentpkg.indexers import SimpleVectorIndex


def run_mcp_server(package_path: str, model_spec: str = "ollama:llama3.2", embed_model_spec: str = "ollama:nomic-embed-text"):
    """Run MCP server over stdio reading commands as JSON-RPC."""

    def search_tool(query: str, top_k: int = 3):
        embed_conn = get_connector(embed_model_spec)
        with zipfile.ZipFile(package_path, "r") as zip_ref:
            if "index/index.json" not in zip_ref.namelist():
                return "Error: El paquete no está indexado."
            index_data = json.loads(zip_ref.read("index/index.json").decode("utf-8"))

        index = SimpleVectorIndex.from_dict(index_data)
        query_vector = embed_conn.embed([query])[0]
        results = index.search(query_vector, top_k=top_k)

        out = []
        for i, res in enumerate(results, 1):
            out.append(f"[{i}] Archivo: {res['file_path']} (Score: {res['score']:.4f})\n{res['text'].strip()}\n")
        return "\n".join(out)

    def ask_tool(question: str, top_k: int = 3):
        context_text = search_tool(question, top_k=top_k)
        if "Error:" in context_text:
            return context_text

        llm_conn = get_connector(model_spec)
        prompt = (
            f"Responde usando ÚNICAMENTE el contexto del paquete '{package_path}':\n"
            f"{context_text}\n\nPregunta: {question}"
        )
        return llm_conn.chat([{"role": "user", "content": prompt}])

    # Loop principal JSON-RPC sobre stdio
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "initialize":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "agentpkg-mcp", "version": "0.1.0"},
                    },
                }
            elif method == "tools/list":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": [
                            {
                                "name": "search_package",
                                "description": "Busca fragmentos relevantes por similitud semántica en el paquete.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {"query": {"type": "string"}},
                                    "required": ["query"],
                                },
                            },
                            {
                                "name": "ask_package",
                                "description": "Realiza una pregunta RAG directa sobre el contenido del paquete.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {"question": {"type": "string"}},
                                    "required": ["question"],
                                },
                            },
                        ]
                    },
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})

                if tool_name == "search_package":
                    content = search_tool(args.get("query", ""))
                elif tool_name == "ask_package":
                    content = ask_tool(args.get("question", ""))
                else:
                    content = f"Herramienta desconocida: {tool_name}"

                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": content}]},
                }
            else:
                res = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}

            sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
            sys.stdout.flush()

        except Exception as err:
            err_res = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(err)}}
            sys.stdout.write(json.dumps(err_res, ensure_ascii=False) + "\n")
            sys.stdout.flush()
