DROP DATABASE IF EXISTS sansilvestre_db;
DROP USER IF EXISTS sansilvestre_user;
CREATE USER sansilvestre_user WITH PASSWORD 'secret';
CREATE DATABASE sansilvestre_db;
GRANT ALL PRIVILEGES ON DATABASE sansilvestre_db TO sansilvestre_user;

\c sansilvestre_db;

CREATE TABLE edicion (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    ano INT
);

CREATE TABLE carrera (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    distancia INT,
    edicion_id INT REFERENCES edicion
);

CREATE TYPE sexo_t AS ENUM ('masculino', 'femenino');
CREATE TABLE corredor (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    apellidos VARCHAR(255),
    sexo sexo_t 
);

CREATE TABLE resultado (
    id SERIAL PRIMARY KEY,
    categoria VARCHAR(100),
    dorsal INT,
    puesto INT,
    p_categoria INT,
    p_sexo INT,
    ritmo INTERVAL,
    ritmo_neto INTERVAL,
    tiempo INTERVAL,
    tiempo_neto INTERVAL,
    carrera_id INT REFERENCES carrera
);

CREATE TABLE corredor_resultado (
corredor_id INT REFERENCES corredor,
resultado_id INT REFERENCES resultado,
PRIMARY KEY(corredor_id, resultado_id)
);

GRANT USAGE ON SCHEMA public TO sansilvestre_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sansilvestre_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sansilvestre_user;
