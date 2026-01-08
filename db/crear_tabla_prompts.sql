-- Script de creación de tabla para almacenar versiones del SuperPrompt del Agente Maestro
-- Proyecto: PMG - Automatización de Planes PTD
-- Fecha: 2025-11-23
-- Base de datos: PostgreSQL

-- Esta tabla vive en el mismo esquema/base de datos que `ptd_planes`.
-- Su objetivo es versionar el prompt del Agente Maestro (y variantes futuras),
-- conservando el historial completo.

-- Eliminar tabla si existe (comentar si no se desea eliminar)
DROP TABLE IF EXISTS ptd_prompts CASCADE;

-- Crear tabla ptd_prompts
CREATE TABLE ptd_prompts (
    -- Llave primaria con auto-incremento
    id SERIAL PRIMARY KEY,

    -- Prompt completo (puede ser muy largo)
    prompt TEXT NOT NULL,

    -- Metadatos opcionales
    version_label VARCHAR(255),          -- etiqueta humana (ej: 'v1.0', 'A/B test B')
    fuente VARCHAR(255),                 -- origen (ej: 'SuperPrompt_AgenteMaestro_PTD.md')
    notas TEXT,                          -- comentarios breves sobre cambios o propósito

    -- Auditoría
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comentarios en las columnas
COMMENT ON TABLE ptd_prompts IS 'Versionado de prompts del Agente Maestro para planes PTD';
COMMENT ON COLUMN ptd_prompts.id IS 'ID único auto-incremental del registro de prompt';
COMMENT ON COLUMN ptd_prompts.prompt IS 'Contenido completo del prompt (texto largo)';
COMMENT ON COLUMN ptd_prompts.version_label IS 'Etiqueta de versión legible por humanos (opcional)';
COMMENT ON COLUMN ptd_prompts.fuente IS 'Archivo o contexto de origen del prompt';
COMMENT ON COLUMN ptd_prompts.notas IS 'Notas sobre cambios o propósito de la versión';
COMMENT ON COLUMN ptd_prompts.fecha_creacion IS 'Fecha de creación del registro';
COMMENT ON COLUMN ptd_prompts.fecha_actualizacion IS 'Fecha de última actualización';

-- Índices útiles
CREATE INDEX idx_ptd_prompts_version_label ON ptd_prompts(version_label);
CREATE INDEX idx_ptd_prompts_fecha_creacion ON ptd_prompts(fecha_creacion);

-- Trigger para mantener fecha_actualizacion al día
CREATE OR REPLACE FUNCTION actualizar_fecha_modificacion_ptd_prompts()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_actualizar_fecha_ptd_prompts
    BEFORE UPDATE ON ptd_prompts
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_fecha_modificacion_ptd_prompts();

-- Mensaje de confirmación
DO $$ 
BEGIN 
    RAISE NOTICE '✅ Tabla ptd_prompts creada exitosamente';
END $$;
