from datetime import date

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

import archivos
import config
import db
from modelos import ErrorValidacion
from modelos.contacto import Contacto
from modelos.documento import ESTADOS, NOMBRE_ESTADO, TRANSICIONES, Documento, Movimiento
from rutas import requiere_login

bp = Blueprint("documentos", __name__, url_prefix="/documentos")


@bp.route("/")
@requiere_login
def lista():
    filtros = {k: request.args.get(k, "") for k in
               ("texto", "sentido", "gestion", "categoria", "estado", "desde", "hasta")}
    return render_template(
        "documentos/lista.html",
        documentos=Documento.buscar(**filtros),
        filtros=filtros,
        gestiones=Documento.gestiones(),
        categorias=config.CATEGORIAS,
        estados=ESTADOS,
        nombre_estado=NOMBRE_ESTADO,
    )


@bp.route("/pendientes")
@requiere_login
def pendientes():
    return render_template("documentos/pendientes.html", pendientes=Documento.pendientes(),
                           nombre_estado=NOMBRE_ESTADO)


@bp.route("/nuevo/<sentido>", methods=["GET", "POST"])
@requiere_login
def nuevo(sentido):
    sentido = sentido.upper()
    if sentido not in ("ENTRADA", "SALIDA"):
        abort(404)
    datos = request.form.to_dict() if request.method == "POST" else {"fecha": date.today().isoformat()}
    if request.method == "POST":
        datos["sentido"] = sentido
        try:
            ruta = archivos.guardar(request.files.get("archivo"), f"documentos/{sentido.lower()}")
            nuevo_id = Documento.registrar(datos, g.usuario["id_usuario"], ruta)
            doc = Documento.obtener(nuevo_id)
            flash(f"Documento registrado: {doc['cite']}", "ok")
            return redirect(url_for("documentos.detalle", id_documento=nuevo_id))
        except ErrorValidacion as e:
            db.deshacer()
            flash(str(e), "error")
    siguiente = None
    if sentido == "SALIDA":
        gestion = date.fromisoformat(datos.get("fecha") or date.today().isoformat()).year
        siguiente = Documento.generar_cite(Documento.generar_numero("SALIDA", gestion), gestion)
    return render_template("documentos/formulario.html", sentido=sentido, datos=datos,
                           contactos=Contacto.buscar(), categorias=config.CATEGORIAS,
                           siguiente_cite=siguiente, original=None)


@bp.route("/<int:id_documento>")
@requiere_login
def detalle(id_documento):
    doc = Documento.obtener(id_documento)
    if not doc:
        abort(404)
    return render_template(
        "documentos/detalle.html",
        doc=doc,
        historial=Movimiento.historial(id_documento),
        respuestas=Documento.respuestas(id_documento),
        siguientes=TRANSICIONES[doc["estado"]],
        nombre_estado=NOMBRE_ESTADO,
        hoy=date.today(),
    )


@bp.route("/<int:id_documento>/estado", methods=["POST"])
@requiere_login
def cambiar_estado(id_documento):
    try:
        Documento.cambiar_estado(id_documento, request.form.get("estado"),
                                 request.form.get("observacion"), g.usuario["id_usuario"])
        flash("Estado actualizado.", "ok")
    except ErrorValidacion as e:
        db.deshacer()
        flash(str(e), "error")
    return redirect(url_for("documentos.detalle", id_documento=id_documento))


@bp.route("/<int:id_documento>/archivo", methods=["POST"])
@requiere_login
def adjuntar(id_documento):
    doc = Documento.obtener(id_documento)
    if not doc:
        abort(404)
    try:
        ruta = archivos.guardar(request.files.get("archivo"), f"documentos/{doc['sentido'].lower()}")
        if not ruta:
            raise ErrorValidacion("Elija un archivo.")
        Documento.adjuntar_archivo(id_documento, ruta)
        flash("Escaneado adjuntado.", "ok")
    except ErrorValidacion as e:
        flash(str(e), "error")
    return redirect(url_for("documentos.detalle", id_documento=id_documento))


@bp.route("/<int:id_documento>/responder", methods=["GET", "POST"])
@requiere_login
def responder(id_documento):
    original = Documento.obtener(id_documento)
    if not original:
        abort(404)
    sentido = "SALIDA" if original["sentido"] == "ENTRADA" else "ENTRADA"
    datos = request.form.to_dict() if request.method == "POST" else {
        "fecha": date.today().isoformat(),
        "id_contacto": str(original["id_contacto"]),
        "categoria": original["categoria"],
        "asunto": f"Respuesta a {original['cite']}",
    }
    if request.method == "POST":
        try:
            ruta = archivos.guardar(request.files.get("archivo"), f"documentos/{sentido.lower()}")
            nuevo_id = Documento.responder(id_documento, datos, g.usuario["id_usuario"], ruta)
            flash(f"Respuesta registrada: {Documento.obtener(nuevo_id)['cite']}", "ok")
            return redirect(url_for("documentos.detalle", id_documento=nuevo_id))
        except ErrorValidacion as e:
            db.deshacer()
            flash(str(e), "error")
    siguiente = None
    if sentido == "SALIDA":
        gestion = date.fromisoformat(datos.get("fecha") or date.today().isoformat()).year
        siguiente = Documento.generar_cite(Documento.generar_numero("SALIDA", gestion), gestion)
    return render_template("documentos/formulario.html", sentido=sentido, datos=datos,
                           contactos=Contacto.buscar(), categorias=config.CATEGORIAS,
                           siguiente_cite=siguiente, original=original)
