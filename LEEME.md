# Sistema de Registro Documental – Versión B

Aplicación web local para la Dirección de Carrera de Ingeniería en Sistemas (F.IN.I. – U.A.G.R.M.).
Python + Flask + MySQL + HTML/CSS, en una ventana propia (pywebview).

## Instalar (una sola vez)

1. Instalar Python 3.11 o superior (marcar "Add Python to PATH").
2. Instalar MySQL 8 Community Server y anotar la contraseña de `root`.
3. En esta carpeta, abrir una consola y ejecutar:

```
pip install -r requirements.txt
python preparar_base.py
```

4. Solo para la demo/defensa: `python datos_demo.py` (usuario `directora`, clave `demo123`).

## Usar

Doble clic en `iniciar.bat`. El sistema se abre en **su propia ventana** (no en una pestaña del
navegador). Al cerrar la ventana, el sistema se apaga. La primera vez pide crear la cuenta de la directora.

La ventana usa el motor de Edge (WebView2), que ya viene en Windows 10 y 11.
Si la ventana no aparece, abrir una consola en esta carpeta y ejecutar `python app.py` para ver el error.

## Pruebas

```
set REGDOC_ROOT_PASS=la_clave_de_root
python -m pytest pruebas -v
```

Crean y borran una base aparte (`regdoc_prueba`); no tocan los datos reales. 23 pruebas.

## Estructura

- `modelos/` — clases del diagrama de clases (reglas + acceso a MySQL)
- `rutas/` — pantallas (qué hace cada dirección web)
- `templates/`, `static/` — HTML y CSS
- `sql/esquema.sql` — tablas
- `archivos/` — escaneados (no se suben a git)

## Configuración

Por variables de entorno (opcional): `REGDOC_DB_HOST`, `REGDOC_DB_PORT`, `REGDOC_DB_USER`,
`REGDOC_DB_PASS`, `REGDOC_DB_NAME`, `REGDOC_CLAVE_SECRETA`. Las listas de categorías y modalidades
están en `config.py`.

Antes de usarlo con datos reales, cambiar `CLAVE_SECRETA` en `config.py` y la contraseña del
usuario `regdoc` de MySQL (en `config.py` y en MySQL).
