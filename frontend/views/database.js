/**
 * views/database.js
 */
import { apiFetch, badgePlat, badgeEstado, renderMetricas, toast } from '../components/badges.js';
import { crearAutocomplete }    from '../components/autocomplete.js';
import { crearDateRangePicker } from '../components/datepicker.js';

const DB_LIMIT = 20;
let dbPage = 0;
let filtro = {};
let acEventoCtrl, acEdicionCtrl, acLugarCtrl, acPlatCtrl, dpFechaCtrl;
let _editId         = null;
let _modalLugarId   = null;
let _modalEdicionId = null;
let _catLugares     = [];
let _catEdiciones   = [];
let _catEventos     = [];

const PLATAFORMAS_CAT = [
  { id: 'TikTok',        nombre: 'TikTok' },
  { id: 'YouTube',       nombre: 'YouTube' },
  { id: 'GoogleReviews', nombre: 'Google Reviews' },
];

export async function render(container, { catEventos, catEdiciones, catLugares }) {
  dbPage = 0; filtro = {};
  _catLugares   = catLugares;
  _catEdiciones = catEdiciones;
  _catEventos   = catEventos;

  container.innerHTML = `
    <div class="card">
      <div class="card-label">Filtros</div>
      <div class="filtros-grid">
        <div class="fg"><label>Evento</label><div id="ac-evento"></div></div>
        <div class="fg">
          <label>Edicion</label>
          <div id="ac-edicion-wrap">
            <div class="ac-bloqueado">Selecciona primero un evento</div>
          </div>
        </div>
        <div class="fg"><label>Lugar</label><div id="ac-lugar"></div></div>
        <div class="fg"><label>Plataforma</label><div id="ac-plat"></div></div>
        <div class="fg"><label>Rango de fechas</label><div id="dp-fecha"></div></div>
        <div class="fg fg-actions">
          <label style="visibility:hidden">x</label>
          <div style="display:flex;gap:8px">
            <button class="btn btn-primary" id="btn-aplicar">Aplicar filtros</button>
            <button class="btn btn-ghost"   id="btn-limpiar">Limpiar</button>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
        <span class="card-label" style="margin:0">Inventario de recursos</span>
        <span id="db-total" style="font-size:12px;color:var(--muted)"></span>
      </div>
      <div id="lista-db"></div>
      <div class="pag" id="pag-ctrl" style="display:none">
        <button class="btn btn-ghost btn-sm" id="pag-prev">Anterior</button>
        <span id="pag-info" style="font-size:12px;color:var(--muted)"></span>
        <button class="btn btn-ghost btn-sm" id="pag-next">Siguiente</button>
      </div>
    </div>

    <!-- Modal edición -->
    <div id="db-modal" style="display:none;position:fixed;inset:0;background:rgba(0,20,60,.45);z-index:100;align-items:center;justify-content:center;overflow-y:auto;padding:20px">
      <div class="modal" style="width:520px;max-width:95vw">
        <div class="modal-title">Editar recurso</div>

        <!-- Info del recurso (solo lectura) -->
        <div id="m-info" style="background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:12px 14px;margin-bottom:16px;font-size:12px;line-height:1.7"></div>

        <div style="border-top:1px solid var(--border);margin-bottom:16px;padding-top:16px">
          <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);margin-bottom:12px">Campos editables</div>

          <div class="form-row">
            <label>Estado de procesamiento</label>
            <select class="input" id="m-estado">
              <option value="Crudo">Crudo — datos sin revisar</option>
              <option value="Clasificado">Clasificado — revisado y aprobado</option>
              <option value="Error">Error — datos incorrectos o no válidos</option>
            </select>
          </div>

          <div class="form-row">
            <label>Asignar lugar <span style="font-weight:400;opacity:.6">(opcional)</span></label>
            <div id="m-lugar-ac"></div>
          </div>

          <div class="form-row">
            <label>Asignar edicion <span style="font-weight:400;opacity:.6">(opcional)</span></label>
            <div id="m-edicion-ac"></div>
            <p style="font-size:11px;color:var(--muted);margin-top:4px">Año de celebración del evento al que pertenece este contenido.</p>
          </div>

          <div class="form-row">
            <label>Notas internas <span style="font-weight:400;opacity:.6">(opcional)</span></label>
            <textarea class="input" id="m-notas" rows="2" placeholder="Ej: Video destacado del festival, pendiente de verificar..."></textarea>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-ghost"   id="btn-modal-cancel">Cancelar</button>
          <button class="btn btn-primary" id="btn-modal-save">Guardar cambios</button>
        </div>
      </div>
    </div>
  `;

  // Autocompletes filtros
  acEventoCtrl = crearAutocomplete('ac-evento', 'Buscar evento...', catEventos,
    c => { filtro.evento_id = c.id; cargarEdicionesDeEvento(c.id); },
    ()=> { delete filtro.evento_id; delete filtro.edicion_id; acEdicionCtrl = null;
           document.getElementById('ac-edicion-wrap').innerHTML = `<div class="ac-bloqueado">Selecciona primero un evento</div>`; }
  );

  acLugarCtrl = crearAutocomplete('ac-lugar', 'Buscar lugar...', catLugares,
    c => { filtro.lugar_id = c.id; }, ()=> { delete filtro.lugar_id; }
  );

  acPlatCtrl = crearAutocomplete('ac-plat', 'Buscar plataforma...', PLATAFORMAS_CAT,
    c => { filtro.plataforma = c.id; }, ()=> { delete filtro.plataforma; }
  );

  dpFechaCtrl = crearDateRangePicker('dp-fecha',
    (d, h) => { filtro.fecha_desde = d; filtro.fecha_hasta = h; },
    ()     => { delete filtro.fecha_desde; delete filtro.fecha_hasta; }
  );

  document.getElementById('btn-aplicar').addEventListener('click', () => { dbPage = 0; cargarRecursos(); });
  document.getElementById('btn-limpiar').addEventListener('click', limpiarFiltros);
  document.getElementById('pag-prev').addEventListener('click', () => { dbPage--; cargarRecursos(true); });
  document.getElementById('pag-next').addEventListener('click', () => { dbPage++; cargarRecursos(true); });
  document.getElementById('btn-modal-cancel').addEventListener('click', cerrarModal);
  document.getElementById('btn-modal-save').addEventListener('click', guardarEdicion);
  document.getElementById('db-modal').addEventListener('click', e => {
    if (e.target === document.getElementById('db-modal')) cerrarModal();
  });

  await cargarRecursos();
}

// ── Ediciones por evento ──────────────────────────────────
async function cargarEdicionesDeEvento(eventoId) {
  const wrap = document.getElementById('ac-edicion-wrap');
  if (!wrap) return;
  wrap.innerHTML = `<div class="ac-bloqueado">Cargando...</div>`;
  try {
    const d = await apiFetch('/api/ediciones');
    const lista = (d.data || [])
      .filter(e => String(e.evento_id) === String(eventoId))
      .map(e => ({ id: e._id, nombre: `${e.anio} — ${e.estado || ''}` }));
    if (!lista.length) {
      wrap.innerHTML = `<div class="ac-bloqueado">Sin ediciones para este evento</div>`; return;
    }
    wrap.innerHTML = `<div id="ac-edicion"></div>`;
    acEdicionCtrl = crearAutocomplete('ac-edicion', 'Buscar edicion...', lista,
      c => { filtro.edicion_id = c.id; }, ()=> { delete filtro.edicion_id; }
    );
  } catch {
    wrap.innerHTML = `<div class="ac-bloqueado" style="color:var(--red)">Error al cargar ediciones</div>`;
  }
}

function limpiarFiltros() {
  filtro = {};
  acEventoCtrl?.reset(); acLugarCtrl?.reset(); acPlatCtrl?.reset(); dpFechaCtrl?.reset();
  acEdicionCtrl = null;
  const wrap = document.getElementById('ac-edicion-wrap');
  if (wrap) wrap.innerHTML = `<div class="ac-bloqueado">Selecciona primero un evento</div>`;
  dbPage = 0; cargarRecursos();
}

// ── Carga de recursos ─────────────────────────────────────
async function cargarRecursos(scroll = false) {
  const lista = document.getElementById('lista-db');
  if (!lista) return;
  lista.innerHTML = `<div class="empty"><p>Cargando...</p></div>`;

  const p = new URLSearchParams();
  if (filtro.plataforma)  p.set('plataforma',  filtro.plataforma);
  if (filtro.estado)      p.set('estado',      filtro.estado);
  if (filtro.lugar_id)    p.set('lugar_id',    filtro.lugar_id);
  if (filtro.edicion_id)  p.set('edicion_id',  filtro.edicion_id);
  if (filtro.evento_id)   p.set('evento_id',   filtro.evento_id);
  if (filtro.fecha_desde) p.set('fecha_desde', filtro.fecha_desde);
  if (filtro.fecha_hasta) p.set('fecha_hasta', filtro.fecha_hasta);
  p.set('skip', dbPage * DB_LIMIT);
  p.set('limit', DB_LIMIT);

  try {
    const d     = await apiFetch('/api/recursos?' + p);
    const total = d.total || 0;
    document.getElementById('db-total').textContent = `${total.toLocaleString()} registro${total !== 1 ? 's' : ''}`;

    if (!d.data?.length) {
      lista.innerHTML = `<div class="empty"><p>Sin resultados para los filtros aplicados.</p></div>`;
      document.getElementById('pag-ctrl').style.display = 'none'; return;
    }

    lista.innerHTML = d.data.map(r => renderCard(r)).join('');
    lista.querySelectorAll('[data-action="editar"]').forEach(btn => {
      btn.addEventListener('click', () => abrirModal(btn.dataset.id));
    });
    lista.querySelectorAll('[data-action="eliminar"]').forEach(btn => {
      btn.addEventListener('click', () => eliminar(btn.dataset.id));
    });

    const totalPags = Math.ceil(total / DB_LIMIT);
    const pagCtrl   = document.getElementById('pag-ctrl');
    if (totalPags > 1) {
      pagCtrl.style.display = 'flex';
      document.getElementById('pag-info').textContent = `Página ${dbPage + 1} de ${totalPags}`;
      document.getElementById('pag-prev').disabled = dbPage === 0;
      document.getElementById('pag-next').disabled = dbPage >= totalPags - 1;
    } else {
      pagCtrl.style.display = 'none';
    }
    if (scroll) lista.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (e) {
    lista.innerHTML = `<div class="empty"><p style="color:var(--red)">Error: ${e.message}</p></div>`;
  }
}

function renderCard(r) {
  const meta    = r.metadata || {};
  const autor   = meta.autor?.name || '—';
  const texto   = (meta.texto_original || '').slice(0, 130) || '(sin texto)';
  const fecha   = (r.origen?.fecha_ingesta || '').slice(0, 10);
  const metHtml = renderMetricas(meta.metricas || {});
  return `
    <div class="rec-card">
      <div class="rec-main">
        <div class="rec-titulo">${texto}${(meta.texto_original?.length||0)>130?'...':''}</div>
        <div class="rec-autor">Por <strong>${autor}</strong></div>
        <div class="rec-meta">
          ${badgePlat(r.origen?.plataforma)}
          ${badgeEstado(r.estado_procesamiento)}
          ${fecha?`<span class="met-item"><span class="met-label">Ingesta</span>${fecha}</span>`:''}
          ${r.fecha_publicacion?`<span class="met-item"><span class="met-label">Publicado</span>${r.fecha_publicacion}</span>`:''}
          ${metHtml}
        </div>
      </div>
      <div class="rec-actions">
        <button class="btn btn-ghost btn-sm" data-action="editar" data-id="${r._id}">Editar</button>
        <button class="btn btn-danger-soft btn-sm" data-action="eliminar" data-id="${r._id}">Eliminar</button>
      </div>
    </div>`;
}

// ── Modal enriquecido ─────────────────────────────────────
async function abrirModal(id) {
  _editId = id;
  _modalLugarId = null; _modalEdicionId = null;

  // Cargar el recurso completo del servidor
  const infoEl = document.getElementById('m-info');
  infoEl.innerHTML = `<span style="color:var(--muted)">Cargando información...</span>`;
  document.getElementById('db-modal').style.display = 'flex';

  try {
    const d = await apiFetch(`/api/recursos/${id}`);
    const r = d.data;
    const meta = r.metadata || {};

    // Buscar nombre del evento/edición en los catálogos
    const edicionId  = r.edicion_id || '';
    const edicionObj = _catEdiciones.find(e => e.id === edicionId);
    const lugarId    = r.lugar_id   || '';
    const lugarObj   = _catLugares.find(l => l.id === lugarId);

    // Panel de info de solo lectura
    const metricas = meta.metricas || {};
    const metItems = Object.entries(metricas)
      .filter(([,v]) => v != null)
      .map(([k,v]) => `<span><strong>${k}:</strong> ${Number(v).toLocaleString()}</span>`)
      .join(' &nbsp;·&nbsp; ');

    infoEl.innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 16px">
        <div><span style="color:var(--muted)">Plataforma:</span> ${badgePlat(r.origen?.plataforma)}</div>
        <div><span style="color:var(--muted)">Estado actual:</span> ${badgeEstado(r.estado_procesamiento)}</div>
        <div><span style="color:var(--muted)">Autor:</span> <strong>${meta.autor?.name || '—'}</strong></div>
        <div><span style="color:var(--muted)">Fecha publicacion:</span> ${r.fecha_publicacion || '—'}</div>
        <div><span style="color:var(--muted)">Lugar asignado:</span> ${lugarObj?.nombre || '<em>Sin asignar</em>'}</div>
        <div><span style="color:var(--muted)">Edicion asignada:</span> ${edicionObj?.nombre || '<em>Sin asignar</em>'}</div>
        ${metItems ? `<div colspan="2" style="grid-column:1/-1"><span style="color:var(--muted)">Metricas:</span> ${metItems}</div>` : ''}
      </div>
      ${meta.texto_original ? `
        <div style="margin-top:8px;padding-top:8px;border-top:1px solid var(--border);font-style:italic;color:var(--muted);font-size:12px">
          "${meta.texto_original.slice(0,180)}${meta.texto_original.length>180?'...':''}"
        </div>` : ''}
    `;

    // Pre-seleccionar estado
    document.getElementById('m-estado').value = r.estado_procesamiento || 'Crudo';
    document.getElementById('m-notas').value  = r.notas_internas || '';

    // Autocomplete de lugares
    document.getElementById('m-lugar-ac').innerHTML = `<div id="m-lugar-ac-i"></div>`;
    crearAutocomplete('m-lugar-ac-i', lugarObj?.nombre || 'Buscar lugar...', _catLugares,
      c => { _modalLugarId = c.id; },
      ()=> { _modalLugarId = null; }
    );

    // Autocomplete de ediciones (todas, con año y estado)
    const todasEdiciones = _catEdiciones.map(e => ({ id: e.id, nombre: e.nombre }));
    document.getElementById('m-edicion-ac').innerHTML = `<div id="m-edicion-ac-i"></div>`;
    crearAutocomplete('m-edicion-ac-i', edicionObj?.nombre || 'Buscar edicion por año...', todasEdiciones,
      c => { _modalEdicionId = c.id; },
      ()=> { _modalEdicionId = null; }
    );

    // Mantener valores actuales si ya estaban asignados
    if (lugarId)   _modalLugarId   = lugarId;
    if (edicionId) _modalEdicionId = edicionId;

  } catch (e) {
    infoEl.innerHTML = `<span style="color:var(--red)">Error al cargar: ${e.message}</span>`;
  }
}

function cerrarModal() {
  document.getElementById('db-modal').style.display = 'none';
  _editId = null; _modalLugarId = null; _modalEdicionId = null;
}

async function guardarEdicion() {
  if (!_editId) return;
  const cambios = {
    estado_procesamiento: document.getElementById('m-estado').value,
    lugar_id   : _modalLugarId   || null,
    edicion_id : _modalEdicionId || null,
  };
  const notas = document.getElementById('m-notas').value.trim();
  if (notas) cambios.notas_internas = notas;

  try {
    const d = await apiFetch(`/api/recursos/${_editId}`, {
      method: 'PUT', body: JSON.stringify(cambios)
    });
    if (d.exito) { toast('Recurso actualizado', 'ok'); cerrarModal(); cargarRecursos(); }
  } catch (e) { toast('Error: ' + e.message, 'err'); }
}

async function eliminar(id) {
  if (!confirm('¿Eliminar este recurso de la base de datos?')) return;
  try {
    const d = await apiFetch(`/api/recursos/${id}`, { method: 'DELETE' });
    if (d.exito) { toast('Eliminado', 'ok'); cargarRecursos(); }
  } catch (e) { toast('Error: ' + e.message, 'err'); }
}
