"""Servidor MCP de ARCHIVOS: el agente puede listar y leer archivos del proyecto.

Seguridad (privilegio mínimo):
  - Solo dentro de la carpeta raíz del proyecto (bloquea ../ y rutas absolutas).
  - Nunca entrega secretos ni carpetas internas (.env, .git, .venv, data/).
  - Lectura con tamaño máximo; escritura exclusiva de notas nuevas en docs/notas/.
IMPORTANTE: en un servidor stdio NO uses print(): stdout es el canal del protocolo.
"""
import logging
import os
import re
from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

RAIZ = Path(os.environ.get("FS_RAIZ", Path(__file__).resolve().parent.parent)).resolve()
BLOQUEADOS = {".env", ".git", ".venv", "data", ".chroma", "logs", "__pycache__"}
MAX_BYTES = 100_000

logging.basicConfig(level=logging.INFO)  # los logs van a stderr, no a stdout
log = logging.getLogger("fs_server")

mcp = MCPServer("cafe-archivos", instructions="Lee archivos y guarda notas del proyecto CaféDMC.")


def _ruta_segura(relativa: str) -> Path:
    """Convierte una ruta relativa en absoluta y verifica que siga dentro de RAIZ."""
    if Path(relativa).is_absolute():
        raise ToolError(f"Acceso denegado: '{relativa}' es una ruta absoluta")
    destino = (RAIZ / relativa).resolve()
    if not destino.is_relative_to(RAIZ):
        raise ToolError(f"Acceso denegado: '{relativa}' está fuera del proyecto")
    if BLOQUEADOS & set(destino.relative_to(RAIZ).parts):
        raise ToolError(f"Acceso denegado: '{relativa}' es una carpeta o archivo protegido")
    return destino


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
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


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def leer_archivo(ruta: str) -> str:
    """Devuelve el contenido de un archivo de texto del proyecto (ruta relativa)."""
    archivo = _ruta_segura(ruta)
    if not archivo.is_file():
        raise ToolError(f"'{ruta}' no existe o no es un archivo")
    if archivo.stat().st_size > MAX_BYTES:
        raise ToolError(f"'{ruta}' supera {MAX_BYTES} bytes; pide una parte más pequeña")
    log.info("leer_archivo %s", ruta)
    return archivo.read_text(encoding="utf-8", errors="replace")


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def contar_lineas(ruta: str) -> int:
    """Cuenta las líneas de un archivo de texto del proyecto (ruta relativa)."""
    return len(leer_archivo(ruta).splitlines())


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def buscar_texto(patron: str) -> list[str]:
    """Busca texto literal en archivos .py y .md y devuelve hasta 30 líneas."""
    coincidencias = []
    for archivo in RAIZ.rglob("*"):
        relativa = archivo.relative_to(RAIZ)
        if BLOQUEADOS.intersection(relativa.parts) or archivo.suffix not in {".py", ".md"}:
            continue
        try:
            seguro = _ruta_segura(str(relativa))
            if not seguro.is_file() or seguro.stat().st_size > MAX_BYTES:
                continue
            for numero, linea in enumerate(
                seguro.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                if patron in linea:
                    coincidencias.append(f"{relativa.as_posix()}:{numero}: {linea}")
                    if len(coincidencias) == 30:
                        return coincidencias
        except (ToolError, OSError):
            continue
    return coincidencias


@mcp.tool(annotations=ToolAnnotations(destructive_hint=False))
def guardar_nota(nombre: str, texto: str) -> str:
    """Crea una nota Markdown nueva en docs/notas, sin sobrescribir otras notas."""
    if not re.fullmatch(r"[a-z0-9-]{1,40}", nombre):
        raise ToolError("Nombre inválido: usa entre 1 y 40 letras minúsculas, números o guiones")
    if len(texto) > 5000:
        raise ToolError("La nota no puede superar 5000 caracteres")
    directorio = RAIZ / "docs" / "notas"
    if directorio.resolve() != directorio:
        raise ToolError("El directorio de notas no puede contener enlaces simbólicos")
    directorio.mkdir(parents=True, exist_ok=True)
    destino = directorio / f"{nombre}.md"
    try:
        with destino.open("x", encoding="utf-8") as archivo:
            archivo.write(texto)
    except FileExistsError as exc:
        raise ToolError(f"La nota '{nombre}' ya existe") from exc
    return f"docs/notas/{nombre}.md"


@mcp.resource("adr://lista", mime_type="text/plain")
def lista_adr() -> str:
    """Lista de decisiones de arquitectura (ADR) del proyecto."""
    return "\n".join(sorted(p.name for p in (RAIZ / "docs" / "adr").glob("*.md")))


if __name__ == "__main__":
    import sys

    if "--http" in sys.argv:  # modo remoto: http://127.0.0.1:8765/mcp
        mcp.run(transport="streamable-http", host="127.0.0.1", port=8765)
    else:
        mcp.run()  # modo local: stdio
