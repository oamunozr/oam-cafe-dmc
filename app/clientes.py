"""Contexto PEDIDOS: consulta de clientes y de su historial de pedidos."""
from fastapi import APIRouter, HTTPException

from app.db import Conexion
from app.modelos import Cliente, Pedido

router = APIRouter(prefix="/clientes", tags=["pedidos"])


def _buscar_cliente(con: Conexion, cliente_id: int):
    fila = con.execute("SELECT id, nombre, email FROM clientes WHERE id = ?",
                       (cliente_id,)).fetchone()
    if fila is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return fila


@router.get("/{cliente_id}", response_model=Cliente)
def obtener_cliente(cliente_id: int, con: Conexion):
    return dict(_buscar_cliente(con, cliente_id))


@router.get("/{cliente_id}/pedidos", response_model=list[Pedido])
def pedidos_de_cliente(cliente_id: int, con: Conexion):
    _buscar_cliente(con, cliente_id)
    filas = con.execute(
        "SELECT id, cliente_id, estado, total FROM pedidos WHERE cliente_id = ? ORDER BY id DESC",
        (cliente_id,)).fetchall()
    return [dict(f) for f in filas]
