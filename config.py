"""Configuración del sistema. Se puede cambiar con variables de entorno
sin tocar el código (útil para las pruebas y para la laptop de la dirección)."""
import os

CARPETA_BASE = os.path.dirname(os.path.abspath(__file__))

MYSQL = {
    "host": os.environ.get("REGDOC_DB_HOST", "localhost"),
    "port": int(os.environ.get("REGDOC_DB_PORT", "3306")),
    "user": os.environ.get("REGDOC_DB_USER", "regdoc"),
    "password": os.environ.get("REGDOC_DB_PASS", "regdoc123"),
    "database": os.environ.get("REGDOC_DB_NAME", "regdoc"),
}

# Los escaneados se guardan en esta carpeta; en la base solo queda la ruta.
CARPETA_ARCHIVOS = os.environ.get("REGDOC_ARCHIVOS", os.path.join(CARPETA_BASE, "archivos"))
CARPETA_RESPALDOS = os.environ.get("REGDOC_RESPALDOS", os.path.join(CARPETA_BASE, "respaldos"))

EXTENSIONES_PERMITIDAS = {"pdf", "jpg", "jpeg", "png"}
TAMANO_MAXIMO_MB = 10

CLAVE_SECRETA = os.environ.get("REGDOC_CLAVE_SECRETA", "cambiar-esta-clave-en-la-laptop-de-la-direccion")

# Listas fijas (por confirmar con la directora).
CATEGORIAS = ["Académico", "Docente", "Auxiliatura", "Graduación", "Administrativo", "Invitación", "Otro"]
MODALIDADES = [
    "Graduación directa por excelencia",
    "Graduación directa por buen desempeño",
    "Tesis de grado",
    "Proyecto de grado",
    "Trabajo dirigido",
    "Examen de grado",
]
