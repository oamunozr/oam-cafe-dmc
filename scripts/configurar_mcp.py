"""Genera la configuración MCP del proyecto para Claude Code, Antigravity (Gemini) y Codex.

Usa rutas ABSOLUTAS al Python del entorno de Poetry (.venv), así el agente
no necesita tener 'poetry' en su PATH. Funciona igual en Windows, macOS y Linux.

Uso:  poetry run python scripts/configurar_mcp.py            (todos los servidores existentes)
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PYTHON = Path(sys.executable)  # al correr con 'poetry run' es el Python de .venv

SERVIDORES = {
    "cafe-archivos": "mcp_servers/fs_server.py",
    "cafe-db": "mcp_servers/db_server.py",
    "cafe-contexto": "mcp_servers/rag_server.py",
}


def main() -> None:
    activos = {n: RAIZ / r for n, r in SERVIDORES.items() if (RAIZ / r).exists()}
    assert activos, "No hay servidores en mcp_servers/. Crea primero fs_server.py"
    bloque = {n: {"command": str(PYTHON), "args": [str(r)]} for n, r in activos.items()}

    # Claude Code: .mcp.json (alcance de proyecto)
    (RAIZ / ".mcp.json").write_text(json.dumps({"mcpServers": bloque}, indent=2), encoding="utf-8")

    # Antigravity (IDE, app y CLI 'agy'): .agents/mcp_config.json (lee AGENTS.md por sí solo)
    (RAIZ / ".agents").mkdir(exist_ok=True)
    (RAIZ / ".agents" / "mcp_config.json").write_text(
        json.dumps({"mcpServers": bloque}, indent=2), encoding="utf-8")

    # Gemini CLI (solo con API key de pago): .gemini/settings.json
    (RAIZ / ".gemini").mkdir(exist_ok=True)
    gemini = {"context": {"fileName": ["AGENTS.md"]}, "mcpServers": bloque}
    (RAIZ / ".gemini" / "settings.json").write_text(json.dumps(gemini, indent=2), encoding="utf-8")

    # Codex: .codex/config.toml (Codex solo lo carga si el proyecto es "trusted")
    (RAIZ / ".codex").mkdir(exist_ok=True)
    toml = []
    for n, cfg in bloque.items():
        toml += [f"[mcp_servers.{n}]",
                 f"command = {json.dumps(cfg['command'])}",
                 f"args = {json.dumps(cfg['args'])}",
                 "startup_timeout_sec = 30", ""]
    (RAIZ / ".codex" / "config.toml").write_text("\n".join(toml), encoding="utf-8")

    print("✅ Configuración escrita para:", ", ".join(activos))
    print("   Claude Code  → .mcp.json")
    print("   Antigravity  → .agents/mcp_config.json")
    print("   Codex        → .codex/config.toml")
    print("   Gemini CLI   → .gemini/settings.json")
    print("   Python del entorno:", PYTHON)


if __name__ == "__main__":
    main()