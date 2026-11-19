"""Migra la base antigua conservando sus columnas y datos originales."""
import os
import sqlite3
from pathlib import Path


def migrar(ruta: Path) -> Path:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe la base de datos: {ruta}")
    copia = ruta.with_name(ruta.stem + ".antes_migracion.db")
    if copia.exists():
        raise FileExistsError(f"Ya existe la copia de seguridad: {copia}")
    con = sqlite3.connect(ruta)
    try:
        columnas = {
            tabla: {fila[1] for fila in con.execute(f"PRAGMA table_info({tabla})")}
            for tabla in ("productos", "pedidos", "detalle_pedido")
        }
        requisitos = {
            "productos": {"id", "precio_centavos", "stock"},
            "pedidos": {"id"},
            "detalle_pedido": {"pedido_id", "cantidad", "precio_unitario_centavos"},
        }
        if any(not requisitos[t] <= columnas[t] for t in requisitos):
            raise ValueError("La base no tiene el esquema antiguo esperado; no se modificó.")
        if any(c in columnas[t] for t, c in (
            ("productos", "precio"), ("productos", "activo"),
            ("pedidos", "total"), ("detalle_pedido", "precio_unitario"),
        )):
            raise ValueError("La base ya fue migrada o tiene un esquema parcial; no se modificó.")
        with sqlite3.connect(copia) as respaldo:
            con.backup(respaldo)
        with con:
            con.execute("BEGIN IMMEDIATE")
            con.execute("ALTER TABLE productos ADD COLUMN precio REAL")
            con.execute("ALTER TABLE productos ADD COLUMN activo INTEGER NOT NULL DEFAULT 1")
            con.execute("UPDATE productos SET precio = precio_centavos / 100.0")
            con.execute("ALTER TABLE pedidos ADD COLUMN total REAL NOT NULL DEFAULT 0")
            con.execute("ALTER TABLE detalle_pedido ADD COLUMN precio_unitario REAL")
            con.execute("UPDATE detalle_pedido SET precio_unitario = precio_unitario_centavos / 100.0")
            con.execute("""UPDATE pedidos SET total = COALESCE((
                SELECT SUM(cantidad * precio_unitario_centavos) / 100.0
                FROM detalle_pedido WHERE detalle_pedido.pedido_id = pedidos.id
            ), 0)""")
            if con.execute("PRAGMA foreign_key_check").fetchone():
                raise ValueError("La base contiene referencias inválidas; migración revertida.")
    finally:
        con.close()
    return copia


if __name__ == "__main__":
    predeterminada = Path(__file__).resolve().parent.parent / "data" / "cafe.db"
    ruta = Path(os.environ.get("CAFE_DB", predeterminada))
    print(f"Migración completada. Copia de seguridad: {migrar(ruta)}")
