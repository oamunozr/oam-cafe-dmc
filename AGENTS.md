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

## Arquitectura
- `app/`: API, interfaz y lógica del sistema.
- `tests/`: pruebas automatizadas.
- `scripts/`: scripts auxiliares.
- `db/`: base SQLite y recursos de persistencia.
- `docs/adr/`: decisiones de arquitectura.

## Reglas
- Agregar dependencias únicamente con `poetry add`.
- Agregar dependencias de desarrollo con `poetry add --group dev`.
- Usar SQL parametrizado; nunca interpolar valores en consultas.
- Cada endpoint debe tener al menos una prueba.
- No leer `.env` ni el contenido de `data/`.
- Mantener `package-mode = false`.
- No documentar comandos de ejecución que todavía no existan.
- Mantener instalado el hook de pre-commit y corregir los errores de Ruff antes de crear un commit; no omitir el hook.
