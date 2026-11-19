-- Esquema de CaféDMC (SQLite)
-- Contexto "catálogo": categorias, productos
-- Contexto "pedidos":  clientes, pedidos, detalle_pedido
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categorias (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre  TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS productos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT    NOT NULL UNIQUE,
    categoria_id  INTEGER NOT NULL REFERENCES categorias(id),
    precio        REAL    NOT NULL CHECK (precio > 0),
    stock         INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    activo        INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);

CREATE TABLE IF NOT EXISTS clientes (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre  TEXT NOT NULL,
    email   TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS pedidos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id  INTEGER NOT NULL REFERENCES clientes(id),
    fecha       TEXT    NOT NULL DEFAULT (datetime('now')),
    estado      TEXT    NOT NULL DEFAULT 'pendiente'
                CHECK (estado IN ('pendiente', 'pagado', 'entregado', 'anulado')),
    total       REAL    NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS detalle_pedido (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id        INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    producto_id      INTEGER NOT NULL REFERENCES productos(id),
    cantidad         INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario  REAL    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_cliente     ON pedidos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_detalle_pedido      ON detalle_pedido(pedido_id);