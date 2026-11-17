# ADR 0001: Stack tecnológico

## Estado
Propuesto.

## Fecha
2026-11-16.

## Contexto
El equipo conoce Python y cada alumno ejecutará el sistema en su laptop, sin Docker. Los agentes de IA deben poder leer, probar y modificar el sistema.

## Decisión
Usar Python 3.11+, Poetry, FastAPI con Pydantic, SQLite, Streamlit, pytest y ruff.

## Consecuencias (+/−)
- **+** Un lenguaje conocido y herramientas accesibles simplifican el desarrollo y las pruebas locales.
- **+** SQLite evita instalar un servidor de base de datos.
- **−** SQLite limita la concurrencia de escritura y puede requerir una migración si crece la carga.
- **−** API e interfaz son componentes separados que deben mantenerse coordinados.

## Alternativas consideradas
- **Django:** ofrece administración y componentes integrados, pero añade estructura que no es necesaria para esta API y la interfaz Streamlit.
- **PostgreSQL:** ofrece mejor concurrencia y capacidades para despliegues mayores, a cambio de instalar y administrar un servidor local.
