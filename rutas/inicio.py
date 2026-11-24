from datetime import date

from flask import Blueprint, abort, render_template, request, send_file

import archivos
from modelos import ErrorValidacion
from modelos.academico import Asignacion, Convocatoria
from modelos.documento import Documento
from rutas import requiere_login

bp = Blueprint("inicio", __name__)


@bp.route("/")
@requiere_login
def inicio():
    gestion = date.today().year
    pendientes = Documento.pendientes()
    return render_template(
        "inicio.html",
        gestion=gestion,
        resumen=Documento.resumen(gestion),
        pendientes=pendientes,
        vencidos=sum(1 for p in pendientes if p["vencido"]),
        informes_faltantes=len(Asignacion.listar(solo_pendientes=True)),
        convocatorias_abiertas=sum(1 for c in Convocatoria.listar() if c["estado"] == "ABIERTA"),
    )


@bp.route("/archivo/<path:ruta>")
@requiere_login
def ver_archivo(ruta):
    """Abre el escaneado en el navegador (PDF o imagen)."""
    try:
        return send_file(archivos.ruta_completa(ruta))
    except (ErrorValidacion, FileNotFoundError):
        abort(404)


@bp.route("/ver")
@requiere_login
def ver():
    """Muestra un escaneado en grande dentro de la misma ventana, con botón para volver."""
    ruta = request.args.get("ruta", "")
    try:
        archivos.ruta_completa(ruta)  # valida que la ruta esté dentro de la carpeta de archivos
    except ErrorValidacion:
        abort(404)
    volver = request.args.get("volver", "/")
    if not volver.startswith("/") or volver.startswith("//"):
        volver = "/"
    return render_template("ver_archivo.html", ruta=ruta, volver=volver)
