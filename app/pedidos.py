"""Contexto PEDIDOS: crea pedidos validando stock, calcula el total y controla su estado."""
from fastapi import APIRouter, HTTPException

from app.db import Conexion
from app.modelos import CambioEstado, Pedido, PedidoNuevo

router = APIRouter(prefix="/pedidos", tags=["pedidos"])

# Transiciones de estado permitidas. Los estados finales no tienen salida.
TRANSICIONES: dict[str, set[str]] = {
    "pendiente": {"pagado", "anulado"},
    "pagado": {"entregado", "anulado"},
    "entregado": set(),
    "anulado": set(),
}


@router.post("", response_model=Pedido, status_code=201)
def crear_pedido(datos: PedidoNuevo, con: Conexion):
    if con.execute("SELECT 1 FROM clientes WHERE id = ?", (datos.cliente_id,)).fetchone() is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    total = 0.0
    lineas = []
    for item in datos.items:
        prod = con.execute(
            "SELECT id, precio, stock FROM productos WHERE id = ? AND activo = 1",
            (item.producto_id,),
        ).fetchone()
        if prod is None:
            raise HTTPException(status_code=404, detail=f"Producto {item.producto_id} no existe")
        if prod["stock"] < item.cantidad:
            raise HTTPException(status_code=409, detail=f"Stock insuficiente para producto {item.producto_id}")
        total += prod["precio"] * item.cantidad
        lineas.append((item.producto_id, item.cantidad, prod["precio"]))
    with con:  # transacción: todo o nada
        cur = con.execute("INSERT INTO pedidos(cliente_id, total) VALUES (?, ?)",
                          (datos.cliente_id, round(total, 2)))
        pedido_id = cur.lastrowid
        columnas_detalle = {fila[1] for fila in con.execute("PRAGMA table_info(detalle_pedido)")}
        for producto_id, cantidad, precio in lineas:
            if "precio_unitario_centavos" in columnas_detalle:
                con.execute(
                    "INSERT INTO detalle_pedido(pedido_id, producto_id, cantidad, precio_unitario, "
                    "precio_unitario_centavos) VALUES (?,?,?,?,?)",
                    (pedido_id, producto_id, cantidad, precio, round(precio * 100)))
            else:
                con.execute(
                    "INSERT INTO detalle_pedido(pedido_id, producto_id, cantidad, precio_unitario)"
                    " VALUES (?,?,?,?)", (pedido_id, producto_id, cantidad, precio))
            con.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (cantidad, producto_id))
    return {"id": pedido_id, "cliente_id": datos.cliente_id, "estado": "pendiente",
            "total": round(total, 2)}


@router.get("/{pedido_id}", response_model=Pedido)
def obtener_pedido(pedido_id: int, con: Conexion):
    fila = con.execute("SELECT id, cliente_id, estado, total FROM pedidos WHERE id = ?",
                       (pedido_id,)).fetchone()
    if fila is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return dict(fila)


@router.patch("/{pedido_id}/estado", response_model=Pedido)
def cambiar_estado(pedido_id: int, cambio: CambioEstado, con: Conexion):
    fila = con.execute("SELECT id, cliente_id, estado, total FROM pedidos WHERE id = ?",
                       (pedido_id,)).fetchone()
    if fila is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    actual = fila["estado"]
    if cambio.estado not in TRANSICIONES.get(actual, set()):
        raise HTTPException(status_code=409,
                            detail=f"No se puede pasar de {actual} a {cambio.estado}")
    with con:  # transacción: el cambio de estado y la devolución de stock van juntos
        cur = con.execute("UPDATE pedidos SET estado = ? WHERE id = ? AND estado = ?",
                          (cambio.estado, pedido_id, actual))
        if cur.rowcount == 0:  # otro proceso cambió el estado entre la lectura y la escritura
            raise HTTPException(status_code=409, detail="El pedido cambió de estado; vuelve a intentarlo")
        if cambio.estado == "anulado":
            con.execute(
                "UPDATE productos SET stock = stock + d.cantidad FROM ("
                " SELECT producto_id, SUM(cantidad) AS cantidad FROM detalle_pedido"
                " WHERE pedido_id = ? GROUP BY producto_id) AS d"
                " WHERE productos.id = d.producto_id", (pedido_id,))
    return {**dict(fila), "estado": cambio.estado}
