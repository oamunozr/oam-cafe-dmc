"""Pruebas de los errores de comunicación mostrados en la interfaz."""
import httpx
import pytest
from streamlit.testing.v1 import AppTest


@pytest.mark.parametrize(
    ("respuesta", "mensaje"),
    [
        (httpx.Response(500, text="Internal Server Error"), "HTTP 500"),
        (httpx.Response(200, text=""), "no es JSON válido"),
        (httpx.Response(200, json={"estado": "ok"}), "formato inesperado"),
    ],
)
def test_error_catalogo(monkeypatch, respuesta, mensaje):
    respuesta.request = httpx.Request("GET", "http://test/productos")
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: respuesta)
    pantalla = AppTest.from_file("../ui/streamlit_app.py").run()
    assert not pantalla.exception
    assert mensaje in pantalla.error[0].value


def test_error_pedido_sin_json(monkeypatch):
    productos = [{"id": 1, "nombre": "Café", "categoria": "Café"}]
    respuesta = httpx.Response(200, json=productos, request=httpx.Request("GET", "http://test"))
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: respuesta)
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: httpx.Response(500, text="error"))
    pantalla = AppTest.from_file("../ui/streamlit_app.py").run()
    pantalla.button[0].click().run()
    assert not pantalla.exception
    assert "HTTP 500" in pantalla.error[0].value
