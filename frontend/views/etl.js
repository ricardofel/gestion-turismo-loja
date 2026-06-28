/**
 * views/etl.js — Vista de ingesta ETL con pipeline completo.
 * - 7 fuentes disponibles
 * - Búsqueda por tags real
 * - Solo muestra registros nuevos (deduplicación en backend)
 * - Modal de confirmación de lugares nuevos detectados
 */
import { apiFetch, badgePlat, toast } from '../components/badges.js';

let tagsActivos = [];
let datosETL    = [];
let lugaresNuevos = [];

export function render(container) {
  tagsActivos = []; datosETL = []; lugaresNuevos = [];

  container.innerHTML = `
    <div class="card">
      <div class="card-label">Configurar extraccion</div>
      <div class="etl-controls">
        <div class="fg">
          <label>Fuente de datos</label>
          <select class="select" id="etl-fuente" style="width:180px">
            <option value="TikTok">TikTok</option>
            <option value="YouTube">YouTube</option>
            <option value="Instagram">Instagram</option>
            <option value="TripAdvisor">TripAdvisor</option>
            <option value="Flickr">Flickr</option>
            <option value="Eventbrite">Eventbrite</option>
            <option value="GoogleReviews">Google Reviews</option>
          </select>
        </div>
        <div class="fg" style="flex:1;min-width:260px">
          <label>Tags de busqueda — escribe y presiona Enter</label>
          <div class="tag-area" id="tag-area">
            <input class="tag-input" id="tag-input"
              placeholder="ej: artes vivas, fiavl, loja, vilcabamba...">
          </div>
          <p style="font-size:11px;color:var(--muted);margin-top:4px">
            Los tags filtran los resultados de la fuente. Sin tags muestra todo.
          </p>
        </div>
        <div class="fg fg-actions">
          <label style="visibility:hidden">x</label>
          <button class="btn btn-primary" id="btn-extraer">Extraer datos</button>
        </div>
      </div>
    </div>

    <!-- Notificación de lugares nuevos -->
    <div id="lugares-alert" style="display:none" class="card" style="border-color:var(--gold)">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <div class="card-label" style="margin:0;color:var(--amber)">Lugares nuevos detectados</div>
          <p style="font-size:12px;color:var(--muted);margin-top:4px" id="lugares-alert-txt"></p>
        </div>
        <button class="btn btn-gold" id="btn-ver-lugares">Revisar y confirmar</button>
      </div>
    </div>

    <!-- Tabla de resultados -->
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
        <div>
          <span class="card-label" style="margin:0">Datos extraidos y procesados</span>
          <p style="font-size:11px;color:var(--muted);margin-top:2px">
            Solo se muestran registros nuevos. Los duplicados se filtran automaticamente.
          </p>
        </div>
        <div style="display:flex;gap:10px;align-items:center">
          <span id="etl-stats" style="font-size:12px;color:var(--muted)"></span>
          <button class="btn btn-gold" id="btn-guardar" disabled>
            Guardar en base de datos
          </button>
        </div>
      </div>
      <div class="tabla-wrap">
        <table>
          <thead><tr>
            <th>Fuente</th>
            <th>Autor</th>
            <th>Contenido</th>
            <th>Metricas</th>
            <th>Lugar detectado</th>
            <th>Edicion</th>
            <th style="text-align:center">Accion</th>
          </tr></thead>
          <tbody id="tbody-etl">
            <tr><td colspan="7">
              <div class="empty">
                <p>Selecciona una fuente, agrega tags y extrae datos.</p>
              </div>
            </td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal lugares nuevos -->
    <div id="modal-lugares" style="display:none;position:fixed;inset:0;background:rgba(0,20,60,.45);z-index:100;align-items:center;justify-content:center;padding:20px">
      <div class="modal" style="width:560px;max-height:80vh;overflow-y:auto">
        <div class="modal-title">Lugares nuevos detectados</div>
        <p style="font-size:13px;color:var(--muted);margin-bottom:16px">
          El sistema detecto los siguientes lugares en los datos extraidos que no existen
          en el catalogo. Selecciona cuales quieres agregar.
        </p>
        <div id="lugares-lista"></div>
        <div class="modal-footer">
          <button class="btn btn-ghost" id="btn-modal-lugares-cancel">Omitir todos</button>
          <button class="btn btn-primary" id="btn-modal-lugares-save">Agregar seleccionados</button>
        </div>
      </div>
    </div>
  `;

  // Tags
  const tagArea  = document.getElementById('tag-area');
  const tagInput = document.getElementById('tag-input');
  tagArea.addEventListener('click', () => tagInput.focus());
  tagInput.addEventListener('keydown', onTagKey);

  // Botones
  document.getElementById('btn-extraer').addEventListener('click', extraer);
  document.getElementById('btn-guardar').addEventListener('click', guardarTodos);
  document.getElementById('btn-ver-lugares').addEventListener('click', abrirModalLugares);
  document.getElementById('btn-modal-lugares-cancel').addEventListener('click', cerrarModalLugares);
  document.getElementById('btn-modal-lugares-save').addEventListener('click', confirmarLugares);
  document.getElementById('modal-lugares').addEventListener('click', e => {
    if (e.target === document.getElementById('modal-lugares')) cerrarModalLugares();
  });
}

// ── Tags ─────────────────────────────────────────────────
function onTagKey(e) {
  if (e.key !== 'Enter' && e.key !== ',') return;
  e.preventDefault();
  const val = e.target.value.trim().replace(/,$/, '');
  if (!val || tagsActivos.includes(val)) { e.target.value = ''; return; }
  tagsActivos.push(val);
  e.target.value = '';
  renderTags();
}

function renderTags() {
  const area  = document.getElementById('tag-area');
  const input = document.getElementById('tag-input');
  area.querySelectorAll('.tag-chip').forEach(c => c.remove());
  tagsActivos.forEach(t => {
    const chip = document.createElement('div');
    chip.className = 'tag-chip';
    chip.innerHTML = `<span>${t}</span><button type="button">×</button>`;
    chip.querySelector('button').addEventListener('click', () => {
      tagsActivos = tagsActivos.filter(x => x !== t);
      renderTags();
    });
    area.insertBefore(chip, input);
  });
}

// ── Extracción ────────────────────────────────────────────
async function extraer() {
  const fuente = document.getElementById('etl-fuente').value;
  const tags   = tagsActivos.join(',') || '';
  const btn    = document.getElementById('btn-extraer');
  const tbody  = document.getElementById('tbody-etl');

  btn.disabled  = true;
  btn.innerHTML = '<span class="spin"></span> Extrayendo y procesando...';
  tbody.innerHTML = `<tr><td colspan="7"><div class="empty">
    <p>Extrayendo datos y ejecutando pipeline ETL...</p>
  </div></td></tr>`;
  document.getElementById('lugares-alert').style.display = 'none';

  try {
    const url = `/api/etl/extraer?fuente=${fuente}&tags=${encodeURIComponent(tags)}`;
    const d   = await apiFetch(url);

    datosETL      = (d.data || []).map((item, i) => ({ ...item, _idx: i }));
    lugaresNuevos = d.lugares_nuevos || [];

    // Stats
    const stats = document.getElementById('etl-stats');
    if (stats) {
      stats.innerHTML = `
        <span>${d.total_extraidos} extraidos</span> ·
        <span style="color:var(--green);font-weight:700">${d.nuevos} nuevos</span> ·
        <span style="color:var(--muted)">${d.duplicados} ya existian (filtrados)</span>
      `;
    }

    // Alerta de lugares nuevos
    if (lugaresNuevos.length > 0) {
      document.getElementById('lugares-alert').style.display = 'block';
      document.getElementById('lugares-alert-txt').textContent =
        `Se detectaron ${lugaresNuevos.length} lugar${lugaresNuevos.length > 1 ? 'es' : ''} que no estan en el catalogo. Puedes agregarlos ahora.`;
    }

    renderTabla();
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="empty">
      <p style="color:var(--red)">Error: ${e.message}</p>
    </div></td></tr>`;
  } finally {
    btn.disabled  = false;
    btn.innerHTML = 'Extraer datos';
  }
}

function renderTabla() {
  const tbody = document.getElementById('tbody-etl');
  if (!tbody) return;

  // Actualizar botón guardar
  const btn = document.getElementById('btn-guardar');
  if (btn) {
    btn.disabled    = datosETL.length === 0;
    btn.textContent = datosETL.length > 0
      ? `Guardar ${datosETL.length} registro${datosETL.length > 1 ? 's' : ''} en base de datos`
      : 'Guardar en base de datos';
  }

  if (!datosETL.length) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="empty">
      <p>${tagsActivos.length > 0
        ? 'Sin resultados nuevos para los tags ingresados. Prueba con otros tags.'
        : 'Sin resultados nuevos. Todos los registros ya existen en la base de datos.'}</p>
    </div></td></tr>`;
    return;
  }

  tbody.innerHTML = datosETL.map(item => {
    const meta   = item.metadata || {};
    const autor  = meta.autor?.name || '—';
    const texto  = (meta.texto_original || '—').slice(0, 80);
    const plays  = meta.metricas?.plays != null
      ? Number(meta.metricas.plays).toLocaleString()
      : meta.metricas?.likes != null
        ? `${Number(meta.metricas.likes).toLocaleString()} likes`
        : '—';

    // Lugar detectado
    const lugarNuevo = item._lugar_nuevo_sugerido;
    const lugarId    = item.lugar_id;
    let lugarHtml = '—';
    if (lugarId) {
      lugarHtml = `<span class="badge b-clasificado">Detectado</span>`;
    } else if (lugarNuevo) {
      lugarHtml = `<span class="badge b-crudo" title="${lugarNuevo}">Nuevo: ${lugarNuevo.slice(0,20)}${lugarNuevo.length>20?'...':''}</span>`;
    }

    // Edición detectada
    const edicionHtml = item.edicion_id
      ? `<span class="badge b-clasificado">Asignada</span>`
      : `<span style="font-size:11px;color:var(--muted)">—</span>`;

    return `
      <tr id="etl-row-${item._idx}">
        <td>${badgePlat(item.origen.plataforma)}</td>
        <td style="font-weight:600;white-space:nowrap">${autor}</td>
        <td style="max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--muted)"
            title="${(meta.texto_original||'').replace(/"/g,'&quot;')}">${texto}</td>
        <td style="white-space:nowrap;font-size:12px">${plays}</td>
        <td>${lugarHtml}</td>
        <td>${edicionHtml}</td>
        <td style="text-align:center">
          <button class="btn btn-danger-soft btn-sm" data-idx="${item._idx}">Quitar</button>
        </td>
      </tr>`;
  }).join('');

  // Eventos de quitar
  tbody.querySelectorAll('[data-idx]').forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = parseInt(btn.dataset.idx);
      datosETL  = datosETL.filter(r => r._idx !== idx);
      renderTabla();
    });
  });
}

// ── Modal lugares nuevos ──────────────────────────────────
function abrirModalLugares() {
  const lista = document.getElementById('lugares-lista');
  lista.innerHTML = lugaresNuevos.map((l, i) => `
    <div style="border:1px solid var(--border);border-radius:6px;padding:14px;margin-bottom:10px">
      <div style="display:flex;gap:10px;align-items:flex-start">
        <input type="checkbox" id="lugar-chk-${i}" checked
          style="margin-top:3px;width:16px;height:16px;accent-color:var(--navy);flex-shrink:0">
        <div style="flex:1">
          <div style="font-weight:600;font-size:13px;margin-bottom:8px">${l.nombre}</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
            <div class="form-row" style="margin:0">
              <label style="font-size:10px">Nombre</label>
              <input class="input" id="lugar-nombre-${i}" value="${l.nombre}" style="font-size:12px;padding:6px 9px">
            </div>
            <div class="form-row" style="margin:0">
              <label style="font-size:10px">Tipo de lugar</label>
              <select class="input" id="lugar-tipo-${i}" style="font-size:12px;padding:6px 9px">
                <option value="Por clasificar" ${l.tipo_lugar==='Por clasificar'?'selected':''}>Por clasificar</option>
                <option value="Teatro">Teatro</option>
                <option value="Santuario">Santuario</option>
                <option value="Plaza Pública">Plaza Pública</option>
                <option value="Iglesia">Iglesia</option>
                <option value="Museo">Museo</option>
                <option value="Área Natural">Área Natural</option>
                <option value="Monumento">Monumento</option>
                <option value="Centro Cultural">Centro Cultural</option>
                <option value="Mercado">Mercado</option>
                <option value="Valle">Valle</option>
                <option value="Festival">Festival</option>
                <option value="Ciudad">Ciudad</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  `).join('');

  document.getElementById('modal-lugares').style.display = 'flex';
}

function cerrarModalLugares() {
  document.getElementById('modal-lugares').style.display = 'none';
}

async function confirmarLugares() {
  const seleccionados = lugaresNuevos
    .map((l, i) => {
      const chk = document.getElementById(`lugar-chk-${i}`);
      if (!chk?.checked) return null;
      return {
        nombre         : document.getElementById(`lugar-nombre-${i}`)?.value || l.nombre,
        tipo_lugar     : document.getElementById(`lugar-tipo-${i}`)?.value   || l.tipo_lugar,
        direccion_texto: l.direccion_texto,
        coordenadas_geo: l.coordenadas_geo || null,
      };
    })
    .filter(Boolean);

  if (!seleccionados.length) {
    cerrarModalLugares();
    return;
  }

  try {
    const d = await apiFetch('/api/etl/lugares/confirmar', {
      method: 'POST', body: JSON.stringify(seleccionados)
    });
    if (d.exito) {
      toast(`${d.insertados} lugar${d.insertados !== 1 ? 'es' : ''} agregado${d.insertados !== 1 ? 's' : ''} al catalogo`, 'ok');
      cerrarModalLugares();
      document.getElementById('lugares-alert').style.display = 'none';
    }
  } catch (e) {
    toast('Error al guardar lugares: ' + e.message, 'err');
  }
}

// ── Guardar recursos ──────────────────────────────────────
async function guardarTodos() {
  const payload = datosETL.map(r => {
    const item = { ...r };
    delete item._idx;
    delete item._lugar_nuevo_sugerido;
    return item;
  });

  if (!payload.length) return;

  const btn = document.getElementById('btn-guardar');
  btn.disabled  = true;
  btn.innerHTML = '<span class="spin"></span> Guardando...';

  try {
    const d = await apiFetch('/api/recursos/bulk', {
      method: 'POST', body: JSON.stringify(payload)
    });
    if (d.exito) {
      toast(`${d.insertados} insertados · ${d.actualizados} actualizados`, 'ok');
      datosETL = [];
      renderTabla();
    }
  } catch (e) {
    toast('Error al guardar: ' + e.message, 'err');
  } finally {
    btn.innerHTML = 'Guardar en base de datos';
  }
}
