from werkzeug.security import check_password_hash, generate_password_hash

import db
from modelos import ErrorValidacion

ROLES = ("DIRECTORA", "SECRETARIA")


class Usuario:
    @staticmethod
    def autenticar(usuario, clave):
        """Devuelve el usuario si el nombre y la clave son correctos; si no, None."""
        fila = db.consultar(
            "SELECT * FROM usuario WHERE usuario=%s AND activo=1", (usuario.strip(),), uno=True
        )
        if fila and check_password_hash(fila["clave_hash"], clave):
            return fila
        return None

    @staticmethod
    def registrar(nombre, usuario, clave, rol):
        nombre, usuario = (nombre or "").strip(), (usuario or "").strip()
        if not nombre or not usuario:
            raise ErrorValidacion("El nombre y el usuario son obligatorios.")
        if len(clave or "") < 6:
            raise ErrorValidacion("La contraseña debe tener al menos 6 caracteres.")
        if rol not in ROLES:
            raise ErrorValidacion("Rol no válido.")
        if db.consultar("SELECT 1 FROM usuario WHERE usuario=%s", (usuario,), uno=True):
            raise ErrorValidacion(f"El usuario «{usuario}» ya existe.")
        nuevo = db.ejecutar(
            "INSERT INTO usuario (nombre, usuario, clave_hash, rol) VALUES (%s,%s,%s,%s)",
            (nombre, usuario, generate_password_hash(clave), rol),
        )
        db.confirmar()
        return nuevo

    @staticmethod
    def cambiar_clave(id_usuario, actual, nueva):
        fila = db.consultar("SELECT * FROM usuario WHERE id_usuario=%s", (id_usuario,), uno=True)
        if not fila or not check_password_hash(fila["clave_hash"], actual):
            raise ErrorValidacion("La contraseña actual no es correcta.")
        if len(nueva or "") < 6:
            raise ErrorValidacion("La contraseña nueva debe tener al menos 6 caracteres.")
        db.ejecutar(
            "UPDATE usuario SET clave_hash=%s WHERE id_usuario=%s",
            (generate_password_hash(nueva), id_usuario),
        )
        db.confirmar()

    @staticmethod
    def cambiar_activo(id_usuario, activo, id_quien):
        if int(id_usuario) == int(id_quien):
            raise ErrorValidacion("No puede desactivar su propio usuario.")
        db.ejecutar("UPDATE usuario SET activo=%s WHERE id_usuario=%s", (1 if activo else 0, id_usuario))
        db.confirmar()

    @staticmethod
    def listar():
        return db.consultar("SELECT id_usuario, nombre, usuario, rol, activo FROM usuario ORDER BY nombre")

    @staticmethod
    def hay_usuarios():
        return db.consultar("SELECT COUNT(*) AS n FROM usuario", uno=True)["n"] > 0
