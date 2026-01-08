# models/plan_dynamic.py
from sqlalchemy import MetaData, Table
from extensions.db import db

metadata = MetaData()

def reflect_table(table_name: str) -> Table:
    """
    Refleja una tabla existente en PostgreSQL (con columna id PK).
    No añade ni modifica columnas.
    """
    metadata.bind = db.engine
    return Table(table_name, metadata, autoload_with=db.engine)
