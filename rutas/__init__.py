"""Rutas (pantallas) del sistema y control de acceso."""
from functools import wraps

from flask import flash, g, redirect, request, session, url_for

import db


def cargar_usuario():
    g.usuario = None
    if "id_usuario" in session:
        g.usuario = db.consultar(
            "SELECT id_usuario, nombre, usuario, rol FROM usuario WHERE id_usuario=%s AND activo=1",
            (session["id_usuario"],),
            uno=True,
        )
        if g.usuario is None:
            session.clear()


def requiere_login(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if g.usuario is None:
            return redirect(url_for("auth.ingresar", siguiente=request.path))
        return vista(*args, **kwargs)
    return envoltura


def solo_directora(vista):
    @wraps(vista)
    @requiere_login
    def envoltura(*args, **kwargs):
        if g.usuario["rol"] != "DIRECTORA":
            flash("Esta opción solo la puede usar la directora.", "error")
            return redirect(url_for("inicio.inicio"))
        return vista(*args, **kwargs)
    return envoltura
