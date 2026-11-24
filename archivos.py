"""Guarda los escaneados en la carpeta de archivos y devuelve la ruta relativa
que se anota en la base de datos."""
import os
import uuid

from werkzeug.utils import secure_filename

import config
from modelos import ErrorValidacion


def extension_valida(nombre):
    return "." in nombre and nombre.rsplit(".", 1)[1].lower() in config.EXTENSIONES_PERMITIDAS


def guardar(archivo, subcarpeta):
    """archivo: el archivo que llegó del formulario. Devuelve None si no se eligió ninguno."""
    if archivo is None or not archivo.filename:
        return None
    if not extension_valida(archivo.filename):
        raise ErrorValidacion("Solo se aceptan archivos PDF, JPG o PNG.")
    archivo.stream.seek(0, os.SEEK_END)
    tamano = archivo.stream.tell()
    archivo.stream.seek(0)
    if tamano > config.TAMANO_MAXIMO_MB * 1024 * 1024:
        raise ErrorValidacion(
            f"El archivo pesa más de {config.TAMANO_MAXIMO_MB} MB. Escanee en blanco y negro o a menor resolución."
        )
    carpeta = os.path.join(config.CARPETA_ARCHIVOS, subcarpeta)
    os.makedirs(carpeta, exist_ok=True)
    nombre = f"{uuid.uuid4().hex[:8]}_{secure_filename(archivo.filename)}"
    archivo.save(os.path.join(carpeta, nombre))
    return f"{subcarpeta}/{nombre}"


def ruta_completa(ruta_relativa):
    ruta = os.path.normpath(os.path.join(config.CARPETA_ARCHIVOS, ruta_relativa))
    if not ruta.startswith(os.path.normpath(config.CARPETA_ARCHIVOS)):
        raise ErrorValidacion("Ruta de archivo no válida.")
    return ruta
