"""Contexto CATÁLOGO: productos y categorías. Solo lee sus propias tablas."""
from fastapi import APIRouter, HTTPException

from app.db import Conexion
from app.modelos import Producto

router = APIRouter(prefix="/productos", tags=["catálogo"])

SQL_BASE = """
SELECT p.id, p.nombre, c.nombre AS categoria, p.precio, p.stock
FROM productos p JOIN categorias c ON c.id = p.categoria_id
WHERE p.activo = 1
"""


@router.get("", response_model=list[Producto])
def listar_productos(con: Conexion, categoria: str | None = None):
    if categoria:
        filas = con.execute(SQL_BASE + " AND c.nombre = ? ORDER BY p.id", (categoria,)).fetchall()
    else:
        filas = con.execute(SQL_BASE + " ORDER BY p.id").fetchall()
    return [dict(f) for f in filas]


@router.get("/{producto_id}", response_model=Producto)
def obtener_producto(producto_id: int, con: Conexion):
    fila = con.execute(SQL_BASE + " AND p.id = ?", (producto_id,)).fetchone()
    if fila is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return dict(fila)