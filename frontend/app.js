/**
 * app.js — Router principal de la SPA.
 * Carga catálogos, gestiona navegación y health check.
 */
import { render as renderHome }     from './views/home.js';
import { render as renderDB }       from './views/database.js';
import { render as renderETL }      from './views/etl.js';
import { render as renderLugares }  from './views/lugares.js';
import { render as renderEventos }  from './views/eventos.js';
import { render as renderReviews }  from './views/reviews.js';
import { apiFetch, toast }          from './components/badges.js';
import { nuevoToken, esTokenVigente } from './components/nav-state.js';

const main = document.getElementById('main');

// Estado global compartido entre vistas
const state = {
  catEventos  : [],
  catEdiciones: [],
  catLugares  : [],
};

// ── Catálogos ──────────────────────────────────────────────
// Se cargan al inicio y se refrescan cada vez que se entra a una vista de
// "Base de Datos" — si no, crear un lugar/evento nuevo no se reflejaría en
// los filtros/selectores hasta recargar toda la página.
async function cargarCatalogos() {
  try {
    const [re, rl, rev] = await Promise.all([
      apiFetch('/api/catalogos/ediciones'),
      apiFetch('/api/catalogos/lugares'),
      apiFetch('/api/catalogos/eventos'),
    ]);
    state.catEdiciones = re.exito  ? re.data  : [];
    state.catLugares   = rl.exito  ? rl.data  : [];
    state.catEventos   = rev.exito ? rev.data : [];
  } catch (e) {
    console.warn('No se pudieron cargar los catálogos:', e.message);
  }
}

// ── Health check ─────────────────────────────────────────
async function checkHealth() {
  const dot = document.getElementById('status-dot');
  const txt = document.getElementById('status-txt');
  try {
    const d  = await apiFetch('/api/health');
    const ok = d.mongodb === 'conectado';
    dot.className    = 'dot ' + (ok ? 'ok' : 'err');
    txt.textContent  = ok ? 'Base de datos conectada' : 'Sin base de datos';
    txt.style.color  = ok ? 'var(--green)' : 'var(--red)';
  } catch {
    dot.className   = 'dot err';
    txt.textContent = 'API no disponible';
    txt.style.color = 'var(--red)';
  }
}

// ── Navegación ────────────────────────────────────────────
const TITULOS = {
  home: 'Inicio',
  etl: 'Ingesta ETL',
  reviews: 'Reviews',
  'db-eventos' : 'Base de Datos · Eventos',
  'db-lugares' : 'Base de Datos · Lugares',
  'db-recursos': 'Base de Datos · Recursos',
};

let dbAbierto = false;

function setDbAbierto(abierto) {
  dbAbierto = abierto;
  document.getElementById('db-submenu')?.classList.toggle('open', dbAbierto);
  document.getElementById('db-chevron')?.classList.toggle('rot', dbAbierto);
}

// Alterna el desplegable "Base de Datos" al hacer click en el item padre
export function toggleDbMenu() {
  setDbAbierto(!dbAbierto);
}
window.toggleDbMenu = toggleDbMenu;

export async function ir(vista) {
  document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
  document.getElementById('nav-' + vista)?.classList.add('active');
  document.getElementById('header-title').textContent = TITULOS[vista] || vista;

  if (vista.startsWith('db-')) setDbAbierto(true);

  const token = nuevoToken();

  if (vista.startsWith('db-')) {
    await cargarCatalogos();
    if (!esTokenVigente(token)) return; // el usuario ya navegó a otra vista
  }

  switch (vista) {
    case 'home':         renderHome(main, state, token); break;
    case 'db-recursos':  renderDB(main, state);          break;
    case 'db-lugares':   renderLugares(main);            break;
    case 'db-eventos':   renderEventos(main);            break;
    case 'etl':          renderETL(main);                break;
    case 'reviews':      renderReviews(main);            break;
  }
}

// Exponer ir() globalmente para los onclick del HTML
window.irVista = ir;

// ── Inicio ────────────────────────────────────────────────
(async () => {
  checkHealth();
  setInterval(checkHealth, 20000);
  await cargarCatalogos();
  ir('home');
})();
