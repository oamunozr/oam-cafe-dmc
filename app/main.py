"""API de CaféDMC: monolito modular con dos contextos (catálogo y pedidos)."""
from fastapi import FastAPI

from app import catalogo, pedidos

app = FastAPI(title="CaféDMC API", version="0.1.0")
app.include_router(catalogo.router)
app.include_router(pedidos.router)


@app.get("/salud", tags=["sistema"])
def salud():
    return {"estado": "ok"}