"""Conexión con MySQL. Cada petición del navegador abre una conexión
y la cierra al terminar."""
import pymysql
import pymysql.cursors
from flask import g

import config


def conectar():
    return pymysql.connect(
        **config.MYSQL,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def obtener():
    if "db" not in g:
        g.db = conectar()
    return g.db


def cerrar(_error=None):
    conexion = g.pop("db", None)
    if conexion is not None:
        conexion.close()


def consultar(sql, parametros=(), uno=False):
    with obtener().cursor() as cur:
        cur.execute(sql, parametros)
        return cur.fetchone() if uno else cur.fetchall()


def ejecutar(sql, parametros=()):
    """Ejecuta un INSERT/UPDATE/DELETE y devuelve el id generado (si hay)."""
    with obtener().cursor() as cur:
        cur.execute(sql, parametros)
        return cur.lastrowid


def confirmar():
    obtener().commit()


def deshacer():
    obtener().rollback()
