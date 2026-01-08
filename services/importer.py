# services/importer.py
from __future__ import annotations
from typing import Dict, List, Tuple
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from extensions.db import db
import pandas as pd

class ImportErrorExcel(RuntimeError):
    pass

def read_excel_sheets(file_stream) -> Dict[str, "pd.DataFrame"]:
    """
    Lee todas las hojas de un .xlsx y retorna {sheet_name: DataFrame}.
    No transforma nombres de columnas (respetar el Excel).
    """
    try:
        xls = pd.ExcelFile(file_stream)
        data = {}
        for sheet in xls.sheet_names:
            df = xls.parse(sheet)
            data[sheet] = df
        return data
    except Exception as e:
        raise ImportErrorExcel(f"No se pudo leer el Excel: {e}")

def normalize_sheet_name(name: str) -> str:
    """Normaliza sutilmente espacios finales, etc., manteniendo el texto."""
    return str(name).strip()

def df_bulk_upsert(table, df: "pd.DataFrame") -> Tuple[int, int]:
    """
    Inserta/actualiza en bloque.
    - Si la columna 'id' está en df y tiene valores → UPDATE por id.
    - Filas sin 'id' o con id vacío → INSERT nuevas.
    Retorna (insertados, actualizados).
    """
    inserted = 0
    updated = 0

    # Asegura que solo pasamos columnas que existen en la tabla
    table_cols = set(table.c.keys())
    if "id" in df.columns:
        # pandas puede traer NaN -> convertir a None
        df["id"] = df["id"].where(df["id"].notna(), None)

    safe_cols = [c for c in df.columns if c in table_cols and c != "id"]

    inserts = []
    updates = []

    for _, row in df.iterrows():
        row_dict = row.to_dict()

        row_id = row_dict.get("id", None)
        payload = {k: row_dict.get(k, None) for k in safe_cols}

        if row_id is None or (isinstance(row_id, float) and pd.isna(row_id)):
            inserts.append(payload)
        else:
            updates.append((row_id, payload))

    # Transacción
    try:
        # INSERTS
        if inserts:
            db.session.execute(table.insert(), inserts)
            inserted = len(inserts)

        # UPDATES (uno a uno para claridad; si quieres optimizar, arma un CASE WHEN)
        for row_id, payload in updates:
            db.session.execute(table.update().where(table.c.id == int(row_id)).values(**payload))
        updated = len(updates)

        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise

    return inserted, updated
