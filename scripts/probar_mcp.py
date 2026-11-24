"""Cliente MCP de prueba (sin agente): arranca un servidor y llama sus herramientas.

Uso:  poetry run python scripts/probar_mcp.py mcp_servers/fs_server.py
      poetry run python scripts/probar_mcp.py mcp_servers/fs_server.py leer_archivo ruta=AGENTS.md
      poetry run python scripts/probar_mcp.py http://127.0.0.1:8765/mcp
"""
import asyncio
import json
import sys

from mcp import Client, StdioServerParameters


async def main(servidor: str, herramienta: str | None, argumentos: dict) -> None:
    destino = servidor if servidor.startswith("http") else StdioServerParameters(
        command=sys.executable, args=[servidor])
    async with Client(destino) as cliente:
        herramientas = await cliente.list_tools()
        print("Herramientas:", [h.name for h in herramientas.tools])
        if herramienta:
            r = await cliente.call_tool(herramienta, argumentos)
            print("¿Error?:", r.is_error)
            for bloque in r.content:
                print(getattr(bloque, "text", bloque))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Indica el servidor: scripts/probar_mcp.py mcp_servers/fs_server.py")
    args = {}
    for par in sys.argv[3:]:  # argumentos como clave=valor (funciona igual en Windows)
        clave, _, valor = par.partition("=")
        try:
            args[clave] = json.loads(valor)  # números: cantidad=2
        except json.JSONDecodeError:
            args[clave] = valor  # textos: ruta=AGENTS.md
    asyncio.run(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None, args))