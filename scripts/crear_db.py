"""Crea data/cafe.db desde db/schema.sql y carga datos de prueba.

Uso:  poetry run python scripts/crear_db.py          (crea si no existe)
      poetry run python scripts/crear_db.py --reset  (borra y vuelve a crear)
"""
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DB = RAIZ / "data" / "cafe.db"
SCHEMA = RAIZ / "db" / "schema.sql"

CATEGORIAS = ["Café", "Bebidas frías", "Pastelería"]
PRODUCTOS = [  # (nombre, categoría, precio, stock)
    ("Espresso", "Café", 7.0, 100),
    ("Americano", "Café", 8.0, 100),
    ("Capuchino", "Café", 10.5, 80),
    ("Latte", "Café", 11.0, 80),
    ("Frappé de vainilla", "Bebidas frías", 14.0, 40),
    ("Limonada", "Bebidas frías", 9.0, 60),
    ("Croissant", "Pastelería", 6.5, 30),
    ("Torta de chocolate", "Pastelería", 12.0, 20),
]
CLIENTES = [("Ana Torres", "ana@ejemplo.com"), ("Luis Ríos", "luis@ejemplo.com"),
            ("María Paz", "maria@ejemplo.com")]
PEDIDOS = [  # (email cliente, estado, [(producto, cantidad)])
    ("ana@ejemplo.com", "entregado", [("Capuchino", 2), ("Croissant", 2)]),
    ("luis@ejemplo.com", "pagado", [("Americano", 1), ("Torta de chocolate", 1)]),
    ("maria@ejemplo.com", "pendiente", [("Latte", 1)]),
    ("ana@ejemplo.com", "entregado", [("Espresso", 3)]),
]


def crear(db: Path = DB, reset: bool = False) -> Path:
    db.parent.mkdir(exist_ok=True)
    if reset and db.exists():
        db.unlink()
    nueva = not db.exists()
    con = sqlite3.connect(db)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    if nueva:
        cur = con.cursor()
        cur.executemany("INSERT INTO categorias(nombre) VALUES (?)", [(c,) for c in CATEGORIAS])
        cat = {n: i for i, n in cur.execute("SELECT id, nombre FROM categorias")}
        cur.executemany(
            "INSERT INTO productos(nombre, categoria_id, precio, stock) VALUES (?,?,?,?)",
            [(n, cat[c], p, s) for n, c, p, s in PRODUCTOS],
        )
        cur.executemany("INSERT INTO clientes(nombre, email) VALUES (?,?)", CLIENTES)
        prod = {n: (i, p) for i, n, p in cur.execute("SELECT id, nombre, precio FROM productos")}
        cli = {e: i for i, e in cur.execute("SELECT id, email FROM clientes")}
        for email, estado, items in PEDIDOS:
            total = sum(prod[n][1] * q for n, q in items)
            cur.execute("INSERT INTO pedidos(cliente_id, estado, total) VALUES (?,?,?)",
                        (cli[email], estado, total))
            pid = cur.lastrowid
            cur.executemany(
                "INSERT INTO detalle_pedido(pedido_id, producto_id, cantidad, precio_unitario)"
                " VALUES (?,?,?,?)",
                [(pid, prod[n][0], q, prod[n][1]) for n, q in items],
            )
        con.commit()
    con.close()
    return db


if __name__ == "__main__":
    ruta = crear(reset="--reset" in sys.argv)
    con = sqlite3.connect(ruta)
    for tabla in ["categorias", "productos", "clientes", "pedidos", "detalle_pedido"]:
        n = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        print(f"{tabla:<15} {n:>3} filas")
    print(f"✅ Base lista en {ruta}")