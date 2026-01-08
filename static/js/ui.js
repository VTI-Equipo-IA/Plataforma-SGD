// static/js/ui.js

function enterEditMode(rowEl) {
  const actions = rowEl.querySelector(".row-actions");
  const editBtn = actions.querySelector(".btn-edit");
  const deleteForm = actions.querySelector(".inline-delete-form");
  const editActions = actions.querySelector(".edit-actions");
  const form = rowEl.querySelector("form.inline-edit-form");

  // Oculta botones lectura, muestra acciones edición
  editBtn.style.display = "none";
  deleteForm.style.display = "none";
  editActions.style.display = "inline-flex";

  // Convierte celdas a inputs
  const cells = rowEl.querySelectorAll("td.cell");
  cells.forEach(td => {
    const col = td.getAttribute("data-col");
    const type = td.getAttribute("data-type") || "text";
    // Intenta leer el valor actual desde la estructura visible
    // 1) Si hay un enlace dentro de .cell-content, usa su texto
    // 2) Si hay .cell-content, usa su textContent
    // 3) Fallback a span por compatibilidad antigua
    let currentVal = "";
    const content = td.querySelector(".cell-content");
    if (content) {
      const link = content.querySelector("a");
      if (link && link.textContent) {
        currentVal = link.textContent.trim();
      } else if (content.textContent) {
        currentVal = content.textContent.trim();
      }
    } else {
      const legacySpan = td.querySelector("span");
      if (legacySpan && legacySpan.textContent) {
        currentVal = legacySpan.textContent.trim();
      }
    }

    // Evita duplicar inputs
    if (td.querySelector("input, textarea")) return;

    let input;
    if (type === "textarea") {
      input = document.createElement("textarea");
      input.rows = 6;
    } else {
      input = document.createElement("input");
      input.type = "text";
    }
    input.name = col;
    input.value = currentVal || "";
    // Asegura asociación con el formulario aunque el DOM tenga <form> fuera de celdas
    if (form && form.id) {
      input.setAttribute("form", form.id);
    }

    // Reemplaza visualmente
    td.innerHTML = "";
    td.appendChild(input);
  });

  // Handlers Guardar/Cancelar
  const saveBtn = actions.querySelector(".btn-save");
  const cancelBtn = actions.querySelector(".btn-cancel");

  const onSave = () => {
    form.submit();
  };
  const onCancel = () => {
    // Recargar la página para restaurar (simple y robusto)
    window.location.reload();
  };

  saveBtn.addEventListener("click", onSave, { once: true });
  cancelBtn.addEventListener("click", onCancel, { once: true });
}

function setupRowActions() {
  document.querySelectorAll(".row-actions .btn-edit").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const rowId = e.currentTarget.getAttribute("data-row-id");
      const rowEl = document.getElementById(`row-${rowId}`);
      if (rowEl) enterEditMode(rowEl);
    });
  });
}

function buildInsertRow(baseRowEl) {
  const table = document.getElementById("main-table");
  const dim = table?.getAttribute("data-dim") || "";
  const order = table?.getAttribute("data-order") || "";
  const dir = table?.getAttribute("data-dir") || "asc";
  const subdim = table?.getAttribute("data-subdim") || "";
  const page = table?.getAttribute("data-page") || "1";
  const baseId = parseInt(baseRowEl.id.replace("row-", ""), 10);

  // Construye <tr> nuevo
  const tr = document.createElement("tr");
  tr.className = "insert-below-row";

  // Celda de acciones con Guardar/Cancelar
  const tdActions = document.createElement("td");
  tdActions.className = "col-actions";
  const saveBtn = document.createElement("button");
  saveBtn.type = "button";
  saveBtn.className = "btn-small";
  saveBtn.textContent = "💾";
  saveBtn.title = "Guardar";
  const cancelBtn = document.createElement("button");
  cancelBtn.type = "button";
  cancelBtn.className = "btn-small";
  cancelBtn.textContent = "✖";
  cancelBtn.title = "Cancelar";
  tdActions.appendChild(saveBtn);
  tdActions.appendChild(cancelBtn);
  tr.appendChild(tdActions);

  // Formulario oculto que enviaremos al backend
  const form = document.createElement("form");
  form.method = "post";
  form.action = `${window.location.origin}${window.location.pathname.replace(/\/$/, '')}/${dim}/${baseId}/insert-below?order=${encodeURIComponent(order)}&dir=${encodeURIComponent(dir)}&subdim=${encodeURIComponent(subdim)}&page=${encodeURIComponent(page)}`;
  form.style.display = "none";
  form.id = `insert-form-${baseId}-${Date.now()}`;
  // Token CSRF: tomar del form de edición inline de la fila base
  const baseForm = baseRowEl.querySelector("form.inline-edit-form");
  const csrfInput = baseForm ? baseForm.querySelector('input[name="csrf_token"]') : null;
  if (csrfInput && csrfInput.value) {
    const c = document.createElement("input");
    c.type = "hidden";
    c.name = "csrf_token";
    c.value = csrfInput.value;
    form.appendChild(c);
  } else {
    // Fallback al meta tag en <head>
    const meta = document.querySelector('meta[name="csrf-token"]');
    const token = meta ? meta.getAttribute('content') : '';
    if (token) {
      const c = document.createElement("input");
      c.type = "hidden";
      c.name = "csrf_token";
      c.value = token;
      form.appendChild(c);
    }
  }

  // Construir celdas replicando columnas y añadiendo inputs necesarios
  const cells = baseRowEl.querySelectorAll("td.cell");
  cells.forEach(origTd => {
    const col = origTd.getAttribute("data-col");
    const colKey = (col || "").toLowerCase();
    const newTd = document.createElement("td");
    newTd.className = origTd.className;
    newTd.setAttribute("data-col", col);

    // Lee el valor de texto de la celda base
    let currentVal = "";
    const content = origTd.querySelector(".cell-content");
    if (content) {
      const link = content.querySelector("a");
      if (link && link.textContent) currentVal = link.textContent.trim();
      else if (content.textContent) currentVal = content.textContent.trim();
    }

    if (colKey === "autor") {
      const sel = document.createElement("select");
      sel.name = "Autor";
      sel.setAttribute("form", form.id);
      ["Comite", "Agente Maestro"].forEach(optVal => {
        const opt = document.createElement("option");
        opt.value = optVal;
        opt.textContent = optVal;
        if (currentVal && currentVal === optVal) opt.selected = true;
        sel.appendChild(opt);
      });
      // Placeholder visual
      newTd.appendChild(sel);

      // Actualizar Indicador_Resultado cuando cambie Autor
      sel.addEventListener("change", async () => {
        const autor = sel.value;
        try {
          const url = `${window.location.origin}/planes/${dim}/indicador-resultado?base_id=${encodeURIComponent(baseId)}&autor=${encodeURIComponent(autor)}`;
          const res = await fetch(url, { credentials: 'same-origin' });
          const text = await res.text();
          const indInput = form.querySelector('input[name="Indicador_Resultado"], input[name="indicador_resultado"]');
          const indView = tr.querySelector('[data-col="Indicador_Resultado"] .cell-content, [data-col="indicador_resultado"] .cell-content');
          if (indInput) indInput.value = text || "";
          if (indView) indView.textContent = text || "";
        } catch (e) {
          // ignorar errores silenciosamente
        }
      });
      // Disparar una vez para prefijar Indicador_Resultado
      setTimeout(() => sel.dispatchEvent(new Event('change')), 0);
    } else if (colKey === "tipo") {
      const sel = document.createElement("select");
      sel.name = "Tipo";
      sel.setAttribute("form", form.id);
      ["Actividad", "Hito"].forEach(optVal => {
        const opt = document.createElement("option");
        opt.value = optVal;
        opt.textContent = optVal;
        if (currentVal && currentVal === optVal) opt.selected = true;
        sel.appendChild(opt);
      });
      newTd.appendChild(sel);
    } else if (colKey === "descripcion") {
      const input = document.createElement("input");
      input.type = "text";
      input.name = "Descripcion";
      input.setAttribute("form", form.id);
      input.placeholder = "Escribe la descripción…";
      newTd.appendChild(input);
    } else {
      // Resto de columnas: mostrar texto y enviar oculto
      const view = document.createElement("div");
      view.className = "cell-content";
      view.textContent = currentVal || "";
      newTd.appendChild(view);
      const hidden = document.createElement("input");
      hidden.type = "hidden";
      hidden.name = col;
      hidden.value = currentVal || "";
      form.appendChild(hidden);
    }

    // Si es la columna Indicador_Resultado, mostrar y añadir hidden input para permitir actualización automática
    if (colKey === "indicador_resultado") {
      // Asegura input hidden para poder actualizarse desde el cambio de Autor
      const indHidden = document.createElement("input");
      indHidden.type = "hidden";
      indHidden.name = (col || "Indicador_Resultado");
      indHidden.value = currentVal || "";
      form.appendChild(indHidden);
      // Y una vista legible por el usuario (ya creada arriba si no variable)
      if (!newTd.querySelector('.cell-content')) {
        const v = document.createElement("div");
        v.className = "cell-content";
        v.textContent = currentVal || "";
        newTd.appendChild(v);
      }
    }

    tr.appendChild(newTd);
  });

  // Acciones: Guardar/Cancelar
  saveBtn.addEventListener("click", async () => {
    const tokenMeta = document.querySelector('meta[name="csrf-token"]');
    const token = tokenMeta ? tokenMeta.getAttribute('content') : '';
    const fd = new FormData(form);
    if (token && !fd.get('csrf_token')) {
      fd.append('csrf_token', token);
    }
    // Also include visible inputs (Autor, Tipo, Descripcion) that live outside the form via 'form' attribute
    tr.querySelectorAll('select[form="'+form.id+'"], input[form="'+form.id+'"]').forEach(el => {
      if (el.name) fd.set(el.name, el.value || '');
    });
    try {
      const res = await fetch(form.action, {
        method: 'POST',
        body: fd,
        credentials: 'same-origin',
        headers: token ? { 'X-CSRFToken': token } : {}
      });
      // Follow final URL
      if (res.redirected) {
        window.location.href = res.url;
      } else {
        // on success our endpoint redirects; if not, reload to reflect state
        window.location.reload();
      }
    } catch (e) {
      window.location.reload();
    }
  });
  cancelBtn.addEventListener("click", () => {
    tr.remove();
  });

  // Inserta el <form> al final del tbody para no romper el layout
  const tbody = baseRowEl.parentElement;
  tbody.appendChild(form);

  return tr;
}

function setupInsertBelow() {
  const table = document.getElementById("main-table");
  const subdim = table?.getAttribute("data-subdim") || "";
  // Solo habilitar si estamos viendo una subdimensión específica
  const enabled = !!subdim;
  if (!enabled) return;

  document.querySelectorAll(".row-actions .btn-insert-below").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const rowId = e.currentTarget.getAttribute("data-row-id");
      const baseRowEl = document.getElementById(`row-${rowId}`);
      if (!baseRowEl) return;
      // Evitar múltiples filas de inserción debajo del mismo registro
      if (baseRowEl.nextElementSibling && baseRowEl.nextElementSibling.classList.contains("insert-below-row")) {
        return;
      }
      const tr = buildInsertRow(baseRowEl);
      baseRowEl.parentElement.insertBefore(tr, baseRowEl.nextElementSibling);
    });
  });
}

function setupClampToggles() {
  // Per-cell toggle
  document.querySelectorAll(".toggle-more").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const td = e.currentTarget.closest("td");
      const content = td.querySelector(".cell-content");
      const expanded = content.classList.toggle("expanded");
      e.currentTarget.textContent = expanded ? "Ver menos" : "Ver más";
      e.currentTarget.setAttribute("aria-expanded", expanded ? "true" : "false");
    });
  });

  // Global toggle
  const toggleAll = document.getElementById("toggle-expand-all");
  if (toggleAll) {
    let allExpanded = false;
    toggleAll.addEventListener("click", () => {
      allExpanded = !allExpanded;
      document.querySelectorAll(".cell-content").forEach(el => {
        if (allExpanded) el.classList.add("expanded");
        else el.classList.remove("expanded");
      });
      document.querySelectorAll(".toggle-more").forEach(btn => {
        btn.textContent = allExpanded ? "Ver menos" : "Ver más";
        btn.setAttribute("aria-expanded", allExpanded ? "true" : "false");
      });
      toggleAll.textContent = allExpanded ? "Contraer texto" : "Expandir texto";
    });
  }
}

function setupDensityToggle(){
  const btn = document.getElementById("toggle-density");
  const table = document.getElementById("main-table");
  if (!btn || !table) return;
  let comfy = false;
  btn.addEventListener("click", () => {
    comfy = !comfy;
    table.classList.toggle("comfortable", comfy);
    btn.textContent = comfy ? "Menos espacio" : "Más espacio";
  });
}

// ============================================================================
// REGENERACIÓN DE PLANES CON AGENTE MAESTRO
// ============================================================================

let currentRegenerationTask = null;
let regenerationInterval = null;

function showRegenerationModal(message) {
  // Crear modal si no existe
  let modal = document.getElementById("regeneration-modal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "regeneration-modal";
    modal.innerHTML = `
      <div class="modal-overlay">
        <div class="modal-content">
          <div class="modal-header">
            <h3>Regenerando planes</h3>
          </div>
          <div class="modal-body">
            <div class="spinner"></div>
            <p id="regen-message">${message}</p>
            <div class="progress-bar">
              <div class="progress-fill" id="regen-progress" style="width: 0%"></div>
            </div>
            <p class="progress-text" id="regen-percent">0%</p>
          </div>
          <div class="modal-footer">
            <button type="button" onclick="cancelRegeneration()" class="btn-cancel">Cancelar</button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }
  
  document.getElementById("regen-message").textContent = message;
  document.getElementById("regen-progress").style.width = "0%";
  document.getElementById("regen-percent").textContent = "0%";
  modal.style.display = "block";
}

function hideRegenerationModal() {
  const modal = document.getElementById("regeneration-modal");
  if (modal) {
    modal.style.display = "none";
  }
  if (regenerationInterval) {
    clearInterval(regenerationInterval);
    regenerationInterval = null;
  }
  currentRegenerationTask = null;
}

function updateRegenerationStatus(status) {
  const messageEl = document.getElementById("regen-message");
  const progressEl = document.getElementById("regen-progress");
  const percentEl = document.getElementById("regen-percent");
  
  if (messageEl) messageEl.textContent = status.message || "Procesando...";
  if (progressEl) progressEl.style.width = `${status.progress || 0}%`;
  if (percentEl) percentEl.textContent = `${status.progress || 0}%`;
  
  // Si completó o falló, mostrar resultado y cerrar
  if (status.status === "completed") {
    if (messageEl) messageEl.textContent = "✓ " + status.message;
    setTimeout(() => {
      hideRegenerationModal();
      window.location.reload(); // Recargar para ver los nuevos planes
    }, 2000);
  } else if (status.status === "failed") {
    if (messageEl) messageEl.textContent = "✗ Error: " + (status.error || "Error desconocido");
    if (progressEl) progressEl.style.backgroundColor = "#ef4444";
    setTimeout(() => {
      hideRegenerationModal();
    }, 5000);
  }
}

function pollRegenerationStatus(dim, taskId) {
  const url = `/planes/${dim}/regeneration-status/${taskId}`;
  
  fetch(url)
    .then(response => response.json())
    .then(status => {
      updateRegenerationStatus(status);
      
      // Si aún está en progreso, seguir consultando
      if (status.status === "running" || status.status === "pending") {
        // Continuar polling
      } else {
        // Terminar polling
        if (regenerationInterval) {
          clearInterval(regenerationInterval);
          regenerationInterval = null;
        }
      }
    })
    .catch(error => {
      console.error("Error consultando estado:", error);
      updateRegenerationStatus({
        status: "failed",
        message: "Error de comunicación",
        error: error.message,
        progress: 0
      });
    });
}

function regeneratePlan(dim, subdimension, instrumento, nivelMadurez) {
  if (currentRegenerationTask) {
    alert("Ya hay una regeneración en curso. Por favor espere.");
    return;
  }
  
  if (!confirm(`¿Desea regenerar el plan de Agente Maestro para "${subdimension}"?\n\nEsto sobrescribirá los planes existentes.`)) {
    return;
  }
  
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
  
  const formData = new FormData();
  formData.append("subdimension", subdimension);
  if (instrumento) formData.append("instrumento", instrumento);
  if (nivelMadurez) formData.append("nivel_madurez", nivelMadurez);
  
  showRegenerationModal(`Iniciando regeneración para "${subdimension}"...`);
  
  fetch(`/planes/${dim}/regenerate-plan`, {
    method: "POST",
    headers: {
      "X-CSRFToken": csrfToken
    },
    body: formData
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        currentRegenerationTask = data.task_id;
        
        // Iniciar polling cada 2 segundos
        regenerationInterval = setInterval(() => {
          pollRegenerationStatus(dim, data.task_id);
        }, 2000);
        
        // Primera consulta inmediata
        pollRegenerationStatus(dim, data.task_id);
      } else {
        updateRegenerationStatus({
          status: "failed",
          message: "Error al iniciar regeneración",
          error: data.error,
          progress: 0
        });
      }
    })
    .catch(error => {
      console.error("Error iniciando regeneración:", error);
      updateRegenerationStatus({
        status: "failed",
        message: "Error al iniciar regeneración",
        error: error.message,
        progress: 0
      });
    });
}

function regenerateFull(dim) {
  if (currentRegenerationTask) {
    alert("Ya hay una regeneración en curso. Por favor espere.");
    return;
  }
  
  if (!confirm("¿Desea regenerar TODOS los planes de Agente Maestro para esta dimensión?\n\nEsto puede tomar varios minutos y sobrescribirá todos los planes existentes.")) {
    return;
  }
  
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
  
  showRegenerationModal("Iniciando regeneración completa de la dimensión...");
  
  fetch(`/planes/${dim}/regenerate-full`, {
    method: "POST",
    headers: {
      "X-CSRFToken": csrfToken
    }
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        currentRegenerationTask = data.task_id;
        
        // Iniciar polling cada 3 segundos (más lento para regeneración completa)
        regenerationInterval = setInterval(() => {
          pollRegenerationStatus(dim, data.task_id);
        }, 3000);
        
        // Primera consulta inmediata
        pollRegenerationStatus(dim, data.task_id);
      } else {
        updateRegenerationStatus({
          status: "failed",
          message: "Error al iniciar regeneración",
          error: data.error,
          progress: 0
        });
      }
    })
    .catch(error => {
      console.error("Error iniciando regeneración:", error);
      updateRegenerationStatus({
        status: "failed",
        message: "Error al iniciar regeneración",
        error: error.message,
        progress: 0
      });
    });
}

function cancelRegeneration() {
  if (!currentRegenerationTask) {
    hideRegenerationModal();
    return;
  }
  
  if (!confirm("¿Desea cancelar la regeneración en curso?")) {
    return;
  }
  
  const dim = window.location.pathname.split('/')[2] || 'gobernanza-datos';
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
  
  fetch(`/planes/${dim}/cancel-regeneration/${currentRegenerationTask}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": csrfToken
    }
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        updateRegenerationStatus({
          status: "failed",
          message: "Regeneración cancelada",
          error: "Cancelado por el usuario",
          progress: 0
        });
      }
    })
    .catch(error => {
      console.error("Error cancelando regeneración:", error);
    });
}

// ============================================================================
// FUNCIONES PARA REGENERACIÓN CON COMITÉ
// ============================================================================

/**
 * Regenera un plan individual usando el sistema de comité
 * NOTA: Esta función está lista para usar cuando los scripts del comité estén disponibles
 * 
 * @param {number} rowId - ID de la fila a procesar
 * @param {string} mode - Modo de regeneración (regen-planes-only, regen-hitos-only, hito, activity)
 */
function regeneratePlanComite(rowId, mode = 'regen-planes-only') {
  const dim = window.location.pathname.split('/')[2] || 'gobernanza-datos';
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
  
  const formData = new FormData();
  formData.append('row_id', rowId);
  formData.append('mode', mode);
  
  fetch(`/planes/${dim}/regenerate-plan-comite`, {
    method: "POST",
    headers: {
      "X-CSRFToken": csrfToken
    },
    body: formData
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        showRegenerationModal(`Refinando fila ${rowId} con comité de agentes...`);
        pollComiteStatus(dim, data.task_id);
      } else {
        alert(`Error: ${data.error}${data.help ? '\n\n' + data.help : ''}`);
      }
    })
    .catch(error => {
      console.error("Error iniciando refinamiento con comité:", error);
      alert("Error al iniciar refinamiento con comité");
    });
}

/**
 * Regenera todos los planes del comité para una subdimensión específica
 * Esto ejecutará el script main_*_bd.py con filtros de subdimensión
 */
function regeneratePlanComiteSubdimension(dim, subdimension, instrumento, nivelMadurez) {
  if (currentRegenerationTask) {
    alert("Ya hay una regeneración en curso. Por favor espere.");
    return;
  }
  
  if (!confirm(`¿Desea regenerar TODOS los planes del Comité para "${subdimension}"?\n\nEsto ejecutará el sistema completo de comité con 5 agentes especializados.\nEl proceso puede tomar varios minutos.`)) {
    return;
  }
  
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
  const formData = new FormData();
  formData.append("subdimension", subdimension);
  if (instrumento) formData.append("instrumento", instrumento);
  if (nivelMadurez) formData.append("nivel_madurez", nivelMadurez);
  formData.append("mode", "subdimension");  // Modo especial para subdimensión
  
  showRegenerationModal(`Iniciando regeneración con Comité para "${subdimension}"...`);
  
  fetch(`/planes/${dim}/regenerate-comite-subdimension`, {
    method: "POST",
    headers: {
      "X-CSRFToken": csrfToken
    },
    body: formData
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        currentRegenerationTask = data.task_id;
        
        // Iniciar polling cada 3 segundos
        regenerationInterval = setInterval(() => {
          pollComiteStatus(dim, data.task_id);
        }, 3000);
        
        // Primera consulta inmediata
        pollComiteStatus(dim, data.task_id);
      } else {
        updateRegenerationStatus({
          status: "failed",
          message: "Error al iniciar regeneración con Comité",
          error: data.error || data.help || "Error desconocido",
          progress: 0
        });
      }
    })
    .catch(error => {
      console.error("Error iniciando regeneración con Comité:", error);
      updateRegenerationStatus({
        status: "failed",
        message: "Error al iniciar regeneración con Comité",
        error: error.message,
        progress: 0
      });
    });
}

/**
 * Regenera todos los planes del comité para toda la dimensión
 * Esto procesará todas las subdimensiones de la dimensión actual
 */
function regenerateFullComite(dim) {
  if (currentRegenerationTask) {
    alert("Ya hay una regeneración en curso. Por favor espere.");
    return;
  }
  
  if (!confirm("¿Desea regenerar TODOS los planes del Comité para esta dimensión completa?\n\nEsto ejecutará el sistema completo de comité para todas las subdimensiones.\nEl proceso puede tomar mucho tiempo (30+ minutos dependiendo de la cantidad de datos).")) {
    return;
  }
  
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
  
  showRegenerationModal("Iniciando regeneración completa con Comité...");
  
  fetch(`/planes/${dim}/regenerate-comite-full`, {
    method: "POST",
    headers: {
      "X-CSRFToken": csrfToken
    }
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        currentRegenerationTask = data.task_id;
        
        // Iniciar polling cada 5 segundos (más lento para procesos largos)
        regenerationInterval = setInterval(() => {
          pollComiteStatus(dim, data.task_id);
        }, 5000);
        
        // Primera consulta inmediata
        pollComiteStatus(dim, data.task_id);
      } else {
        updateRegenerationStatus({
          status: "failed",
          message: "Error al iniciar regeneración completa con Comité",
          error: data.error || data.help || "Error desconocido",
          progress: 0
        });
      }
    })
    .catch(error => {
      console.error("Error iniciando regeneración completa con Comité:", error);
      updateRegenerationStatus({
        status: "failed",
        message: "Error al iniciar regeneración completa con Comité",
        error: error.message,
        progress: 0
      });
    });
}

/**
 * Consulta el estado de una tarea del comité periódicamente
 */
function pollComiteStatus(dim, taskId) {
  currentRegenerationTask = taskId;
  
  const pollInterval = setInterval(() => {
    fetch(`/planes/${dim}/comite-status/${taskId}`)
      .then(response => response.json())
      .then(data => {
        updateRegenerationStatus(data);
        
        if (data.status === "completed") {
          clearInterval(pollInterval);
          setTimeout(() => {
            hideRegenerationModal();
            location.reload(); // Recargar para mostrar cambios
          }, 2000);
        } else if (data.status === "failed") {
          clearInterval(pollInterval);
          // No cerrar automáticamente en caso de error
        }
      })
      .catch(error => {
        console.error("Error obteniendo estado del comité:", error);
        clearInterval(pollInterval);
      });
  }, 2500); // Consultar cada 2.5 segundos
}

/**
 * Cancela una regeneración del comité en curso
 */
function cancelComiteRegeneration() {
  if (!currentRegenerationTask) return;
  
  if (!confirm("¿Desea cancelar el refinamiento del comité en curso?")) {
    return;
  }
  
  const dim = window.location.pathname.split('/')[2] || 'gobernanza-datos';
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
  
  fetch(`/planes/${dim}/cancel-comite/${currentRegenerationTask}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": csrfToken
    }
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        updateRegenerationStatus({
          status: "failed",
          message: "Refinamiento del comité cancelado",
          error: "Cancelado por el usuario",
          progress: 0
        });
      }
    })
    .catch(error => {
      console.error("Error cancelando refinamiento del comité:", error);
    });
}

document.addEventListener("DOMContentLoaded", () => {
  setupRowActions();
  setupClampToggles();
  setupDensityToggle();
  setupInsertBelow();
});
