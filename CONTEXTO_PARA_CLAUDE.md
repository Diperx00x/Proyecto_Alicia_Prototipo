# Contexto del proyecto (pegar esto al empezar un chat con Claude)

Soy estudiante de Ingeniería en Sistemas de la Facultad Integral de Ichilo (F.IN.I. – U.A.G.R.M.), Bolivia. Este es mi proyecto final de Sistemas de Información: un sistema para la Dirección de Carrera de Ingeniería en Sistemas. Método cascada, documentado con UML. La defensa es individual: la docente pregunta sobre la documentación (casos de uso, clases, secuencia, objetivo, justificación, metodología, qué hace el sistema). Necesito entender todo y poder explicarlo con mis palabras.

## Qué hace el sistema
Registra y da seguimiento a: documentos recibidos y enviados (con historial de estados y enlace a su respuesta), actas de graduación, informes finales de docentes y convocatorias a auxiliares de cátedra. Tiene login para directora y secretaria.

## Tecnología
- Python 3 + Flask (lógica y pantallas), MySQL 8 (base de datos), HTML y CSS (diseño).
- Las pantallas se abren en una ventana propia con pywebview (no en pestañas del navegador).
- PyMySQL conecta Python con MySQL. pytest: 23 pruebas automáticas.

## Estructura del código (carpeta regdoc)
- app.py arranca el sistema. config.py: datos de conexión y listas fijas. db.py: conexión a MySQL.
- modelos/: clases del diagrama de clases (Usuario, Contacto, Documento, Movimiento, Estudiante, Acta, Docente, Materia, Asignacion, Convocatoria; Postulacion es tabla).
- rutas/: qué hace cada pantalla. templates/ y static/: HTML y CSS.
- sql/esquema.sql: 12 tablas. pruebas/: 23 pruebas.

## Decisiones de diseño (para defender)
- Recibidos y enviados son una sola clase Documento con el atributo sentido (ENTRADA/SALIDA).
- Movimiento guarda cada cambio de estado (historial), con fecha y usuario.
- Estados: registrado → en trámite → respondido → archivado (no se vuelve atrás).
- CITE de enviados: prefijo + NN/AAAA, correlativo que vuelve a 01 cada gestión. Configurable el último número usado.
- Estudiante se comparte entre actas y postulaciones. Una acta por estudiante; N° de acta único (lo da el CPD).
- Directora hereda los casos de uso de la secretaria y además: gestionar usuarios, configurar numeración, cerrar convocatoria.
- Diagramas de secuencia hechos: "responder un documento" y "registrar un acta" (con fragmento alt).

## Por confirmar
Mi nombre, docente y fechas; si la secretaria usa la misma PC; listas de categorías y modalidades; cómo se califica la auxiliatura (hoy méritos + examen).

## Cómo quiero que me ayudes
En español, simple, sin jerga (o explicando cada término). Directo y honesto. Que documento, diagramas, base de datos y código digan siempre lo mismo. No inventes datos de la dirección: si falta algo, márcalo "por confirmar".
