-- Script de eliminación de tabla para Planes de Transformación Digital (PTD)
-- Proyecto: PMG - Automatización de Planes PTD
-- Fecha: 2025-10-14
-- Base de datos: PostgreSQL
-- ADVERTENCIA: Este script eliminará permanentemente la tabla y TODOS sus datos

-- ============================================================================
-- VERIFICACIÓN DE SEGURIDAD
-- ============================================================================
-- Descomenta la siguiente línea SOLO si estás seguro de eliminar la tabla
-- SET session.confirmar_eliminacion = 'SI';

-- ============================================================================
-- VERIFICAR EXISTENCIA DE LA TABLA
-- ============================================================================
DO $$ 
DECLARE
    tabla_existe INTEGER;
    num_registros INTEGER;
BEGIN
    SELECT COUNT(*) INTO tabla_existe
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
      AND table_name = 'ptd_planes';
    
    IF tabla_existe > 0 THEN
        SELECT COUNT(*) INTO num_registros FROM ptd_planes;
        RAISE NOTICE '⚠️  La tabla ptd_planes existe y contiene % registros. Se procederá a eliminarla.', num_registros;
    ELSE
        RAISE NOTICE '❌ La tabla ptd_planes NO existe.';
    END IF;
END $$;

-- ============================================================================
-- RESPALDAR DATOS ANTES DE ELIMINAR (OPCIONAL)
-- ============================================================================
-- Si deseas hacer un respaldo antes de eliminar, descomenta las siguientes líneas:

/*
-- Crear tabla de respaldo con fecha
CREATE TABLE IF NOT EXISTS ptd_planes_backup_20251014 AS 
SELECT * FROM ptd_planes;

DO $$ 
DECLARE
    num_respaldo INTEGER;
BEGIN
    SELECT COUNT(*) INTO num_respaldo FROM ptd_planes_backup_20251014;
    RAISE NOTICE '✅ Respaldo creado: ptd_planes_backup_20251014 con % registros', num_respaldo;
END $$;
*/

-- ============================================================================
-- ELIMINAR TABLA Y TIPOS ENUM
-- ============================================================================
-- Eliminar tabla (CASCADE elimina dependencias como triggers)
DROP TABLE IF EXISTS ptd_planes CASCADE;

-- Eliminar tipos ENUM asociados
DROP TYPE IF EXISTS tipo_nivel_madurez CASCADE;
DROP TYPE IF EXISTS tipo_autor CASCADE;

DO $$ 
BEGIN 
    RAISE NOTICE '✅ Tabla ptd_planes eliminada exitosamente';
    RAISE NOTICE '✅ Tipos ENUM eliminados: tipo_nivel_madurez, tipo_autor';
END $$;

-- ============================================================================
-- VERIFICAR ELIMINACIÓN
-- ============================================================================
DO $$ 
DECLARE
    tabla_existe INTEGER;
BEGIN
    SELECT COUNT(*) INTO tabla_existe
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
      AND table_name = 'ptd_planes';
    
    IF tabla_existe = 0 THEN
        RAISE NOTICE '✅ Confirmado: La tabla ptd_planes ya no existe en la base de datos';
    ELSE
        RAISE NOTICE '⚠️  Advertencia: La tabla ptd_planes todavía existe';
    END IF;
END $$;

-- ============================================================================
-- NOTAS IMPORTANTES
-- ============================================================================
/*
ADVERTENCIAS:
1. Este script elimina PERMANENTEMENTE la tabla ptd_planes
2. TODOS los datos almacenados en la tabla se perderán
3. Esta operación NO se puede deshacer sin un respaldo previo
4. Los índices, claves y restricciones asociados también se eliminarán

RECOMENDACIONES:
1. Hacer un respaldo de la base de datos ANTES de ejecutar este script
2. Verificar que no hay procesos o aplicaciones usando esta tabla
3. Considerar usar TRUNCATE en lugar de DROP si solo quieres vaciar la tabla:
   
   TRUNCATE TABLE ptd_planes;  -- Vacía la tabla pero mantiene la estructura

ALTERNATIVAS A DROP TABLE:
- Si solo quieres eliminar los datos pero mantener la estructura:
  TRUNCATE TABLE ptd_planes;

- Si quieres eliminar registros con condiciones:
  DELETE FROM ptd_planes WHERE Autor = 'Comite';

- Si quieres renombrar en lugar de eliminar:
  RENAME TABLE ptd_planes TO ptd_planes_old;

RESTAURACIÓN:
- Si ejecutaste este script por error, la única forma de recuperar los datos
  es restaurando desde un respaldo previo
- Si creaste la tabla de respaldo (sección de respaldo), puedes restaurar con:
  
  CREATE TABLE ptd_planes AS SELECT * FROM ptd_planes_backup_20251014;
  
  -- Recrear tipos ENUM:
  CREATE TYPE tipo_nivel_madurez AS ENUM ('Insuficiente', 'Basico', 'Medio');
  CREATE TYPE tipo_autor AS ENUM ('Comite', 'Agente Maestro');
  
  -- Luego ejecutar crear_tabla_ptd.sql para recrear estructura completa
*/