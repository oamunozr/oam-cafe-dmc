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


PRODUCTOS = [{"id": 1, "nombre": "Café", "categoria": "Café"}]


def _get_falso(historial: httpx.Response):
    """Devuelve el catálogo para /productos y `historial` para /clientes/{id}/pedidos."""
    def get(url, *args, **kwargs):
        if url.endswith("/pedidos"):
            historial.request = httpx.Request("GET", url)
            return historial
        return httpx.Response(200, json=PRODUCTOS, request=httpx.Request("GET", url))
    return get


def _boton_historial(pantalla):
    return next(b for b in pantalla.button if b.label == "Ver mis pedidos")


def test_historial_muestra_pedidos(monkeypatch):
    pedidos = [{"id": 4, "cliente_id": 1, "estado": "entregado", "total": 21.0},
               {"id": 1, "cliente_id": 1, "estado": "entregado", "total": 34.0}]
    monkeypatch.setattr(httpx, "get", _get_falso(httpx.Response(200, json=pedidos)))
    pantalla = AppTest.from_file("../ui/streamlit_app.py").run()
    _boton_historial(pantalla).click().run()
    assert not pantalla.exception
    tabla = pantalla.dataframe[-1].value
    assert list(tabla["Pedido"]) == [4, 1]


def test_historial_cliente_inexistente(monkeypatch):
    monkeypatch.setattr(httpx, "get", _get_falso(httpx.Response(404, json={"detail": "Cliente no encontrado"})))
    pantalla = AppTest.from_file("../ui/streamlit_app.py").run()
    _boton_historial(pantalla).click().run()
    assert not pantalla.exception
    assert "No existe un cliente" in pantalla.warning[0].value


def test_historial_sin_streamlit_tocando_sqlite():
    """Regla de AGENTS.md: la pantalla solo habla con la API."""
    from pathlib import Path
    codigo = (Path(__file__).parent.parent / "ui" / "streamlit_app.py").read_text(encoding="utf-8")
    assert "sqlite3" not in codigo
