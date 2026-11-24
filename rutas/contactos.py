from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

import db
from modelos import ErrorValidacion
from modelos.contacto import Contacto
from rutas import requiere_login

bp = Blueprint("contactos", __name__, url_prefix="/contactos")


@bp.route("/", methods=["GET", "POST"])
@requiere_login
def lista():
    if request.method == "POST":
        try:
            Contacto.registrar(request.form.get("nombre"), request.form.get("cargo"), request.form.get("institucion"))
            flash("Contacto agregado.", "ok")
            volver = request.form.get("volver", "")
            if volver.startswith("/") and not volver.startswith("//"):
                return redirect(volver)
            return redirect(url_for("contactos.lista"))
        except ErrorValidacion as e:
            db.deshacer()
            flash(str(e), "error")
    texto = request.args.get("texto", "")
    return render_template("contactos/lista.html", contactos=Contacto.buscar(texto), texto=texto)


@bp.route("/<int:id_contacto>", methods=["GET", "POST"])
@requiere_login
def editar(id_contacto):
    contacto = Contacto.obtener(id_contacto)
    if not contacto:
        abort(404)
    if request.method == "POST":
        try:
            Contacto.actualizar(id_contacto, request.form.get("nombre"), request.form.get("cargo"),
                                request.form.get("institucion"))
            flash("Contacto actualizado.", "ok")
            return redirect(url_for("contactos.lista"))
        except ErrorValidacion as e:
            db.deshacer()
            flash(str(e), "error")
    return render_template("contactos/editar.html", c=contacto)
