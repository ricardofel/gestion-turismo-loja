/**
 * views/lugares.js — CRUD completo de Lugares.
 */
import { apiFetch, toast } from '../components/badges.js';
import { buscarSimilares } from '../components/similitud.js';
import { confirmarModal } from '../components/confirm-modal.js';

const TIPOS_LUGAR = [
  "Teatro", "Santuario", "Iglesia", "Plaza Pública", "Museo",
  "Área Natural", "Monumento", "Centro Cultural", "Mercado",
  "Valle", "Festival", "Ciudad", "Zona Histórica", "Por clasificar"
];

export async function render(container) {
  container.innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 380px;gap:18px;align-items:start">

      <!-- Lista de lugares -->
      <div>
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
            <span class="card-label" style="margin:0">Lugares registrados</span>
            <span id="lug-total" style="font-size:12px;color:var(--muted)"></span>
          </div>
          <div id="lug-lista"></div>
        </div>
      </div>

      <!-- Formulario -->
      <div class="card" style="position:sticky;top:80px">
        <div class="card-label" id="form-lug-titulo">Nuevo lugar</div>

        <div class="form-row">
          <label>Nombre <span style="color:var(--red)">*</span></label>
          <input class="input" id="lug-nombre" placeholder="ej: Teatro Benjamín Carrión">
        </div>
        <div class="form-row">
          <label>Tipo de lugar</label>
          <select class="input" id="lug-tipo">
            ${TIPOS_LUGAR.map(t => `<option value="${t}">${t}</option>`).join('')}
          </select>
        </div>
        <div class="form-row">
          <label>Dirección</label>
          <input class="input" id="lug-dir" placeholder="ej: Av. Salvador Bustamante Celi, Loja">
        </div>

        <!-- Coordenadas -->
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:12px;margin-bottom:13px">
          <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;color:var(--muted);margin-bottom:8px">
            Coordenadas <span style="font-weight:400;opacity:.7">(opcionales)</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px">
            <div>
              <label style="font-size:11px;color:var(--muted);display:block;margin-bottom:3px">Latitud</label>
              <input class="input" id="lug-lat" placeholder="-3.9931" type="number" step="any">
            </div>
            <div>
              <label style="font-size:11px;color:var(--muted);display:block;margin-bottom:3px">Longitud</label>
              <input class="input" id="lug-lon" placeholder="-79.2042" type="number" step="any">
            </div>
          </div>
          <p style="font-size:11px;color:var(--muted);line-height:1.5">
            Para obtener las coordenadas: abre
            <a href="https://maps.google.com" target="_blank" style="color:var(--navy)">Google Maps</a>,
            haz click derecho sobre el lugar y copia los números que aparecen
            (el primero es latitud, el segundo longitud).
          </p>
        </div>

        <div style="display:flex;gap:8px">
          <button class="btn btn-primary" style="flex:1" id="btn-lug-guardar">Guardar lugar</button>
          <button class="btn btn-ghost" id="btn-lug-cancelar" style="display:none">Cancelar</button>
        </div>
      </div>
    </div>

    <!-- Modal eliminar -->
    <div id="modal-del-lug" style="display:none;position:fixed;inset:0;background:rgba(0,20,60,.45);z-index:100;align-items:center;justify-content:center">
      <div class="modal" style="max-width:420px">
        <div class="modal-title" style="color:var(--red)">Eliminar lugar</div>
        <p id="modal-del-lug-txt" style="font-size:13px;color:var(--text);line-height:1.6;margin-bottom:16px"></p>
        <div class="modal-footer">
          <button class="btn btn-ghost" onclick="cerrarModalLug()">Cancelar</button>
          <button class="btn" id="btn-del-lug-confirm"
            style="background:var(--red);color:#fff">Sí, eliminar</button>
        </div>
      </div>
    </div>
  `;

  document.getElementById('btn-lug-guardar').addEventListener('click', guardarLugar);
  document.getElementById('btn-lug-cancelar').addEventListener('click', resetForm);
  document.getElementById('modal-del-lug').addEventListener('click', e => {
    if (e.target === document.getElementById('modal-del-lug')) cerrarModalLug();
  });

  await cargarLugares();
}

let editandoId = null;

async function cargarLugares() {
  const lista = document.getElementById('lug-lista');
  lista.innerHTML = `<div class="empty"><p>Cargando...</p></div>`;
  try {
    const d = await apiFetch('/api/lugares');
    document.getElementById('lug-total').textContent = `${d.total} registrados`;
    if (!d.data.length) {
      lista.innerHTML = `<div class="empty"><p>No hay lugares. Agrega el primero.</p></div>`;
      return;
    }
    lista.innerHTML = d.data.map(l => `
      <div class="rec-card" style="grid-template-columns:1fr auto">
        <div class="rec-main">
          <div class="rec-titulo">${l.nombre}</div>
          <div class="rec-meta" style="margin-top:4px">
            <span class="badge b-mock">${l.tipo_lugar || 'Sin tipo'}</span>
            ${l.direccion_texto
              ? `<span style="font-size:11px;color:var(--muted)">${l.direccion_texto}</span>`
              : ''}
            ${l.coordenadas_geo?.coordinates
              ? `<span style="font-size:11px;color:var(--muted)">
                  📍 ${l.coordenadas_geo.coordinates[1]}, ${l.coordenadas_geo.coordinates[0]}
                </span>`
              : `<span style="font-size:11px;color:#ccc;font-style:italic">Sin coordenadas</span>`}
          </div>
        </div>
        <div class="rec-actions">
          <button class="btn btn-ghost btn-sm" data-id="${l._id}" data-action="editar-lug">Editar</button>
          <button class="btn btn-danger-soft btn-sm" data-id="${l._id}" data-nombre="${l.nombre}" data-action="eliminar-lug">Eliminar</button>
        </div>
      </div>
    `).join('');

    lista.querySelectorAll('[data-action="editar-lug"]').forEach(btn =>
      btn.addEventListener('click', () => cargarEdicion(btn.dataset.id))
    );
    lista.querySelectorAll('[data-action="eliminar-lug"]').forEach(btn =>
      btn.addEventListener('click', () => confirmarEliminar(btn.dataset.id, btn.dataset.nombre))
    );
  } catch (e) {
    lista.innerHTML = `<div class="empty"><p style="color:var(--red)">Error: ${e.message}</p></div>`;
  }
}

async function cargarEdicion(id) {
  try {
    const d = await apiFetch('/api/lugares');
    const lugar = d.data.find(l => l._id === id);
    if (!lugar) return;
    editandoId = id;
    document.getElementById('form-lug-titulo').textContent = 'Editar lugar';
    document.getElementById('lug-nombre').value = lugar.nombre || '';
    document.getElementById('lug-tipo').value   = lugar.tipo_lugar || TIPOS_LUGAR[0];
    document.getElementById('lug-dir').value    = lugar.direccion_texto || '';
    const coords = lugar.coordenadas_geo?.coordinates;
    document.getElementById('lug-lat').value = coords ? coords[1] : '';
    document.getElementById('lug-lon').value = coords ? coords[0] : '';
    document.getElementById('btn-lug-cancelar').style.display = 'inline-flex';
    document.getElementById('btn-lug-guardar').textContent = 'Actualizar lugar';
    document.getElementById('lug-nombre').focus();
  } catch(e) { toast('Error al cargar lugar: ' + e.message, 'err'); }
}

async function guardarLugar() {
  const nombre = document.getElementById('lug-nombre').value.trim();
  if (!nombre) { toast('El nombre es obligatorio', 'err'); return; }

  try {
    const d = await apiFetch('/api/lugares');
    const similares = buscarSimilares(nombre, d.data, { excluirId: editandoId });
    if (similares.length) {
      const top = similares[0].item;
      const continuar = await confirmarModal({
        titulo         : 'Posible lugar duplicado',
        mensaje        : `Ya existe un lugar con un nombre muy parecido:\n"${top.nombre}" (${top.tipo_lugar || 'sin tipo'})\n\n¿Guardar "${nombre}" de todas formas?`,
        textoConfirmar : 'Guardar de todas formas',
      });
      if (!continuar) return;
    }
  } catch (e) {
    // Si falla la verificación no bloqueamos el guardado, pero lo dejamos
    // visible en consola para poder diagnosticarlo.
    console.warn('No se pudo verificar lugares parecidos:', e);
  }

  const payload = {
    nombre,
    tipo_lugar      : document.getElementById('lug-tipo').value,
    direccion_texto : document.getElementById('lug-dir').value.trim() || null,
    lat             : document.getElementById('lug-lat').value || null,
    lon             : document.getElementById('lug-lon').value || null,
  };

  try {
    if (editandoId) {
      await apiFetch(`/api/lugares/${editandoId}`, { method: 'PUT', body: JSON.stringify(payload) });
      toast('Lugar actualizado', 'ok');
    } else {
      await apiFetch('/api/lugares', { method: 'POST', body: JSON.stringify(payload) });
      toast('Lugar creado', 'ok');
    }
    resetForm();
    await cargarLugares();
  } catch (e) { toast('Error: ' + e.message, 'err'); }
}

function resetForm() {
  editandoId = null;
  ['lug-nombre','lug-dir','lug-lat','lug-lon'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  document.getElementById('lug-tipo').value = TIPOS_LUGAR[0];
  document.getElementById('form-lug-titulo').textContent = 'Nuevo lugar';
  document.getElementById('btn-lug-cancelar').style.display = 'none';
  document.getElementById('btn-lug-guardar').textContent = 'Guardar lugar';
}

let _delLugId = null;

async function confirmarEliminar(id, nombre) {
  _delLugId = id;
  try {
    const imp = await apiFetch(`/api/lugares/${id}/impacto`);
    const n   = imp.recursos_afectados;
    document.getElementById('modal-del-lug-txt').innerHTML = `
      Estás a punto de eliminar el lugar <strong>"${nombre}"</strong>.<br><br>
      ${n > 0
        ? `<span style="color:var(--red)">⚠️ ${n} recurso${n>1?'s':''} tiene${n>1?'n':''} este lugar asignado.
           Al eliminarlo, esos recursos quedarán sin lugar asignado.</span>`
        : 'Este lugar no tiene recursos asociados. Se puede eliminar sin consecuencias.'}
      <br><br>Esta acción no se puede deshacer.
    `;
    document.getElementById('btn-del-lug-confirm').onclick = ejecutarEliminar;
    document.getElementById('modal-del-lug').style.display = 'flex';
  } catch(e) { toast('Error al verificar impacto', 'err'); }
}

async function ejecutarEliminar() {
  if (!_delLugId) return;
  try {
    await apiFetch(`/api/lugares/${_delLugId}`, { method: 'DELETE' });
    toast('Lugar eliminado', 'ok');
    cerrarModalLug();
    await cargarLugares();
  } catch(e) { toast('Error: ' + e.message, 'err'); }
}

window.cerrarModalLug = () => {
  document.getElementById('modal-del-lug').style.display = 'none';
  _delLugId = null;
};
