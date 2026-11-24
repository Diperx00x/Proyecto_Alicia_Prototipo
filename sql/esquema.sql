-- =====================================================================
-- Sistema de Registro Documental – Versión B
-- Dirección de Carrera de Ingeniería en Sistemas – F.IN.I. – U.A.G.R.M.
-- Base de datos: MySQL 8 (también funciona en MariaDB 10.6 o superior)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS regdoc
  CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci;
USE regdoc;

-- Quién entra al sistema: la directora y la secretaria.
CREATE TABLE IF NOT EXISTS usuario (
  id_usuario   INT AUTO_INCREMENT PRIMARY KEY,
  nombre       VARCHAR(100) NOT NULL,
  usuario      VARCHAR(40)  NOT NULL UNIQUE,
  clave_hash   VARCHAR(255) NOT NULL,
  rol          ENUM('DIRECTORA','SECRETARIA') NOT NULL,
  activo       TINYINT(1) NOT NULL DEFAULT 1
);

-- Datos que la directora puede cambiar sin tocar el código
-- (prefijo del CITE, último número usado al empezar a usar el sistema).
CREATE TABLE IF NOT EXISTS parametro (
  clave  VARCHAR(60) PRIMARY KEY,
  valor  VARCHAR(255) NOT NULL
);

-- Catálogo de personas e instituciones con las que se intercambian documentos.
CREATE TABLE IF NOT EXISTS contacto (
  id_contacto  INT AUTO_INCREMENT PRIMARY KEY,
  nombre       VARCHAR(150) NOT NULL,
  cargo        VARCHAR(150),
  institucion  VARCHAR(150),
  UNIQUE KEY uq_contacto (nombre, cargo)
);

-- Un solo registro para todo lo que entra y todo lo que sale.
CREATE TABLE IF NOT EXISTS documento (
  id_documento        INT AUTO_INCREMENT PRIMARY KEY,
  sentido             ENUM('ENTRADA','SALIDA') NOT NULL,
  gestion             SMALLINT NOT NULL,
  numero              INT NOT NULL,                 -- correlativo interno por sentido y gestión
  cite                VARCHAR(120) NOT NULL,        -- salida: lo genera el sistema; entrada: el N° de oficio del remitente
  fecha               DATE NOT NULL,                -- salida: fecha de envío; entrada: fecha del sello de recibido
  id_contacto         INT NOT NULL,                 -- destinatario (salida) o remitente (entrada)
  asunto              VARCHAR(255) NOT NULL,
  categoria           VARCHAR(40)  NOT NULL,
  requiere_respuesta  TINYINT(1) NOT NULL DEFAULT 0,
  fecha_limite        DATE NULL,                    -- plazo para responder (opcional)
  estado              ENUM('REGISTRADO','EN_TRAMITE','RESPONDIDO','ARCHIVADO') NOT NULL DEFAULT 'REGISTRADO',
  archivo             VARCHAR(255) NULL,            -- ruta del escaneado (el archivo vive fuera de la base)
  id_responde_a       INT NULL,                     -- documento al que contesta
  id_usuario          INT NOT NULL,                 -- quién lo registró
  creado_en           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_numero (sentido, gestion, numero),
  CONSTRAINT fk_doc_contacto  FOREIGN KEY (id_contacto)   REFERENCES contacto(id_contacto),
  CONSTRAINT fk_doc_responde  FOREIGN KEY (id_responde_a) REFERENCES documento(id_documento),
  CONSTRAINT fk_doc_usuario   FOREIGN KEY (id_usuario)    REFERENCES usuario(id_usuario)
);

-- Historial: cada cambio de estado queda guardado (no se borra ni se edita).
CREATE TABLE IF NOT EXISTS movimiento (
  id_movimiento  INT AUTO_INCREMENT PRIMARY KEY,
  id_documento   INT NOT NULL,
  fecha_hora     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  estado         ENUM('REGISTRADO','EN_TRAMITE','RESPONDIDO','ARCHIVADO') NOT NULL,
  observacion    VARCHAR(255),
  id_usuario     INT NOT NULL,
  CONSTRAINT fk_mov_doc     FOREIGN KEY (id_documento) REFERENCES documento(id_documento) ON DELETE CASCADE,
  CONSTRAINT fk_mov_usuario FOREIGN KEY (id_usuario)   REFERENCES usuario(id_usuario)
);

-- Estudiantes: se usan en las actas de graduación y en las postulaciones a auxiliar.
CREATE TABLE IF NOT EXISTS estudiante (
  id_estudiante  INT AUTO_INCREMENT PRIMARY KEY,
  carnet         VARCHAR(20)  NOT NULL UNIQUE,
  nombres        VARCHAR(100) NOT NULL,
  apellidos      VARCHAR(100) NOT NULL
);

-- Actas de graduación: número asignado por el CPD, una por estudiante.
CREATE TABLE IF NOT EXISTS acta (
  id_acta        INT AUTO_INCREMENT PRIMARY KEY,
  nro_acta       VARCHAR(30) NOT NULL UNIQUE,
  id_estudiante  INT NOT NULL UNIQUE,
  fecha          DATE NOT NULL,
  modalidad      VARCHAR(60) NOT NULL,
  nota           TINYINT UNSIGNED NOT NULL,
  archivo        VARCHAR(255) NULL,
  CONSTRAINT ck_acta_nota CHECK (nota BETWEEN 0 AND 100),
  CONSTRAINT fk_acta_est  FOREIGN KEY (id_estudiante) REFERENCES estudiante(id_estudiante)
);

CREATE TABLE IF NOT EXISTS docente (
  id_docente  INT AUTO_INCREMENT PRIMARY KEY,
  nombre      VARCHAR(150) NOT NULL,
  ci          VARCHAR(20)  NOT NULL UNIQUE,
  correo      VARCHAR(120)
);

CREATE TABLE IF NOT EXISTS materia (
  id_materia  INT AUTO_INCREMENT PRIMARY KEY,
  sigla       VARCHAR(15)  NOT NULL UNIQUE,
  nombre      VARCHAR(120) NOT NULL
);

-- Qué docente dicta qué materia en qué periodo, y si entregó su informe final.
CREATE TABLE IF NOT EXISTS asignacion (
  id_asignacion   INT AUTO_INCREMENT PRIMARY KEY,
  id_docente      INT NOT NULL,
  id_materia      INT NOT NULL,
  gestion         SMALLINT NOT NULL,
  periodo         TINYINT  NOT NULL,          -- 1 o 2 (semestre)
  fecha_informe   DATE NULL,                  -- vacío = informe final no entregado
  archivo_informe VARCHAR(255) NULL,
  UNIQUE KEY uq_asig (id_materia, gestion, periodo),
  CONSTRAINT ck_asig_periodo CHECK (periodo IN (1,2)),
  CONSTRAINT fk_asig_doc FOREIGN KEY (id_docente) REFERENCES docente(id_docente),
  CONSTRAINT fk_asig_mat FOREIGN KEY (id_materia) REFERENCES materia(id_materia)
);

-- Convocatoria a auxiliares de cátedra (una por materia y periodo).
CREATE TABLE IF NOT EXISTS convocatoria (
  id_convocatoria  INT AUTO_INCREMENT PRIMARY KEY,
  id_materia       INT NOT NULL,
  gestion          SMALLINT NOT NULL,
  periodo          TINYINT  NOT NULL,
  fecha_publicacion DATE NOT NULL,
  estado           ENUM('ABIERTA','CERRADA') NOT NULL DEFAULT 'ABIERTA',
  UNIQUE KEY uq_conv (id_materia, gestion, periodo),
  CONSTRAINT ck_conv_periodo CHECK (periodo IN (1,2)),
  CONSTRAINT fk_conv_mat FOREIGN KEY (id_materia) REFERENCES materia(id_materia)
);

-- Estudiantes que se presentan a una convocatoria y su evaluación.
CREATE TABLE IF NOT EXISTS postulacion (
  id_postulacion   INT AUTO_INCREMENT PRIMARY KEY,
  id_convocatoria  INT NOT NULL,
  id_estudiante    INT NOT NULL,
  nota_meritos     DECIMAL(5,2) NULL,
  nota_examen      DECIMAL(5,2) NULL,
  UNIQUE KEY uq_post (id_convocatoria, id_estudiante),
  CONSTRAINT fk_post_conv FOREIGN KEY (id_convocatoria) REFERENCES convocatoria(id_convocatoria) ON DELETE CASCADE,
  CONSTRAINT fk_post_est  FOREIGN KEY (id_estudiante)   REFERENCES estudiante(id_estudiante)
);

INSERT IGNORE INTO parametro (clave, valor) VALUES
  ('prefijo_cite', 'DIR.CARR.ING.SISTEMAS F.IN.I. OF. No.');
