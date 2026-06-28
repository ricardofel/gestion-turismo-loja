/**
 * components/datepicker.js — Selector de rango de fechas.
 * Usa tabla HTML para el grid del calendario, evitando
 * problemas de alineación al cambiar de mes/año.
 */

const MESES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
               'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];

function strFecha(y, m, d) {
  return `${y}-${String(m+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
}

function buildCal(inst) {
  const { viewYear, viewMonth, desde, hasta, id } = inst;
  const hoy    = new Date();
  const primer = new Date(viewYear, viewMonth, 1).getDay(); // 0=Dom
  const offset = primer === 0 ? 6 : primer - 1;
  const total  = new Date(viewYear, viewMonth + 1, 0).getDate();

  // Selector de año
  const anioMin = hoy.getFullYear() - 10;
  const anioMax = hoy.getFullYear() + 2;
  let optsAnio = '';
  for (let y = anioMax; y >= anioMin; y--) {
    optsAnio += `<option value="${y}"${y === viewYear ? ' selected' : ''}>${y}</option>`;
  }

  // Construir filas de la tabla
  let celdas = [];
  for (let i = 0; i < offset; i++) celdas.push(`<td></td>`);
  for (let d = 1; d <= total; d++) {
    const str     = strFecha(viewYear, viewMonth, d);
    const esDesde = desde === str;
    const esHasta = hasta === str;
    const enRango = desde && hasta && str > desde && str < hasta;
    const esHoy   = d === hoy.getDate() && viewMonth === hoy.getMonth() && viewYear === hoy.getFullYear();
    let cls = 'cd';
    if (esDesde || esHasta) cls += ' sel';
    else if (enRango)       cls += ' rng';
    else if (esHoy)         cls += ' hoy';
    celdas.push(`<td class="${cls}" data-date="${str}" data-dp="${id}">${d}</td>`);
  }
  // Rellenar última fila
  while (celdas.length % 7 !== 0) celdas.push(`<td></td>`);

  // Agrupar en filas de 7
  let filas = '';
  for (let i = 0; i < celdas.length; i += 7) {
    filas += `<tr>${celdas.slice(i, i+7).join('')}</tr>`;
  }

  return `
    <div class="cal-header">
      <button class="cal-nav" data-dp="${id}" data-dir="-1" type="button">‹</button>
      <div class="cal-hcenter">
        <span class="cal-mes">${MESES[viewMonth]}</span>
        <select class="cal-anio" data-dp="${id}">${optsAnio}</select>
      </div>
      <button class="cal-nav" data-dp="${id}" data-dir="1" type="button">›</button>
    </div>
    <table class="cal-tabla">
      <thead><tr>
        <th>Lu</th><th>Ma</th><th>Mi</th><th>Ju</th><th>Vi</th><th>Sa</th><th>Do</th>
      </tr></thead>
      <tbody>${filas}</tbody>
    </table>
    <div class="cal-range-labels">
      <span>Desde: <strong>${desde || '—'}</strong></span>
      <span>Hasta: <strong>${hasta || '—'}</strong></span>
    </div>
    ${(desde || hasta)
      ? `<button class="btn btn-ghost cal-clear btn-sm" data-dp="${id}" data-action="clear" type="button">Limpiar fechas</button>`
      : ''}
  `;
}

const instancias = {};
let dpCount = 0;

export function crearDateRangePicker(wrapperId, onSelect, onClear) {
  const wrap = document.getElementById(wrapperId);
  if (!wrap) return null;

  const id   = 'dp_' + (++dpCount);
  const inst = {
    id,
    viewYear : new Date().getFullYear(),
    viewMonth: new Date().getMonth(),
    desde: null, hasta: null,
    onSelect, onClear
  };
  instancias[id] = inst;

  wrap.innerHTML = `
    <div class="date-wrap">
      <button class="date-btn" id="${id}-btn" type="button">
        <span id="${id}-lbl" style="color:var(--muted)">Seleccionar rango...</span>
      </button>
      <div class="date-cal" id="${id}-cal"></div>
    </div>`;

  const btn = document.getElementById(`${id}-btn`);
  const cal = document.getElementById(`${id}-cal`);

  btn.addEventListener('click', e => {
    e.stopPropagation();
    const abierto = cal.classList.contains('open');
    cerrarTodos();
    if (!abierto) { renderCal(); cal.classList.add('open'); btn.classList.add('open'); }
  });

  document.addEventListener('click', e => {
    if (!wrap.contains(e.target)) cerrarTodos();
  });

  function cerrarTodos() {
    document.querySelectorAll('.date-cal.open').forEach(c => c.classList.remove('open'));
    document.querySelectorAll('.date-btn.open').forEach(b => b.classList.remove('open'));
  }

  function renderCal() {
    cal.innerHTML = buildCal(inst);

    // Días — click
    cal.querySelectorAll('td[data-date]').forEach(td => {
      td.addEventListener('click', e => {
        e.stopPropagation();
        const fecha = td.dataset.date;
        if (!inst.desde || (inst.desde && inst.hasta)) {
          inst.desde = fecha; inst.hasta = null;
        } else if (fecha === inst.desde) {
          return;
        } else if (fecha < inst.desde) {
          inst.hasta = inst.desde; inst.desde = fecha;
        } else {
          inst.hasta = fecha;
        }
        actualizarLabel();
        renderCal();
        if (inst.desde && inst.hasta && onSelect) onSelect(inst.desde, inst.hasta);
      });
    });

    // Flechas mes
    cal.querySelectorAll('.cal-nav').forEach(btn => {
      btn.addEventListener('click', e => {
        e.stopPropagation();
        inst.viewMonth += parseInt(btn.dataset.dir);
        if (inst.viewMonth > 11) { inst.viewMonth = 0; inst.viewYear++; }
        if (inst.viewMonth < 0)  { inst.viewMonth = 11; inst.viewYear--; }
        renderCal();
      });
    });

    // Selector año
    const selAnio = cal.querySelector('.cal-anio');
    if (selAnio) {
      selAnio.addEventListener('change', e => {
        e.stopPropagation();
        inst.viewYear = parseInt(selAnio.value);
        renderCal();
      });
    }

    // Limpiar
    const btnClear = cal.querySelector('[data-action="clear"]');
    if (btnClear) {
      btnClear.addEventListener('click', e => {
        e.stopPropagation();
        inst.desde = null; inst.hasta = null;
        actualizarLabel();
        renderCal();
        if (onClear) onClear();
      });
    }

    // Evitar que cualquier click dentro cierre el calendario
    cal.addEventListener('click', e => e.stopPropagation(), { once: false });
  }

  function actualizarLabel() {
    const lbl = document.getElementById(`${id}-lbl`);
    if (!lbl) return;
    if (inst.desde && inst.hasta) {
      lbl.textContent = `${inst.desde}  →  ${inst.hasta}`;
      lbl.style.color = 'var(--navy)'; btn.classList.add('has-date');
    } else if (inst.desde) {
      lbl.textContent = `Desde: ${inst.desde}`;
      lbl.style.color = 'var(--navy)'; btn.classList.add('has-date');
    } else {
      lbl.textContent = 'Seleccionar rango...';
      lbl.style.color = 'var(--muted)'; btn.classList.remove('has-date');
    }
  }

  return {
    getDesde: () => inst.desde,
    getHasta: () => inst.hasta,
    reset: () => { inst.desde = null; inst.hasta = null; actualizarLabel(); }
  };
}
