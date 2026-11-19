"""Comprueba la migración de datos antiguos y su uso por la API."""
import sqlite3

from fastapi.testclient import TestClient

from app.main import app
from scripts.migrar_bd import migrar


def test_migracion_conserva_pedidos_y_permite_crear_otros(tmp_path, monkeypatch):
    ruta = tmp_path / "cafe.db"
    with sqlite3.connect(ruta) as con:
        con.executescript("""
            CREATE TABLE categorias (id INTEGER PRIMARY KEY, nombre TEXT);
            CREATE TABLE clientes (id INTEGER PRIMARY KEY, nombre TEXT);
            CREATE TABLE productos (id INTEGER PRIMARY KEY, categoria_id INTEGER,
                nombre TEXT, precio_centavos INTEGER NOT NULL, stock INTEGER);
            CREATE TABLE pedidos (id INTEGER PRIMARY KEY, cliente_id INTEGER,
                fecha TEXT DEFAULT CURRENT_TIMESTAMP, estado TEXT DEFAULT 'pendiente');
            CREATE TABLE detalle_pedido (pedido_id INTEGER, producto_id INTEGER,
                cantidad INTEGER, precio_unitario_centavos INTEGER NOT NULL,
                PRIMARY KEY (pedido_id, producto_id));
            INSERT INTO categorias VALUES (1, 'Café');
            INSERT INTO clientes VALUES (1, 'Ana');
            INSERT INTO productos VALUES (1, 1, 'Espresso', 725, 10);
            INSERT INTO pedidos (id, cliente_id) VALUES (1, 1);
            INSERT INTO detalle_pedido VALUES (1, 1, 2, 700);
        """)
    copia = migrar(ruta)
    with sqlite3.connect(copia) as respaldo:
        assert "precio" not in {f[1] for f in respaldo.execute("PRAGMA table_info(productos)")}
    monkeypatch.setenv("CAFE_DB", str(ruta))
    cliente = TestClient(app)
    assert cliente.get("/productos").json()[0]["precio"] == 7.25
    assert cliente.get("/pedidos/1").json()["total"] == 14
    respuesta = cliente.post("/pedidos", json={"cliente_id": 1, "items": [
        {"producto_id": 1, "cantidad": 2}]})
    assert respuesta.status_code == 201
    assert respuesta.json()["total"] == 14.5
