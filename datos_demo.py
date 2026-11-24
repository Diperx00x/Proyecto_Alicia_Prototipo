"""Carga datos de ejemplo para mostrar el sistema en la defensa.
NO usar en la base real de la dirección.

    python datos_demo.py

Crea los usuarios  directora / demo123  y  secretaria / demo123."""
import os
from datetime import date, timedelta

import config

from app import crear_app
from modelos.academico import Acta, Asignacion, Convocatoria, Docente, Materia
from modelos.contacto import Contacto
from modelos.documento import Documento
from modelos.usuario import Usuario

HOY = date.today()


def pdf_ejemplo(ruta_relativa, titulo):
    """Crea un PDF de una página que dice DOCUMENTO DE EJEMPLO (para que el visor muestre algo)."""
    texto = f"BT /F1 20 Tf 72 720 Td (DOCUMENTO DE EJEMPLO) Tj 0 -32 Td /F1 13 Tf ({titulo}) Tj ET"
    objetos = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(texto)} >>\nstream\n{texto}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    salida, posiciones = "%PDF-1.4\n", []
    for i, o in enumerate(objetos, 1):
        posiciones.append(len(salida))
        salida += f"{i} 0 obj\n{o}\nendobj\n"
    inicio_xref = len(salida)
    salida += f"xref\n0 {len(objetos)+1}\n0000000000 65535 f \n"
    salida += "".join(f"{p:010d} 00000 n \n" for p in posiciones)
    salida += f"trailer\n<< /Size {len(objetos)+1} /Root 1 0 R >>\nstartxref\n{inicio_xref}\n%%EOF\n"
    completa = os.path.join(config.CARPETA_ARCHIVOS, ruta_relativa)
    os.makedirs(os.path.dirname(completa), exist_ok=True)
    with open(completa, "w", encoding="latin-1") as f:
        f.write(salida)
    return ruta_relativa


def dias(n):
    return (HOY - timedelta(days=n)).isoformat()


def cargar():
    dir_ = Usuario.registrar("M.Sc. Ing. Alicia Serrano Rodríguez", "directora", "demo123", "DIRECTORA")
    sec = Usuario.registrar("Secretaria de Dirección", "secretaria", "demo123", "SECRETARIA")

    decano = Contacto.registrar("Decanatura (ejemplo)", "Decano", "F.IN.I. – U.A.G.R.M.")
    vice = Contacto.registrar("Vicedecanatura (ejemplo)", "Vicedecano", "F.IN.I. – U.A.G.R.M.")
    cpd = Contacto.registrar("Centro de Procesamiento de Datos (ejemplo)", "Jefe del CPD", "F.IN.I. – U.A.G.R.M.")
    adm = Contacto.registrar("Administración de Facultad (ejemplo)", "Administrador", "F.IN.I. – U.A.G.R.M.")
    doc = Contacto.registrar("Ing. Docente de ejemplo", "Docente", "Carrera Ing. en Sistemas")

    def salida(dias_atras, contacto, asunto, categoria, requiere=True, limite=None, usuario=dir_):
        return Documento.registrar({"sentido": "SALIDA", "fecha": dias(dias_atras), "id_contacto": contacto,
                                    "asunto": asunto, "categoria": categoria,
                                    "requiere_respuesta": "1" if requiere else "", "fecha_limite": limite}, usuario)

    def entrada(dias_atras, contacto, cite, asunto, categoria, requiere=True, limite=None, usuario=sec):
        return Documento.registrar({"sentido": "ENTRADA", "fecha": dias(dias_atras), "id_contacto": contacto,
                                    "cite": cite, "asunto": asunto, "categoria": categoria,
                                    "requiere_respuesta": "1" if requiere else "", "fecha_limite": limite}, usuario)

    s1 = salida(40, decano, "Propuesta de auxiliares de cátedra 2/2026", "Auxiliatura")
    Documento.cambiar_estado(s1, "EN_TRAMITE", "Pasó a consejo facultativo", dir_)
    salida(30, cpd, "Remisión de actas de graduación", "Graduación", requiere=False)
    salida(20, adm, "Solicitud de certificación presupuestaria", "Administrativo", limite=dias(5))
    salida(6, vice, "Solicitud de ambientes para defensas", "Académico", limite=(HOY + timedelta(days=7)).isoformat())

    e1 = entrada(25, vice, "VD-0215/2026", "Solicitud de informe de avance académico", "Académico", limite=dias(3))
    e2 = entrada(15, doc, "S/N", "Entrega de informe final de materia", "Docente", requiere=False)
    Documento.cambiar_estado(e2, "ARCHIVADO", "Archivado en carpeta de docentes", sec)
    e3 = entrada(12, decano, "DEC-0480/2026", "Invitación a reunión de directores", "Invitación")
    Documento.responder(e3, {"fecha": dias(10), "asunto": "Confirmación de asistencia a reunión",
                             "categoria": "Invitación"}, dir_)
    entrada(2, cpd, "CPD-0102/2026", "Pedido de lista de egresados", "Graduación",
            limite=(HOY + timedelta(days=10)).isoformat())
    Documento.cambiar_estado(e1, "EN_TRAMITE", "Se está preparando el informe", dir_)
    Documento.adjuntar_archivo(e1, pdf_ejemplo("documentos/entrada/ejemplo_VD-0215.pdf", "Oficio VD-0215/2026"))
    Documento.adjuntar_archivo(e3, pdf_ejemplo("documentos/entrada/ejemplo_DEC-0480.pdf", "Oficio DEC-0480/2026"))

    for i, (carnet, nom, ape, mod, nota) in enumerate([
        ("8123456 SC", "María", "Gutiérrez Flores", "Graduación directa por excelencia", 92),
        ("7654321 SC", "José", "Mamani Choque", "Graduación directa por buen desempeño", 84),
        ("9012345 SC", "Lucía", "Rojas Vaca", "Proyecto de grado", 88),
    ], start=1):
        ruta = pdf_ejemplo(f"actas/ejemplo_acta_{i}.pdf", f"Acta DEMO-{i:03d}")
        Acta.registrar({"nro_acta": f"DEMO-{i:03d}/{HOY.year}", "fecha": dias(60 - i * 10), "carnet": carnet,
                        "nombres": nom, "apellidos": ape, "modalidad": mod, "nota": nota}, ruta)

    d1 = Docente.registrar("Ing. Docente Uno (ejemplo)", "1000001")
    d2 = Docente.registrar("Lic. Docente Dos (ejemplo)", "1000002")
    m1 = Materia.registrar("INF-110", "Introducción a la Informática")
    m2 = Materia.registrar("INF-120", "Programación I")
    m3 = Materia.registrar("INF-312", "Base de Datos I")
    a1 = Asignacion.registrar(d1, m1, HOY.year, 2)
    Asignacion.registrar(d2, m2, HOY.year, 2)
    Asignacion.registrar(d1, m3, HOY.year, 2)
    Asignacion.registrar_informe(a1, dias(1), pdf_ejemplo("informes/ejemplo_INF-110.pdf", "Informe final INF-110"))

    c1 = Convocatoria.registrar(m2, HOY.year, 2, dias(50))
    for carnet, nom, ape, mer, exa in [("9012345 SC", "Lucía", "Rojas Vaca", 38, 55),
                                       ("9345678 SC", "Pedro", "Suárez Ortiz", 35, 51)]:
        p = Convocatoria.agregar_postulante(c1, carnet, nom, ape)
        Convocatoria.calificar(p, mer, exa)
    Convocatoria.cerrar(c1)
    c2 = Convocatoria.registrar(m3, HOY.year, 2, dias(5))
    Convocatoria.agregar_postulante(c2, "9456789 SC", "Ana", "Pinto Rocha")


if __name__ == "__main__":
    with crear_app().app_context():
        if Usuario.hay_usuarios():
            print("La base ya tiene usuarios: no se cargan datos de ejemplo para no mezclar.")
            raise SystemExit(0)
        cargar()
    print("Datos de ejemplo cargados. Ingrese con  directora / demo123")
