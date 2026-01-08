"""
Script para ejecutar archivos SQL en PostgreSQL (Docker)
Proyecto: PMG - Automatización de Planes PTD
Fecha: 2025-10-14
"""

import psycopg2
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de conexión PostgreSQL
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'ptd_db'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
}

def conectar_db():
    """Establece conexión con PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print(f"✅ Conectado a PostgreSQL: {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
        return conn
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print(f"\nVerifica que:")
        print(f"  1. El contenedor Docker esté corriendo")
        print(f"  2. Las variables de entorno en .env sean correctas")
        print(f"  3. El puerto {DB_CONFIG['port']} esté expuesto")
        sys.exit(1)

def ejecutar_script_sql(archivo_sql, mostrar_notices=True):
    """
    Ejecuta un archivo SQL en PostgreSQL
    
    Args:
        archivo_sql: Ruta al archivo .sql
        mostrar_notices: Si debe mostrar mensajes NOTICE de PostgreSQL
    """
    if not os.path.exists(archivo_sql):
        print(f"❌ Error: El archivo '{archivo_sql}' no existe")
        return False
    
    print(f"\n{'='*80}")
    print(f"Ejecutando: {archivo_sql}")
    print(f"{'='*80}\n")
    
    try:
        # Conectar a la base de datos
        conn = conectar_db()
        
        # Configurar autocommit para scripts DDL
        conn.autocommit = True
        
        # Leer el archivo SQL
        with open(archivo_sql, 'r', encoding='utf-8') as f:
            script_sql = f.read()
        
        # Crear cursor
        cursor = conn.cursor()
        
        # Ejecutar el script
        try:
            cursor.execute(script_sql)
            
            # Mostrar NOTICE si está habilitado
            if mostrar_notices and conn.notices:
                for notice in conn.notices:
                    # Los notices en psycopg2 son strings directamente
                    print(f"  NOTICE: {notice.strip()}")
            
            print(f"\n✅ Script '{archivo_sql}' ejecutado exitosamente\n")
            resultado = True
        except psycopg2.Error as e:
            print(f"\n❌ Error ejecutando SQL:")
            print(f"  Código: {e.pgcode}")
            print(f"  Mensaje: {e.pgerror}\n")
            resultado = False
        
        # Cerrar cursor y conexión
        cursor.close()
        conn.close()
        
        return resultado
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

def verificar_tabla_existe(nombre_tabla='ptd_planes'):
    """Verifica si una tabla existe"""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, (nombre_tabla,))
        
        existe = cursor.fetchone()[0]
        
        if existe:
            cursor.execute(f"SELECT COUNT(*) FROM {nombre_tabla};")
            num_registros = cursor.fetchone()[0]
            print(f"✅ La tabla '{nombre_tabla}' existe con {num_registros} registros")
        else:
            print(f"❌ La tabla '{nombre_tabla}' NO existe")
        
        cursor.close()
        conn.close()
        
        return existe
        
    except Exception as e:
        print(f"❌ Error verificando tabla: {e}")
        return False

def menu_principal():
    """Menú interactivo para ejecutar scripts"""
    print("\n" + "="*80)
    print("GESTOR DE SCRIPTS SQL - PostgreSQL")
    print("Proyecto: PMG - Planes de Transformación Digital")
    print("="*80)
    
    while True:
        print("\nOpciones:")
        print("  1. Crear tabla ptd_planes")
        print("  2. Crear tabla ptd_prompts")
        print("  3. Crear ambas tablas (ptd_planes + ptd_prompts)")
        print("  4. Eliminar tabla ptd_planes")
        print("  5. Verificar si tablas existen")
        print("  6. Ejecutar script SQL personalizado")
        print("  7. Ver configuración de conexión")
        print("  0. Salir")
        
        opcion = input("\nSelecciona una opción (0-7): ").strip()
        
        if opcion == "1":
            print("\n⚠️  Esto creará la tabla ptd_planes (eliminará si existe)")
            confirmacion = input("¿Continuar? (s/n): ").strip().lower()
            if confirmacion == 's':
                ejecutar_script_sql('crear_tabla_ptd.sql')
        
        elif opcion == "2":
            print("\n⚠️  Esto creará la tabla ptd_prompts (eliminará si existe)")
            confirmacion = input("¿Continuar? (s/n): ").strip().lower()
            if confirmacion == 's':
                ejecutar_script_sql('crear_tabla_prompts.sql')
        
        elif opcion == "3":
            print("\n⚠️  Esto creará ambas tablas (eliminará si existen)")
            confirmacion = input("¿Continuar? (s/n): ").strip().lower()
            if confirmacion == 's':
                print("\n📋 Creando tabla ptd_planes...")
                if ejecutar_script_sql('crear_tabla_ptd.sql'):
                    print("\n📋 Creando tabla ptd_prompts...")
                    ejecutar_script_sql('crear_tabla_prompts.sql')
                else:
                    print("\n❌ Error al crear ptd_planes, abortando...")
        
        elif opcion == "4":
            print("\n⚠️  ADVERTENCIA: Esto eliminará PERMANENTEMENTE la tabla y TODOS sus datos")
            confirmacion = input("¿Estás seguro? (escribe 'ELIMINAR' para confirmar): ").strip()
            if confirmacion == 'ELIMINAR':
                ejecutar_script_sql('eliminar_tabla_ptd.sql')
            else:
                print("❌ Cancelado")
        
        elif opcion == "5":
            print("\n📊 Verificando tablas del sistema...")
            print("\n1️⃣  Tabla de planes:")
            verificar_tabla_existe('ptd_planes')
            print("\n2️⃣  Tabla de prompts:")
            verificar_tabla_existe('ptd_prompts')
        
        elif opcion == "6":
            archivo = input("Ruta del archivo SQL: ").strip()
            ejecutar_script_sql(archivo)
        
        elif opcion == "7":
            print("\nConfiguración de conexión:")
            print(f"  Host: {DB_CONFIG['host']}")
            print(f"  Puerto: {DB_CONFIG['port']}")
            print(f"  Base de datos: {DB_CONFIG['database']}")
            print(f"  Usuario: {DB_CONFIG['user']}")
            print(f"  Password: {'*' * len(DB_CONFIG['password'])}")
        
        elif opcion == "0":
            print("\n👋 Saliendo...")
            break
        
        else:
            print("❌ Opción inválida")

def main():
    """Función principal"""
    if len(sys.argv) > 1:
        # Modo línea de comandos
        archivo = sys.argv[1]
        ejecutar_script_sql(archivo)
    else:
        # Modo interactivo
        menu_principal()

if __name__ == "__main__":
    main()