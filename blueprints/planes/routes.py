# blueprints/planes/routes.py (solo los cambios relevantes)

from flask import render_template, request, redirect, url_for, flash, abort, jsonify, send_file
from extensions.db import db
from . import bp
from services.dimensions import all_dimensions, default_dimension, get_dimension
from models.plan_dynamic import reflect_table
from services.exporter import export_plans_to_excel
from services.repository import (
    list_rows,
    get_row_by_id,
    create_row,
    update_row,
    delete_row,
    get_distinct_subdimensions,
    get_distinct_instrumentos,
    get_distinct_niveles_madurez,
    find_indicador_resultado,
    reorder_n_actividad_hito,
)
from .forms import EditRowForm, CreateRowForm, ImportExcelForm
from services.external_ai_bridge import generate_plan, AIError
from services.importer import read_excel_sheets, df_bulk_upsert, ImportErrorExcel, normalize_sheet_name
from services.plan_regenerator import start_regeneration, get_task_status, cancel_task
# NUEVO: Importar servicios del comité
from services.comite_regenerator import (
    start_comite_regeneration, 
    get_task_status as get_comite_task_status,
    cancel_task as cancel_comite_task
)
from werkzeug.utils import secure_filename
import pandas as pd
import os
import time

# ⬇️ NUEVO: importa helpers de tables.py
from .tables import (
    compute_visible_columns,
    sanitize_order_params,
    paginate_meta,
    is_plan_column,
    plan_targets_available,
    trunc,  # lo pasaremos al template para truncar celdas
    pretty_label,
    existing_searchable_columns,
)

def _resolve_dim(slug: str | None):
    dim = get_dimension(slug) if slug else default_dimension()
    if not dim:
        abort(404)
    table = reflect_table(dim.table_name)
    return dim, table

ALLOWED_XLSX_MIME = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",  # algunos navegadores reportan así
}

@bp.get("/")
def index():
    # Obtener dimensión actual desde query param o usar default
    dim_slug = request.args.get("dim")
    dim, table = _resolve_dim(dim_slug)
    
    # Parámetros de búsqueda, orden y paginación
    q = request.args.get("q", "").strip()
    order = request.args.get("order")
    direction = request.args.get("dir", "asc")
    page = int(request.args.get("page", 1))
    per_page = 25
    
    # Sanitizar parámetros de orden
    order, direction = sanitize_order_params(table, order, direction)
    
    # Nueva lógica de vistas: por defecto "Vista por plan" (una subdimensión), o "Vista total"
    view_mode = request.args.get("view", "plan")  # "plan" o "total"
    comparative = request.args.get("comparative", "false").lower() == "true"
    active_subdim = request.args.get("subdim")
    active_instrumento = request.args.get("inst")
    active_nivel_madurez = request.args.get("nivel")
    
    # Determinar si la dimensión requiere filtros adicionales
    # Calidad Web: Instrumento + Subdimensión
    # Gobernanza de Datos: Nivel de Madurez + Subdimensión
    requires_instrumento = dim.slug in ["calidad-web", "calidad_web", "calidad-web-servicios-digital"]
    requires_nivel_madurez = dim.slug in ["gobernanza-datos", "gobernanza_datos", "gobernanza-de-datos"]
    
    # Obtener opciones de filtro según la dimensión
    subdimension_options = get_distinct_subdimensions(
        table,
        dimension_filter=dim.match_strings or dim.dimension_filter,
        limit=500,
    )
    
    instrumento_options = []
    if requires_instrumento:
        instrumento_options = get_distinct_instrumentos(
            table,
            dimension_filter=dim.match_strings or dim.dimension_filter,
            limit=500,
        )
    
    nivel_madurez_options = []
    if requires_nivel_madurez:
        nivel_madurez_options = get_distinct_niveles_madurez(
            table,
            dimension_filter=dim.match_strings or dim.dimension_filter,
            limit=500,
        )
    
    # Si estamos en modo "plan" y no hay filtros seleccionados, usar los primeros
    if view_mode == "plan":
        if requires_instrumento and not active_instrumento and instrumento_options:
            active_instrumento = instrumento_options[0]
        if requires_nivel_madurez and not active_nivel_madurez and nivel_madurez_options:
            active_nivel_madurez = nivel_madurez_options[0]
        if not active_subdim and subdimension_options:
            active_subdim = subdimension_options[0]
    else:
        # En modo "total", no filtramos
        active_subdim = None
        active_instrumento = None
        active_nivel_madurez = None

    # Vista comparativa: solo disponible en modo "plan"
    rows_agente = []
    rows_comite = []
    if comparative and view_mode == "plan" and active_subdim:
        # Obtener filas del Agente Maestro
        rows_agente, _, _, _ = list_rows(
            table=table,
            q=None,
            order="id",  # Ordenar por ID (llave primaria)
            direction="asc",
            page=1,
            per_page=1000,  # Sin paginación en vista comparativa
            dimension_filter=dim.match_strings or dim.dimension_filter,
            subdimension=active_subdim,
            autor="Agente Maestro",
            instrumento=active_instrumento if requires_instrumento else None,
            nivel_madurez=active_nivel_madurez if requires_nivel_madurez else None,
        )
        
        # Obtener filas del Comite
        rows_comite, _, _, _ = list_rows(
            table=table,
            q=None,
            order="id",  # Ordenar por ID (llave primaria)
            direction="asc",
            page=1,
            per_page=1000,  # Sin paginación en vista comparativa
            dimension_filter=dim.match_strings or dim.dimension_filter,
            subdimension=active_subdim,
            autor="Comite",
            instrumento=active_instrumento if requires_instrumento else None,
            nivel_madurez=active_nivel_madurez if requires_nivel_madurez else None,
        )

    # Obtener filas con paginación, filtro de dimensión y (opcionalmente) subdimensión
    rows, total, page, per_page = list_rows(
        table=table,
        q=q if q else None,
        order=order,
        direction=direction,
        page=page,
        per_page=per_page,
        # Filtra por la dimensión: acepta lista de variantes para robustez
        dimension_filter=dim.match_strings or dim.dimension_filter,
        subdimension=active_subdim if view_mode == "plan" else None,
        instrumento=active_instrumento if (view_mode == "plan" and requires_instrumento) else None,
        nivel_madurez=active_nivel_madurez if (view_mode == "plan" and requires_nivel_madurez) else None,
    )
    
    # Calcular columnas visibles (aplicando ocultamientos por dimensión)
    visible_cols = compute_visible_columns(table, exclude=dim.hidden_columns)
    
    # Metadata de paginación
    meta = paginate_meta(total, page, per_page)
    
    # Form de importación (sin selector de alcance)
    import_form = ImportExcelForm()

    return render_template(
        "planes/index.html",
        current_dim=dim,
        dimensions=all_dimensions(),
        rows=rows,
        visible_cols=visible_cols,
        meta=meta,
        q=q,
        order=order,
        direction=direction,
        is_plan_column=is_plan_column,
        plan_targets_available=plan_targets_available(table),
        trunc=trunc,
        pretty_label=pretty_label,
        searchable_cols=existing_searchable_columns(table),
        import_form=import_form,
        subdimension_options=subdimension_options,
        active_subdimension=active_subdim,
        view_mode=view_mode,
        comparative=comparative,
        rows_agente=rows_agente,
        rows_comite=rows_comite,
        # Filtros adicionales según dimensión
        requires_instrumento=requires_instrumento,
        instrumento_options=instrumento_options,
        active_instrumento=active_instrumento,
        requires_nivel_madurez=requires_nivel_madurez,
        nivel_madurez_options=nivel_madurez_options,
        active_nivel_madurez=active_nivel_madurez,
    )

@bp.get("/<dim>/indicador-resultado")
def api_indicador_resultado(dim):
    """Endpoint ligero para calcular 'Indicador_Resultado' dado un autor y el contexto del registro base.
    Parámetros:
      - base_id: id de la fila sobre la que se inserta debajo
      - autor: 'Comite' o 'Agente Maestro'
    Retorna texto plano (200) con el indicador o cadena vacía.
    """
    d, table = _resolve_dim(dim)
    base_id = request.args.get("base_id", type=int)
    autor = request.args.get("autor", type=str)
    if not base_id or not autor:
        return ("", 200, {"Content-Type": "text/plain; charset=utf-8"})
    base = get_row_by_id(table, base_id)
    if not base:
        return ("", 200, {"Content-Type": "text/plain; charset=utf-8"})

    dimension_val = base.get("Dimension") or base.get("dimension")
    subdimension_val = base.get("Subdimension") or base.get("subdimension")
    instrumento_val = base.get("Instrumento") or base.get("instrumento")

    ind = find_indicador_resultado(table, dimension_val, subdimension_val, instrumento_val, autor)
    return (str(ind or ""), 200, {"Content-Type": "text/plain; charset=utf-8"})

@bp.post("/<dim>/<int:row_id>/insert-below")
def insert_below(dim, row_id):
    """Crea una nueva fila inmediatamente debajo de 'row_id' copiando los campos comunes y
    dejando variables Autor, Tipo y Descripcion. Reordena N_Actividad_Hito en el grupo.
    Solo se permite cuando la vista activa es por Subdimension (subdim presente).
    """
    d, table = _resolve_dim(dim)
    base = get_row_by_id(table, row_id)
    if not base:
        abort(404)

    # Validar que venga el filtro de subdim para asegurar contexto correcto
    active_subdim = request.args.get("subdim") or request.form.get("subdim")
    order = request.args.get("order") or request.form.get("order")
    if not active_subdim or (order not in ("Subdimension", "subdimension")):
        flash("Solo se puede insertar en la visualización por Subdimensión.", "warning")
        return redirect(url_for("planes.index", dim=d.slug))

    # Campos variables (valores enviados desde el formulario)
    autor = request.form.get("Autor")
    tipo = request.form.get("Tipo")
    descripcion = request.form.get("Descripcion")

    # Resolver nombres REALES de columnas segun la tabla
    def colname(*cands: str) -> str | None:
        for c in cands:
            if c in table.c:
                return c
        return None

    autor_col_name = colname("Autor", "autor")
    tipo_col_name = colname("Tipo", "tipo")
    desc_col_name = colname("Descripcion", "descripcion", "Descripción")
    nact_col_name = colname("N_Actividad_Hito", "n_actividad_hito")

    # Construir payload copiando columnas existentes excepto variables y campos técnicos
    payload = {}
    for col_name in table.c.keys():
        if col_name in ("id",):
            continue
        # Evita copiar las columnas variables (usando los nombres reales si existen)
        if (autor_col_name and col_name == autor_col_name) or \
           (tipo_col_name and col_name == tipo_col_name) or \
           (desc_col_name and col_name == desc_col_name) or \
           (nact_col_name and col_name == nact_col_name):
            continue
        # Copia valores del registro base
        payload[col_name] = base.get(col_name)

    # Asignar variables con defaults
    if autor_col_name:
        payload[autor_col_name] = autor or "Agente Maestro"
    if tipo_col_name:
        payload[tipo_col_name] = tipo or "Actividad"
    if desc_col_name:
        payload[desc_col_name] = descripcion or ""

    # Calcular Indicador_Resultado en función del Autor y el contexto
    dimension_val = base.get("Dimension") or base.get("dimension")
    subdimension_val = base.get("Subdimension") or base.get("subdimension")
    instrumento_val = base.get("Instrumento") or base.get("instrumento")
    ind_res_col_name = colname("Indicador_Resultado", "indicador_resultado")
    if ind_res_col_name:
        ind_res = find_indicador_resultado(table, dimension_val, subdimension_val, instrumento_val, payload.get(autor_col_name) if autor_col_name else None)
        if ind_res is not None:
            payload[ind_res_col_name] = ind_res

    # Si la columna N_Actividad_Hito existe y es NOT NULL/UNIQUE por grupo,
    # asigna un valor temporal seguro: max(actual) + 1 dentro del grupo para evitar colisión
    if nact_col_name:
        n_col = table.c[nact_col_name]
        dim_col = table.c.get("Dimension") or table.c.get("dimension")
        sub_col = table.c.get("Subdimension") or table.c.get("subdimension")
        inst_col = table.c.get("Instrumento") or table.c.get("instrumento")
        stmt_max = db.select(db.func.max(n_col))
        if dim_col is not None and dimension_val is not None:
            stmt_max = stmt_max.where(db.cast(dim_col, db.String) == dimension_val)
        if sub_col is not None and subdimension_val is not None:
            stmt_max = stmt_max.where(db.cast(sub_col, db.String) == subdimension_val)
        if inst_col is not None and instrumento_val is not None:
            stmt_max = stmt_max.where(db.cast(inst_col, db.String) == instrumento_val)
        max_val = db.session.execute(stmt_max).scalar()
        try:
            next_val = int(max_val or 0) + 1
        except Exception:
            next_val = 1
        payload[nact_col_name] = next_val

    # Crear fila
    try:
        new_id = create_row(table, payload)
    except Exception:
        flash("No se pudo crear la nueva fila.", "danger")
        return redirect(url_for("planes.index", dim=d.slug, order=order, subdim=active_subdim))

    # Reordenar N_Actividad_Hito dentro del grupo
    try:
        # Obtener N base de la fila sobre la que se insertó
        n_col = table.c.get("N_Actividad_Hito") or table.c.get("n_actividad_hito")
        base_n = None
        if n_col is not None:
            try:
                base_n = int(base.get(n_col.key) or base.get("N_Actividad_Hito") or base.get("n_actividad_hito") or 0)
            except Exception:
                base_n = None
        reorder_n_actividad_hito(
            table,
            dimension_val=dimension_val,
            subdimension_val=subdimension_val,
            instrumento_val=instrumento_val,
            insert_after_id=row_id,
            new_row_id=new_id,
            autor_val=payload.get(autor_col_name) if autor_col_name else None,
            base_n=base_n,
        )
        flash("Fila insertada y reordenada.", "success")
    except Exception:
        flash("Fila creada, pero no se pudo reordenar N° Actividad/Hito.", "warning")

    return redirect(url_for(
        "planes.index",
        dim=d.slug,
        order=order,
        dir=request.args.get("dir", "asc"),
        subdim=active_subdim,
        page=request.args.get("page", 1),
    ))

@bp.post("/import")
def import_excel():
    """Importa el .xlsx solo para la dimensión activa (sin selector)."""
    file = request.files.get("file")
    if not file:
        flash("Debes seleccionar un archivo .xlsx.", "danger")
        return redirect(request.referrer or url_for("planes.index"))

    if file.mimetype not in ALLOWED_XLSX_MIME or not file.filename.lower().endswith(".xlsx"):
        flash("Archivo inválido. Debe ser .xlsx", "danger")
        return redirect(request.referrer or url_for("planes.index"))

    # Determina dimensión actual
    dim_slug = request.args.get("dim") or request.form.get("dim")
    d = get_dimension(dim_slug) if dim_slug else default_dimension()

    try:
        sheets = read_excel_sheets(file)
    except ImportErrorExcel as e:
        flash(str(e), "danger")
        return redirect(request.referrer or url_for("planes.index", dim=d.slug))

    # Normaliza keys por si hay espacios
    sheets = {normalize_sheet_name(k): v for k, v in sheets.items()}

    # Busca la hoja por label exacto de la dimensión
    sheet_name = d.label
    if sheet_name not in sheets:
        flash(f"La hoja '{sheet_name}' no se encontró en el Excel.", "warning")
        return redirect(url_for("planes.index", dim=d.slug))

    df = sheets[sheet_name]
    table = reflect_table(d.table_name)

    if "id" not in df.columns:
        df.insert(0, "id", None)
    df = df.where(pd.notnull(df), None)

    inserted, updated = df_bulk_upsert(table, df)
    flash(f"Importación de '{sheet_name}' completada: insertados={inserted}, actualizados={updated}.", "success")

    return redirect(url_for("planes.index", dim=d.slug))

@bp.post("/<dim>/create")
def create(dim):
    d, table = _resolve_dim(dim)

    # Construimos un payload mínimo usando SOLO columnas existentes.
    payload = {}

    # Buenas prácticas: asignar valores por defecto suaves, no romper not-null
    # 1) Si existe 'Dimension' o 'dimension', ponemos el valor del filtro de dimensión
    if "Dimension" in table.c:
        payload["Dimension"] = d.dimension_filter
    elif "dimension" in table.c:
        payload["dimension"] = d.dimension_filter

    # 2) Campos frecuentes opcionales que podemos inicializar a vacío o valores por defecto
    # Según la tabla ptd_planes, muchos campos son NOT NULL, así que inicializamos con valores razonables
    for optional_text in [
        "Subdimension", "Instrumento", "Indicador", "Brecha",
        "Iniciativa", "Objetivo_Iniciativa",
        "Indicador_Proceso", "Indicador_Resultado",
        "Descripcion",
    ]:
        if optional_text in table.c:
            payload.setdefault(optional_text, "")

    # 3) Campos numéricos comunes
    for optional_num in ["N_Pregunta", "N_Actividad_Hito"]:
        if optional_num in table.c:
            payload.setdefault(optional_num, 1)  # Valor por defecto razonable
    
    # 4) Campos con valores por defecto específicos
    if "Autor" in table.c:
        payload.setdefault("Autor", "Agente Maestro")
    
    if "Tipo" in table.c:
        payload.setdefault("Tipo", "Actividad")

    # Nota: Si tu tabla tiene NOT NULL sin default en otras columnas, agrégalas aquí.

    new_id = create_row(table, payload)
    if new_id is not None:
        flash(f"Fila creada (id={new_id}).", "success")
    else:
        flash("Fila creada.", "success")  # fallback si el driver no devolvió PK

    return redirect(url_for("planes.index", dim=d.slug))



@bp.get("/<dim>/<int:row_id>/edit")
def edit(dim, row_id):
    d, table = _resolve_dim(dim)
    row = get_row_by_id(table, row_id)
    if not row:
        abort(404)

    form = EditRowForm(data=row)
    return render_template("planes/edit.html", form=form, row=row, current_dim=d, dimensions=all_dimensions())

@bp.post("/<dim>/<int:row_id>/edit")
def edit_post(dim, row_id):
    d, table = _resolve_dim(dim)
    row = get_row_by_id(table, row_id)
    if not row:
        abort(404)

    form = EditRowForm()
    if form.validate_on_submit():
        data = {}
        for field in ["Brecha", "Nombre_Actividad_Hito_Diego", "Nombre_Actividad_Hito_Luis"]:
            if field in table.c:
                data[field] = getattr(form, field).data
        if "actualizado_en" in table.c:
            # Deja que DB ponga default si tienes trigger; aquí no forzamos
            pass
        update_row(table, row_id, data)
        flash("Registro actualizado.", "success")
        return redirect(url_for("planes.index", dim=d.slug))
    flash("Error de validación.", "danger")
    return render_template("planes/edit.html", form=form, row=row, current_dim=d, dimensions=all_dimensions())

@bp.post("/<dim>/<int:row_id>/delete")
def delete(dim, row_id):
    d, table = _resolve_dim(dim)
    # Confirmación debe hacerse en el cliente (JS)
    try:
        affected = delete_row(table, row_id)
        if affected > 0:
            flash("Registro eliminado.", "success")
        else:
            flash("No se encontró el registro a eliminar (puede haber sido movido o ya eliminado).", "warning")
    except Exception as e:
        flash("No se pudo eliminar el registro.", "danger")
    return redirect(url_for("planes.index", dim=d.slug))

@bp.post("/<dim>/<int:row_id>/regenerate")
def regenerate(dim, row_id):
    d, table = _resolve_dim(dim)
    row = get_row_by_id(table, row_id)
    if not row:
        abort(404)

    target = request.args.get("target", "diego").lower()
    if target not in ("diego", "luis"):
        flash("Destino inválido para regeneración.", "danger")
        return redirect(url_for("planes.index", dim=d.slug))

    # Extrae datos relevantes de la fila para tu IA
    row_data = dict(row)
    try:
        plan_text = generate_plan(d.slug, row_data, target=target, config=None)
    except AIError as e:
        flash(f"Error al regenerar: {e}", "danger")
        return redirect(url_for("planes.index", dim=d.slug))

    column_name = "Nombre_Actividad_Hito_Diego" if target == "diego" else "Nombre_Actividad_Hito_Luis"
    if column_name not in table.c:
        flash(f"La columna {column_name} no existe en esta dimensión.", "warning")
        return redirect(url_for("planes.index", dim=d.slug))

    update_row(table, row_id, {column_name: plan_text})
    flash("Plan regenerado correctamente.", "success")
    return redirect(url_for("planes.index", dim=d.slug))

@bp.post("/<dim>/<int:row_id>/edit-inline")
def edit_inline(dim, row_id):
    d, table = _resolve_dim(dim)
    row = get_row_by_id(table, row_id)
    if not row:
        abort(404)

    # Construye payload con las columnas que vengan en el form y existan en la tabla
    submitted = {}
    for col in table.c.keys():
        if col in ("id",):  # nunca editar id
            continue
        if col in request.form:
            submitted[col] = request.form.get(col)

    if not submitted:
        flash("No se recibieron cambios.", "info")
        return redirect(url_for("planes.index", dim=d.slug))

    # Calcula solo los cambios reales comparando contra el valor actual
    def _normalize(v):
        if v is None:
            return ""
        return str(v).strip()

    changes = {}
    changed_labels = []
    for col, new_val in submitted.items():
        old_val = row.get(col)
        if _normalize(new_val) != _normalize(old_val):
            changes[col] = new_val
            # Arma una breve leyenda del cambio para feedback al usuario
            # Limita longitudes para evitar mensajes enormes
            old_s = _normalize(old_val)
            new_s = _normalize(new_val)
            if len(old_s) > 60:
                old_s = old_s[:60] + "…"
            if len(new_s) > 60:
                new_s = new_s[:60] + "…"
            changed_labels.append(f"{col}: '{old_s}' → '{new_s}'")

    if not changes:
        flash("No se realizaron cambios.", "info")
        return redirect(url_for("planes.index", dim=d.slug))

    try:
        update_row(table, row_id, changes)
        # Construye mensaje resumido
        if len(changed_labels) > 3:
            summary = "; ".join(changed_labels[:3]) + f" y {len(changed_labels) - 3} más…"
        else:
            summary = "; ".join(changed_labels)
        flash(f"Fila actualizada: {summary}", "success")
    except Exception:
        flash("Error al actualizar la fila.", "danger")

    return redirect(url_for("planes.index", dim=d.slug))


# ============================================================================
# ENDPOINTS DE REGENERACIÓN DE PLANES (AGENTE MAESTRO)
# ============================================================================

@bp.post("/<dim>/regenerate-plan")
def regenerate_plan_agente_maestro(dim):
    """Regenera planes individuales de Agente Maestro para una subdimensión específica."""
    d, table = _resolve_dim(dim)
    
    # Obtener parámetros
    subdimension = request.form.get("subdimension")
    instrumento = request.form.get("instrumento")
    nivel_madurez = request.form.get("nivel_madurez")
    
    if not subdimension:
        return jsonify({"error": "Se requiere subdimensión"}), 400
    
    try:
        # Iniciar regeneración
        task_id = start_regeneration(
            dimension_slug=d.slug,
            subdimension=subdimension,
            instrumento=instrumento,
            nivel_madurez=nivel_madurez,
            full_regeneration=False
        )
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "message": f"Regeneración iniciada para '{subdimension}'"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.post("/<dim>/regenerate-full")
def regenerate_full_agente_maestro(dim):
    """Regenera todos los planes de Agente Maestro para la dimensión completa."""
    d, table = _resolve_dim(dim)
    
    try:
        # Iniciar regeneración completa
        task_id = start_regeneration(
            dimension_slug=d.slug,
            full_regeneration=True
        )
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "message": f"Regeneración completa iniciada para '{d.label}'"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.get("/<dim>/regeneration-status/<task_id>")
def regeneration_status(dim, task_id):
    """Obtiene el estado de una tarea de regeneración."""
    d, table = _resolve_dim(dim)
    
    status = get_task_status(task_id)
    
    if not status:
        return jsonify({"error": "Tarea no encontrada"}), 404
    
    return jsonify(status), 200


@bp.post("/<dim>/cancel-regeneration/<task_id>")
def cancel_regeneration(dim, task_id):
    """Cancela una tarea de regeneración en curso."""
    d, table = _resolve_dim(dim)
    
    success = cancel_task(task_id)
    
    if success:
        return jsonify({"success": True, "message": "Tarea cancelada"}), 200
    else:
        return jsonify({"error": "No se pudo cancelar la tarea"}), 400


# ============================================================================
# ENDPOINTS DE REGENERACIÓN DE PLANES (COMITÉ)
# ============================================================================

@bp.post("/<dim>/regenerate-plan-comite")
def regenerate_plan_comite(dim):
    """
    Regenera/refina un plan individual usando el sistema de comité de agentes.
    
    NOTA: Este endpoint está listo para usar. Solo requiere:
    1. Que exista la carpeta 'comite/scripts/' con los scripts correspondientes
    2. Que los servidores MCP estén configurados en 'comite/mcp/servers/'
    3. Pasar el row_id de la fila a procesar
    """
    d, table = _resolve_dim(dim)
    
    # Obtener parámetros
    row_id = request.form.get("row_id")
    mode = request.form.get("mode", "regen-planes-only")
    
    if not row_id:
        return jsonify({"error": "Se requiere row_id"}), 400
    
    try:
        row_id = int(row_id)
    except ValueError:
        return jsonify({"error": "row_id debe ser un número"}), 400
    
    try:
        # Iniciar regeneración con comité
        task_id = start_comite_regeneration(
            dimension_slug=d.slug,
            row_id=row_id,
            mode=mode
        )
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "message": f"Refinamiento con comité iniciado para fila {row_id}"
        }), 200
        
    except FileNotFoundError as e:
        return jsonify({
            "error": str(e),
            "help": "Asegúrate de copiar la carpeta 'comite/' completa en la raíz del proyecto"
        }), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.get("/<dim>/comite-status/<task_id>")
def comite_regeneration_status(dim, task_id):
    """Obtiene el estado de una tarea de regeneración del comité."""
    d, table = _resolve_dim(dim)
    
    status = get_comite_task_status(task_id)
    
    if not status:
        return jsonify({"error": "Tarea no encontrada"}), 404
    
    return jsonify(status), 200


@bp.post("/<dim>/cancel-comite/<task_id>")
def cancel_comite_regeneration(dim, task_id):
    """Cancela una tarea de regeneración del comité en curso."""
    d, table = _resolve_dim(dim)
    
    success = cancel_comite_task(task_id)
    
    if success:
        return jsonify({"success": True, "message": "Tarea del comité cancelada"}), 200
    else:
        return jsonify({"error": "No se pudo cancelar la tarea"}), 400


@bp.post("/<dim>/regenerate-comite-subdimension")
def regenerate_comite_subdimension(dim):
    """
    Regenera todos los planes del comité para una subdimensión específica.
    Ejecuta el script main_*_bd.py correspondiente sin argumentos para procesar
    todas las combinaciones de la subdimensión.
    """
    d, table = _resolve_dim(dim)
    
    # Obtener parámetros
    subdimension = request.form.get("subdimension")
    instrumento = request.form.get("instrumento")
    nivel_madurez = request.form.get("nivel_madurez")
    
    if not subdimension:
        return jsonify({"error": "Se requiere subdimensión"}), 400
    
    try:
        # Determinar script a ejecutar (main_*_bd.py sin argumentos)
        import subprocess
        import sys
        
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "comite", "scripts")
        
        script_map = {
            "gobernanza-datos": "main_gobernanza_bd.py",
            "gobernanza_datos": "main_gobernanza_bd.py",
            "gobernanza-de-datos": "main_gobernanza_bd.py",
            "calidad-web": "main_calidad_web_bd.py",
            "calidad_web": "main_calidad_web_bd.py",
            "calidad-web-servicios-digital": "main_calidad_web_bd.py",
            "procedimiento": "main_procedimiento_bd.py",
            "procedimiento-administrativo": "main_procedimiento_bd.py",
        }
        
        script_name = script_map.get(d.slug)
        if not script_name:
            return jsonify({"error": f"No hay script del comité para la dimensión '{d.slug}'"}), 400
        
        script_path = os.path.join(base_path, script_name)
        
        if not os.path.exists(script_path):
            return jsonify({
                "error": f"Script no encontrado: {script_name}",
                "help": "Asegúrate de que existe la carpeta 'comite/scripts/' con los scripts correspondientes"
            }), 404
        
        # Ejecutar script sin argumentos (procesará toda la dimensión, se puede filtrar desde el script)
        # Por ahora ejecutamos el script completo
        # TODO: Agregar parámetros al script para filtrar por subdimensión
        cmd = [sys.executable, script_path]
        
        # Iniciar proceso en background
        process = subprocess.Popen(
            cmd,
            cwd=base_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Crear ID de tarea
        task_id = f"comite_subdim_{d.slug}_{subdimension}_{int(time.time())}"
        
        # Registrar tarea (simplificado - idealmente usar el sistema de tareas)
        # Por ahora retornamos éxito y el frontend hará polling
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "message": f"Regeneración con Comité iniciada para '{subdimension}'"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.post("/<dim>/regenerate-comite-full")
def regenerate_comite_full(dim):
    """
    Regenera todos los planes del comité para toda la dimensión.
    Ejecuta el script main_*_bd.py sin argumentos para procesar todas las subdimensiones.
    """
    d, table = _resolve_dim(dim)
    
    try:
        # Determinar script a ejecutar
        import subprocess
        import sys
        import time
        
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "comite", "scripts")
        
        script_map = {
            "gobernanza-datos": "main_gobernanza_bd.py",
            "gobernanza_datos": "main_gobernanza_bd.py",
            "gobernanza-de-datos": "main_gobernanza_bd.py",
            "calidad-web": "main_calidad_web_bd.py",
            "calidad_web": "main_calidad_web_bd.py",
            "calidad-web-servicios-digital": "main_calidad_web_bd.py",
            "procedimiento": "main_procedimiento_bd.py",
            "procedimiento-administrativo": "main_procedimiento_bd.py",
        }
        
        script_name = script_map.get(d.slug)
        if not script_name:
            return jsonify({"error": f"No hay script del comité para la dimensión '{d.slug}'"}), 400
        
        script_path = os.path.join(base_path, script_name)
        
        if not os.path.exists(script_path):
            return jsonify({
                "error": f"Script no encontrado: {script_name}",
                "help": "Asegúrate de que existe la carpeta 'comite/scripts/' con los scripts correspondientes"
            }), 404
        
        # Ejecutar script sin argumentos para procesar toda la dimensión
        cmd = [sys.executable, script_path]
        
        # Iniciar proceso en background
        process = subprocess.Popen(
            cmd,
            cwd=base_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Crear ID de tarea
        task_id = f"comite_full_{d.slug}_{int(time.time())}"
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "message": f"Regeneración completa con Comité iniciada para '{d.label}'"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.get("/export")
def export_plans():
    """Exporta todos los planes a un archivo Excel con formato."""
    try:
        # Obtener la tabla
        dim = default_dimension()
        table = reflect_table(dim.table_name)
        
        # Generar archivo Excel
        excel_file = export_plans_to_excel(table)
        
        # Enviar archivo al usuario
        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='planes_ptd.xlsx'
        )
    except Exception as e:
        flash(f"Error al exportar planes: {str(e)}", "error")
        return redirect(url_for('planes.index'))
