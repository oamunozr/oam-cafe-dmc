"""Contratos (Pydantic) de la API. Son la 'especificación' que lee el agente."""
from typing import Literal

from pydantic import BaseModel, Field

EstadoPedido = Literal["pendiente", "pagado", "entregado", "anulado"]


class Producto(BaseModel):
    id: int
    nombre: str
    categoria: str
    precio: float
    stock: int


class ItemPedido(BaseModel):
    producto_id: int
    cantidad: int = Field(gt=0, le=20)


class PedidoNuevo(BaseModel):
    cliente_id: int
    items: list[ItemPedido] = Field(min_length=1)


class Pedido(BaseModel):
    id: int
    cliente_id: int
    estado: str
    total: float


class CambioEstado(BaseModel):
    estado: EstadoPedido


class Cliente(BaseModel):
    id: int
    nombre: str
    email: str
