"""Borra TODOS los datos del sistema (usuarios, documentos, actas, docentes, convocatorias)
y los escaneados, para empezar de cero. Las tablas y la configuración del CITE se mantienen.

    python vaciar_datos.py
"""
import os
import shutil
import sys

import pymysql

import config

TABLAS = ["postulacion", "convocatoria", "asignacion", "materia", "docente", "acta", "estudiante",
          "movimiento", "documento", "contacto", "usuario"]


def vaciar():
    conexion = pymysql.connect(**config.MYSQL, charset="utf8mb4", autocommit=False)
    with conexion.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        for tabla in TABLAS:
            cur.execute(f"DELETE FROM {tabla}")
        cur.execute("DELETE FROM parametro WHERE clave LIKE 'ultimo_%%'")
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
    conexion.commit()
    conexion.close()
    for carpeta in (config.CARPETA_ARCHIVOS, config.CARPETA_RESPALDOS):
        if os.path.isdir(carpeta):
            shutil.rmtree(carpeta)


if __name__ == "__main__":
    print("ATENCIÓN: esto borra TODOS los datos del sistema y los escaneados.")
    respuesta = input("Escriba SI (en mayúsculas) para confirmar: ").strip()
    if respuesta != "SI":
        print("Cancelado. No se borró nada.")
        sys.exit(0)
    try:
        vaciar()
    except pymysql.err.OperationalError as e:
        print("No se puede conectar con MySQL:", e)
        sys.exit(1)
    print("Listo. El sistema quedó vacío.")
    print("Al abrirlo con iniciar.bat pedirá crear la cuenta de la directora.")
