/**
 * components/nav-state.js — Token de navegación.
 * Cada cambio de vista genera un token nuevo. Una vista asíncrona debe
 * verificar que su token siga vigente antes de escribir en el DOM, para no
 * pisar el contenido de otra vista si el usuario navegó antes de que
 * terminara de cargar.
 */
let tokenActual = 0;

export function nuevoToken() {
  return ++tokenActual;
}

export function esTokenVigente(token) {
  return token === tokenActual;
}
