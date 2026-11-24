"""Pruebas del sistema. Usan una base aparte (regdoc_prueba) que se crea y se borra sola.

    python -m pytest pruebas -v

Requiere MySQL encendido y el usuario root (variable REGDOC_ROOT_PASS si tiene contraseña)."""
import io
import os
import sys
import tempfile
from datetime import date, timedelta

import pymysql
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["REGDOC_DB_NAME"] = "regdoc_prueba"
os.environ["REGDOC_ARCHIVOS"] = tempfile.mkdtemp(prefix="regdoc_archivos_")
os.environ["REGDOC_RESPALDOS"] = tempfile.mkdtemp(prefix="regdoc_respaldos_")

import config  # noqa: E402
import preparar_base  # noqa: E402
from app import crear_app  # noqa: E402
from modelos import ErrorValidacion  # noqa: E402
from modelos.academico import Acta, Asignacion, Convocatoria, Docente, Materia  # noqa: E402
from modelos.contacto import Contacto  # noqa: E402
from modelos.documento import Documento  # noqa: E402
from modelos.usuario import Usuario  # noqa: E402

ROOT = {"host": config.MYSQL["host"], "port": config.MYSQL["port"], "user": os.environ.get("REGDOC_ROOT_USER", "root"),
        "password": os.environ.get("REGDOC_ROOT_PASS", "")}
HOY = date.today()


def _root():
    return pymysql.connect(**ROOT, autocommit=True)


@pytest.fixture()
def app():
    c = _root()
    c.cursor().execute("DROP DATABASE IF EXISTS regdoc_prueba")
    c.close()
    preparar_base.preparar(ROOT["host"], ROOT["port"], ROOT["user"], ROOT["password"], "regdoc_prueba")
    aplicacion = crear_app()
    aplicacion.config["TESTING"] = True
    with aplicacion.app_context():
        yield aplicacion
    c = _root()
    c.cursor().execute("DROP DATABASE IF EXISTS regdoc_prueba")
    c.close()


@pytest.fixture()
def directora(app):
    return Usuario.registrar("M.Sc. Ing. Directora Prueba", "directora", "clave123", "DIRECTORA")


@pytest.fixture()
def contacto(app):
    return Contacto.registrar("Lic. Decano Prueba", "Decano", "F.IN.I.")


def _salida(id_contacto, **extra):
    datos = {"sentido": "SALIDA", "fecha": HOY.isoformat(), "id_contacto": id_contacto,
             "asunto": "Solicitud de aulas", "categoria": "Académico", "requiere_respuesta": "1"}
    datos.update(extra)
    return datos


def _entrada(id_contacto, cite="VR-001/2026", **extra):
    datos = {"sentido": "ENTRADA", "fecha": HOY.isoformat(), "id_contacto": id_contacto, "cite": cite,
             "asunto": "Pedido de informe", "categoria": "Docente", "requiere_respuesta": "1"}
    datos.update(extra)
    return datos


# ------------------------------------------------------------------ PR01-PR06 documentos
def test_pr01_cite_correlativo(directora, contacto):
    a = Documento.obtener(Documento.registrar(_salida(contacto), directora))
    b = Documento.obtener(Documento.registrar(_salida(contacto), directora))
    assert a["numero"] == 1 and b["numero"] == 2
    assert a["cite"].endswith(f" 01/{HOY.year}") and b["cite"].endswith(f" 02/{HOY.year}")


def test_pr02_numero_vuelve_a_1_cada_gestion(directora, contacto):
    Documento.registrar(_salida(contacto, fecha="2025-12-30"), directora)
    Documento.registrar(_salida(contacto, fecha="2025-12-31"), directora)
    nuevo = Documento.obtener(Documento.registrar(_salida(contacto, fecha=f"{HOY.year}-01-02"), directora))
    assert nuevo["numero"] == 1


def test_pr03_sigue_desde_ultimo_numero_configurado(app, directora, contacto):
    import db
    db.ejecutar("REPLACE INTO parametro VALUES (%s,'120')", (f"ultimo_salida_{HOY.year}",))
    db.confirmar()
    doc = Documento.obtener(Documento.registrar(_salida(contacto), directora))
    assert doc["numero"] == 121


def test_pr04_entrada_repetida_del_mismo_remitente(directora, contacto):
    Documento.registrar(_entrada(contacto), directora)
    with pytest.raises(ErrorValidacion):
        Documento.registrar(_entrada(contacto), directora)
    otro = Contacto.registrar("Ing. Otro Remitente", "Jefe", "CPD")
    Documento.registrar(_entrada(otro), directora)  # mismo número, otro remitente: se acepta


def test_pr05_campos_obligatorios(directora, contacto):
    with pytest.raises(ErrorValidacion):
        Documento.registrar(_salida(contacto, asunto="  "), directora)
    with pytest.raises(ErrorValidacion):
        Documento.registrar(_salida(None), directora)
    with pytest.raises(ErrorValidacion):
        Documento.registrar(_entrada(contacto, cite=""), directora)
    with pytest.raises(ErrorValidacion):
        Documento.registrar(_salida(contacto, categoria="Inventada"), directora)


def test_pr06_fecha_limite_no_antes_de_fecha(directora, contacto):
    with pytest.raises(ErrorValidacion):
        Documento.registrar(_salida(contacto, fecha_limite=(HOY - timedelta(days=1)).isoformat()), directora)


# ------------------------------------------------------------------ PR07-PR10 estados e historial
def test_pr07_historial_guarda_cada_cambio(directora, contacto):
    d = Documento.registrar(_entrada(contacto), directora)
    Documento.cambiar_estado(d, "EN_TRAMITE", "Pasado a secretaría", directora)
    Documento.cambiar_estado(d, "ARCHIVADO", None, directora)
    from modelos.documento import Movimiento
    estados = [m["estado"] for m in Movimiento.historial(d)]
    assert estados == ["REGISTRADO", "EN_TRAMITE", "ARCHIVADO"]


def test_pr08_transicion_no_permitida(directora, contacto):
    d = Documento.registrar(_entrada(contacto), directora)
    Documento.cambiar_estado(d, "ARCHIVADO", None, directora)
    with pytest.raises(ErrorValidacion):
        Documento.cambiar_estado(d, "EN_TRAMITE", None, directora)


def test_pr09_responder_enlaza_y_marca_respondido(directora, contacto):
    entrada = Documento.registrar(_entrada(contacto), directora)
    respuesta = Documento.responder(entrada, {"fecha": HOY.isoformat(), "asunto": "Respuesta",
                                              "categoria": "Docente"}, directora)
    r = Documento.obtener(respuesta)
    assert r["sentido"] == "SALIDA" and r["id_responde_a"] == entrada
    assert Documento.obtener(entrada)["estado"] == "RESPONDIDO"
    with pytest.raises(ErrorValidacion):  # no se responde dos veces
        Documento.responder(entrada, {"fecha": HOY.isoformat(), "asunto": "Otra", "categoria": "Docente"}, directora)


def test_pr10_pendientes_y_vencidos(directora, contacto):
    con_plazo = Documento.registrar(_salida(contacto, fecha=(HOY - timedelta(days=10)).isoformat(),
                                            fecha_limite=(HOY - timedelta(days=2)).isoformat()), directora)
    Documento.registrar(_salida(contacto, requiere_respuesta=""), directora)  # solo de conocimiento
    pend = Documento.pendientes()
    assert [p["id_documento"] for p in pend] == [con_plazo]
    assert pend[0]["vencido"] and pend[0]["dias"] == 10


def test_pr11_busqueda_por_texto_y_filtros(directora, contacto):
    Documento.registrar(_salida(contacto, asunto="Certificación presupuestaria"), directora)
    Documento.registrar(_entrada(contacto, asunto="Invitación a congreso", categoria="Invitación"), directora)
    assert len(Documento.buscar(texto="presupuestaria")) == 1
    assert len(Documento.buscar(categoria="Invitación")) == 1
    assert len(Documento.buscar(sentido="SALIDA")) == 1
    assert len(Documento.buscar(texto="Decano")) == 2


# ------------------------------------------------------------------ PR12-PR14 actas
def _acta(**extra):
    datos = {"nro_acta": "150/2026", "fecha": HOY.isoformat(), "carnet": "9876543 sc", "nombres": "Ana",
             "apellidos": "Rojas", "modalidad": config.MODALIDADES[0], "nota": "95"}
    datos.update(extra)
    return datos


def test_pr12_acta_y_busqueda_por_carnet(app):
    Acta.registrar(_acta())
    assert Acta.buscar("9876543")[0]["nombres"] == "Ana"
    assert Acta.buscar("150/2026")[0]["carnet"] == "9876543 SC"


def test_pr13_acta_repetida_y_estudiante_con_dos_actas(app):
    Acta.registrar(_acta())
    with pytest.raises(ErrorValidacion):
        Acta.registrar(_acta(carnet="111"))          # mismo número de acta
    with pytest.raises(ErrorValidacion):
        Acta.registrar(_acta(nro_acta="151/2026"))  # mismo estudiante


def test_pr14_nota_fuera_de_rango(app):
    with pytest.raises(ErrorValidacion):
        Acta.registrar(_acta(nota="101"))
    with pytest.raises(ErrorValidacion):
        Acta.registrar(_acta(nota="ochenta"))


# ------------------------------------------------------------------ PR15-PR16 docentes
def test_pr15_informes_pendientes(app):
    d = Docente.registrar("Ing. Docente Uno", "123456")
    m = Materia.registrar("inf-110", "Introducción a la informática")
    a = Asignacion.registrar(d, m, HOY.year, 1)
    assert len(Asignacion.listar(solo_pendientes=True)) == 1
    with pytest.raises(ErrorValidacion):
        Asignacion.registrar_informe(a, HOY.isoformat(), None)  # sin archivo no se acepta
    Asignacion.registrar_informe(a, HOY.isoformat(), "informes/x.pdf")
    assert len(Asignacion.listar(solo_pendientes=True)) == 0


def test_pr16_materia_con_un_docente_por_periodo(app):
    d1, d2 = Docente.registrar("Doc A", "1"), Docente.registrar("Doc B", "2")
    m = Materia.registrar("INF-120", "Programación I")
    Asignacion.registrar(d1, m, HOY.year, 1)
    with pytest.raises(ErrorValidacion):
        Asignacion.registrar(d2, m, HOY.year, 1)


# ------------------------------------------------------------------ PR17-PR18 auxiliares
def test_pr17_convocatoria_ganador(app):
    m = Materia.registrar("INF-210", "Programación II")
    c = Convocatoria.registrar(m, HOY.year, 2, HOY.isoformat())
    p1 = Convocatoria.agregar_postulante(c, "111 SC", "Luis", "Paz")
    p2 = Convocatoria.agregar_postulante(c, "222 SC", "Eva", "Soto")
    with pytest.raises(ErrorValidacion):
        Convocatoria.cerrar(c)  # faltan notas
    Convocatoria.calificar(p1, "30", "40")
    Convocatoria.calificar(p2, "35", "50")
    Convocatoria.cerrar(c)
    assert Convocatoria.ganador(c)["carnet"] == "222 SC"
    with pytest.raises(ErrorValidacion):
        Convocatoria.agregar_postulante(c, "333", "X", "Y")  # cerrada


def test_pr18_estudiante_compartido_entre_auxiliatura_y_acta(app):
    m = Materia.registrar("INF-310", "Base de datos")
    c = Convocatoria.registrar(m, HOY.year, 1, HOY.isoformat())
    Convocatoria.agregar_postulante(c, "555 SC", "Rosa", "Vaca")
    Acta.registrar(_acta(carnet="555 sc", nombres="otro", apellidos="nombre"))
    acta = Acta.buscar("555")[0]
    assert acta["nombres"] == "Rosa"  # se reutiliza el estudiante, no se duplica


# ------------------------------------------------------------------ PR19-PR22 pantallas, login y roles
def _ingresar(cliente, usuario, clave):
    return cliente.post("/ingresar", data={"usuario": usuario, "clave": clave}, follow_redirects=True)


def test_pr19_sin_login_no_se_entra(app, directora):
    cliente = app.test_client()
    r = cliente.get("/documentos/")
    assert r.status_code == 302 and "/ingresar" in r.headers["Location"]
    assert "incorrectos" in _ingresar(cliente, "directora", "mala").get_data(as_text=True)


def test_pr20_secretaria_no_entra_a_usuarios(app, directora):
    Usuario.registrar("Secretaria Prueba", "secre", "clave123", "SECRETARIA")
    cliente = app.test_client()
    _ingresar(cliente, "secre", "clave123")
    r = cliente.get("/administracion/usuarios", follow_redirects=True)
    assert "solo la puede usar la directora" in r.get_data(as_text=True)


def test_pr21_registrar_por_pantalla_con_escaneado(app, directora, contacto):
    cliente = app.test_client()
    _ingresar(cliente, "directora", "clave123")
    datos = _entrada(contacto)
    datos.pop("sentido")
    datos["archivo"] = (io.BytesIO(b"%PDF-1.4 prueba"), "oficio.pdf")
    r = cliente.post("/documentos/nuevo/entrada", data=datos, content_type="multipart/form-data",
                     follow_redirects=True)
    texto = r.get_data(as_text=True)
    assert "Documento registrado" in texto and "VR-001/2026" in texto
    doc = Documento.buscar()[0]
    assert doc["archivo"] and os.path.exists(os.path.join(config.CARPETA_ARCHIVOS, doc["archivo"]))
    assert cliente.get(f"/archivo/{doc['archivo']}").status_code == 200


def test_pr22_archivo_no_permitido_y_respaldo(app, directora, contacto):
    cliente = app.test_client()
    _ingresar(cliente, "directora", "clave123")
    datos = _entrada(contacto)
    datos.pop("sentido")
    datos["archivo"] = (io.BytesIO(b"MZ"), "virus.exe")
    r = cliente.post("/documentos/nuevo/entrada", data=datos, content_type="multipart/form-data",
                     follow_redirects=True)
    assert "Solo se aceptan archivos PDF" in r.get_data(as_text=True)
    r = cliente.post("/administracion/respaldo")
    assert r.status_code == 200 and r.data[:2] == b"PK"  # es un .zip


def test_pr23_todas_las_pantallas_abren(app, directora, contacto):
    cliente = app.test_client()
    _ingresar(cliente, "directora", "clave123")
    for ruta in ["/", "/documentos/", "/documentos/pendientes", "/documentos/nuevo/salida",
                 "/documentos/nuevo/entrada", "/contactos/", "/actas", "/actas/nueva", "/docentes",
                 "/auxiliares", "/administracion/usuarios", "/administracion/configuracion",
                 "/administracion/respaldo", "/mi-clave"]:
        assert cliente.get(ruta).status_code == 200, ruta
