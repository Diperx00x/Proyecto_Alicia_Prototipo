"""Clases Documento y Movimiento.

Un solo registro para todo lo que entra (ENTRADA) y lo que sale (SALIDA).
Cada cambio de estado se guarda como un Movimiento, así queda el historial completo."""
from datetime import date

import pymysql

import config
import db
from modelos import ErrorValidacion

SENTIDOS = ("ENTRADA", "SALIDA")
ESTADOS = ("REGISTRADO", "EN_TRAMITE", "RESPONDIDO", "ARCHIVADO")

# Desde qué estado se puede pasar a cuál.
TRANSICIONES = {
    "REGISTRADO": ("EN_TRAMITE", "RESPONDIDO", "ARCHIVADO"),
    "EN_TRAMITE": ("RESPONDIDO", "ARCHIVADO"),
    "RESPONDIDO": ("ARCHIVADO",),
    "ARCHIVADO": (),
}

NOMBRE_ESTADO = {
    "REGISTRADO": "Registrado",
    "EN_TRAMITE": "En trámite",
    "RESPONDIDO": "Respondido",
    "ARCHIVADO": "Archivado",
}


def _a_fecha(valor, campo, obligatorio=True):
    if not valor:
        if obligatorio:
            raise ErrorValidacion(f"La {campo} es obligatoria.")
        return None
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise ErrorValidacion(f"La {campo} no es válida.")


class Movimiento:
    @staticmethod
    def registrar(id_documento, estado, observacion, id_usuario):
        db.ejecutar(
            "INSERT INTO movimiento (id_documento, estado, observacion, id_usuario) VALUES (%s,%s,%s,%s)",
            (id_documento, estado, observacion, id_usuario),
        )

    @staticmethod
    def historial(id_documento):
        return db.consultar(
            """SELECT m.*, u.nombre AS usuario FROM movimiento m
               JOIN usuario u ON u.id_usuario=m.id_usuario
               WHERE m.id_documento=%s ORDER BY m.fecha_hora, m.id_movimiento""",
            (id_documento,),
        )


class Documento:
    # ---------- numeración ----------
    @staticmethod
    def generar_numero(sentido, gestion):
        """Siguiente número de la gestión. Vuelve a 1 cada año. Si la directora configuró
        el último número usado (porque empezó a usar el sistema a mitad de año), sigue desde ahí."""
        fila = db.consultar(
            "SELECT COALESCE(MAX(numero),0) AS ultimo FROM documento WHERE sentido=%s AND gestion=%s",
            (sentido, gestion),
            uno=True,
        )
        inicial = db.consultar(
            "SELECT valor FROM parametro WHERE clave=%s", (f"ultimo_{sentido.lower()}_{gestion}",), uno=True
        )
        ultimo = max(int(fila["ultimo"]), int(inicial["valor"]) if inicial else 0)
        return ultimo + 1

    @staticmethod
    def generar_cite(numero, gestion):
        prefijo = db.consultar("SELECT valor FROM parametro WHERE clave='prefijo_cite'", uno=True)
        prefijo = prefijo["valor"] if prefijo else "OF. No."
        return f"{prefijo} {numero:02d}/{gestion}"

    # ---------- registro ----------
    @staticmethod
    def registrar(datos, id_usuario, archivo=None, id_responde_a=None, confirmar=True):
        """datos: diccionario con sentido, fecha, id_contacto, asunto, categoria,
        requiere_respuesta, fecha_limite y (solo para ENTRADA) cite = N° de oficio del remitente."""
        sentido = datos.get("sentido")
        if sentido not in SENTIDOS:
            raise ErrorValidacion("Indique si el documento entra o sale.")
        fecha = _a_fecha(datos.get("fecha"), "fecha")
        fecha_limite = _a_fecha(datos.get("fecha_limite"), "fecha límite", obligatorio=False)
        if fecha_limite and fecha_limite < fecha:
            raise ErrorValidacion("La fecha límite no puede ser anterior a la fecha del documento.")
        asunto = (datos.get("asunto") or "").strip()
        if not asunto:
            raise ErrorValidacion("El asunto es obligatorio.")
        if not datos.get("id_contacto"):
            raise ErrorValidacion(
                "Elija el destinatario." if sentido == "SALIDA" else "Elija el remitente."
            )
        categoria = datos.get("categoria")
        if categoria not in config.CATEGORIAS:
            raise ErrorValidacion("Elija una categoría de la lista.")
        requiere = 1 if datos.get("requiere_respuesta") in (True, 1, "1", "on", "si") else 0
        gestion = fecha.year

        cite_origen = (datos.get("cite") or "").strip()
        if sentido == "ENTRADA":
            if not cite_origen:
                raise ErrorValidacion("El número de oficio del remitente es obligatorio.")
            repetido = db.consultar(
                "SELECT 1 FROM documento WHERE sentido='ENTRADA' AND gestion=%s AND id_contacto=%s AND cite=%s",
                (gestion, datos["id_contacto"], cite_origen),
                uno=True,
            )
            if repetido:
                raise ErrorValidacion(
                    f"Ya se registró el oficio «{cite_origen}» de este remitente en la gestión {gestion}."
                )

        # Dos usuarias pueden registrar al mismo tiempo: si chocan en el número,
        # la base lo rechaza (UNIQUE) y se vuelve a intentar con el siguiente.
        for _intento in range(3):
            numero = Documento.generar_numero(sentido, gestion)
            cite = Documento.generar_cite(numero, gestion) if sentido == "SALIDA" else cite_origen
            try:
                nuevo = db.ejecutar(
                    """INSERT INTO documento (sentido, gestion, numero, cite, fecha, id_contacto, asunto,
                       categoria, requiere_respuesta, fecha_limite, archivo, id_responde_a, id_usuario)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (sentido, gestion, numero, cite, fecha, datos["id_contacto"], asunto, categoria,
                     requiere, fecha_limite, archivo, id_responde_a, id_usuario),
                )
                break
            except pymysql.err.IntegrityError as error:
                db.deshacer()
                if "uq_numero" not in str(error):
                    raise
        else:
            raise ErrorValidacion("No se pudo asignar el número. Intente de nuevo.")

        Movimiento.registrar(nuevo, "REGISTRADO", "Registro inicial", id_usuario)
        if confirmar:
            db.confirmar()
        return nuevo

    @staticmethod
    def responder(id_original, datos, id_usuario, archivo=None):
        """Registra la respuesta (documento del sentido contrario) y marca el original como RESPONDIDO."""
        original = Documento.obtener(id_original)
        if not original:
            raise ErrorValidacion("El documento que quiere responder no existe.")
        if original["estado"] in ("RESPONDIDO", "ARCHIVADO"):
            raise ErrorValidacion("Ese documento ya está respondido o archivado.")
        datos = dict(datos)
        datos["sentido"] = "SALIDA" if original["sentido"] == "ENTRADA" else "ENTRADA"
        datos.setdefault("id_contacto", original["id_contacto"])
        nuevo = Documento.registrar(datos, id_usuario, archivo, id_responde_a=id_original, confirmar=False)
        respuesta = Documento.obtener(nuevo)
        db.ejecutar("UPDATE documento SET estado='RESPONDIDO' WHERE id_documento=%s", (id_original,))
        Movimiento.registrar(id_original, "RESPONDIDO", f"Respondido con {respuesta['cite']}", id_usuario)
        db.confirmar()
        return nuevo

    @staticmethod
    def cambiar_estado(id_documento, estado, observacion, id_usuario):
        doc = Documento.obtener(id_documento)
        if not doc:
            raise ErrorValidacion("El documento no existe.")
        if estado not in TRANSICIONES[doc["estado"]]:
            raise ErrorValidacion(
                f"No se puede pasar de «{NOMBRE_ESTADO[doc['estado']]}» a «{NOMBRE_ESTADO.get(estado, estado)}»."
            )
        db.ejecutar("UPDATE documento SET estado=%s WHERE id_documento=%s", (estado, id_documento))
        Movimiento.registrar(id_documento, estado, (observacion or "").strip() or None, id_usuario)
        db.confirmar()

    @staticmethod
    def adjuntar_archivo(id_documento, ruta):
        db.ejecutar("UPDATE documento SET archivo=%s WHERE id_documento=%s", (ruta, id_documento))
        db.confirmar()

    # ---------- consultas ----------
    @staticmethod
    def obtener(id_documento):
        return db.consultar(
            """SELECT d.*, c.nombre AS contacto, c.cargo AS contacto_cargo, c.institucion,
                      u.nombre AS registrado_por, r.cite AS cite_responde_a
               FROM documento d
               JOIN contacto c ON c.id_contacto=d.id_contacto
               JOIN usuario u ON u.id_usuario=d.id_usuario
               LEFT JOIN documento r ON r.id_documento=d.id_responde_a
               WHERE d.id_documento=%s""",
            (id_documento,),
            uno=True,
        )

    @staticmethod
    def respuestas(id_documento):
        return db.consultar(
            "SELECT id_documento, cite, fecha, sentido FROM documento WHERE id_responde_a=%s ORDER BY fecha",
            (id_documento,),
        )

    @staticmethod
    def buscar(texto="", sentido="", gestion="", categoria="", estado="", desde="", hasta=""):
        sql = [
            """SELECT d.id_documento, d.sentido, d.numero, d.cite, d.fecha, d.asunto, d.categoria,
                      d.estado, d.requiere_respuesta, d.fecha_limite, d.archivo, c.nombre AS contacto
               FROM documento d JOIN contacto c ON c.id_contacto=d.id_contacto WHERE 1=1"""
        ]
        p = []
        if texto:
            sql.append("AND (d.cite LIKE %s OR d.asunto LIKE %s OR c.nombre LIKE %s OR c.institucion LIKE %s)")
            p += [f"%{texto.strip()}%"] * 4
        for campo, valor in (("d.sentido", sentido), ("d.gestion", gestion),
                             ("d.categoria", categoria), ("d.estado", estado)):
            if valor:
                sql.append(f"AND {campo}=%s")
                p.append(valor)
        if desde:
            sql.append("AND d.fecha>=%s")
            p.append(desde)
        if hasta:
            sql.append("AND d.fecha<=%s")
            p.append(hasta)
        sql.append("ORDER BY d.fecha DESC, d.id_documento DESC LIMIT 500")
        return db.consultar(" ".join(sql), p)

    @staticmethod
    def pendientes():
        """Documentos que requieren respuesta y todavía no la tienen, el más antiguo primero."""
        filas = db.consultar(
            """SELECT d.id_documento, d.sentido, d.cite, d.fecha, d.asunto, d.estado, d.fecha_limite,
                      c.nombre AS contacto, DATEDIFF(CURDATE(), d.fecha) AS dias
               FROM documento d JOIN contacto c ON c.id_contacto=d.id_contacto
               WHERE d.requiere_respuesta=1 AND d.estado IN ('REGISTRADO','EN_TRAMITE')
               ORDER BY (d.fecha_limite IS NULL), d.fecha_limite, d.fecha"""
        )
        hoy = date.today()
        for f in filas:
            f["vencido"] = bool(f["fecha_limite"] and f["fecha_limite"] < hoy)
        return filas

    @staticmethod
    def gestiones():
        filas = db.consultar("SELECT DISTINCT gestion FROM documento ORDER BY gestion DESC")
        return [f["gestion"] for f in filas]

    @staticmethod
    def resumen(gestion):
        fila = db.consultar(
            """SELECT SUM(sentido='ENTRADA') AS entradas, SUM(sentido='SALIDA') AS salidas
               FROM documento WHERE gestion=%s""",
            (gestion,),
            uno=True,
        )
        return {"entradas": int(fila["entradas"] or 0), "salidas": int(fila["salidas"] or 0)}
