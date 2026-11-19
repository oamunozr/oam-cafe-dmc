# ADR 0002: Migraciones de base de datos con Alembic

## Estado
Propuesto.

## Fecha
2026-11-18.

## Contexto
CaféDMC usa SQLite y define su esquema en `db/schema.sql`. El script de creación ejecuta ese esquema y carga datos de prueba en una base nueva. Las sentencias `CREATE TABLE IF NOT EXISTS` crean tablas faltantes, pero no actualizan las existentes cuando cambia su definición. La opción de reinicio elimina la base y sus datos.

Necesitamos una forma de registrar y aplicar cambios de esquema en orden, tanto en bases nuevas como en bases existentes, sin depender de recrearlas.

## Decisión
Adoptar Alembic para versionar y aplicar las migraciones de esquema de SQLite. Las migraciones serán la fuente de verdad del esquema; se retirará `db/schema.sql` como fuente independiente cuando se implemente la transición.

Inicialmente las migraciones se escribirán y revisarán manualmente. No se introducirán modelos ORM únicamente para generar migraciones automáticamente. La aplicación podrá seguir accediendo a SQLite mediante `sqlite3`.

La implementación deberá contemplar:

- Crear una revisión inicial equivalente al esquema actual, con sus índices y restricciones.
- Para bases existentes, comprobar su equivalencia con esa revisión antes de marcarlas como correspondientes a ella; marcar una revisión no modifica ni valida el esquema. Resolver cualquier diferencia antes de continuar.
- Separar la carga de datos de prueba de las migraciones de esquema y mantener una forma explícita de cargar esos datos.
- Probar la creación desde una base vacía y la actualización de una base anterior que contenga datos.
- Revisar los cambios que requieran recrear tablas en SQLite, especialmente sus restricciones y claves foráneas, y prever respaldos cuando corresponda.

## Consecuencias (+/−)
- **+** El historial de revisiones permite identificar y aplicar los cambios de esquema pendientes de forma ordenada.
- **+** Las bases existentes pueden evolucionar sin recurrir necesariamente a su eliminación y recreación.
- **+** Alembic puede convivir con el acceso actual mediante `sqlite3`.
- **−** Se añaden Alembic y SQLAlchemy, su configuración y el mantenimiento de las revisiones.
- **−** Las migraciones requieren revisión y pruebas; algunas operaciones de SQLite necesitan recrear tablas y copiar datos.
- **−** La generación automática requeriría metadatos de SQLAlchemy y aun así produciría migraciones candidatas que deben revisarse.

## Alternativas consideradas
- **Archivos SQL numerados y un registro de versión en SQLite:** menos dependencias, pero el proyecto tendría que implementar y mantener la aplicación ordenada y el seguimiento de migraciones.
- **Mantener el esquema actual y recrear la base:** es sencillo durante el desarrollo inicial, pero no ofrece evolución versionada y el reinicio elimina los datos.
- **Introducir modelos ORM y usar generación automática:** puede reducir trabajo repetitivo, pero añade otra representación del esquema y complejidad que aún no necesitamos.
