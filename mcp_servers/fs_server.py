"""Servidor MCP de ARCHIVOS: el agente puede listar y leer archivos del proyecto.

Seguridad (privilegio mínimo):
  - Solo dentro de la carpeta raíz del proyecto (bloquea ../ y rutas absolutas).
  - Nunca entrega secretos ni carpetas internas (.env, .git, .venv, data/).
  - Solo lectura y con tamaño máximo.
IMPORTANTE: en un servidor stdio NO uses print(): stdout es el canal del protocolo.
"""
import logging
import os
from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

RAIZ = Path(os.environ.get("FS_RAIZ", Path(__file__).resolve().parent.parent)).resolve()
BLOQUEADOS = {".env", ".git", ".venv", "data", ".chroma", "logs", "__pycache__"}
MAX_BYTES = 100_000

logging.basicConfig(level=logging.INFO)  # los logs van a stderr, no a stdout
log = logging.getLogger("fs_server")

mcp = MCPServer("cafe-archivos", instructions="Lee archivos del proyecto CaféDMC (solo lectura).")


def _ruta_segura(relativa: str) -> Path:
    """Convierte una ruta relativa en absoluta y verifica que siga dentro de RAIZ."""
    destino = (RAIZ / relativa).resolve()
    if not destino.is_relative_to(RAIZ):
        raise ToolError(f"Acceso denegado: '{relativa}' está fuera del proyecto")
    if BLOQUEADOS & set(destino.relative_to(RAIZ).parts):
        raise ToolError(f"Acceso denegado: '{relativa}' es una carpeta o archivo protegido")
    return destino


@mcp.tool()
def listar_archivos(carpeta: str = ".") -> list[str]:
    """Lista archivos y carpetas dentro de una carpeta del proyecto (ruta relativa)."""
    base = _ruta_segura(carpeta)
    if not base.is_dir():
        raise ToolError(f"'{carpeta}' no es una carpeta")
    log.info("listar_archivos %s", carpeta)
    return sorted(
        p.name + ("/" if p.is_dir() else "")
        for p in base.iterdir()
        if p.name not in BLOQUEADOS
    )


@mcp.tool()
def leer_archivo(ruta: str) -> str:
    """Devuelve el contenido de un archivo de texto del proyecto (ruta relativa)."""
    archivo = _ruta_segura(ruta)
    if not archivo.is_file():
        raise ToolError(f"'{ruta}' no existe o no es un archivo")
    if archivo.stat().st_size > MAX_BYTES:
        raise ToolError(f"'{ruta}' supera {MAX_BYTES} bytes; pide una parte más pequeña")
    log.info("leer_archivo %s", ruta)
    return archivo.read_text(encoding="utf-8", errors="replace")


if __name__ == "__main__":
    import sys

    if "--http" in sys.argv:  # modo remoto: http://127.0.0.1:8765/mcp
        mcp.run(transport="streamable-http", host="127.0.0.1", port=8765)
    else:
        mcp.run()  # modo local: stdio