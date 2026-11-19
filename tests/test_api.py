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

# --- Ejercicio 2.1: consultar un cliente ---------------------------------------
def test_obtener_cliente(cliente):
    r = cliente.get("/clientes/1")
    assert r.status_code == 200
    assert r.json() == {"id": 1, "nombre": "Ana Torres", "email": "ana@ejemplo.com"}


def test_cliente_inexistente(cliente):
    assert cliente.get("/clientes/99").status_code == 404


# --- Ejercicio 2.3: cambio de estado del pedido --------------------------------
# Datos de prueba: pedido 1 entregado, 2 pagado, 3 pendiente, 4 entregado.
def test_estado_transicion_valida(cliente):
    r = cliente.patch("/pedidos/3/estado", json={"estado": "pagado"})
    assert r.status_code == 200
    assert r.json()["estado"] == "pagado"
    assert cliente.get("/pedidos/3").json()["estado"] == "pagado"
    r = cliente.patch("/pedidos/3/estado", json={"estado": "entregado"})
    assert r.status_code == 200


def test_estado_transicion_invalida(cliente):
    r = cliente.patch("/pedidos/1/estado", json={"estado": "pendiente"})
    assert r.status_code == 409
    assert cliente.get("/pedidos/1").json()["estado"] == "entregado"


def test_estado_no_salta_pasos(cliente):
    assert cliente.patch("/pedidos/3/estado", json={"estado": "entregado"}).status_code == 409


def test_estado_pedido_inexistente(cliente):
    assert cliente.patch("/pedidos/999/estado", json={"estado": "pagado"}).status_code == 404


def test_estado_desconocido(cliente):
    assert cliente.patch("/pedidos/3/estado", json={"estado": "en preparación"}).status_code == 422


def test_anular_devuelve_stock(cliente):
    # Pedido 3 (pendiente) contiene 1 Latte (id 4, stock inicial 80)
    assert cliente.get("/productos/4").json()["stock"] == 80
    r = cliente.patch("/pedidos/3/estado", json={"estado": "anulado"})
    assert r.status_code == 200
    assert cliente.get("/productos/4").json()["stock"] == 81
    # Un pedido anulado ya no cambia de estado (y no devuelve el stock dos veces)
    assert cliente.patch("/pedidos/3/estado", json={"estado": "anulado"}).status_code == 409
    assert cliente.get("/productos/4").json()["stock"] == 81


# --- Ejercicio 2.4: historial de pedidos de un cliente -------------------------
def test_pedidos_de_cliente(cliente):
    r = cliente.get("/clientes/1/pedidos")
    assert r.status_code == 200
    pedidos = r.json()
    assert [p["id"] for p in pedidos] == [4, 1]  # más reciente primero
    assert all(p["cliente_id"] == 1 for p in pedidos)


def test_pedidos_de_cliente_inexistente(cliente):
    assert cliente.get("/clientes/99/pedidos").status_code == 404
