/**
 * views/eventos.js — CRUD completo de Eventos y sus Ediciones.
 */
import { apiFetch, toast } from '../components/badges.js';

const CATEGORIAS = [
  "Cultura y Arte", "Religioso", "Cívico", "Gastronomía",
  "Deporte", "Ecoturismo", "Musical", "Académico", "Festival", "Otro"
];
const ESTADOS_EDICION = ["Planificada", "En curso", "Finalizada"];

export async function render(container) {
  container.innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 400px;gap:18px;align-items:start">

      <!-- Lista de eventos -->
      <div id="ev-panel-lista">
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
            <span class="card-label" style="margin:0">Eventos registrados</span>
            <span id="ev-total" style="font-size:12px;color:var(--muted)"></span>
          </div>
          <div id="ev-lista"></div>
        </div>
      </div>

      <!-- Formulario evento -->
      <div style="position:sticky;top:80px;display:flex;flex-direction:column;gap:14px">
        <div class="card">
          <div class="card-label" id="form-ev-titulo">Nuevo evento</div>

          <div class="form-row">
            <label>Nombre oficial <span style="color:var(--red)">*</span></label>
            <input class="input" id="ev-nombre" placeholder="ej: Festival Internacional de Artes Vivas de Loja">
          </div>
          <div class="form-row">
            <label>Categoría</label>
            <select class="input" id="ev-cat">
              ${CATEGORIAS.map(c => `<option value="${c}">${c}</option>`).join('')}
            </select>
          </div>
          <div class="form-row">
            <label>Descripción</label>
            <textarea class="input" id="ev-desc" rows="3"
              placeholder="Breve descripción del evento..."></textarea>
          </div>
          <div class="form-row">
            <label>Palabras clave <span style="font-weight:400;opacity:.6">(separadas por coma)</span></label>
            <textarea class="input" id="ev-tags" rows="2"
              placeholder="fiavl, artesvivas, loja, festival, teatro..."></textarea>
          </div>
          <div class="form-row">
            <label>Estado</label>
            <div style="display:flex;align-items:center;gap:8px;margin-top:4px">
              <input type="checkbox" id="ev-activo" checked
                style="width:16px;height:16px;accent-color:var(--navy)">
              <label for="ev-activo" style="font-size:13px;font-weight:400;margin:0;cursor:pointer">
                Evento activo
              </label>
            </div>
          </div>

          <div style="display:flex;gap:8px">
            <button class="btn btn-primary" style="flex:1" id="btn-ev-guardar">Guardar evento</button>
            <button class="btn btn-ghost" id="btn-ev-cancelar" style="display:none">Cancelar</button>
          </div>
        </div>

        <!-- Panel de ediciones (aparece al seleccionar evento) -->
        <div class="card" id="panel-ediciones" style="display:none">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
            <span class="card-label" style="margin:0">Ediciones</span>
            <span id="ed-evento-nombre" style="font-size:11px;color:var(--muted);max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"></span>
          </div>
          <div id="ed-lista" style="margin-bottom:14px"></div>

          <!-- Formulario nueva edición -->
          <div style="border-top:1px solid var(--border);padding-top:14px">
            <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:var(--muted);margin-bottom:10px"
                 id="form-ed-titulo">Nueva edición</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px">
              <div class="form-row" style="margin:0">
                <label>Año <span style="color:var(--red)">*</span></label>
                <input class="input" id="ed-anio" type="number" placeholder="2026" min="1900" max="2100">
              </div>
              <div class="form-row" style="margin:0">
                <label>Estado</label>
                <select class="input" id="ed-estado">
                  ${ESTADOS_EDICION.map(e => `<option value="${e}">${e}</option>`).join('')}
                </select>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px">
              <div class="form-row" style="margin:0">
                <label>Fecha inicio <span style="font-weight:400;opacity:.6">(opcional)</span></label>
                <input class="input" id="ed-inicio" type="date">
              </div>
              <div class="form-row" style="margin:0">
                <label>Fecha fin <span style="font-weight:400;opacity:.6">(opcional)</span></label>
                <input class="input" id="ed-fin" type="date">
              </div>
            </div>
            <div style="display:flex;gap:8px">
              <button class="btn btn-primary" style="flex:1;font-size:12px" id="btn-ed-guardar">Guardar edición</button>
              <button class="btn btn-ghost" id="btn-ed-cancelar" style="display:none;font-size:12px">Cancelar</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal eliminar evento -->
    <div id="modal-del-ev" style="display:none;position:fixed;inset:0;background:rgba(0,20,60,.45);z-index:100;align-items:center;justify-content:center">
      <div class="modal" style="max-width:440px">
        <div class="modal-title" style="color:var(--red)">Eliminar evento</div>
        <div id="modal-del-ev-txt" style="font-size:13px;color:var(--text);line-height:1.6;margin-bottom:16px"></div>
        <div class="modal-footer">
          <button class="btn btn-ghost" id="btn-del-ev-cancel">Cancelar</button>
          <button class="btn" id="btn-del-ev-confirm" style="background:var(--red);color:#fff">Sí, eliminar todo</button>
        </div>
      </div>
    </div>

    <!-- Modal eliminar edición -->
    <div id="modal-del-ed" style="display:none;position:fixed;inset:0;background:rgba(0,20,60,.45);z-index:100;align-items:center;justify-content:center">
      <div class="modal" style="max-width:420px">
        <div class="modal-title" style="color:var(--red)">Eliminar edición</div>
        <div id="modal-del-ed-txt" style="font-size:13px;color:var(--text);line-height:1.6;margin-bottom:16px"></div>
        <div class="modal-footer">
          <button class="btn btn-ghost" id="btn-del-ed-cancel">Cancelar</button>
          <button class="btn" id="btn-del-ed-confirm" style="background:var(--red);color:#fff">Sí, eliminar</button>
        </div>
      </div>
    </div>
  `;

  // Listeners modales
  document.getElementById('btn-del-ev-cancel').addEventListener('click', () =>
    document.getElementById('modal-del-ev').style.display = 'none'
  );
  document.getElementById('btn-del-ed-cancel').addEventListener('click', () =>
    document.getElementById('modal-del-ed').style.display = 'none'
  );
  ['modal-del-ev','modal-del-ed'].forEach(id => {
    document.getElementById(id).addEventListener('click', e => {
      if (e.target === document.getElementById(id))
        document.getElementById(id).style.display = 'none';
    });
  });

  document.getElementById('btn-ev-guardar').addEventListener('click', guardarEvento);
  document.getElementById('btn-ev-cancelar').addEventListener('click', resetFormEvento);
  document.getElementById('btn-ed-guardar').addEventListener('click', guardarEdicion);
  document.getElementById('btn-ed-cancelar').addEventListener('click', resetFormEdicion);

  await cargarEventos();
}

// ── Estado ────────────────────────────────────────────────
let editandoEvId  = null;
let editandoEdId  = null;
let eventoActivo  = null;   // { id, nombre }

// ── Eventos ───────────────────────────────────────────────
async function cargarEventos() {
  const lista = document.getElementById('ev-lista');
  lista.innerHTML = `<div class="empty"><p>Cargando...</p></div>`;
  try {
    const d = await apiFetch('/api/eventos');
    document.getElementById('ev-total').textContent = `${d.total} registrados`;
    if (!d.data.length) {
      lista.innerHTML = `<div class="empty"><p>No hay eventos. Agrega el primero.</p></div>`;
      return;
    }
    lista.innerHTML = d.data.map(ev => `
      <div class="rec-card" id="ev-card-${ev._id}" style="grid-template-columns:1fr auto;cursor:default">
        <div class="rec-main">
          <div style="display:flex;align-items:center;gap:8px">
            <span class="rec-titulo">${ev.nombre_oficial}</span>
            ${ev.activo
              ? `<span class="badge b-clasificado" style="font-size:10px">Activo</span>`
              : `<span class="badge b-error" style="font-size:10px">Inactivo</span>`}
          </div>
          <div class="rec-meta" style="margin-top:4px">
            <span class="badge b-mock">${ev.categoria || 'Sin categoría'}</span>
            ${ev.descripcion_general
              ? `<span style="font-size:11px;color:var(--muted)">${ev.descripcion_general.slice(0,60)}${ev.descripcion_general.length>60?'...':''}</span>`
              : ''}
          </div>
          <div style="margin-top:6px">
            <button class="btn btn-ghost btn-sm" data-id="${ev._id}" data-nombre="${ev.nombre_oficial}" data-action="ver-ediciones"
              style="font-size:11px">
              Ver ediciones
            </button>
          </div>
        </div>
        <div class="rec-actions">
          <button class="btn btn-ghost btn-sm" data-id="${ev._id}" data-action="editar-ev">Editar</button>
          <button class="btn btn-danger-soft btn-sm" data-id="${ev._id}" data-nombre="${ev.nombre_oficial}" data-action="eliminar-ev">Eliminar</button>
        </div>
      </div>
    `).join('');

    lista.querySelectorAll('[data-action="editar-ev"]').forEach(btn =>
      btn.addEventListener('click', () => cargarEdicionEvento(btn.dataset.id))
    );
    lista.querySelectorAll('[data-action="eliminar-ev"]').forEach(btn =>
      btn.addEventListener('click', () => confirmarEliminarEvento(btn.dataset.id, btn.dataset.nombre))
    );
    lista.querySelectorAll('[data-action="ver-ediciones"]').forEach(btn =>
      btn.addEventListener('click', () => abrirPanelEdiciones(btn.dataset.id, btn.dataset.nombre))
    );
  } catch(e) {
    lista.innerHTML = `<div class="empty"><p style="color:var(--red)">Error: ${e.message}</p></div>`;
  }
}

async function cargarEdicionEvento(id) {
  try {
    const d = await apiFetch('/api/eventos');
    const ev = d.data.find(e => e._id === id);
    if (!ev) return;
    editandoEvId = id;
    document.getElementById('form-ev-titulo').textContent = 'Editar evento';
    document.getElementById('ev-nombre').value = ev.nombre_oficial || '';
    document.getElementById('ev-cat').value    = ev.categoria || CATEGORIAS[0];
    document.getElementById('ev-desc').value   = ev.descripcion_general || '';
    document.getElementById('ev-tags').value   = (ev.palabras_clave || []).join(', ');
    document.getElementById('ev-activo').checked = ev.activo !== false;
    document.getElementById('btn-ev-cancelar').style.display = 'inline-flex';
    document.getElementById('btn-ev-guardar').textContent = 'Actualizar evento';
    document.getElementById('ev-nombre').focus();
  } catch(e) { toast('Error al cargar evento', 'err'); }
}

async function guardarEvento() {
  const nombre = document.getElementById('ev-nombre').value.trim();
  if (!nombre) { toast('El nombre oficial es obligatorio', 'err'); return; }

  const tagsRaw = document.getElementById('ev-tags').value;
  const tags    = tagsRaw.split(',').map(t => t.trim()).filter(Boolean);

  const payload = {
    nombre_oficial     : nombre,
    categoria          : document.getElementById('ev-cat').value,
    descripcion_general: document.getElementById('ev-desc').value.trim() || null,
    palabras_clave     : tags,
    activo             : document.getElementById('ev-activo').checked,
  };

  try {
    if (editandoEvId) {
      await apiFetch(`/api/eventos/${editandoEvId}`, { method:'PUT', body:JSON.stringify(payload) });
      toast('Evento actualizado', 'ok');
    } else {
      await apiFetch('/api/eventos', { method:'POST', body:JSON.stringify(payload) });
      toast('Evento creado', 'ok');
    }
    resetFormEvento();
    await cargarEventos();
  } catch(e) { toast('Error: ' + e.message, 'err'); }
}

function resetFormEvento() {
  editandoEvId = null;
  ['ev-nombre','ev-desc','ev-tags'].forEach(id => {
    const el = document.getElementById(id); if (el) el.value = '';
  });
  document.getElementById('ev-cat').value = CATEGORIAS[0];
  document.getElementById('ev-activo').checked = true;
  document.getElementById('form-ev-titulo').textContent = 'Nuevo evento';
  document.getElementById('btn-ev-cancelar').style.display = 'none';
  document.getElementById('btn-ev-guardar').textContent = 'Guardar evento';
}

// ── Modal eliminar evento ─────────────────────────────────
let _delEvId = null;

async function confirmarEliminarEvento(id, nombre) {
  _delEvId = id;
  try {
    const imp = await apiFetch(`/api/eventos/${id}/impacto`);
    document.getElementById('modal-del-ev-txt').innerHTML = `
      Estás a punto de eliminar el evento <strong>"${nombre}"</strong>.<br><br>
      ${imp.ediciones_afectadas > 0 || imp.recursos_afectados > 0 ? `
        <span style="color:var(--red)">⚠️ Esta acción también eliminará:</span><br>
        <ul style="margin:8px 0 0 16px;line-height:1.8">
          ${imp.ediciones_afectadas > 0
            ? `<li><strong>${imp.ediciones_afectadas} edición${imp.ediciones_afectadas>1?'es':''}</strong> asociadas a este evento</li>` : ''}
          ${imp.recursos_afectados > 0
            ? `<li><strong>${imp.recursos_afectados} recurso${imp.recursos_afectados>1?'s':''}</strong> quedarán sin edición asignada</li>` : ''}
        </ul>
      ` : 'Este evento no tiene ediciones ni recursos asociados.'}
      <br>Esta acción no se puede deshacer.
    `;
    document.getElementById('btn-del-ev-confirm').onclick = ejecutarEliminarEvento;
    document.getElementById('modal-del-ev').style.display = 'flex';
  } catch(e) { toast('Error al verificar impacto', 'err'); }
}

async function ejecutarEliminarEvento() {
  if (!_delEvId) return;
  try {
    await apiFetch(`/api/eventos/${_delEvId}`, { method: 'DELETE' });
    toast('Evento eliminado', 'ok');
    document.getElementById('modal-del-ev').style.display = 'none';
    if (eventoActivo?.id === _delEvId) {
      document.getElementById('panel-ediciones').style.display = 'none';
      eventoActivo = null;
    }
    await cargarEventos();
  } catch(e) { toast('Error: ' + e.message, 'err'); }
}

// ── Ediciones ─────────────────────────────────────────────
async function abrirPanelEdiciones(eventoId, nombre) {
  eventoActivo = { id: eventoId, nombre };
  document.getElementById('panel-ediciones').style.display = 'block';
  document.getElementById('ed-evento-nombre').textContent = nombre;
  resetFormEdicion();
  await cargarEdiciones();
}

async function cargarEdiciones() {
  if (!eventoActivo) return;
  const lista = document.getElementById('ed-lista');
  lista.innerHTML = `<p style="font-size:12px;color:var(--muted)">Cargando...</p>`;
  try {
    const d = await apiFetch(`/api/eventos/${eventoActivo.id}/ediciones`);
    if (!d.data.length) {
      lista.innerHTML = `<p style="font-size:12px;color:var(--muted);font-style:italic">Sin ediciones. Agrega la primera.</p>`;
      return;
    }

    const ESTADO_CLS = { Planificada:'b-crudo', 'En curso':'b-nuevo', Finalizada:'b-mock' };
    lista.innerHTML = d.data.map(ed => `
      <div style="border:1px solid var(--border);border-radius:6px;padding:10px 12px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center">
        <div>
          <span style="font-weight:700;font-size:13px">${ed.anio}</span>
          <span class="badge ${ESTADO_CLS[ed.estado]||'b-mock'}" style="margin-left:8px">${ed.estado}</span>
          ${ed.fecha_inicio ? `<span style="font-size:11px;color:var(--muted);margin-left:8px">${ed.fecha_inicio}${ed.fecha_fin?' → '+ed.fecha_fin:''}</span>` : ''}
        </div>
        <div style="display:flex;gap:6px">
          <button class="btn btn-ghost btn-sm" style="font-size:11px" data-id="${ed._id}" data-action="editar-ed">Editar</button>
          <button class="btn btn-danger-soft btn-sm" style="font-size:11px" data-id="${ed._id}" data-anio="${ed.anio}" data-action="eliminar-ed">Eliminar</button>
        </div>
      </div>
    `).join('');

    lista.querySelectorAll('[data-action="editar-ed"]').forEach(btn =>
      btn.addEventListener('click', () => cargarEdicionEdicion(btn.dataset.id))
    );
    lista.querySelectorAll('[data-action="eliminar-ed"]').forEach(btn =>
      btn.addEventListener('click', () => confirmarEliminarEdicion(btn.dataset.id, btn.dataset.anio))
    );
  } catch(e) {
    lista.innerHTML = `<p style="font-size:12px;color:var(--red)">Error: ${e.message}</p>`;
  }
}

async function cargarEdicionEdicion(id) {
  try {
    const d = await apiFetch(`/api/eventos/${eventoActivo.id}/ediciones`);
    const ed = d.data.find(e => e._id === id);
    if (!ed) return;
    editandoEdId = id;
    document.getElementById('form-ed-titulo').textContent = `Editar edición ${ed.anio}`;
    document.getElementById('ed-anio').value   = ed.anio;
    document.getElementById('ed-estado').value = ed.estado || 'Planificada';
    document.getElementById('ed-inicio').value = ed.fecha_inicio || '';
    document.getElementById('ed-fin').value    = ed.fecha_fin    || '';
    document.getElementById('btn-ed-cancelar').style.display = 'inline-flex';
    document.getElementById('btn-ed-guardar').textContent = 'Actualizar';
  } catch(e) { toast('Error al cargar edición', 'err'); }
}

async function guardarEdicion() {
  const anio = document.getElementById('ed-anio').value;
  if (!anio) { toast('El año es obligatorio', 'err'); return; }

  const payload = {
    anio        : parseInt(anio),
    estado      : document.getElementById('ed-estado').value,
    fecha_inicio: document.getElementById('ed-inicio').value || null,
    fecha_fin   : document.getElementById('ed-fin').value    || null,
  };

  try {
    if (editandoEdId) {
      await apiFetch(`/api/ediciones/${editandoEdId}`, { method:'PUT', body:JSON.stringify(payload) });
      toast('Edición actualizada', 'ok');
    } else {
      await apiFetch(`/api/eventos/${eventoActivo.id}/ediciones`, { method:'POST', body:JSON.stringify(payload) });
      toast('Edición creada', 'ok');
    }
    resetFormEdicion();
    await cargarEdiciones();
  } catch(e) { toast('Error: ' + e.message, 'err'); }
}

function resetFormEdicion() {
  editandoEdId = null;
  document.getElementById('ed-anio').value   = '';
  document.getElementById('ed-estado').value = 'Planificada';
  document.getElementById('ed-inicio').value = '';
  document.getElementById('ed-fin').value    = '';
  document.getElementById('form-ed-titulo').textContent = 'Nueva edición';
  document.getElementById('btn-ed-cancelar').style.display = 'none';
  document.getElementById('btn-ed-guardar').textContent = 'Guardar edición';
}

// ── Modal eliminar edición ────────────────────────────────
let _delEdId = null;

async function confirmarEliminarEdicion(id, anio) {
  _delEdId = id;
  try {
    const imp = await apiFetch(`/api/ediciones/${id}/impacto`);
    const n   = imp.recursos_afectados;
    document.getElementById('modal-del-ed-txt').innerHTML = `
      Estás a punto de eliminar la edición <strong>${anio}</strong>
      del evento <strong>"${eventoActivo?.nombre}"</strong>.<br><br>
      ${n > 0
        ? `<span style="color:var(--red)">⚠️ ${n} recurso${n>1?'s':''} tiene${n>1?'n':''} esta edición asignada.
           Al eliminarla, esos recursos quedarán sin edición asignada.</span>`
        : 'Esta edición no tiene recursos asociados. Se puede eliminar sin consecuencias.'}
      <br><br>Esta acción no se puede deshacer.
    `;
    document.getElementById('btn-del-ed-confirm').onclick = ejecutarEliminarEdicion;
    document.getElementById('modal-del-ed').style.display = 'flex';
  } catch(e) { toast('Error al verificar impacto', 'err'); }
}

async function ejecutarEliminarEdicion() {
  if (!_delEdId) return;
  try {
    await apiFetch(`/api/ediciones/${_delEdId}`, { method: 'DELETE' });
    toast('Edición eliminada', 'ok');
    document.getElementById('modal-del-ed').style.display = 'none';
    await cargarEdiciones();
  } catch(e) { toast('Error: ' + e.message, 'err'); }
}
