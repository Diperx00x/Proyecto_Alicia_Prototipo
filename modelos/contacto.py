import db
from modelos import ErrorValidacion


class Contacto:
    @staticmethod
    def registrar(nombre, cargo="", institucion=""):
        nombre = (nombre or "").strip()
        cargo = (cargo or "").strip()
        if not nombre:
            raise ErrorValidacion("El nombre del contacto es obligatorio.")
        existe = db.consultar(
            "SELECT id_contacto FROM contacto WHERE nombre=%s AND cargo=%s", (nombre, cargo), uno=True
        )
        if existe:
            raise ErrorValidacion("Ese contacto ya está registrado con el mismo cargo.")
        nuevo = db.ejecutar(
            "INSERT INTO contacto (nombre, cargo, institucion) VALUES (%s,%s,%s)",
            (nombre, cargo, (institucion or "").strip()),
        )
        db.confirmar()
        return nuevo

    @staticmethod
    def actualizar(id_contacto, nombre, cargo, institucion):
        if not (nombre or "").strip():
            raise ErrorValidacion("El nombre del contacto es obligatorio.")
        db.ejecutar(
            "UPDATE contacto SET nombre=%s, cargo=%s, institucion=%s WHERE id_contacto=%s",
            (nombre.strip(), (cargo or "").strip(), (institucion or "").strip(), id_contacto),
        )
        db.confirmar()

    @staticmethod
    def buscar(texto=""):
        patron = f"%{(texto or '').strip()}%"
        return db.consultar(
            """SELECT c.*, (SELECT COUNT(*) FROM documento d WHERE d.id_contacto=c.id_contacto) AS documentos
               FROM contacto c
               WHERE c.nombre LIKE %s OR c.cargo LIKE %s OR c.institucion LIKE %s
               ORDER BY c.nombre""",
            (patron, patron, patron),
        )

    @staticmethod
    def obtener(id_contacto):
        return db.consultar("SELECT * FROM contacto WHERE id_contacto=%s", (id_contacto,), uno=True)
