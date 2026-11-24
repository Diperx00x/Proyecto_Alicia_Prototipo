"""Crea la base de datos 'regdoc', sus tablas y el usuario de MySQL que usa el sistema.
Se ejecuta UNA sola vez, después de instalar MySQL:

    python preparar_base.py

Pide la contraseña del usuario 'root' de MySQL (la que se puso al instalar MySQL)."""
import getpass
import os
import re

import pymysql

import config


def sentencias(ruta, nombre_base):
    texto = open(ruta, encoding="utf-8").read()
    texto = re.sub(r"--[^\n]*", "", texto)
    texto = texto.replace("regdoc", nombre_base) if nombre_base != "regdoc" else texto
    return [s.strip() for s in texto.split(";") if s.strip()]


def preparar(host, puerto, usuario_admin, clave_admin, nombre_base=None, crear_usuario=True):
    nombre_base = nombre_base or config.MYSQL["database"]
    conexion = pymysql.connect(host=host, port=puerto, user=usuario_admin, password=clave_admin,
                               charset="utf8mb4", autocommit=True)
    with conexion.cursor() as cur:
        for s in sentencias(os.path.join(config.CARPETA_BASE, "sql", "esquema.sql"), nombre_base):
            cur.execute(s)
        if crear_usuario:
            u, c = config.MYSQL["user"], config.MYSQL["password"]
            cur.execute("CREATE USER IF NOT EXISTS %s@'localhost' IDENTIFIED BY %s", (u, c))
            cur.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON `{nombre_base}`.* TO %s@'localhost'", (u,))
            cur.execute("FLUSH PRIVILEGES")
    conexion.close()


if __name__ == "__main__":
    import sys
    print("Preparación de la base de datos del Sistema de Registro Documental")
    print("(Al escribir la contraseña no se ve nada en pantalla: es normal.)")
    for intento in range(3):
        clave = getpass.getpass("Contraseña del usuario root de MySQL: ")
        try:
            preparar(config.MYSQL["host"], config.MYSQL["port"], "root", clave)
            print("Base de datos lista.")
            sys.exit(0)
        except pymysql.err.OperationalError as e:
            codigo = e.args[0]
            if codigo == 1045:
                print("Contraseña incorrecta. Intente de nuevo.")
            elif codigo == 2003:
                print("No se puede conectar con MySQL. ¿Está instalado y encendido?")
                print("En Windows: Servicios -> MySQL80 -> Iniciar.")
                sys.exit(1)
            else:
                print("Error de MySQL:", e)
                sys.exit(1)
    sys.exit(1)
