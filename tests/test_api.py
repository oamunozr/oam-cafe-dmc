"""Pruebas de la API. Usan una base temporal para no tocar data/cafe.db."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from scripts.crear_db import crear


@pytest.fixture()
def cliente(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setenv("CAFE_DB", str(db))
    crear(db)
    return TestClient(app)


def test_salud(cliente):
    assert cliente.get("/salud").json() == {"estado": "ok"}


def test_listar_productos(cliente):
    r = cliente.get("/productos")
    assert r.status_code == 200
    assert len(r.json()) == 8


def test_filtrar_por_categoria(cliente):
    r = cliente.get("/productos", params={"categoria": "Pastelería"})
    assert {p["nombre"] for p in r.json()} == {"Croissant", "Torta de chocolate"}


def test_producto_inexistente(cliente):
    assert cliente.get("/productos/999").status_code == 404


def test_crear_pedido_calcula_total(cliente):
    r = cliente.post("/pedidos", json={"cliente_id": 1, "items": [
        {"producto_id": 1, "cantidad": 2}, {"producto_id": 7, "cantidad": 1}]})
    assert r.status_code == 201
    assert r.json()["total"] == 20.5  # 2 x 7.0 + 1 x 6.5


def test_stock_insuficiente(cliente):
    # La torta (id 8) tiene 20 unidades en stock: 2 líneas de 15 superan el stock
    r = cliente.post("/pedidos", json={"cliente_id": 1, "items": [
        {"producto_id": 8, "cantidad": 15}]})
    assert r.status_code == 201
    r = cliente.post("/pedidos", json={"cliente_id": 1, "items": [
        {"producto_id": 8, "cantidad": 15}]})
    assert r.status_code == 409


def test_cantidad_maxima(cliente):
    r = cliente.post("/pedidos", json={"cliente_id": 1, "items": [{"producto_id": 1, "cantidad": 21}]})
    assert r.status_code == 422