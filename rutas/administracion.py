"""Usuarios, configuración y copia de seguridad."""
from datetime import date
import io

from flask import Blueprint, flash, g, redirect, render_template, request, send_file, url_for

import db
import respaldo
from modelos import ErrorValidacion
from modelos.usuario import Usuario
from rutas import requiere_login, solo_directora

bp = Blueprint("admin", __name__, url_prefix="/administracion")


@bp.route("/usuarios", methods=["GET", "POST"])
@solo_directora
def usuarios():
    if request.method == "POST":
        try:
            if request.form.get("accion") == "estado":
                Usuario.cambiar_activo(request.form.get("id_usuario"), request.form.get("activo") == "1",
                                       g.usuario["id_usuario"])
                flash("Usuario actualizado.", "ok")
            else:
                Usuario.registrar(request.form.get("nombre"), request.form.get("usuario"),
                                  request.form.get("clave"), request.form.get("rol"))
                flash("Usuario creado.", "ok")
            return redirect(url_for("admin.usuarios"))
        except ErrorValidacion as e:
            db.deshacer()
            flash(str(e), "error")
    return render_template("usuarios/lista.html", usuarios=Usuario.listar())


@bp.route("/configuracion", methods=["GET", "POST"])
@solo_directora
def configuracion():
    gestion = date.today().year
    if request.method == "POST":
        try:
            prefijo = (request.form.get("prefijo_cite") or "").strip()
            if not prefijo:
                raise ErrorValidacion("El prefijo del CITE no puede quedar vacío.")
            ultimo = request.form.get("ultimo_salida", "").strip()
            if ultimo and (not ultimo.isdigit()):
                raise ErrorValidacion("El último número usado debe ser un número entero.")
            db.ejecutar("REPLACE INTO parametro (clave, valor) VALUES ('prefijo_cite', %s)", (prefijo,))
            if ultimo:
                db.ejecutar("REPLACE INTO parametro (clave, valor) VALUES (%s, %s)",
                            (f"ultimo_salida_{gestion}", ultimo))
            db.confirmar()
            flash("Configuración guardada.", "ok")
            return redirect(url_for("admin.configuracion"))
        except ErrorValidacion as e:
            db.deshacer()
            flash(str(e), "error")
    prefijo = db.consultar("SELECT valor FROM parametro WHERE clave='prefijo_cite'", uno=True)
    ultimo = db.consultar("SELECT valor FROM parametro WHERE clave=%s", (f"ultimo_salida_{gestion}",), uno=True)
    return render_template("usuarios/configuracion.html", gestion=gestion,
                           prefijo=prefijo["valor"] if prefijo else "", ultimo=ultimo["valor"] if ultimo else "")


@bp.route("/respaldo", methods=["GET", "POST"])
@requiere_login
def copia():
    if request.method == "POST":
        nombre, datos = respaldo.generar_zip()
        return send_file(io.BytesIO(datos), as_attachment=True, download_name=nombre,
                         mimetype="application/zip")
    return render_template("usuarios/respaldo.html")
