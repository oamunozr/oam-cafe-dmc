"""Pruebas de las restricciones de rutas del servidor de archivos."""

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mcp_servers import fs_server
from mcp_servers.fs_server import RAIZ, _ruta_segura


@pytest.mark.parametrize(
    "ruta",
    [
        "../x",
        "docs/../../x",
        str(RAIZ / "archivo.py"),
        ".env",
        ".git/config",
        "data/cafe.db",
    ],
)
def test_ruta_segura_bloquea_rutas_no_permitidas(ruta):
    with pytest.raises(ToolError, match="Acceso denegado"):
        _ruta_segura(ruta)


def test_guardar_nota_crea_sin_sobrescribir(tmp_path, monkeypatch):
    monkeypatch.setattr(fs_server, "RAIZ", tmp_path)
    assert fs_server.guardar_nota("nota-1", "á" * 5000) == "docs/notas/nota-1.md"
    nota = tmp_path / "docs" / "notas" / "nota-1.md"
    with pytest.raises(ToolError, match="ya existe"):
        fs_server.guardar_nota("nota-1", "otro texto")
    assert nota.read_text(encoding="utf-8") == "á" * 5000


@pytest.mark.parametrize("nombre", ["../x", "a/b", ".env", "Mayuscula", "", "a" * 41])
def test_guardar_nota_rechaza_nombres_invalidos(tmp_path, monkeypatch, nombre):
    monkeypatch.setattr(fs_server, "RAIZ", tmp_path)
    with pytest.raises(ToolError, match="Nombre inválido"):
        fs_server.guardar_nota(nombre, "texto")
    assert not (tmp_path / "docs").exists()


def test_guardar_nota_rechaza_texto_largo(tmp_path, monkeypatch):
    monkeypatch.setattr(fs_server, "RAIZ", tmp_path)
    with pytest.raises(ToolError, match="5000 caracteres"):
        fs_server.guardar_nota("nota", "a" * 5001)
    assert not (tmp_path / "docs").exists()


def test_guardar_nota_rechaza_directorio_enlazado(tmp_path, monkeypatch):
    raiz = tmp_path / "proyecto"
    raiz.mkdir()
    (raiz / "docs").symlink_to(tmp_path, target_is_directory=True)
    monkeypatch.setattr(fs_server, "RAIZ", raiz)
    with pytest.raises(ToolError, match="enlaces simbólicos"):
        fs_server.guardar_nota("nota", "texto")
    assert not (tmp_path / "notas").exists()
