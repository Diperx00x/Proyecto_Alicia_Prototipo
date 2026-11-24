"""Copia de seguridad: un archivo .zip con todos los datos de la base (en SQL)
y todos los escaneados. Se genera con un botón y se descarga."""
import datetime
import io
import os
import zipfile
from decimal import Decimal

import config
import db

TABLAS = ["usuario", "parametro", "contacto", "documento", "movimiento", "estudiante", "acta",
          "docente", "materia", "asignacion", "convocatoria", "postulacion"]


def _valor_sql(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float, Decimal)):
        return str(v)
    if isinstance(v, (datetime.date, datetime.datetime)):
        return f"'{v.isoformat(sep=' ') if isinstance(v, datetime.datetime) else v.isoformat()}'"
    texto = str(v).replace("\\", "\\\\").replace("'", "''")
    return f"'{texto}'"


def volcado_sql():
    lineas = ["-- Respaldo del Sistema de Registro Documental – Versión B",
              f"-- Generado: {datetime.datetime.now():%Y-%m-%d %H:%M}",
              "SET FOREIGN_KEY_CHECKS=0;"]
    for tabla in TABLAS:
        lineas.append(f"DELETE FROM {tabla};")
        for fila in db.consultar(f"SELECT * FROM {tabla}"):
            columnas = ", ".join(fila.keys())
            valores = ", ".join(_valor_sql(v) for v in fila.values())
            lineas.append(f"INSERT INTO {tabla} ({columnas}) VALUES ({valores});")
    lineas.append("SET FOREIGN_KEY_CHECKS=1;")
    return "\n".join(lineas) + "\n"


def generar_zip():
    """Devuelve (nombre_archivo, bytes_del_zip). También guarda una copia en la carpeta de respaldos."""
    nombre = f"respaldo_{datetime.datetime.now():%Y-%m-%d_%H%M}.zip"
    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("datos.sql", volcado_sql())
        if os.path.isdir(config.CARPETA_ARCHIVOS):
            for raiz, _dirs, archivos in os.walk(config.CARPETA_ARCHIVOS):
                for a in archivos:
                    completo = os.path.join(raiz, a)
                    z.write(completo, os.path.join("archivos", os.path.relpath(completo, config.CARPETA_ARCHIVOS)))
    datos = memoria.getvalue()
    os.makedirs(config.CARPETA_RESPALDOS, exist_ok=True)
    with open(os.path.join(config.CARPETA_RESPALDOS, nombre), "wb") as f:
        f.write(datos)
    return nombre, datos
