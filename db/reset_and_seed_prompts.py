# -*- coding: utf-8 -*-
"""
reset_and_seed_prompts.py
-------------------------
Elimina la tabla ptd_prompts (si existe), la crea de nuevo usando
`crear_tabla_prompts.sql` y luego inserta como primer registro
el contenido del archivo `SuperPrompt_AgenteMaestro_PTD.md`.

Se conecta a la misma base de datos que usa el resto de la app,
leyendo las variables de entorno:
- POSTGRES_HOST / PGHOST
- POSTGRES_PORT / PGPORT
- POSTGRES_DB   / PGDATABASE
- POSTGRES_USER / PGUSER
- POSTGRES_PASSWORD / PGPASSWORD

Uso (desde la raíz del proyecto):

    python db/reset_and_seed_prompts.py \
        --prompt-file "agente maestro/SuperPrompt_AgenteMaestro_PTD.md" \
        --version "v1.0" \
        --fuente "SuperPrompt_AgenteMaestro_PTD.md"

Si no se pasan parámetros, usa los valores por defecto anteriores.
"""

import os
import sys
import logging
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Paths base
BASE_DIR = Path(__file__).resolve().parent.parent  # raíz del repo (../)
DB_DIR = BASE_DIR / "db"

SQL_FILE = DB_DIR / "crear_tabla_prompts.sql"
DEFAULT_PROMPT_FILE = BASE_DIR / "agente maestro" / "SuperPrompt_AgenteMaestro_PTD.md"


def _pg_conn():
    cfg = dict(
        host=os.getenv("POSTGRES_HOST", os.getenv("PGHOST", "localhost")),
        port=int(os.getenv("POSTGRES_PORT", os.getenv("PGPORT", "5432"))),
        dbname=os.getenv("POSTGRES_DB", os.getenv("PGDATABASE", "ptd_db")),
        user=os.getenv("POSTGRES_USER", os.getenv("PGUSER", "postgres")),
        password=os.getenv("POSTGRES_PASSWORD", os.getenv("PGPASSWORD", "postgres")),
    )
    logging.info("Conectando a PostgreSQL %s:%s/%s ...", cfg["host"], cfg["port"], cfg["dbname"])
    return psycopg2.connect(**cfg)


def run_sql_file(conn, path: Path):
    """Ejecuta un archivo SQL completo (puede contener varios comandos)."""
    logging.info("Ejecutando script SQL: %s", path)
    sql = path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    logging.info("Script SQL ejecutado correctamente")


def read_prompt_file(path: Path) -> str:
    """Lee el archivo de prompt y lo retorna como texto."""
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de prompt: {path}")
    logging.info("Leyendo prompt desde: %s", path)
    return path.read_text(encoding="utf-8")


def insert_initial_prompt(conn, prompt_text: str, version_label: str, fuente: str):
    """Inserta el primer registro en ptd_prompts."""
    sql = """
        INSERT INTO ptd_prompts (prompt, version_label, fuente, notas)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """
    notas = "Versión inicial importada desde archivo de SuperPrompt"
    with conn.cursor() as cur:
        cur.execute(sql, (prompt_text, version_label, fuente, notas))
        new_id = cur.fetchone()[0]
    logging.info("Insertado prompt inicial con id=%s", new_id)
    return new_id


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Recrear tabla ptd_prompts e insertar SuperPrompt inicial")
    parser.add_argument(
        "--prompt-file",
        default=str(DEFAULT_PROMPT_FILE),
        help="Ruta al archivo de SuperPrompt a insertar (por defecto: agente maestro/SuperPrompt_AgenteMaestro_PTD.md)",
    )
    parser.add_argument(
        "--version",
        default="v1.0",
        help="Etiqueta de versión para este prompt inicial (por defecto: v1.0)",
    )
    parser.add_argument(
        "--fuente",
        default="SuperPrompt_AgenteMaestro_PTD.md",
        help="Cadena que describe la fuente del prompt (por defecto: nombre del archivo)",
    )

    args = parser.parse_args(argv)

    prompt_path = Path(args.prompt_file)

    # 1) Leer prompt
    prompt_text = read_prompt_file(prompt_path)

    # 2) Conectar a BD y ejecutar script SQL + insertar registro
    conn = _pg_conn()
    try:
        # Ejecuta el script que DROP + CREATE la tabla
        run_sql_file(conn, SQL_FILE)

        # Insertar el primer registro
        insert_initial_prompt(conn, prompt_text, args.version, args.fuente)

        # Confirmar transacción
        conn.commit()
        logging.info("Operación completada con éxito")
    except Exception as e:
        conn.rollback()
        logging.exception("Fallo al recrear tabla ptd_prompts o insertar prompt inicial: %s", e)
        raise SystemExit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
