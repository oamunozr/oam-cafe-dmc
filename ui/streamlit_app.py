"""Pantalla de CaféDMC. Consume la API (no toca la base directamente)."""
import os

import httpx
import streamlit as st

API = os.environ.get("CAFE_API", "http://127.0.0.1:8000")

st.set_page_config(page_title="CaféDMC", page_icon="☕")
st.title("☕ CaféDMC")

try:
    respuesta = httpx.get(f"{API}/productos", timeout=5)
    respuesta.raise_for_status()
    productos = respuesta.json()
except httpx.HTTPStatusError as error:
    st.error(f"La API en {API} respondió con el error HTTP {error.response.status_code} al consultar productos.")
    st.stop()
except httpx.RequestError:
    st.error(f"No se pudo conectar con la API en {API}. Comprueba que esté en ejecución y que CAFE_API sea correcta.")
    st.stop()
except ValueError:
    st.error(f"La API en {API} devolvió una respuesta que no es JSON válido al consultar productos.")
    st.stop()

if not isinstance(productos, list) or any(
    not isinstance(p, dict) or not {"id", "nombre", "categoria"} <= p.keys()
    for p in productos
):
    st.error("La API devolvió un catálogo con un formato inesperado. Comprueba CAFE_API.")
    st.stop()
if not productos:
    st.info("No hay productos disponibles para crear pedidos.")
    st.stop()

categorias = sorted({p["categoria"] for p in productos})
filtro = st.selectbox("Categoría", ["Todas", *categorias])
visibles = [p for p in productos if filtro == "Todas" or p["categoria"] == filtro]
st.dataframe(visibles, width="stretch", hide_index=True)

st.subheader("Nuevo pedido")
with st.form("pedido"):
    cliente_id = st.number_input("ID de cliente", min_value=1, value=1)
    nombres = {p["nombre"]: p["id"] for p in productos}
    elegido = st.selectbox("Producto", list(nombres))
    cantidad = st.number_input("Cantidad", min_value=1, max_value=20, value=1)
    if st.form_submit_button("Crear pedido"):
        try:
            r = httpx.post(f"{API}/pedidos", json={
                "cliente_id": int(cliente_id),
                "items": [{"producto_id": nombres[elegido], "cantidad": int(cantidad)}]},
                timeout=5)
        except httpx.RequestError:
            st.error("No se pudo completar la solicitud. Comprueba el estado del pedido antes de volver a intentarlo.")
        else:
            try:
                contenido = r.json()
            except ValueError:
                contenido = None
            if r.status_code == 201 and isinstance(contenido, dict) and (
                "id" in contenido and isinstance(contenido.get("total"), (int, float))
            ):
                st.success(f"Pedido #{contenido['id']} creado. Total: S/ {contenido['total']:.2f}")
            elif r.status_code == 201:
                st.error("La API confirmó el pedido, pero devolvió una respuesta inválida. Comprueba el pedido antes de volver a intentarlo.")
            else:
                detalle = contenido.get("detail") if isinstance(contenido, dict) else None
                st.error(f"Error HTTP {r.status_code}: {detalle or 'respuesta inesperada de la API'}")
