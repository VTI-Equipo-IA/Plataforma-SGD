# -*- coding: utf-8 -*-
"""
Servicio para gestión de prompts en base de datos
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class PromptService:
    """Servicio para operaciones CRUD de prompts"""
    
    def __init__(self):
        self.table_name = os.getenv("PTD_PROMPTS_TABLE", "ptd_prompts")
    
    def _get_connection(self):
        """Obtiene conexión a la base de datos"""
        cfg = dict(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            dbname=os.getenv("POSTGRES_DB", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        )
        return psycopg2.connect(**cfg)
    
    def get_latest_prompt(self):
        """Obtiene el prompt más reciente (versión activa)"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"""
                    SELECT id, prompt, version_label, fuente, notas, 
                           fecha_creacion, fecha_actualizacion
                    FROM {self.table_name}
                    ORDER BY id DESC
                    LIMIT 1
                """)
                result = cur.fetchone()
                return dict(result) if result else None
        finally:
            conn.close()
    
    def get_all_prompts(self):
        """Obtiene todas las versiones de prompts, ordenadas por más reciente"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"""
                    SELECT id, version_label, fuente, notas, 
                           fecha_creacion, fecha_actualizacion,
                           LENGTH(prompt) as prompt_length
                    FROM {self.table_name}
                    ORDER BY id DESC
                """)
                results = cur.fetchall()
                return [dict(row) for row in results]
        finally:
            conn.close()
    
    def get_prompt_by_id(self, prompt_id):
        """Obtiene un prompt específico por ID"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"""
                    SELECT id, prompt, version_label, fuente, notas, 
                           fecha_creacion, fecha_actualizacion
                    FROM {self.table_name}
                    WHERE id = %s
                """, (prompt_id,))
                result = cur.fetchone()
                return dict(result) if result else None
        finally:
            conn.close()
    
    def save_prompt(self, prompt_text, version_label=None, fuente=None, notas=None):
        """
        Guarda un nuevo prompt en la base de datos
        Retorna el ID del nuevo registro
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(f"""
                    INSERT INTO {self.table_name} 
                    (prompt, version_label, fuente, notas)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (
                    prompt_text,
                    version_label or f'v{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                    fuente or 'Editor Web',
                    notas
                ))
                new_id = cur.fetchone()[0]
                conn.commit()
                return new_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def delete_versions_after(self, prompt_id):
        """
        Elimina todas las versiones con ID mayor al especificado
        (para restaurar a una versión anterior)
        Retorna el número de registros eliminados
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(f"""
                    DELETE FROM {self.table_name}
                    WHERE id > %s
                """, (prompt_id,))
                deleted_count = cur.rowcount
                conn.commit()
                return deleted_count
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def delete_prompt(self, prompt_id):
        """
        Elimina un prompt específico por ID
        Retorna True si se eliminó, False si no existía
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(f"""
                    DELETE FROM {self.table_name}
                    WHERE id = %s
                """, (prompt_id,))
                deleted = cur.rowcount > 0
                conn.commit()
                return deleted
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def update_prompt(self, prompt_id, prompt_text=None, version_label=None, notas=None):
        """
        Actualiza un prompt existente
        Retorna True si se actualizó, False si no existía
        """
        conn = self._get_connection()
        try:
            updates = []
            params = []
            
            if prompt_text is not None:
                updates.append("prompt = %s")
                params.append(prompt_text)
            if version_label is not None:
                updates.append("version_label = %s")
                params.append(version_label)
            if notas is not None:
                updates.append("notas = %s")
                params.append(notas)
            
            if not updates:
                return False
            
            params.append(prompt_id)
            
            with conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE {self.table_name}
                    SET {', '.join(updates)}, fecha_actualizacion = NOW()
                    WHERE id = %s
                """, params)
                updated = cur.rowcount > 0
                conn.commit()
                return updated
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
