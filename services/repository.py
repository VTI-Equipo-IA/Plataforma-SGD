# services/repository.py
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
from extensions.db import db

SEARCHABLE_CANDIDATES = [
    # Campos de texto más usados en búsquedas libres
    "Brecha", "Indicador", "Pregunta", "Iniciativa",
    "Descripcion", "Subdimension", "Instrumento",
    "Objetivo_Iniciativa", "Indicador_Proceso", "Indicador_Resultado",
    # Extras útiles que aparecen a menudo en la UI
    "Tipo", "Autor", "Nivel_de_madurez", "nivel_de_madurez",
    # Por si se desea encontrar por contexto
    "Dimension", "dimension"
]

def create_row(table, data: dict):
    try:
        ins = table.insert()
        if data:
            ins = ins.values(**data)
        # Si data está vacío, ins.values() produce INSERT DEFAULT VALUES (válido para PK serial)
        res = db.session.execute(ins)
        db.session.commit()
        # Algunos drivers retornan pk en res.inserted_primary_key
        return (res.inserted_primary_key[0] if res.inserted_primary_key else None)
    except SQLAlchemyError:
        db.session.rollback()
        raise

def list_rows(
    table,
    q=None,
    order=None,
    direction="asc",
    page=1,
    per_page=None,
    dimension_filter=None,
    subdimension: str | None = None,
    autor: str | None = None,
    instrumento: str | None = None,
    nivel_madurez: str | None = None,
):
    per_page = per_page or current_app.config.get("PAGE_SIZE", 25)
    stmt = select(table)

    # Filtrar por dimensión si se proporciona (OR ILIKE para variantes)
    if dimension_filter:
        dim_col_name = None
        if "Dimension" in table.c:
            dim_col_name = "Dimension"
        elif "dimension" in table.c:
            dim_col_name = "dimension"
        if dim_col_name:
            col = table.c[dim_col_name]
            if isinstance(dimension_filter, (list, tuple, set)):
                ors = [col.ilike(f"%{val}%") for val in dimension_filter if val]
                if ors:
                    stmt = stmt.where(db.or_(*ors))
            else:
                stmt = stmt.where(col.ilike(f"%{dimension_filter}%"))

    # Filtro por subdimensión exacto si se proporciona
    if subdimension and ("Subdimension" in table.c or "subdimension" in table.c):
        sub_col = table.c["Subdimension"] if "Subdimension" in table.c else table.c["subdimension"]
        stmt = stmt.where(db.cast(sub_col, db.String) == subdimension)

    # Filtro por autor exacto si se proporciona
    if autor and ("Autor" in table.c or "autor" in table.c):
        autor_col = table.c["Autor"] if "Autor" in table.c else table.c["autor"]
        stmt = stmt.where(db.cast(autor_col, db.String) == autor)
    
    # Filtro por instrumento exacto si se proporciona
    if instrumento and ("Instrumento" in table.c or "instrumento" in table.c):
        inst_col = table.c["Instrumento"] if "Instrumento" in table.c else table.c["instrumento"]
        stmt = stmt.where(db.cast(inst_col, db.String) == instrumento)
    
    # Filtro por nivel de madurez exacto si se proporciona
    if nivel_madurez and ("Nivel_de_madurez" in table.c or "nivel_de_madurez" in table.c):
        nm_col = table.c["Nivel_de_madurez"] if "Nivel_de_madurez" in table.c else table.c["nivel_de_madurez"]
        stmt = stmt.where(db.cast(nm_col, db.String) == nivel_madurez)

    # Búsqueda simple OR sobre columnas existentes de la tabla
    if q:
        ors = []
        for col_name in SEARCHABLE_CANDIDATES:
            if col_name in table.c:
                # Para columnas no-texto (ENUM, numéricas), castear a String antes de ILIKE
                col = table.c[col_name]
                ors.append(db.cast(col, db.String).ilike(f"%{q}%"))
        if ors:
            stmt = stmt.where(db.or_(*ors))

    # Orden
    if order and order in table.c:
        # Caso especial: vista por Subdimensión con filtro activo -> ordenar por N_Actividad_Hito
        if (order in ("Subdimension", "subdimension")) and subdimension:
            n_col = table.c.get("N_Actividad_Hito") or table.c.get("n_actividad_hito")
            if n_col is not None:
                stmt = stmt.order_by(n_col.asc(), table.c.id.asc())
            else:
                # Si no existe N_Actividad_Hito, al menos orden estable por id
                stmt = stmt.order_by(table.c.id.asc())
        else:
            col = table.c[order]
            if direction == "desc":
                col = col.desc()
            stmt = stmt.order_by(col)
    else:
        # fallback: por id
        if "id" in table.c:
            stmt = stmt.order_by(table.c.id.asc())

    # Paginación
    page = max(int(page or 1), 1)
    per_page = max(int(per_page), 1)
    offset = (page - 1) * per_page
    stmt = stmt.limit(per_page).offset(offset)

    rows = db.session.execute(stmt).mappings().all()

    # Total (para controles de paginación)
    total_stmt = select(db.func.count()).select_from(table)
    
    # Aplicar el mismo filtro de dimensión al conteo
    if dimension_filter:
        dim_col_name = None
        if "Dimension" in table.c:
            dim_col_name = "Dimension"
        elif "dimension" in table.c:
            dim_col_name = "dimension"
        if dim_col_name:
            col = table.c[dim_col_name]
            if isinstance(dimension_filter, (list, tuple, set)):
                ors = [col.ilike(f"%{val}%") for val in dimension_filter if val]
                if ors:
                    total_stmt = total_stmt.where(db.or_(*ors))
            else:
                total_stmt = total_stmt.where(col.ilike(f"%{dimension_filter}%"))

    if subdimension and ("Subdimension" in table.c or "subdimension" in table.c):
        sub_col = table.c["Subdimension"] if "Subdimension" in table.c else table.c["subdimension"]
        total_stmt = total_stmt.where(db.cast(sub_col, db.String) == subdimension)
    
    if autor and ("Autor" in table.c or "autor" in table.c):
        autor_col = table.c["Autor"] if "Autor" in table.c else table.c["autor"]
        total_stmt = total_stmt.where(db.cast(autor_col, db.String) == autor)
    
    if instrumento and ("Instrumento" in table.c or "instrumento" in table.c):
        inst_col = table.c["Instrumento"] if "Instrumento" in table.c else table.c["instrumento"]
        total_stmt = total_stmt.where(db.cast(inst_col, db.String) == instrumento)
    
    if nivel_madurez and ("Nivel_de_madurez" in table.c or "nivel_de_madurez" in table.c):
        nm_col = table.c["Nivel_de_madurez"] if "Nivel_de_madurez" in table.c else table.c["nivel_de_madurez"]
        total_stmt = total_stmt.where(db.cast(nm_col, db.String) == nivel_madurez)
    
    if q:
        ors = []
        for col_name in SEARCHABLE_CANDIDATES:
            if col_name in table.c:
                col = table.c[col_name]
                ors.append(db.cast(col, db.String).ilike(f"%{q}%"))
        if ors:
            total_stmt = total_stmt.where(db.or_(*ors))
    total = db.session.execute(total_stmt).scalar() or 0

    return rows, total, page, per_page

def get_distinct_instrumentos(
    table,
    dimension_filter: str | list[str] | None = None,
    limit: int | None = 500,
):
    """
    Devuelve lista de instrumentos distintos (strings) filtrados por dimensión.
    Soporta columnas 'Instrumento' o 'instrumento'.
    """
    col_name = None
    if "Instrumento" in table.c:
        col_name = "Instrumento"
    elif "instrumento" in table.c:
        col_name = "instrumento"
    if not col_name:
        return []

    col = table.c[col_name]
    stmt = select(db.func.distinct(col)).where(col.isnot(None))
    stmt = stmt.where(db.func.length(db.cast(col, db.String)) > 0)

    if dimension_filter:
        dim_col_name = None
        if "Dimension" in table.c:
            dim_col_name = "Dimension"
        elif "dimension" in table.c:
            dim_col_name = "dimension"
        if dim_col_name:
            dcol = table.c[dim_col_name]
            if isinstance(dimension_filter, (list, tuple, set)):
                ors = [dcol.ilike(f"%{val}%") for val in dimension_filter if val]
                if ors:
                    stmt = stmt.where(db.or_(*ors))
            else:
                stmt = stmt.where(dcol.ilike(f"%{dimension_filter}%"))

    stmt = stmt.order_by(col.asc())
    if limit and int(limit) > 0:
        stmt = stmt.limit(int(limit))

    vals = db.session.execute(stmt).scalars().all()
    out = []
    seen = set()
    for v in vals:
        s = (str(v) if v is not None else "").strip()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out

def get_distinct_niveles_madurez(
    table,
    dimension_filter: str | list[str] | None = None,
    limit: int | None = 500,
):
    """
    Devuelve lista de niveles de madurez distintos (strings) filtrados por dimensión.
    Soporta columnas 'Nivel_de_madurez' o 'nivel_de_madurez'.
    """
    col_name = None
    if "Nivel_de_madurez" in table.c:
        col_name = "Nivel_de_madurez"
    elif "nivel_de_madurez" in table.c:
        col_name = "nivel_de_madurez"
    if not col_name:
        return []

    col = table.c[col_name]
    stmt = select(db.func.distinct(col)).where(col.isnot(None))
    stmt = stmt.where(db.func.length(db.cast(col, db.String)) > 0)

    if dimension_filter:
        dim_col_name = None
        if "Dimension" in table.c:
            dim_col_name = "Dimension"
        elif "dimension" in table.c:
            dim_col_name = "dimension"
        if dim_col_name:
            dcol = table.c[dim_col_name]
            if isinstance(dimension_filter, (list, tuple, set)):
                ors = [dcol.ilike(f"%{val}%") for val in dimension_filter if val]
                if ors:
                    stmt = stmt.where(db.or_(*ors))
            else:
                stmt = stmt.where(dcol.ilike(f"%{dimension_filter}%"))

    stmt = stmt.order_by(col.asc())
    if limit and int(limit) > 0:
        stmt = stmt.limit(int(limit))

    vals = db.session.execute(stmt).scalars().all()
    out = []
    seen = set()
    for v in vals:
        s = (str(v) if v is not None else "").strip()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out

def get_distinct_subdimensions(
    table,
    dimension_filter: str | list[str] | None = None,
    limit: int | None = 500,
):
    """
    Devuelve lista de subdimensiones distintas (strings) filtradas por dimensión.
    Soporta columnas 'Subdimension' o 'subdimension'.
    """
    col_name = None
    if "Subdimension" in table.c:
        col_name = "Subdimension"
    elif "subdimension" in table.c:
        col_name = "subdimension"
    if not col_name:
        return []

    col = table.c[col_name]
    stmt = select(db.func.distinct(col)).where(col.isnot(None))
    stmt = stmt.where(db.func.length(db.cast(col, db.String)) > 0)

    if dimension_filter:
        dim_col_name = None
        if "Dimension" in table.c:
            dim_col_name = "Dimension"
        elif "dimension" in table.c:
            dim_col_name = "dimension"
        if dim_col_name:
            dcol = table.c[dim_col_name]
            if isinstance(dimension_filter, (list, tuple, set)):
                ors = [dcol.ilike(f"%{val}%") for val in dimension_filter if val]
                if ors:
                    stmt = stmt.where(db.or_(*ors))
            else:
                stmt = stmt.where(dcol.ilike(f"%{dimension_filter}%"))

    stmt = stmt.order_by(col.asc())
    if limit and int(limit) > 0:
        stmt = stmt.limit(int(limit))

    vals = db.session.execute(stmt).scalars().all()
    out = []
    seen = set()
    for v in vals:
        s = (str(v) if v is not None else "").strip()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out

def get_row_by_id(table, row_id: int):
    stmt = select(table).where(table.c.id == row_id)
    return db.session.execute(stmt).mappings().first()

def create_row(table, data: dict):
    try:
        ins = table.insert().values(**data)
        res = db.session.execute(ins)
        db.session.commit()
        return res.inserted_primary_key[0]
    except SQLAlchemyError:
        db.session.rollback()
        raise

def update_row(table, row_id: int, data: dict):
    try:
        upd = table.update().where(table.c.id == row_id).values(**data)
        db.session.execute(upd)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise

def delete_row(table, row_id: int) -> int:
    """Elimina por id y retorna el número de filas afectadas (0 si no existe)."""
    try:
        dele = table.delete().where(table.c.id == row_id)
        res = db.session.execute(dele)
        db.session.commit()
        # rowcount puede ser -1 con algunos drivers; normalizamos a 0 si es None
        return max(int(res.rowcount or 0), 0)
    except SQLAlchemyError:
        db.session.rollback()
        raise


def find_indicador_resultado(table, dimension_val: str | None, subdimension_val: str | None, instrumento_val: str | None, autor_val: str | None) -> str | None:
    """
    Busca un valor de Indicador_Resultado existente en la misma tabla que coincida con
    (Dimension/Subdimension/Instrumento) y Autor. Retorna el primero encontrado.
    """
    # Determinar nombres reales de columnas
    dim_col = table.c.get("Dimension") or table.c.get("dimension")
    sub_col = table.c.get("Subdimension") or table.c.get("subdimension")
    inst_col = table.c.get("Instrumento") or table.c.get("instrumento")
    autor_col = table.c.get("Autor") or table.c.get("autor")
    ind_res_col = table.c.get("Indicador_Resultado") or table.c.get("indicador_resultado")

    if ind_res_col is None or autor_col is None:
        return None

    stmt = select(ind_res_col).where(ind_res_col.isnot(None)).limit(1)
    if autor_val is not None:
        stmt = stmt.where(db.cast(autor_col, db.String) == autor_val)
    if dim_col is not None and dimension_val is not None:
        stmt = stmt.where(db.cast(dim_col, db.String) == dimension_val)
    if sub_col is not None and subdimension_val is not None:
        stmt = stmt.where(db.cast(sub_col, db.String) == subdimension_val)
    if inst_col is not None and instrumento_val is not None:
        stmt = stmt.where(db.cast(inst_col, db.String) == instrumento_val)

    res = db.session.execute(stmt).scalar()
    return res


def reorder_n_actividad_hito(
    table,
    dimension_val: str | None,
    subdimension_val: str | None,
    instrumento_val: str | None,
    insert_after_id: int | None,
    new_row_id: int | None,
    autor_val: str | None = None,
    base_n: int | None = None,
) -> None:
    """
    Renumera la columna N_Actividad_Hito (si existe) secuencialmente (1..n) para el grupo
    definido por (Dimension/Subdimension/Instrumento), insertando la nueva fila justo
    después de insert_after_id si ambos están presentes.
    """
    n_col = table.c.get("N_Actividad_Hito") or table.c.get("n_actividad_hito")
    if n_col is None:
        return

    dim_col = table.c.get("Dimension") or table.c.get("dimension")
    sub_col = table.c.get("Subdimension") or table.c.get("subdimension")
    inst_col = table.c.get("Instrumento") or table.c.get("instrumento")
    autor_col = table.c.get("Autor") or table.c.get("autor")

    # Traer ids y su N actual
    stmt = select(table.c.id, n_col.label("n"))
    if dim_col is not None and dimension_val is not None:
        stmt = stmt.where(db.cast(dim_col, db.String) == dimension_val)
    if sub_col is not None and subdimension_val is not None:
        stmt = stmt.where(db.cast(sub_col, db.String) == subdimension_val)
    if inst_col is not None and instrumento_val is not None:
        stmt = stmt.where(db.cast(inst_col, db.String) == instrumento_val)
    if autor_col is not None and autor_val is not None:
        stmt = stmt.where(db.cast(autor_col, db.String) == autor_val)

    # Orden estable por N y luego id
    stmt = stmt.order_by(n_col.asc(), table.c.id.asc())
    rows = db.session.execute(stmt).all()
    # Convert to lists
    ids = [r[0] for r in rows]
    ns = [int(r[1] or 0) for r in rows]

    if new_row_id is not None:
        # Si el nuevo id ya está en la lista por cualquier default, quítalo para reinsertar
        if new_row_id in ids:
            rem_idx = ids.index(new_row_id)
            ids.pop(rem_idx)
            ns.pop(rem_idx)

        insert_idx = None
        if insert_after_id is not None and insert_after_id in ids:
            insert_idx = ids.index(insert_after_id) + 1
        elif base_n is not None:
            # Inserta después del último con n <= base_n
            insert_idx = 0
            for i, n in enumerate(ns):
                if n <= base_n:
                    insert_idx = i + 1
        else:
            insert_idx = len(ids)

        ids.insert(insert_idx, new_row_id)
        # ns se recalculará por completo más abajo

    try:
        # Asignación secuencial 1..n
        for i, rid in enumerate(ids, start=1):
            upd = table.update().where(table.c.id == rid).values({n_col.key: i})
            db.session.execute(upd)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise
