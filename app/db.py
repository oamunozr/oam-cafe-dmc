"""Acceso a SQLite compartido por los dos contextos (catálogo y pedidos)."""
import os
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import Depends

RAIZ = Path(__file__).resolve().parent.parent


def ruta_db() -> Path:
    """La ruta se puede cambiar con la variable CAFE_DB (las pruebas usan una base temporal)."""
    return Path(os.environ.get("CAFE_DB", RAIZ / "data" / "cafe.db"))


def get_conexion() -> Iterator[sqlite3.Connection]:
    """Dependencia de FastAPI: abre una conexión por petición y la cierra al final."""
    con = sqlite3.connect(ruta_db())
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
    finally:
        con.close()


# Tipo reutilizable para inyectar la conexión en los endpoints
Conexion = Annotated[sqlite3.Connection, Depends(get_conexion)]