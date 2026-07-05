/**
 * views/home.js — Dashboard con estadísticas reales desde /api/stats
 */
import { apiFetch } from '../components/badges.js';
import { esTokenVigente } from '../components/nav-state.js';

const COLORES_PLAT = {
  TikTok:        '#9D174D',
  YouTube:       '#DC2626',
  Instagram:     '#7C3AED',
  GoogleReviews: '#16A34A',
  TripAdvisor:   '#D97706',
  Flickr:        '#2563EB',
  Eventbrite:    '#EA580C',
};
const COLOR_DEFAULT = '#64748B';

export async function render(container, { catEventos, catLugares }, token) {
  container.innerHTML = `<div class="empty"><p>Cargando estadísticas...</p></div>`;

  let resumen = null, ingesta = null, statsEventos = null;
  let totalRecursos = 0;

  try {
    [resumen, ingesta, statsEventos] = await Promise.all([
      apiFetch('/api/stats/resumen'),
      apiFetch('/api/stats/ingesta-mensual'),
      apiFetch('/api/stats/eventos'),
    ]);
    totalRecursos = (resumen.por_plataforma || []).reduce((s, p) => s + p.count, 0);
  } catch {
    try {
      const d = await apiFetch('/api/recursos?limit=1');
      totalRecursos = d.total ?? 0;
    } catch {}
  }

  // ── KPIs ──────────────────────────────────────────────────
  const fuentesNombres = (resumen?.fuentes_nombres || []).join(', ') || '—';
  const fuentesCount   = resumen?.fuentes_activas ?? '—';

  const stats = [
    { label: 'Total de recursos',   val: totalRecursos.toLocaleString(), sub: 'en la base de datos' },
    { label: 'Fuentes activas',     val: fuentesCount, sub: fuentesNombres },
    { label: 'Eventos registrados', val: catEventos.length || '—', sub: 'en la colección evento' },
    { label: 'Lugares registrados', val: catLugares.length || '—', sub: 'en la colección lugar' },
  ];

  // ── Plataformas ────────────────────────────────────────────
  const platData = resumen?.por_plataforma || [];
  const maxPlat  = Math.max(...platData.map(p => p.count), 1);
  const porPlat  = platData.map(p => ({
    label: p.plataforma,
    count: p.count,
    pct:   Math.round((p.count / maxPlat) * 100),
    color: COLORES_PLAT[p.plataforma] || COLOR_DEFAULT,
  }));

  // ── Estados ────────────────────────────────────────────────
  const ESTADOS_ORDEN  = ['Crudo', 'Clasificado', 'Error'];
  const COLORES_ESTADO = { Crudo: '#D97706', Clasificado: '#16A34A', Error: '#DC2626' };
  const estadoMap = {};
  (resumen?.por_estado || []).forEach(e => { estadoMap[e.estado] = e.count; });
  const maxEstado = Math.max(...Object.values(estadoMap), 1);
  const porEstado = ESTADOS_ORDEN.map(est => ({
    label: est,
    count: estadoMap[est] || 0,
    pct:   Math.round(((estadoMap[est] || 0) / maxEstado) * 100),
    color: COLORES_ESTADO[est],
  }));

  // ── Ingesta mensual ────────────────────────────────────────
  const mesesData = ingesta?.data || [];
  const maxMes    = Math.max(...mesesData.map(m => m.count), 1);

  // ── Eventos ────────────────────────────────────────────────
  const eventosStats    = statsEventos?.data || [];
  const eventoTop       = eventosStats.find(e => e.es_mas_popular);
  const totalConEdicion = eventosStats.reduce((s, e) => s + e.recursos, 0);
  const maxEventoRec    = Math.max(...eventosStats.map(e => e.recursos), 1);

  // El usuario ya navegó a otra vista mientras se cargaban los datos —
  // no pisar el contenido de la vista actual.
  if (token !== undefined && !esTokenVigente(token)) return;

  container.innerHTML = `
    <!-- KPIs -->
    <div class="stats-grid">
      ${stats.map(s => `
        <div class="stat-card">
          <div class="sc-label">${s.label}</div>
          <div class="sc-val">${s.val}</div>
          <div class="sc-sub">${s.sub}</div>
        </div>`).join('')}
    </div>

    <!-- Plataformas + Estados -->
    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-title">Por plataforma</div>
        ${porPlat.length
          ? porPlat.map(p => `
            <div class="bar-row">
              <div class="bar-label">${p.label}</div>
              <div class="bar-track">
                <div class="bar-fill" style="width:${p.pct}%;background:${p.color}"></div>
              </div>
              <div class="bar-count">${p.count.toLocaleString()}</div>
            </div>`).join('')
          : `<div class="empty"><p>Sin datos de plataformas.</p></div>`}
      </div>
      <div class="chart-card">
        <div class="chart-title">Por estado de procesamiento</div>
        ${porEstado.map(p => `
          <div class="bar-row">
            <div class="bar-label">${p.label}</div>
            <div class="bar-track">
              <div class="bar-fill" style="width:${p.pct}%;background:${p.color}"></div>
            </div>
            <div class="bar-count">${p.count.toLocaleString()}</div>
          </div>`).join('')}
      </div>
    </div>

    <!-- Ingesta mensual -->
    <div class="card">
      <div class="card-label">Ingesta mensual por fecha de publicación</div>
      ${mesesData.length ? `
        <div class="timeline-bars">
          ${mesesData.map(m => `
            <div class="tbar"
                 style="height:${Math.round((m.count / maxMes) * 100)}%"
                 title="${m.label}: ${m.count}">
            </div>`).join('')}
        </div>
        <div class="tmonths">
          ${mesesData.map(m => {
            const [mes, anio] = m.label.split(' ');
            return `<div class="tmonth">${mes}<br><span style="font-size:9px;opacity:.6">${anio || ''}</span></div>`;
          }).join('')}
        </div>`
      : `<div class="empty"><p>Sin datos de ingesta mensual aún.</p></div>`}
    </div>

    <!-- Eventos -->
    ${eventosStats.length ? `
    <div class="charts-grid" style="grid-template-columns:${eventoTop && eventoTop.recursos > 0 ? '1fr 2fr' : '1fr'}">

      ${eventoTop && eventoTop.recursos > 0 ? `
      <!-- KPI popular -->
      <div class="chart-card" style="background:linear-gradient(135deg,var(--navy) 0%,#1e5fa8 100%);color:#fff;display:flex;flex-direction:column;justify-content:center">
        <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;opacity:.7;margin-bottom:8px">
          🏆 Evento más popular
        </div>
        <div style="font-size:17px;font-weight:800;line-height:1.3;margin-bottom:14px">
          ${eventoTop.nombre}
        </div>
        <div style="display:flex;gap:20px;flex-wrap:wrap">
          <div>
            <div style="font-size:30px;font-weight:800;color:var(--gold)">${eventoTop.recursos.toLocaleString()}</div>
            <div style="font-size:11px;opacity:.8">recursos asociados</div>
          </div>
          <div>
            <div style="font-size:30px;font-weight:800;color:var(--gold)">${eventoTop.ediciones}</div>
            <div style="font-size:11px;opacity:.8">edicion${eventoTop.ediciones !== 1 ? 'es' : ''}</div>
          </div>
        </div>
        ${totalConEdicion > 0 ? `
        <div style="margin-top:14px;font-size:11px;opacity:.7">
          ${Math.round((eventoTop.recursos / totalConEdicion) * 100)}% del contenido con evento asignado
        </div>` : ''}
      </div>` : ''}

      <!-- Tabla eventos -->
      <div class="chart-card">
        <div class="chart-title">Recursos por evento</div>
        ${eventosStats.map(ev => `
          <div style="margin-bottom:14px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
              <div style="font-size:12px;font-weight:600;color:var(--text)">
                ${ev.nombre}
                ${ev.es_mas_popular ? `<span style="font-size:10px;color:var(--gold);margin-left:5px">★ Popular</span>` : ''}
              </div>
              <div style="font-size:11px;color:var(--muted);white-space:nowrap;margin-left:8px">
                ${ev.ediciones} edicion${ev.ediciones !== 1 ? 'es' : ''}
                ${ev.anios_ediciones.length
                  ? `(${ev.anios_ediciones.slice(0, 3).join(', ')}${ev.anios_ediciones.length > 3 ? '…' : ''})`
                  : ''}
              </div>
            </div>
            <div style="display:flex;align-items:center;gap:10px">
              <div class="bar-track" style="flex:1">
                <div class="bar-fill" style="width:${Math.round((ev.recursos / maxEventoRec) * 100)}%;background:var(--navy)"></div>
              </div>
              <div style="font-size:12px;font-weight:700;color:var(--navy);min-width:32px;text-align:right">
                ${ev.recursos.toLocaleString()}
              </div>
            </div>
            ${ev.categoria
              ? `<div style="font-size:10px;color:var(--muted);margin-top:2px">${ev.categoria}</div>`
              : ''}
          </div>`).join('')}
        ${eventosStats.every(e => e.recursos === 0) ? `
          <p style="font-size:12px;color:var(--muted);font-style:italic;margin-top:8px">
            Los recursos se asocian a eventos a través de sus ediciones durante la ingesta ETL.
          </p>` : ''}
      </div>
    </div>` : ''}
  `;
}
