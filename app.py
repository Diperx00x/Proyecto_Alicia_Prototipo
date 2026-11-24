"""Sistema de Registro Documental – Versión B.
Para usarlo: python app.py  y abrir http://localhost:5000 en el navegador."""
from datetime import date, datetime

from flask import Flask, render_template

import config
import db
from rutas import cargar_usuario


def crear_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.CLAVE_SECRETA
    app.config["MAX_CONTENT_LENGTH"] = (config.TAMANO_MAXIMO_MB + 1) * 1024 * 1024

    from rutas import academico, administracion, auth, contactos, documentos, inicio
    for modulo in (auth, inicio, documentos, contactos, academico, administracion):
        app.register_blueprint(modulo.bp)

    app.before_request(cargar_usuario)
    app.teardown_appcontext(db.cerrar)

    @app.template_filter("fecha")
    def formato_fecha(valor):
        if not valor:
            return "—"
        if isinstance(valor, datetime):
            return valor.strftime("%d/%m/%Y %H:%M")
        if isinstance(valor, date):
            return valor.strftime("%d/%m/%Y")
        return valor

    @app.errorhandler(404)
    def no_encontrado(_e):
        return render_template("error.html", mensaje="La página o el registro que busca no existe."), 404

    import pymysql

    @app.errorhandler(pymysql.err.OperationalError)
    def sin_mysql(_e):
        return render_template(
            "error.html",
            mensaje="No se puede conectar con MySQL. Verifique que MySQL esté encendido "
                    "(en Windows: Servicios → MySQL80 → Iniciar) y vuelva a cargar la página.",
        ), 503

    @app.errorhandler(413)
    def muy_grande(_e):
        return render_template("error.html",
                               mensaje=f"El archivo pesa más de {config.TAMANO_MAXIMO_MB} MB."), 413

    return app


TITULO_VENTANA = "Registro Documental – Dirección de Carrera"
PUERTO = 5000


def iniciar_servidor():
    """Arranca Flask en segundo plano. Solo escucha en la propia computadora."""
    import threading
    from werkzeug.serving import make_server
    servidor = make_server("127.0.0.1", PUERTO, crear_app(), threaded=True)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor


def abrir_ventana():
    """Abre el sistema en su propia ventana (no en una pestaña del navegador).
    Al cerrar la ventana, el sistema se apaga."""
    import webview  # pywebview: usa el motor de Edge (WebView2) que ya trae Windows 10/11
    webview.settings["ALLOW_DOWNLOADS"] = True                 # para la copia de seguridad
    webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = False
    webview.create_window(TITULO_VENTANA, f"http://127.0.0.1:{PUERTO}",
                          width=1366, height=768, min_size=(1000, 650))
    webview.start()


if __name__ == "__main__":
    servidor = iniciar_servidor()
    try:
        abrir_ventana()
    finally:
        servidor.shutdown()
