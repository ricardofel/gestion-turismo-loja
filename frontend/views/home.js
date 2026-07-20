/**
 * views/home.js — Dashboard con estadísticas reales desde /api/stats
 */
import { apiFetch } from '../components/badges.js';
import { esTokenVigente } from '../components/nav-state.js';

const COLORES_PLAT = {
  TikTok:        '#9D174D',
  YouTube:       '#DC2626',
  Instagram:     '#7C3AED',
  'Google Reviews': '#16A34A',
  TripAdvisor:   '#D97706',
  Flickr:        '#2563EB',
  Eventbrite:    '#EA580C',
};
const COLOR_DEFAULT = '#64748B';

function seccion(titulo) {
  return `<div style="font-size:12px;font-weight:800;color:var(--navy);text-transform:uppercase;letter-spacing:.6px;margin:32px 0 12px;padding-bottom:8px;border-bottom:2px solid var(--border)">${titulo}</div>`;
}

function donutChart(segmentos, size = 130, grosor = 20) {
  const total = segmentos.reduce((s, x) => s + x.count, 0) || 1;
  const r = (size - grosor) / 2;
  const c = 2 * Math.PI * r;
  let acumulado = 0;

  const circulos = segmentos.map(seg => {
    const frac = seg.count / total;
    const dash = frac * c;
    const el = `<circle cx="${size / 2}" cy="${size / 2}" r="${r}" fill="none"
      stroke="${seg.color}" stroke-width="${grosor}"
      stroke-dasharray="${dash} ${c - dash}" stroke-dashoffset="${-acumulado}"
      transform="rotate(-90 ${size / 2} ${size / 2})" />`;
    acumulado += dash;
    return el;
  }).join('');

  return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">${circulos}</svg>`;
}

function nubeDePalabras(items) {
  const counts = items.map(i => i.count);
  const max = Math.max(...counts, 1);
  const min = Math.min(...counts, 1);
  return `<div style="display:flex;flex-wrap:wrap;gap:10px 14px;align-items:baseline">
    ${items.map(i => {
      const escala = max === min ? 1 : (i.count - min) / (max - min);
      const tamano = Math.round(13 + escala * 15);
      const opacidad = (0.55 + escala * 0.45).toFixed(2);
      return `<span style="font-size:${tamano}px;font-weight:700;color:var(--navy);opacity:${opacidad}" title="${i.count} veces">#${i.tag}</span>`;
    }).join('')}
  </div>`;
}

function renderTimelineHTML(mesesData) {
  if (!mesesData.length) {
    return `<div class="empty"><p>Sin datos de ingesta para el rango seleccionado.</p></div>`;
  }
  const maxMes = Math.max(...mesesData.map(m => m.count), 1);
  return `
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
    </div>`;
}

function comparacionMensualHTML(mesesData) {
  if (mesesData.length < 2) return '';
  const actual   = mesesData[mesesData.length - 1];
  const anterior = mesesData[mesesData.length - 2];
  if (!anterior.count) return '';

  const variacion = Math.round(((actual.count - anterior.count) / anterior.count) * 100);
  const subio = variacion >= 0;
  const color = subio ? 'var(--green)' : 'var(--red)';
  const signo = subio ? '+' : '';

  return `<span style="font-size:12px;font-weight:700;color:${color};background:${subio ? '#DCFCE7' : '#FEE2E2'};padding:3px 9px;border-radius:12px">
    ${signo}${variacion}% vs ${anterior.label}
  </span>`;
}

function renderLugarItemHTML(l, maxCount) {
  return `
    <div style="margin-bottom:14px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
        <div style="font-size:12px;font-weight:600;color:var(--text)">${l.nombre}</div>
        ${l.tipo_lugar
          ? `<div style="font-size:10px;color:var(--muted);white-space:nowrap;margin-left:8px">${l.tipo_lugar}</div>`
          : ''}
      </div>
      <div style="display:flex;align-items:center;gap:10px">
        <div class="bar-track" style="flex:1">
          <div class="bar-fill" style="width:${Math.round((l.count / maxCount) * 100)}%;background:var(--navy)"></div>
        </div>
        <div style="font-size:12px;font-weight:700;color:var(--navy);min-width:70px;text-align:right">
          ${l.count.toLocaleString()} recurso${l.count !== 1 ? 's' : ''}
        </div>
      </div>
    </div>`;
}

function renderLugaresListaHTML(lista, maxCount) {
  if (!lista.length) {
    return `<div class="empty"><p>Sin resultados para esa búsqueda.</p></div>`;
  }
  return lista.map(l => renderLugarItemHTML(l, maxCount)).join('');
}

function mapaDePuntos(lugares, size = { w: 320, h: 260 }, margin = 26) {
  const conCoord = lugares.filter(l => l.lat != null && l.lon != null);
  if (!conCoord.length) return null;

  const lats = conCoord.map(l => l.lat);
  const lons = conCoord.map(l => l.lon);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats);
  const minLon = Math.min(...lons), maxLon = Math.max(...lons);
  const rangoLat = (maxLat - minLat) || 0.01;
  const rangoLon = (maxLon - minLon) || 0.01;
  const maxCount = Math.max(...conCoord.map(l => l.count), 1);

  const puntos = conCoord.map((l, i) => ({
    idx: i,
    nombre: l.nombre,
    tipo: l.tipo_lugar,
    count: l.count,
    x: margin + ((l.lon - minLon) / rangoLon) * (size.w - 2 * margin),
    y: margin + (1 - (l.lat - minLat) / rangoLat) * (size.h - 2 * margin),
    radio: 5 + (l.count / maxCount) * 13,
  }));

  const circulos = puntos.map(p => `
    <circle class="mapa-punto" data-idx="${p.idx}"
      cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${p.radio.toFixed(1)}"
      fill="var(--navy)" fill-opacity="0.5" stroke="var(--navy)" stroke-width="1.5"
      style="cursor:pointer" />`).join('');

  return {
    puntos,
    svg: `<svg width="${size.w}" height="${size.h}" viewBox="0 0 ${size.w} ${size.h}" style="max-width:100%;height:auto">${circulos}</svg>`,
  };
}

export async function render(container, { catEventos, catLugares }, token) {
  container.innerHTML = `<div class="empty"><p>Cargando estadísticas...</p></div>`;

  let resumen = null, ingesta = null, statsEventos = null, statsLugares = null;
  let statsEngagement = null, statsHashtags = null, statsPalabras = null;
  let totalRecursos = 0;

  try {
    [resumen, ingesta, statsEventos, statsLugares, statsEngagement, statsHashtags, statsPalabras] = await Promise.all([
      apiFetch('/api/stats/resumen'),
      apiFetch('/api/stats/ingesta-mensual'),
      apiFetch('/api/stats/eventos'),
      apiFetch('/api/stats/top-lugares?limite=30'),
      apiFetch('/api/stats/engagement'),
      apiFetch('/api/stats/hashtags'),
      apiFetch('/api/stats/palabras-frecuentes'),
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

  // ── Plataformas (donut) ─────────────────────────────────────
  const platData = resumen?.por_plataforma || [];
  const platSegmentos = platData.map(p => ({
    label: p.plataforma,
    count: p.count,
    color: COLORES_PLAT[p.plataforma] || COLOR_DEFAULT,
  }));
  const totalPlat = platSegmentos.reduce((s, p) => s + p.count, 0) || 1;

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
  const comparacionHTML = comparacionMensualHTML(mesesData);

  // ── Eventos ────────────────────────────────────────────────
  const eventosStats    = statsEventos?.data || [];
  const eventoTop       = eventosStats.find(e => e.es_mas_popular);
  const totalConEdicion = eventosStats.reduce((s, e) => s + e.recursos, 0);
  const maxEventoRec    = Math.max(...eventosStats.map(e => e.recursos), 1);

  // ── Top lugares ────────────────────────────────────────────
  const lugaresStats = statsLugares?.data || [];
  const maxLugarRec   = Math.max(...lugaresStats.map(l => l.count), 1);
  const mapa = mapaDePuntos(lugaresStats);

  // ── Engagement ───────────────────────────────────────────────
  const totalVistas      = statsEngagement?.total_vistas ?? 0;
  const totalLikes       = statsEngagement?.total_likes ?? 0;
  const totalComentarios = statsEngagement?.total_comentarios ?? 0;
  const destacado        = statsEngagement?.destacado || null;

  // ── Palabras clave ───────────────────────────────────────────
  const hashtags  = statsHashtags?.data || [];
  const palabras  = statsPalabras?.data || [];
  const palabraTop = palabras[0] || null;

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

    ${seccion('Distribución de contenido')}
    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-title">Por plataforma</div>
        ${platSegmentos.length ? `
          <div style="display:flex;align-items:center;gap:24px;flex-wrap:wrap">
            ${donutChart(platSegmentos)}
            <div style="flex:1;min-width:140px">
              ${platSegmentos.map(p => `
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
                  <span style="width:10px;height:10px;border-radius:50%;background:${p.color};flex-shrink:0"></span>
                  <span style="font-size:12px;color:var(--text);flex:1">${p.label}</span>
                  <span style="font-size:12px;font-weight:700;color:var(--navy)">${Math.round((p.count / totalPlat) * 100)}%</span>
                </div>`).join('')}
            </div>
          </div>`
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

    ${seccion('Evolución en el tiempo')}
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:10px">
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
          <div class="card-label" style="margin-bottom:0">Ingesta mensual por fecha de publicación</div>
          ${comparacionHTML}
        </div>
        ${mesesData.length ? `
        <div style="display:flex;align-items:center;gap:8px;font-size:12px;color:var(--muted)">
          <label>Desde <input type="month" id="ingesta-desde" value="${mesesData[0].periodo}"
            style="margin-left:4px;padding:3px 6px;border:1px solid var(--border);border-radius:6px;font-size:12px"></label>
          <label>Hasta <input type="month" id="ingesta-hasta" value="${mesesData[mesesData.length - 1].periodo}"
            style="margin-left:4px;padding:3px 6px;border:1px solid var(--border);border-radius:6px;font-size:12px"></label>
          <button id="ingesta-reset" type="button"
            style="border:1px solid var(--border);background:var(--white);border-radius:6px;padding:3px 10px;font-size:12px;cursor:pointer;color:var(--navy)">
            Ver todo
          </button>
        </div>` : ''}
      </div>
      <div id="ingesta-chart-body">${renderTimelineHTML(mesesData)}</div>
    </div>

    ${(totalVistas + totalLikes + totalComentarios) > 0 || destacado ? `
    ${seccion('Alcance en YouTube')}
    ${(totalVistas + totalLikes + totalComentarios) > 0 ? `
    <div class="stats-grid">
      <div class="stat-card">
        <div class="sc-label">Vistas totales</div>
        <div class="sc-val">${totalVistas.toLocaleString()}</div>
        <div class="sc-sub">acumuladas</div>
      </div>
      <div class="stat-card">
        <div class="sc-label">Likes totales</div>
        <div class="sc-val">${totalLikes.toLocaleString()}</div>
        <div class="sc-sub">acumulados</div>
      </div>
      <div class="stat-card">
        <div class="sc-label">Comentarios totales</div>
        <div class="sc-val">${totalComentarios.toLocaleString()}</div>
        <div class="sc-sub">acumulados</div>
      </div>
    </div>` : ''}

    ${destacado ? `
    <div class="card">
      <div class="card-label">Video con más vistas</div>
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px;margin-top:6px">
        <div>
          <div style="font-size:15px;font-weight:700;color:var(--text);margin-bottom:4px">${destacado.titulo || 'Sin título'}</div>
          <div style="font-size:12px;color:var(--muted)">${destacado.canal}</div>
          ${destacado.url ? `<a href="${destacado.url}" target="_blank" rel="noopener" style="font-size:12px;color:var(--navy)">Ver video ↗</a>` : ''}
        </div>
        <div style="display:flex;gap:24px">
          <div style="text-align:center">
            <div style="font-size:22px;font-weight:800;color:var(--navy)">${destacado.vistas.toLocaleString()}</div>
            <div style="font-size:11px;color:var(--muted)">vistas</div>
          </div>
          <div style="text-align:center">
            <div style="font-size:22px;font-weight:800;color:var(--navy)">${destacado.comentarios.toLocaleString()}</div>
            <div style="font-size:11px;color:var(--muted)">comentarios</div>
          </div>
        </div>
      </div>
    </div>` : ''}` : ''}

    ${hashtags.length || palabraTop ? `
    ${seccion('Palabras más usadas')}
    <div class="charts-grid">
      ${hashtags.length ? `
      <div class="chart-card">
        <div class="chart-title">Hashtags más usados</div>
        ${nubeDePalabras(hashtags)}
      </div>` : ''}

      ${palabraTop ? `
      <div class="chart-card">
        <div class="chart-title">Palabra más repetida en las descripciones</div>
        <div style="text-align:center;padding:8px 0 4px">
          <div style="font-size:26px;font-weight:800;color:var(--navy)">"${palabraTop.palabra}"</div>
          <div style="font-size:12px;color:var(--muted);margin-top:4px">apareció ${palabraTop.count} veces</div>
        </div>
        ${palabras.length > 1 ? `
        <div style="margin-top:14px">
          ${palabras.slice(1, 6).map(p => `
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

    ${eventosStats.length ? `
    ${seccion('Eventos')}
    <div class="charts-grid" style="grid-template-columns:${eventoTop && eventoTop.recursos > 0 ? '1fr 2fr' : '1fr'}">

      ${eventoTop && eventoTop.recursos > 0 ? `
      <div class="chart-card" style="background:linear-gradient(135deg,var(--navy) 0%,#1e5fa8 100%);color:#fff;display:flex;flex-direction:column;justify-content:center">
        <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;opacity:.7;margin-bottom:8px">
          Evento más popular
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

      <div class="chart-card">
        <div class="chart-title">Recursos por evento</div>
        ${eventosStats.map(ev => `
          <div style="margin-bottom:14px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
              <div style="font-size:12px;font-weight:600;color:var(--text)">
                ${ev.nombre}
                ${ev.es_mas_popular ? `<span style="font-size:10px;color:var(--gold);margin-left:5px">Popular</span>` : ''}
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

    ${seccion('Lugares con más contenido')}
    <div class="charts-grid" style="grid-template-columns:${mapa ? '1fr 1fr' : '1fr'}">
      <div class="chart-card">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap">
          <div class="chart-title" style="margin-bottom:0">Top lugares</div>
          ${lugaresStats.length ? `
          <input type="text" id="lugares-buscador" placeholder="Buscar por nombre o tipo..."
            style="padding:5px 10px;border:1px solid var(--border);border-radius:6px;font-size:12px;min-width:180px">
          ` : ''}
        </div>
        <div id="lugares-lista">
          ${lugaresStats.length
            ? renderLugaresListaHTML(lugaresStats.slice(0, 5), maxLugarRec)
            : `<div class="empty"><p>Todavía no hay recursos con un lugar asignado. Los lugares se asocian durante la clasificación en la ingesta ETL.</p></div>`}
        </div>
      </div>

      ${mapa ? `
      <div class="chart-card">
        <div class="chart-title">Mapa de lugares (por cantidad de recursos)</div>
        <div style="display:flex;justify-content:center">${mapa.svg}</div>
        <div id="mapa-caption" style="text-align:center;font-size:12px;color:var(--muted);margin-top:8px">
          Haz clic en un punto para ver el detalle
        </div>
      </div>` : ''}
    </div>
  `;

  // ── Filtro interactivo de ingesta mensual ───────────────────
  const inputDesde = container.querySelector('#ingesta-desde');
  const inputHasta = container.querySelector('#ingesta-hasta');
  const btnReset   = container.querySelector('#ingesta-reset');
  const chartBody  = container.querySelector('#ingesta-chart-body');

  const rangoOriginal = {
    desde: mesesData[0]?.periodo,
    hasta: mesesData[mesesData.length - 1]?.periodo,
  };

  async function actualizarIngesta() {
    if (!inputDesde || !inputHasta || !chartBody) return;
    const desde = inputDesde.value;
    const hasta = inputHasta.value;
    if (!desde || !hasta) return;

    if (desde > hasta) {
      chartBody.innerHTML = `<div class="empty"><p>La fecha "Desde" no puede ser posterior a "Hasta".</p></div>`;
      return;
    }

    chartBody.innerHTML = `<div class="empty"><p>Cargando...</p></div>`;
    try {
      const resp = await apiFetch(`/api/stats/ingesta-mensual?desde=${desde}&hasta=${hasta}`);
      chartBody.innerHTML = renderTimelineHTML(resp?.data || []);
    } catch {
      chartBody.innerHTML = `<div class="empty"><p>No se pudo cargar el rango seleccionado.</p></div>`;
    }
  }

  if (inputDesde && inputHasta) {
    inputDesde.addEventListener('change', actualizarIngesta);
    inputHasta.addEventListener('change', actualizarIngesta);
  }
  if (btnReset) {
    btnReset.addEventListener('click', () => {
      if (inputDesde) inputDesde.value = rangoOriginal.desde;
      if (inputHasta) inputHasta.value = rangoOriginal.hasta;
      chartBody.innerHTML = renderTimelineHTML(mesesData);
    });
  }

  // ── Buscador de lugares ──────────────────────────────────────
  const buscadorLugares = container.querySelector('#lugares-buscador');
  const listaLugaresEl  = container.querySelector('#lugares-lista');
  if (buscadorLugares && listaLugaresEl) {
    buscadorLugares.addEventListener('input', () => {
      const q = buscadorLugares.value.trim().toLowerCase();
      const filtrados = !q
        ? lugaresStats.slice(0, 5)
        : lugaresStats.filter(l =>
            l.nombre.toLowerCase().includes(q) ||
            (l.tipo_lugar || '').toLowerCase().includes(q)
          );
      listaLugaresEl.innerHTML = renderLugaresListaHTML(filtrados, maxLugarRec);
    });
  }

  // ── Mapa de puntos: clic para ver detalle ───────────────────
  if (mapa) {
    const caption = container.querySelector('#mapa-caption');
    container.querySelectorAll('.mapa-punto').forEach(circulo => {
      circulo.addEventListener('click', () => {
        const p = mapa.puntos[Number(circulo.dataset.idx)];
        if (!p || !caption) return;
        caption.innerHTML = `<strong style="color:var(--navy)">${p.nombre}</strong>${p.tipo ? ` · ${p.tipo}` : ''} — ${p.count} recurso${p.count !== 1 ? 's' : ''}`;
      });
    });
  }
}
