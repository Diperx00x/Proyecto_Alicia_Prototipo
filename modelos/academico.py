"""Clases Estudiante, Acta, Docente, Materia, Asignacion, Convocatoria y Postulacion."""
from datetime import date
from decimal import Decimal, InvalidOperation

import config
import db
from modelos import ErrorValidacion
from modelos.documento import _a_fecha


def _texto(valor, nombre):
    valor = (valor or "").strip()
    if not valor:
        raise ErrorValidacion(f"{nombre} es obligatorio.")
    return valor


def _periodo(valor):
    if str(valor) not in ("1", "2"):
        raise ErrorValidacion("El periodo debe ser 1 o 2.")
    return int(valor)


def _gestion(valor):
    try:
        g = int(valor)
    except (TypeError, ValueError):
        raise ErrorValidacion("La gestión no es válida.")
    if not 2000 <= g <= date.today().year + 1:
        raise ErrorValidacion("La gestión no es válida.")
    return g


# ===================================================================== Estudiante
class Estudiante:
    @staticmethod
    def buscar_por_carnet(carnet):
        return db.consultar(
            "SELECT * FROM estudiante WHERE carnet=%s", ((carnet or "").strip().upper(),), uno=True
        )

    @staticmethod
    def obtener_o_crear(carnet, nombres, apellidos):
        """Si el carnet ya existe, usa ese estudiante; si no, lo registra."""
        carnet = _texto(carnet, "El carnet").upper()
        existente = Estudiante.buscar_por_carnet(carnet)
        if existente:
            return existente["id_estudiante"]
        return db.ejecutar(
            "INSERT INTO estudiante (carnet, nombres, apellidos) VALUES (%s,%s,%s)",
            (carnet, _texto(nombres, "El nombre"), _texto(apellidos, "El apellido")),
        )


# ===================================================================== Acta
class Acta:
    @staticmethod
    def verificar_repetido(nro_acta, id_estudiante=None):
        if db.consultar("SELECT 1 FROM acta WHERE nro_acta=%s", (nro_acta,), uno=True):
            raise ErrorValidacion(f"El acta N° {nro_acta} ya está registrada.")
        if id_estudiante and db.consultar(
            "SELECT 1 FROM acta WHERE id_estudiante=%s", (id_estudiante,), uno=True
        ):
            raise ErrorValidacion("Ese estudiante ya tiene un acta de graduación registrada.")

    @staticmethod
    def registrar(datos, archivo=None):
        nro = _texto(datos.get("nro_acta"), "El número de acta")
        fecha = _a_fecha(datos.get("fecha"), "fecha del acta")
        if datos.get("modalidad") not in config.MODALIDADES:
            raise ErrorValidacion("Elija una modalidad de la lista.")
        try:
            nota = int(datos.get("nota"))
        except (TypeError, ValueError):
            raise ErrorValidacion("La nota debe ser un número entero.")
        if not 0 <= nota <= 100:
            raise ErrorValidacion("La nota debe estar entre 0 y 100.")
        Acta.verificar_repetido(nro)
        try:
            id_est = Estudiante.obtener_o_crear(datos.get("carnet"), datos.get("nombres"), datos.get("apellidos"))
            Acta.verificar_repetido(nro, id_est)
            nuevo = db.ejecutar(
                "INSERT INTO acta (nro_acta, id_estudiante, fecha, modalidad, nota, archivo) VALUES (%s,%s,%s,%s,%s,%s)",
                (nro, id_est, fecha, datos["modalidad"], nota, archivo),
            )
        except ErrorValidacion:
            db.deshacer()
            raise
        db.confirmar()
        return nuevo

    @staticmethod
    def adjuntar_archivo(id_acta, ruta):
        db.ejecutar("UPDATE acta SET archivo=%s WHERE id_acta=%s", (ruta, id_acta))
        db.confirmar()

    @staticmethod
    def buscar(texto="", modalidad="", gestion=""):
        sql = """SELECT a.*, e.carnet, e.nombres, e.apellidos FROM acta a
                 JOIN estudiante e ON e.id_estudiante=a.id_estudiante WHERE 1=1"""
        p = []
        if texto:
            sql += " AND (e.carnet LIKE %s OR a.nro_acta LIKE %s OR CONCAT(e.nombres,' ',e.apellidos) LIKE %s)"
            p += [f"%{texto.strip()}%"] * 3
        if modalidad:
            sql += " AND a.modalidad=%s"
            p.append(modalidad)
        if gestion:
            sql += " AND YEAR(a.fecha)=%s"
            p.append(gestion)
        return db.consultar(sql + " ORDER BY a.fecha DESC, a.id_acta DESC", p)

    @staticmethod
    def obtener(id_acta):
        return db.consultar(
            """SELECT a.*, e.carnet, e.nombres, e.apellidos FROM acta a
               JOIN estudiante e ON e.id_estudiante=a.id_estudiante WHERE a.id_acta=%s""",
            (id_acta,),
            uno=True,
        )


# ===================================================================== Docente y Materia
class Docente:
    @staticmethod
    def registrar(nombre, ci, correo=""):
        nombre, ci = _texto(nombre, "El nombre"), _texto(ci, "El carnet de identidad")
        if db.consultar("SELECT 1 FROM docente WHERE ci=%s", (ci,), uno=True):
            raise ErrorValidacion(f"Ya existe un docente con CI {ci}.")
        nuevo = db.ejecutar("INSERT INTO docente (nombre, ci, correo) VALUES (%s,%s,%s)",
                            (nombre, ci, (correo or "").strip()))
        db.confirmar()
        return nuevo

    @staticmethod
    def listar():
        return db.consultar("SELECT * FROM docente ORDER BY nombre")


class Materia:
    @staticmethod
    def registrar(sigla, nombre):
        sigla, nombre = _texto(sigla, "La sigla").upper(), _texto(nombre, "El nombre")
        if db.consultar("SELECT 1 FROM materia WHERE sigla=%s", (sigla,), uno=True):
            raise ErrorValidacion(f"La materia {sigla} ya existe.")
        nuevo = db.ejecutar("INSERT INTO materia (sigla, nombre) VALUES (%s,%s)", (sigla, nombre))
        db.confirmar()
        return nuevo

    @staticmethod
    def listar():
        return db.consultar("SELECT * FROM materia ORDER BY sigla")


# ===================================================================== Asignacion (informe final)
class Asignacion:
    @staticmethod
    def registrar(id_docente, id_materia, gestion, periodo):
        if not id_docente or not id_materia:
            raise ErrorValidacion("Elija el docente y la materia.")
        gestion, periodo = _gestion(gestion), _periodo(periodo)
        if db.consultar("SELECT 1 FROM asignacion WHERE id_materia=%s AND gestion=%s AND periodo=%s",
                        (id_materia, gestion, periodo), uno=True):
            raise ErrorValidacion("Esa materia ya tiene docente asignado en ese periodo.")
        nuevo = db.ejecutar(
            "INSERT INTO asignacion (id_docente, id_materia, gestion, periodo) VALUES (%s,%s,%s,%s)",
            (id_docente, id_materia, gestion, periodo),
        )
        db.confirmar()
        return nuevo

    @staticmethod
    def registrar_informe(id_asignacion, fecha, archivo):
        fecha = _a_fecha(fecha, "fecha de entrega")
        if not archivo:
            raise ErrorValidacion("Adjunte el informe final escaneado.")
        db.ejecutar("UPDATE asignacion SET fecha_informe=%s, archivo_informe=%s WHERE id_asignacion=%s",
                    (fecha, archivo, id_asignacion))
        db.confirmar()

    @staticmethod
    def listar(gestion="", periodo="", solo_pendientes=False):
        sql = """SELECT a.*, d.nombre AS docente, m.sigla, m.nombre AS materia
                 FROM asignacion a JOIN docente d ON d.id_docente=a.id_docente
                 JOIN materia m ON m.id_materia=a.id_materia WHERE 1=1"""
        p = []
        if gestion:
            sql += " AND a.gestion=%s"
            p.append(gestion)
        if periodo:
            sql += " AND a.periodo=%s"
            p.append(periodo)
        if solo_pendientes:
            sql += " AND a.fecha_informe IS NULL"
        return db.consultar(sql + " ORDER BY a.gestion DESC, a.periodo DESC, m.sigla", p)

    @staticmethod
    def obtener(id_asignacion):
        filas = db.consultar(
            """SELECT a.*, d.nombre AS docente, m.sigla, m.nombre AS materia
               FROM asignacion a JOIN docente d ON d.id_docente=a.id_docente
               JOIN materia m ON m.id_materia=a.id_materia WHERE a.id_asignacion=%s""",
            (id_asignacion,),
        )
        return filas[0] if filas else None


# ===================================================================== Auxiliares de cátedra
def _nota(valor, nombre):
    if valor in (None, ""):
        return None
    try:
        n = Decimal(str(valor).replace(",", "."))
    except InvalidOperation:
        raise ErrorValidacion(f"La {nombre} no es un número válido.")
    if not 0 <= n <= 100:
        raise ErrorValidacion(f"La {nombre} debe estar entre 0 y 100.")
    return n


class Convocatoria:
    @staticmethod
    def registrar(id_materia, gestion, periodo, fecha_publicacion):
        if not id_materia:
            raise ErrorValidacion("Elija la materia.")
        gestion, periodo = _gestion(gestion), _periodo(periodo)
        fecha = _a_fecha(fecha_publicacion, "fecha de publicación")
        if db.consultar("SELECT 1 FROM convocatoria WHERE id_materia=%s AND gestion=%s AND periodo=%s",
                        (id_materia, gestion, periodo), uno=True):
            raise ErrorValidacion("Ya existe una convocatoria para esa materia en ese periodo.")
        nuevo = db.ejecutar(
            "INSERT INTO convocatoria (id_materia, gestion, periodo, fecha_publicacion) VALUES (%s,%s,%s,%s)",
            (id_materia, gestion, periodo, fecha),
        )
        db.confirmar()
        return nuevo

    @staticmethod
    def obtener(id_convocatoria):
        return db.consultar(
            """SELECT c.*, m.sigla, m.nombre AS materia FROM convocatoria c
               JOIN materia m ON m.id_materia=c.id_materia WHERE c.id_convocatoria=%s""",
            (id_convocatoria,),
            uno=True,
        )

    @staticmethod
    def listar():
        return db.consultar(
            """SELECT c.*, m.sigla, m.nombre AS materia,
                      (SELECT COUNT(*) FROM postulacion p WHERE p.id_convocatoria=c.id_convocatoria) AS postulantes
               FROM convocatoria c JOIN materia m ON m.id_materia=c.id_materia
               ORDER BY c.gestion DESC, c.periodo DESC, m.sigla"""
        )

    @staticmethod
    def agregar_postulante(id_convocatoria, carnet, nombres, apellidos):
        conv = Convocatoria.obtener(id_convocatoria)
        if not conv:
            raise ErrorValidacion("La convocatoria no existe.")
        if conv["estado"] == "CERRADA":
            raise ErrorValidacion("La convocatoria está cerrada; ya no se aceptan postulantes.")
        try:
            id_est = Estudiante.obtener_o_crear(carnet, nombres, apellidos)
            if db.consultar("SELECT 1 FROM postulacion WHERE id_convocatoria=%s AND id_estudiante=%s",
                            (id_convocatoria, id_est), uno=True):
                raise ErrorValidacion("Ese estudiante ya está postulado a esta convocatoria.")
            nuevo = db.ejecutar("INSERT INTO postulacion (id_convocatoria, id_estudiante) VALUES (%s,%s)",
                                (id_convocatoria, id_est))
        except ErrorValidacion:
            db.deshacer()
            raise
        db.confirmar()
        return nuevo

    @staticmethod
    def calificar(id_postulacion, nota_meritos, nota_examen):
        fila = db.consultar(
            """SELECT c.estado FROM postulacion p JOIN convocatoria c ON c.id_convocatoria=p.id_convocatoria
               WHERE p.id_postulacion=%s""", (id_postulacion,), uno=True)
        if not fila:
            raise ErrorValidacion("La postulación no existe.")
        if fila["estado"] == "CERRADA":
            raise ErrorValidacion("La convocatoria está cerrada; ya no se pueden cambiar notas.")
        db.ejecutar("UPDATE postulacion SET nota_meritos=%s, nota_examen=%s WHERE id_postulacion=%s",
                    (_nota(nota_meritos, "nota de méritos"), _nota(nota_examen, "nota de examen"), id_postulacion))
        db.confirmar()

    @staticmethod
    def postulantes(id_convocatoria):
        """Postulantes ordenados por nota total (méritos + examen), el mejor primero."""
        return db.consultar(
            """SELECT p.*, e.carnet, e.nombres, e.apellidos,
                      CASE WHEN p.nota_meritos IS NULL OR p.nota_examen IS NULL THEN NULL
                           ELSE p.nota_meritos + p.nota_examen END AS total
               FROM postulacion p JOIN estudiante e ON e.id_estudiante=p.id_estudiante
               WHERE p.id_convocatoria=%s
               ORDER BY (p.nota_meritos IS NULL OR p.nota_examen IS NULL),
                        (p.nota_meritos + p.nota_examen) DESC, e.apellidos""",
            (id_convocatoria,),
        )

    @staticmethod
    def cerrar(id_convocatoria):
        """Cierra la convocatoria. Solo se puede si hay postulantes y todos tienen sus dos notas."""
        lista = Convocatoria.postulantes(id_convocatoria)
        if not lista:
            raise ErrorValidacion("No se puede cerrar una convocatoria sin postulantes.")
        if any(p["total"] is None for p in lista):
            raise ErrorValidacion("Faltan notas: todos los postulantes deben tener méritos y examen.")
        db.ejecutar("UPDATE convocatoria SET estado='CERRADA' WHERE id_convocatoria=%s", (id_convocatoria,))
        db.confirmar()

    @staticmethod
    def ganador(id_convocatoria):
        conv = Convocatoria.obtener(id_convocatoria)
        if not conv or conv["estado"] != "CERRADA":
            return None
        lista = Convocatoria.postulantes(id_convocatoria)
        return lista[0] if lista else None
