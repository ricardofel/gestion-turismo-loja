/**
 * components/similitud.js — Detección de nombres parecidos (posibles duplicados).
 *
 * Compara el nombre nuevo contra un catálogo ya existente usando distancia de
 * Levenshtein sobre texto normalizado (sin tildes, minúsculas, sin artículos
 * ni preposiciones). Así detecta tanto variantes de redacción ("Plaza San
 * Francisco" vs "Plaza de San Francisco") como errores de tipeo ("Fransico").
 * No bloquea nada — solo permite advertir antes de guardar.
 */

const PALABRAS_VACIAS = new Set(['de', 'del', 'la', 'el', 'los', 'las', 'y', 'a', 'en']);

export function normalizar(texto) {
  return (texto || '')
    .normalize('NFD').replace(/[̀-ͯ]/g, '') // quita tildes
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')                      // quita puntuación/comillas
    .split(/\s+/)
    .filter(p => p && !PALABRAS_VACIAS.has(p))
    .join(' ')
    .trim();
}

function distanciaLevenshtein(a, b) {
  const m = a.length, n = b.length;
  const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = 0; i <= m; i++) dp[i][0] = i;
  for (let j = 0; j <= n; j++) dp[0][j] = j;
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      dp[i][j] = a[i - 1] === b[j - 1]
        ? dp[i - 1][j - 1]
        : 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
    }
  }
  return dp[m][n];
}

/**
 * Similitud entre 0 (nada parecido) y 1 (idéntico tras normalizar).
 * Combina dos señales:
 *  - Distancia de Levenshtein sobre el string completo (detecta typos y
 *    reordenamientos, ej. "Fransico" vs "Francisco").
 *  - Contención de palabras (detecta cuando falta la palabra genérica del
 *    lugar, ej. "San Sebastián" vs "Parque San Sebastián" — si se comparara
 *    solo el string completo, la diferencia de longitud hunde el score
 *    aunque en realidad es el mismo lugar).
 */
export function similitud(a, b) {
  const na = normalizar(a), nb = normalizar(b);
  if (!na || !nb) return 0;
  if (na === nb) return 1;

  const maxLen = Math.max(na.length, nb.length);
  const distRatio = 1 - distanciaLevenshtein(na, nb) / maxLen;

  const tokensA = na.split(' ').filter(Boolean);
  const tokensB = nb.split(' ').filter(Boolean);
  let contencion = 0;
  if (tokensA.length >= 2 && tokensB.length >= 2) {
    const setA = new Set(tokensA), setB = new Set(tokensB);
    const interseccion = [...setA].filter(t => setB.has(t)).length;
    contencion = interseccion / Math.min(setA.size, setB.size);
  }

  return Math.max(distRatio, contencion);
}

/**
 * Busca en `catalogo` los elementos cuyo nombre sea muy parecido a `nombreNuevo`.
 * `campoNombre` indica qué propiedad del elemento contiene el nombre a comparar
 * (por defecto 'nombre'; usar 'nombre_oficial' para eventos).
 * Devuelve los candidatos ordenados de más a menos parecido.
 */
export function buscarSimilares(nombreNuevo, catalogo, opciones = {}) {
  const { umbral = 0.78, excluirId = null, campoNombre = 'nombre' } = opciones;
  return (catalogo || [])
    .filter(item => item._id !== excluirId)
    .map(item => ({ item, score: similitud(nombreNuevo, item[campoNombre]) }))
    .filter(r => r.score >= umbral)
    .sort((a, b) => b.score - a.score);
}
