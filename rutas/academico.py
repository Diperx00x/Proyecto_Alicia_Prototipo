"""Pantallas de actas de graduación, docentes (informes finales) y auxiliares de cátedra."""
from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

import archivos
import config
import db
from modelos import ErrorValidacion
from modelos.academico import Acta, Asignacion, Convocatoria, Docente, Estudiante, Materia
from rutas import requiere_login, solo_directora

bp = Blueprint("academico", __name__)


def _error(e):
    db.deshacer()
    flash(str(e), "error")


# ------------------------------------------------------------------ Actas
@bp.route("/actas")
@requiere_login
def actas():
    texto, modalidad, gestion = (request.args.get(k, "") for k in ("texto", "modalidad", "gestion"))
    return render_template("actas/lista.html", actas=Acta.buscar(texto, modalidad, gestion),
                           texto=texto, modalidad=modalidad, gestion=gestion, modalidades=config.MODALIDADES)


@bp.route("/actas/nueva", methods=["GET", "POST"])
@requiere_login
def acta_nueva():
    datos = request.form.to_dict() if request.method == "POST" else {"fecha": date.today().isoformat()}
    if request.method == "POST":
        try:
            ruta = archivos.guardar(request.files.get("archivo"), "actas")
            nuevo = Acta.registrar(datos, ruta)
            flash(f"Acta N° {datos['nro_acta']} registrada.", "ok")
            return redirect(url_for("academico.acta_detalle", id_acta=nuevo))
        except ErrorValidacion as e:
            _error(e)
    return render_template("actas/formulario.html", datos=datos, modalidades=config.MODALIDADES)


@bp.route("/actas/<int:id_acta>", methods=["GET", "POST"])
@requiere_login
def acta_detalle(id_acta):
    acta = Acta.obtener(id_acta)
    if not acta:
        abort(404)
    if request.method == "POST":
        try:
            ruta = archivos.guardar(request.files.get("archivo"), "actas")
            if not ruta:
                raise ErrorValidacion("Elija un archivo.")
            Acta.adjuntar_archivo(id_acta, ruta)
            flash("Escaneado adjuntado.", "ok")
            return redirect(url_for("academico.acta_detalle", id_acta=id_acta))
        except ErrorValidacion as e:
            _error(e)
    return render_template("actas/detalle.html", a=acta)


@bp.route("/estudiante/<carnet>")
@requiere_login
def estudiante_json(carnet):
    """Lo usa el formulario: al escribir el carnet, completa nombre y apellido si ya existe."""
    e = Estudiante.buscar_por_carnet(carnet)
    return {"encontrado": bool(e), "nombres": e["nombres"] if e else "", "apellidos": e["apellidos"] if e else ""}


# ------------------------------------------------------------------ Docentes e informes finales
@bp.route("/docentes", methods=["GET", "POST"])
@requiere_login
def docentes():
    if request.method == "POST":
        try:
            accion = request.form.get("accion")
            if accion == "docente":
                Docente.registrar(request.form.get("nombre"), request.form.get("ci"), request.form.get("correo"))
                flash("Docente registrado.", "ok")
            elif accion == "materia":
                Materia.registrar(request.form.get("sigla"), request.form.get("nombre_materia"))
                flash("Materia registrada.", "ok")
            elif accion == "asignacion":
                Asignacion.registrar(request.form.get("id_docente"), request.form.get("id_materia"),
                                     request.form.get("gestion"), request.form.get("periodo"))
                flash("Asignación registrada.", "ok")
            return redirect(url_for("academico.docentes", **request.args))
        except ErrorValidacion as e:
            _error(e)
    gestion, periodo = request.args.get("gestion", ""), request.args.get("periodo", "")
    solo = request.args.get("pendientes") == "1"
    return render_template("docentes/lista.html",
                           asignaciones=Asignacion.listar(gestion, periodo, solo),
                           docentes=Docente.listar(), materias=Materia.listar(),
                           gestion=gestion, periodo=periodo, solo=solo, anio=date.today().year)


@bp.route("/docentes/informe/<int:id_asignacion>", methods=["GET", "POST"])
@requiere_login
def informe(id_asignacion):
    asig = Asignacion.obtener(id_asignacion)
    if not asig:
        abort(404)
    if request.method == "POST":
        try:
            ruta = archivos.guardar(request.files.get("archivo"), "informes")
            Asignacion.registrar_informe(id_asignacion, request.form.get("fecha"), ruta)
            flash("Informe final registrado.", "ok")
            return redirect(url_for("academico.docentes"))
        except ErrorValidacion as e:
            _error(e)
    return render_template("docentes/informe.html", a=asig, hoy=date.today().isoformat())


# ------------------------------------------------------------------ Auxiliares de cátedra
@bp.route("/auxiliares", methods=["GET", "POST"])
@requiere_login
def convocatorias():
    if request.method == "POST":
        try:
            nuevo = Convocatoria.registrar(request.form.get("id_materia"), request.form.get("gestion"),
                                           request.form.get("periodo"), request.form.get("fecha"))
            flash("Convocatoria registrada.", "ok")
            return redirect(url_for("academico.convocatoria", id_convocatoria=nuevo))
        except ErrorValidacion as e:
            _error(e)
    return render_template("auxiliares/lista.html", convocatorias=Convocatoria.listar(),
                           materias=Materia.listar(), anio=date.today().year, hoy=date.today().isoformat())


@bp.route("/auxiliares/<int:id_convocatoria>", methods=["GET", "POST"])
@requiere_login
def convocatoria(id_convocatoria):
    conv = Convocatoria.obtener(id_convocatoria)
    if not conv:
        abort(404)
    if request.method == "POST":
        try:
            accion = request.form.get("accion")
            if accion == "postulante":
                Convocatoria.agregar_postulante(id_convocatoria, request.form.get("carnet"),
                                                request.form.get("nombres"), request.form.get("apellidos"))
                flash("Postulante agregado.", "ok")
            elif accion == "notas":
                Convocatoria.calificar(request.form.get("id_postulacion"), request.form.get("nota_meritos"),
                                       request.form.get("nota_examen"))
                flash("Notas guardadas.", "ok")
            return redirect(url_for("academico.convocatoria", id_convocatoria=id_convocatoria))
        except ErrorValidacion as e:
            _error(e)
    postulantes = Convocatoria.postulantes(id_convocatoria)
    ganador = Convocatoria.ganador(id_convocatoria)
    empate = bool(ganador and len(postulantes) > 1 and postulantes[1]["total"] == ganador["total"])
    return render_template("auxiliares/detalle.html", c=conv, postulantes=postulantes,
                           ganador=ganador, empate=empate)


@bp.route("/auxiliares/<int:id_convocatoria>/cerrar", methods=["POST"])
@solo_directora
def cerrar_convocatoria(id_convocatoria):
    try:
        Convocatoria.cerrar(id_convocatoria)
        flash("Convocatoria cerrada. Resultado calculado.", "ok")
    except ErrorValidacion as e:
        _error(e)
    return redirect(url_for("academico.convocatoria", id_convocatoria=id_convocatoria))
