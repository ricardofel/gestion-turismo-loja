/**
 * components/badges.js
 * Helpers de visualización compartidos entre vistas.
 */

export function badgePlat(p) {
  const cls = { TikTok:'b-TikTok', YouTube:'b-YouTube', GoogleReviews:'b-GoogleReviews' };
  return `<span class="badge ${cls[p] || 'b-mock'}">${p || '—'}</span>`;
}

export function badgeEstado(e) {
  const cls = { Crudo:'b-crudo', Clasificado:'b-clasificado', Error:'b-error' };
  return `<span class="badge ${cls[e] || ''}">${e}</span>`;
}

export const LABELS_MET = {
  likes       : 'Likes',
  shares      : 'Compartidos',
  plays       : 'Reproducciones',
  guardados   : 'Guardados',
  comentarios : 'Comentarios',
  vistas      : 'Vistas',
};

export function renderMetricas(metricas = {}) {
  return Object.entries(metricas)
    .filter(([, v]) => v != null && v !== 0)
    .map(([k, v]) =>
      `<span class="met-item">
        <span class="met-label">${LABELS_MET[k] || k}</span>
        <strong>${Number(v).toLocaleString()}</strong>
      </span>`)
    .join('');
}

export function toast(msg, tipo = '') {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.className   = 'show ' + tipo;
  clearTimeout(t._t);
  t._t = setTimeout(() => t.className = '', 3200);
}

export async function apiFetch(path, opts = {}) {
  const API = 'http://127.0.0.1:8000';
  const r   = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts
  });
  if (!r.ok) {
    const e = await r.json().catch(() => ({}));
    throw new Error(e.detail || r.statusText);
  }
  return r.json();
}
