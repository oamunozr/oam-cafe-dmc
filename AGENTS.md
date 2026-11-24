# CaféDMC

## Qué es el sistema
CaféDMC es un sistema de pedidos para una cafetería.
Usa una API FastAPI, una pantalla Streamlit y SQLite, con Poetry (`package-mode = false`).

## Comandos
- Instalar dependencias: `poetry install`
- Ejecutar pruebas: `poetry run pytest -q`
- Revisar estilo: `poetry run ruff check .`
- Instalar el hook de Git: `poetry run pre-commit install`
- Ejecutar los hooks en todos los archivos: `poetry run pre-commit run --all-files`
- Crear la base de datos: `poetry run python scripts/crear_bd.py`

## Arquitectura
- `app/`: API, interfaz y lógica del sistema.
- `tests/`: pruebas automatizadas.
- `scripts/`: scripts auxiliares.
- `db/`: base SQLite y recursos de persistencia.
- `docs/adr/`: decisiones de arquitectura.

## Reglas
- Ejecutar los scripts y comandos de Python del proyecto mediante `poetry run`.
- Agregar dependencias únicamente con `poetry add`.
- Agregar dependencias de desarrollo con `poetry add --group dev`.
- Usar SQL parametrizado; nunca interpolar valores en consultas.
- Cada endpoint debe tener al menos una prueba.
- No leer `.env` ni el contenido de `data/`.
- Mantener `package-mode = false`.
- No documentar comandos de ejecución que todavía no existan.
- Mantener instalado el hook de pre-commit y corregir los errores de Ruff antes de crear un commit; no omitir el hook.

## Herramientas MCP
- cafe-archivos: lee archivos del proyecto (solo lectura, sin .env/.git/data).
- Probar sin agente: `poetry run python scripts/probar_mcp.py mcp_servers/fs_server.py`
- Regenerar configuración: `poetry run python scripts/configurar_mcp.py`