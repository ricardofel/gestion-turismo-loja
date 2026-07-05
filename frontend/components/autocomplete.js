/**
 * components/autocomplete.js
 * Componente de búsqueda con sugerencias reutilizable.
 * Solo acepta una selección válida del catálogo.
 */

export function crearAutocomplete(wrapperId, placeholder, catalogo, onSelect, onClear, valorInicial = null) {
  const wrap = document.getElementById(wrapperId);
  if (!wrap) return null;

  wrap.innerHTML = `
    <div class="ac-wrap">
      <input class="ac-input" placeholder="${placeholder}" autocomplete="off">
      <button class="ac-clear" style="display:none" title="Limpiar">×</button>
      <div class="ac-dropdown"></div>
    </div>`;

  const input    = wrap.querySelector('.ac-input');
  const dropdown = wrap.querySelector('.ac-dropdown');
  const clearBtn = wrap.querySelector('.ac-clear');
  let seleccionado = null;

  // Si ya hay un valor asignado (ej. editando un recurso que ya tiene lugar),
  // se muestra como realmente seleccionado — no como placeholder — para que
  // el campo no se vea vacío cuando en realidad sí tiene un valor guardado.
  if (valorInicial) {
    seleccionado = valorInicial;
    input.value = valorInicial.nombre;
    input.classList.add('has-value');
    clearBtn.style.display = 'block';
  }

  function mostrarOpciones(txt) {
    const q = txt.toLowerCase().trim();
    const lista = q
      ? catalogo.filter(c => c.nombre.toLowerCase().includes(q))
      : catalogo.slice(0, 8);

    dropdown.innerHTML = '';
    if (!q && !lista.length) { dropdown.classList.remove('open'); return; }

    if (!lista.length) {
      dropdown.innerHTML = `<div class="ac-item no-match">Sin coincidencias</div>`;
    } else {
      lista.forEach(c => {
        const el = document.createElement('div');
        el.className = 'ac-item';
        el.textContent = c.nombre;
        el.addEventListener('mousedown', e => {
          e.preventDefault();
          seleccionado = c;
          input.value = c.nombre;
          input.classList.add('has-value');
          clearBtn.style.display = 'block';
          dropdown.classList.remove('open');
          if (onSelect) onSelect(c);
        });
        dropdown.appendChild(el);
      });
    }
    dropdown.classList.add('open');
  }

  input.addEventListener('input', () => {
    seleccionado = null;
    input.classList.remove('has-value');
    clearBtn.style.display = 'none';
    mostrarOpciones(input.value);
    if (onClear) onClear();
  });

  input.addEventListener('focus', () => mostrarOpciones(input.value));

  input.addEventListener('blur', () => {
    setTimeout(() => {
      dropdown.classList.remove('open');
      if (!seleccionado && input.value) {
        input.value = '';
        input.classList.remove('has-value');
        clearBtn.style.display = 'none';
        if (onClear) onClear();
      }
    }, 150);
  });

  clearBtn.addEventListener('click', () => {
    seleccionado = null;
    input.value  = '';
    input.classList.remove('has-value');
    clearBtn.style.display = 'none';
    dropdown.classList.remove('open');
    if (onClear) onClear();
  });

  return {
    getValue : () => seleccionado?.id   || null,
    getNombre: () => seleccionado?.nombre || null,
    reset    : () => clearBtn.click(),
  };
}
