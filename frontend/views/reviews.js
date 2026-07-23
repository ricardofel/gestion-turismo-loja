/**
 * views/reviews.js — EDA de reseñas de Google (Google Reviews vía SerpApi).
 */
import { apiFetch } from '../components/badges.js';

function seccion(titulo) {
  return `<div style="font-size:12px;font-weight:800;color:var(--navy);text-transform:uppercase;letter-spacing:.6px;margin:32px 0 12px;padding-bottom:8px;border-bottom:2px solid var(--border)">${titulo}</div>`;
}

function estrellas(rating) {
  if (rating == null) return '—';
  const llenas = Math.round(rating);
  return `<span style="color:var(--gold);letter-spacing:1px">${'★'.repeat(llenas)}${'☆'.repeat(5 - llenas)}</span>`;
}

function renderReviewCardHTML(r) {
  const fecha = r.fecha ? new Date(r.fecha).toLocaleDateString('es-EC', { year: 'numeric', month: 'short', day: 'numeric' }) : '';
  return `
    <div style="padding:14px 0;border-bottom:1px solid var(--border)">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:6px">
        <div>
          <span style="font-size:13px;font-weight:700;color:var(--text)">${r.autor}</span>
          ${r.es_local_guide ? `<span style="font-size:10px;color:var(--navy);background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1px 7px;margin-left:6px">Local Guide</span>` : ''}
        </div>
        <div style="text-align:right;white-space:nowrap">
          <div>${estrellas(r.rating)}</div>
          <div style="font-size:10px;color:var(--muted)">${fecha}</div>
        </div>
      </div>
      ${r.lugar_nombre ? `<div style="font-size:11px;color:var(--muted);margin-bottom:4px">${r.lugar_nombre}</div>` : ''}
      <p style="font-size:13px;color:var(--text);line-height:1.5;margin:0">${r.texto || '(sin comentario, solo calificación)'}</p>
    </div>`;
}

export async function render(container) {
  container.innerHTML = `<div class="empty"><p>Cargando reseñas...</p></div>`;

  let resumen = null, porLugar = null, palabras = null, recientes = null;
  try {
    [resumen, porLugar, palabras, recientes] = await Promise.all([
      apiFetch('/api/stats/reviews-resumen'),
      apiFetch('/api/stats/reviews-por-lugar?limite=10'),
      apiFetch('/api/stats/palabras-frecuentes?plataforma=GoogleReviews'),
      apiFetch('/api/stats/reviews-recientes?limite=20'),
    ]);
  } catch (e) {
    container.innerHTML = `<div class="empty"><p style="color:var(--red)">Error cargando reseñas: ${e.message}</p></div>`;
    return;
  }

  const total = resumen?.total || 0;

  if (!total) {
    container.innerHTML = `
      <div class="empty">
        <p>Todavía no hay reseñas de Google en la base de datos.</p>
        <p style="font-size:12px;color:var(--muted);margin-top:6px">
          Ve a Ingesta ETL, elige la fuente "GoogleReviews" y extrae datos.
          Recuerda que cada lugar necesita su ID de Google Maps configurado
          en la pantalla Lugares.
        </p>
      </div>`;
    return;
  }

  const distribucion = resumen?.distribucion || [];
  const maxDist = Math.max(...distribucion.map(d => d.count), 1);

  const lugares = porLugar?.data || [];
  const maxLugarCount = Math.max(...lugares.map(l => l.count), 1);

  const palabrasData = palabras?.data || [];
  const palabraTop = palabrasData[0] || null;

  const recientesData = recientes?.data || [];

  container.innerHTML = `
    <div class="stats-grid">
      <div class="stat-card">
        <div class="sc-label">Total de reseñas</div>
        <div class="sc-val">${total.toLocaleString()}</div>
        <div class="sc-sub">de Google Reviews</div>
      </div>
      <div class="stat-card">
        <div class="sc-label">Calificación promedio</div>
        <div class="sc-val">${resumen.rating_promedio ?? '—'}</div>
        <div class="sc-sub">${estrellas(resumen.rating_promedio)}</div>
      </div>
      <div class="stat-card">
        <div class="sc-label">Reseñas de Local Guides</div>
        <div class="sc-val">${resumen.pct_local_guides}%</div>
        <div class="sc-sub">del total</div>
      </div>
    </div>

    ${seccion('Distribución de calificaciones')}
    <div class="card">
      ${distribucion.map(d => `
        <div class="bar-row">
          <div class="bar-label">${d.estrellas} ${d.estrellas === 1 ? 'estrella' : 'estrellas'}</div>
          <div class="bar-track">
            <div class="bar-fill" style="width:${Math.round((d.count / maxDist) * 100)}%;background:var(--gold)"></div>
          </div>
          <div class="bar-count">${d.count}</div>
        </div>`).join('')}
    </div>

    ${lugares.length || palabraTop ? `
    ${seccion('Por lugar y por palabras')}
    <div class="charts-grid">
      ${lugares.length ? `
      <div class="chart-card">
        <div class="chart-title">Lugares con más reseñas</div>
        ${lugares.map(l => `
          <div style="margin-bottom:14px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
              <div style="font-size:12px;font-weight:600;color:var(--text)">${l.nombre}</div>
              <div style="font-size:11px;color:var(--muted);white-space:nowrap;margin-left:8px">${estrellas(l.rating_promedio)} ${l.rating_promedio}</div>
            </div>
            <div style="display:flex;align-items:center;gap:10px">
              <div class="bar-track" style="flex:1">
                <div class="bar-fill" style="width:${Math.round((l.count / maxLugarCount) * 100)}%;background:var(--navy)"></div>
              </div>
              <div style="font-size:12px;font-weight:700;color:var(--navy);min-width:60px;text-align:right">${l.count} reseña${l.count !== 1 ? 's' : ''}</div>
            </div>
          </div>`).join('')}
      </div>` : ''}

      ${palabraTop ? `
      <div class="chart-card">
        <div class="chart-title">Palabra más repetida en las reseñas</div>
        <div style="text-align:center;padding:8px 0 4px">
          <div style="font-size:26px;font-weight:800;color:var(--navy)">"${palabraTop.palabra}"</div>
          <div style="font-size:12px;color:var(--muted);margin-top:4px">apareció ${palabraTop.count} veces</div>
        </div>
        ${palabrasData.length > 1 ? `
        <div style="margin-top:14px">
          ${palabrasData.slice(1, 6).map(p => `
            <div class="bar-row">
              <div class="bar-label">${p.palabra}</div>
              <div class="bar-track">
                <div class="bar-fill" style="width:${Math.round((p.count / palabraTop.count) * 100)}%;background:var(--gold)"></div>
              </div>
              <div class="bar-count">${p.count}</div>
            </div>`).join('')}
        </div>` : ''}
      </div>` : ''}
    </div>` : ''}

    ${seccion('Reseñas recientes')}
    <div class="card">
      <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:14px">
        <select class="input" id="reviews-filtro-lugar" style="max-width:240px">
          <option value="">Todos los lugares</option>
          ${lugares.map(l => `<option value="${l.lugar_id}">${l.nombre}</option>`).join('')}
        </select>

        <select class="input" id="reviews-filtro-rating" style="max-width:180px">
          <option value="">Todas las calificaciones</option>
          <option value="5">5 estrellas</option>
          <option value="4">4 estrellas</option>
          <option value="3">3 estrellas</option>
          <option value="2">2 estrellas</option>
          <option value="1">1 estrella</option>
          <option value="quejas">1-2 estrellas (quejas)</option>
        </select>

        <select class="input" id="reviews-orden" style="max-width:170px">
          <option value="recientes">Más recientes</option>
          <option value="likes">Más útiles (likes)</option>
        </select>

        <label style="font-size:12px;color:var(--muted);display:flex;align-items:center;gap:4px">
          Desde <input type="month" id="reviews-desde"
            style="padding:5px 6px;border:1px solid var(--border);border-radius:6px;font-size:12px">
        </label>
        <label style="font-size:12px;color:var(--muted);display:flex;align-items:center;gap:4px">
          Hasta <input type="month" id="reviews-hasta"
            style="padding:5px 6px;border:1px solid var(--border);border-radius:6px;font-size:12px">
        </label>
        <button id="reviews-reset" type="button"
          style="border:1px solid var(--border);background:var(--white);border-radius:6px;padding:5px 12px;font-size:12px;cursor:pointer;color:var(--navy)">
          Limpiar filtros
        </button>
      </div>
      <div id="reviews-lista">
        ${recientesData.length
          ? recientesData.map(renderReviewCardHTML).join('')
          : `<div class="empty"><p>Sin reseñas para mostrar.</p></div>`}
      </div>
    </div>
  `;

  const selectLugar  = container.querySelector('#reviews-filtro-lugar');
  const selectRating = container.querySelector('#reviews-filtro-rating');
  const selectOrden  = container.querySelector('#reviews-orden');
  const inputDesde   = container.querySelector('#reviews-desde');
  const inputHasta   = container.querySelector('#reviews-hasta');
  const btnReset     = container.querySelector('#reviews-reset');
  const listaEl      = container.querySelector('#reviews-lista');

  async function actualizarLista() {
    listaEl.innerHTML = `<div class="empty"><p>Cargando...</p></div>`;

    const params = new URLSearchParams({ limite: '20' });
    if (selectLugar.value)  params.set('lugar_id', selectLugar.value);
    if (selectOrden.value)  params.set('orden', selectOrden.value);
    if (inputDesde.value)   params.set('desde', inputDesde.value + '-01');
    if (inputHasta.value) {
      const [y, m] = inputHasta.value.split('-').map(Number);
      const ultimoDia = new Date(y, m, 0).getDate();
      params.set('hasta', `${inputHasta.value}-${String(ultimoDia).padStart(2, '0')}`);
    }
    if (selectRating.value === 'quejas') {
      params.set('rating_max', '2');
    } else if (selectRating.value) {
      params.set('rating', selectRating.value);
    }

    try {
      const resp = await apiFetch(`/api/stats/reviews-recientes?${params.toString()}`);
      const data = resp?.data || [];
      listaEl.innerHTML = data.length
        ? data.map(renderReviewCardHTML).join('')
        : `<div class="empty"><p>Sin reseñas para estos filtros.</p></div>`;
    } catch {
      listaEl.innerHTML = `<div class="empty"><p>No se pudo aplicar el filtro.</p></div>`;
    }
  }

  [selectLugar, selectRating, selectOrden, inputDesde, inputHasta].forEach(el =>
    el.addEventListener('change', actualizarLista)
  );
  btnReset.addEventListener('click', () => {
    selectLugar.value = '';
    selectRating.value = '';
    selectOrden.value = 'recientes';
    inputDesde.value = '';
    inputHasta.value = '';
    actualizarLista();
  });
}
