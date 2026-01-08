-- Script de creación de tabla para Planes de Transformación Digital (PTD)
-- Proyecto: PMG - Automatización de Planes PTD
-- Fecha: 2025-10-14
-- Base de datos: PostgreSQL

-- Eliminar tipos ENUM si existen (para permitir recreación)
DROP TYPE IF EXISTS tipo_nivel_madurez CASCADE;
DROP TYPE IF EXISTS tipo_autor CASCADE;
DROP TYPE IF EXISTS tipo_actividad_hito CASCADE;

-- Eliminar tabla si existe (comentar si no se desea eliminar)
DROP TABLE IF EXISTS ptd_planes CASCADE;

-- Crear tipos ENUM para PostgreSQL
CREATE TYPE tipo_nivel_madurez AS ENUM ('Insuficiente', 'Basico', 'Medio');
CREATE TYPE tipo_autor AS ENUM ('Comite', 'Agente Maestro');
CREATE TYPE tipo_actividad_hito AS ENUM ('Actividad', 'Hito');

-- Crear tabla ptd_planes
CREATE TABLE ptd_planes (
    -- Llave primaria con auto-incremento (SERIAL en PostgreSQL)
    id SERIAL PRIMARY KEY,
    
    -- Campos obligatorios
    Dimension VARCHAR(255) NOT NULL,
    Subdimension VARCHAR(255) NOT NULL,
    Instrumento VARCHAR(255) NOT NULL,
    Indicador VARCHAR(500) NOT NULL,
    Brecha TEXT NOT NULL,
    
    -- Campos opcionales (específicos para Gobernanza de Datos)
    Nivel_de_madurez tipo_nivel_madurez NULL,
    N_Pregunta INT NULL,
    Pregunta TEXT NULL,
    
    -- Campos obligatorios de iniciativa
    Iniciativa VARCHAR(500) NOT NULL,
    Objetivo_Iniciativa TEXT NOT NULL,
    
    -- Autor del plan (obligatorio)
    Autor tipo_autor NOT NULL,
    
    -- Indicadores obligatorios
    Indicador_Proceso VARCHAR(500) NOT NULL,
    Indicador_Resultado VARCHAR(500) NOT NULL,
    
    -- Detalle de actividades e hitos (obligatorios)
    N_Actividad_Hito INT NOT NULL,
    Tipo tipo_actividad_hito NOT NULL,
    Descripcion TEXT NOT NULL,
    
    -- Metadata de auditoría
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comentarios en las columnas (PostgreSQL usa COMMENT ON)
COMMENT ON TABLE ptd_planes IS 'Tabla de Planes de Transformación Digital generados por el sistema PMG';
COMMENT ON COLUMN ptd_planes.id IS 'ID único auto-incremental';
COMMENT ON COLUMN ptd_planes.Dimension IS 'Dimensión PMG (ej: Procedimiento Administrativo, Gobernanza de Datos)';
COMMENT ON COLUMN ptd_planes.Subdimension IS 'Subdimensión específica de la dimensión';
COMMENT ON COLUMN ptd_planes.Instrumento IS 'Instrumento de evaluación utilizado';
COMMENT ON COLUMN ptd_planes.Indicador IS 'Indicador de cumplimiento';
COMMENT ON COLUMN ptd_planes.Brecha IS 'Descripción de la brecha identificada';
COMMENT ON COLUMN ptd_planes.Nivel_de_madurez IS 'Nivel de madurez MGDE (solo acepta: Insuficiente, Basico o Medio)';
COMMENT ON COLUMN ptd_planes.N_Pregunta IS 'Número de pregunta';
COMMENT ON COLUMN ptd_planes.Pregunta IS 'Texto de la pregunta';
COMMENT ON COLUMN ptd_planes.Iniciativa IS 'Nombre de la iniciativa';
COMMENT ON COLUMN ptd_planes.Objetivo_Iniciativa IS 'Objetivo a alcanzar con la iniciativa';
COMMENT ON COLUMN ptd_planes.Autor IS 'Autor que generó el plan (Comite o Agente Maestro)';
COMMENT ON COLUMN ptd_planes.Indicador_Proceso IS 'Indicador de proceso para medir avance';
COMMENT ON COLUMN ptd_planes.Indicador_Resultado IS 'Indicador de resultado para medir impacto';
COMMENT ON COLUMN ptd_planes.N_Actividad_Hito IS 'Número secuencial de la actividad o hito';
COMMENT ON COLUMN ptd_planes.Tipo IS 'Tipo de entrada: solo permite "Actividad" o "Hito" (tipo_actividad_hito ENUM)';
COMMENT ON COLUMN ptd_planes.Descripcion IS 'Descripción detallada de la actividad o hito';
COMMENT ON COLUMN ptd_planes.fecha_creacion IS 'Fecha de creación del registro';
COMMENT ON COLUMN ptd_planes.fecha_actualizacion IS 'Fecha de última actualización';

-- Crear índices para mejorar búsquedas
CREATE INDEX idx_dimension ON ptd_planes(Dimension);
CREATE INDEX idx_subdimension ON ptd_planes(Subdimension);
CREATE INDEX idx_nivel_madurez ON ptd_planes(Nivel_de_madurez);
CREATE INDEX idx_instrumento ON ptd_planes(Instrumento);
CREATE INDEX idx_autor ON ptd_planes(Autor);
CREATE INDEX idx_tipo ON ptd_planes(Tipo);

-- Crear trigger para actualizar fecha_actualizacion automáticamente
CREATE OR REPLACE FUNCTION actualizar_fecha_modificacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_actualizar_fecha
    BEFORE UPDATE ON ptd_planes
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_fecha_modificacion();

-- Comentarios sobre el uso de la tabla
/*
NOTAS DE USO:

1. DIMENSIONES SOPORTADAS:
   - Procedimiento administrativo de función específica
   - Gobernanza de datos (MGDE)
   - Calidad web y servicios digitales

2. NIVELES DE MADUREZ (solo para Gobernanza de Datos):
   - Insuficiente
   - Básico
   - Medio

3. ESTRUCTURA DE LA TABLA:
   Cada fila representa UNA actividad o UN hito individual.
   Para reconstruir un plan completo, agrupar por:
   - Dimension + Subdimension + Nivel_de_madurez + Autor
   
   Ejemplo de registros:
   | N_Actividad_Hito | Tipo       | Descripcion                          | Autor          |
   |------------------|------------|--------------------------------------|----------------|
   | 1                | Actividad  | Definir marco conceptual             | Agente Maestro |
   | 2                | Actividad  | Designar responsable del programa    | Agente Maestro |
   | 3                | Actividad  | Establecer canales de comunicación   | Agente Maestro |
   | 4                | Hito       | Diseño del programa completado       | Agente Maestro |

4. VALORES PERMITIDOS:
   - Autor: "Comite" o "Agente Maestro" (tipo_autor ENUM)
   - Tipo: "Actividad" o "Hito" (tipo_actividad_hito ENUM)
   - Nivel_de_madurez: "Insuficiente", "Basico" o "Medio" (tipo_nivel_madurez ENUM, solo para Gobernanza de Datos)
   - N_Actividad_Hito: Número secuencial (1, 2, 3, ...)

5. ESTRUCTURA DE PLANES:
   - Procedimiento Administrativo: 3 hitos máximo, 9-12 actividades
   - Gobernanza de Datos: 3 hitos máximo, 9-12 actividades
   - Calidad Web: Por definir

6. CONSULTAS ÚTILES:
   
   -- Ver todos los planes de una dimensión:
   SELECT * FROM ptd_planes WHERE Dimension = 'Gobernanza de datos';
   
   -- Ver planes por nivel de madurez:
   SELECT * FROM ptd_planes WHERE Nivel_de_madurez = 'Básico';
   
   -- Reconstruir un plan completo ordenado:
   SELECT N_Actividad_Hito, Tipo, Descripcion 
   FROM ptd_planes 
   WHERE Subdimension = 'Visión Estratégica' 
     AND Nivel_de_madurez = 'Básico'
     AND Autor = 'Agente Maestro'
   ORDER BY N_Actividad_Hito;
   
   -- Contar actividades y hitos por subdimensión:
   SELECT Subdimension, Tipo, COUNT(*) as total 
   FROM ptd_planes 
   GROUP BY Subdimension, Tipo;
   
   -- Comparar planes del Comité vs Agente Maestro:
   SELECT Autor, COUNT(*) as total_items
   FROM ptd_planes
   WHERE Subdimension = 'Visión Estratégica'
   GROUP BY Autor;
   
   -- Buscar por brecha específica:
   SELECT DISTINCT Subdimension, Brecha, Autor 
   FROM ptd_planes 
   WHERE Brecha LIKE '%datos maestros%';
*/

-- Mensaje de confirmación
DO $$ 
BEGIN 
    RAISE NOTICE '✅ Tabla ptd_planes creada exitosamente';
    RAISE NOTICE '✅ Tipos ENUM creados: tipo_nivel_madurez, tipo_autor, tipo_actividad_hito';
    RAISE NOTICE '✅ Índices creados: 6 índices';
    RAISE NOTICE '✅ Trigger creado: trigger_actualizar_fecha';
END $$;