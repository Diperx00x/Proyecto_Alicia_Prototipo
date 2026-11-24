from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

import db
from modelos import ErrorValidacion
from modelos.usuario import Usuario
from rutas import requiere_login

bp = Blueprint("auth", __name__)


@bp.route("/ingresar", methods=["GET", "POST"])
def ingresar():
    if not Usuario.hay_usuarios():
        return redirect(url_for("auth.primer_uso"))
    if request.method == "POST":
        usuario = Usuario.autenticar(request.form.get("usuario", ""), request.form.get("clave", ""))
        if usuario:
            session.clear()
            session["id_usuario"] = usuario["id_usuario"]
            siguiente = request.args.get("siguiente", "")
            return redirect(siguiente if siguiente.startswith("/") and not siguiente.startswith("//")
                            else url_for("inicio.inicio"))
        flash("Usuario o contraseña incorrectos.", "error")
    return render_template("ingresar.html")


@bp.route("/primer-uso", methods=["GET", "POST"])
def primer_uso():
    """La primera vez que se abre el sistema se crea la cuenta de la directora."""
    if Usuario.hay_usuarios():
        return redirect(url_for("auth.ingresar"))
    if request.method == "POST":
        try:
            if request.form.get("clave") != request.form.get("clave2"):
                raise ErrorValidacion("Las contraseñas no coinciden.")
            nuevo = Usuario.registrar(request.form.get("nombre"), request.form.get("usuario"),
                                      request.form.get("clave"), "DIRECTORA")
            session.clear()
            session["id_usuario"] = nuevo
            flash("Cuenta creada. Bienvenida al sistema.", "ok")
            return redirect(url_for("inicio.inicio"))
        except ErrorValidacion as e:
            db.deshacer()
            flash(str(e), "error")
    return render_template("primer_uso.html")


@bp.route("/salir")
def salir():
    session.clear()
    return redirect(url_for("auth.ingresar"))


@bp.route("/mi-clave", methods=["GET", "POST"])
@requiere_login
def mi_clave():
    if request.method == "POST":
        try:
            if request.form.get("nueva") != request.form.get("nueva2"):
                raise ErrorValidacion("Las contraseñas nuevas no coinciden.")
            Usuario.cambiar_clave(g.usuario["id_usuario"], request.form.get("actual", ""), request.form.get("nueva", ""))
            flash("Contraseña cambiada.", "ok")
            return redirect(url_for("inicio.inicio"))
        except ErrorValidacion as e:
            flash(str(e), "error")
    return render_template("mi_clave.html")
