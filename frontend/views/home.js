/**
 * views/home.js — Vista de inicio con EDA / dashboard.
 * Los datos del dashboard actualmente son simulados.
 * TODO: conectar a endpoints GET /api/stats cuando estén disponibles.
 */
import { apiFetch } from '../components/badges.js';

export async function render(container, { catEventos, catLugares }) {
  // Intentamos obtener el total real de recursos
  let totalRecursos = '—';
  try {
    const d = await apiFetch('/api/recursos?limit=1');
    totalRecursos = d.total ?? '—';
  } catch {}

  const stats = [
    { label: 'Total de recursos',    val: totalRecursos,        sub: 'en la base de datos' },
    { label: 'Fuentes activas',      val: 1,                    sub: 'TikTok activa' },
    { label: 'Eventos registrados',  val: catEventos.length || '—', sub: 'en la colección evento' },
    { label: 'Lugares registrados',  val: catLugares.length || '—', sub: 'en la colección lugar' },
  ];

  // Datos simulados — reemplazar con endpoints reales en próxima iteración
  const porPlat = [
    { label: 'TikTok',         count: totalRecursos, pct: 100, color: '#9D174D' },
  ];
  const porEstado = [
    { label: 'Crudo',       count: totalRecursos, pct: 100, color: '#D97706' },
    { label: 'Clasificado', count: 0,             pct: 0,   color: '#16A34A' },
    { label: 'Error',       count: 0,             pct: 0,   color: '#DC2626' },
  ];
  const meses = [
    { m: 'Ene', v: 0 }, { m: 'Feb', v: 0 }, { m: 'Mar', v: 0 },
    { m: 'Abr', v: 0 }, { m: 'May', v: 0 }, { m: 'Jun', v: totalRecursos === '—' ? 0 : totalRecursos },
  ];
  const maxV = Math.max(...meses.map(m => m.v), 1);

  container.innerHTML = `
    <div class="stats-grid">
      ${stats.map(s => `
        <div class="stat-card">
          <div class="sc-label">${s.label}</div>
          <div class="sc-val">${s.val}</div>
          <div class="sc-sub">${s.sub}</div>
        </div>`).join('')}
    </div>

    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-title">Por plataforma</div>
        ${porPlat.map(p => `
          <div class="bar-row">
            <div class="bar-label">${p.label}</div>
            <div class="bar-track"><div class="bar-fill" style="width:${p.pct}%;background:${p.color}"></div></div>
            <div class="bar-count">${p.count}</div>
          </div>`).join('')}
      </div>
      <div class="chart-card">
        <div class="chart-title">Por estado de procesamiento</div>
        ${porEstado.map(p => `
          <div class="bar-row">
            <div class="bar-label">${p.label}</div>
            <div class="bar-track"><div class="bar-fill" style="width:${p.pct}%;background:${p.color}"></div></div>
            <div class="bar-count">${p.count}</div>
          </div>`).join('')}
      </div>
    </div>

    <div class="card">
      <div class="card-label">Ingesta mensual — 2026</div>
      <div class="timeline-bars">
        ${meses.map(m => `
          <div class="tbar" style="height:${Math.round((m.v / maxV) * 100)}%" title="${m.m}: ${m.v}"></div>
        `).join('')}
      </div>
      <div class="tmonths">
        ${meses.map(m => `<div class="tmonth">${m.m}</div>`).join('')}
      </div>
    </div>

    <p style="font-size:11px;color:var(--muted);text-align:center;margin-top:4px">
      El total de recursos es real. Las distribuciones por estado y plataforma se conectaran
      a endpoints dedicados /api/stats en la siguiente iteracion.
    </p>
  `;
}
