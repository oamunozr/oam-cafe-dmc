"""Pantalla de CaféDMC. Consume la API (no toca la base directamente)."""
import os

import httpx
import streamlit as st

API = os.environ.get("CAFE_API", "http://127.0.0.1:8000")

st.set_page_config(page_title="CaféDMC", page_icon="☕", layout="wide")
st.markdown("""
<style>
    .stApp { background: #fff; color: #202b27; }
    .block-container { max-width: 1200px; padding-top: 3rem; padding-bottom: 4rem; }
    .cafe-header { border-bottom: 1px solid #e3ebe6; padding-bottom: 1.5rem; margin-bottom: 2rem; }
    .cafe-brand { color: #205c49; font-size: .8rem; font-weight: 800; letter-spacing: .12em; }
    .cafe-header h1 { color: #192a23; font-size: clamp(2.3rem, 5vw, 3.5rem); letter-spacing: -.05em; margin: .35rem 0; padding: 0; }
    .cafe-header p { color: #65746c; font-size: 1rem; margin: 0; }
    .section-label { color: #205c49; font-size: .75rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; margin-bottom: .3rem; }
    .section-title { color: #192a23; font-size: 1.55rem; font-weight: 700; letter-spacing: -.03em; margin: 0 0 .35rem; }
    .section-copy { color: #65746c; font-size: .92rem; margin: 0 0 1.4rem; }
    div[data-testid="stForm"] { border: 1px solid #dce8e1; border-radius: 12px; padding: 1.4rem; background: #f8fbf9; }
    div[data-testid="stFormSubmitButton"] button { background: #205c49; color: white; border: 0; min-height: 2.8rem; font-weight: 700; }
    div[data-testid="stFormSubmitButton"] button:hover { background: #174636; color: white; }
    @media (max-width: 640px) { .block-container { padding-top: 2rem; } }
</style>
<div class="cafe-header">
    <div class="cafe-brand">CAFÉDMC</div>
    <h1>Un buen café empieza aquí.</h1>
    <p>Explora el catálogo y prepara tu próximo pedido.</p>
</div>
""", unsafe_allow_html=True)

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

catalogo, pedido = st.columns([3, 2], gap="large")
with catalogo:
    st.markdown("""<div class="section-label">Para descubrir</div>
    <div class="section-title">Nuestro catálogo</div>
    <p class="section-copy">Encuentra lo que se te antoja hoy.</p>""", unsafe_allow_html=True)
    categorias = sorted({p["categoria"] for p in productos})
    filtro = st.selectbox("Categoría", ["Todas", *categorias])
    visibles = [p for p in productos if filtro == "Todas" or p["categoria"] == filtro]
    st.dataframe(visibles, width="stretch", hide_index=True)

with pedido:
    st.markdown("""<div class="section-label">Hecho a tu gusto</div>
    <div class="section-title">Nuevo pedido</div>
    <p class="section-copy">Elige un producto y confirma tu pedido.</p>""", unsafe_allow_html=True)
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

st.divider()
st.markdown("""<div class="section-label">Tu historial</div>
<div class="section-title">Mis pedidos</div>
<p class="section-copy">Consulta los pedidos que has hecho y su estado.</p>""", unsafe_allow_html=True)
with st.form("historial"):
    id_historial = st.number_input("ID de cliente", min_value=1, value=1, key="id_historial")
    if st.form_submit_button("Ver mis pedidos"):
        try:
            r = httpx.get(f"{API}/clientes/{int(id_historial)}/pedidos", timeout=5)
        except httpx.RequestError:
            st.error(f"No se pudo conectar con la API en {API} para consultar el historial.")
        else:
            try:
                historial = r.json()
            except ValueError:
                historial = None
            if r.status_code == 404:
                st.warning(f"No existe un cliente con ID {int(id_historial)}.")
            elif r.status_code != 200:
                st.error(f"Error HTTP {r.status_code} al consultar el historial.")
            elif not isinstance(historial, list) or any(
                not isinstance(p, dict) or not {"id", "estado", "total"} <= p.keys() for p in historial
            ):
                st.error("La API devolvió el historial con un formato inesperado.")
            elif not historial:
                st.info("Este cliente todavía no tiene pedidos.")
            else:
                st.dataframe(
                    [{"Pedido": p["id"], "Estado": p["estado"], "Total (S/)": p["total"]} for p in historial],
                    width="stretch", hide_index=True)
