/**
 * components/confirm-modal.js — Modal de confirmación reutilizable.
 * Reemplaza a window.confirm() con un modal que respeta el estilo del resto
 * de la app (mismas clases .modal/.modal-title/.modal-footer que ya usan los
 * modales de "Eliminar"). Devuelve una Promise<boolean>: true si confirma.
 *
 * El mensaje se asigna via textContent (no innerHTML) para no correr riesgo
 * de inyectar HTML con nombres ingresados por el usuario.
 */
export function confirmarModal({
  titulo = 'Confirmar',
  mensaje = '',
  textoConfirmar = 'Continuar',
  textoCancelar = 'Cancelar',
} = {}) {
  return new Promise(resolve => {
    const overlay = document.createElement('div');
    overlay.style.cssText =
      'position:fixed;inset:0;background:rgba(0,20,60,.45);z-index:200;' +
      'display:flex;align-items:center;justify-content:center;padding:20px';
    overlay.innerHTML = `
      <div class="modal" style="max-width:440px">
        <div class="modal-title"></div>
        <div class="cm-mensaje" style="font-size:13px;color:var(--text);line-height:1.6;white-space:pre-line"></div>
        <div class="modal-footer">
          <button class="btn btn-ghost" data-accion="cancelar"></button>
          <button class="btn btn-primary" data-accion="confirmar"></button>
        </div>
      </div>`;

    overlay.querySelector('.modal-title').textContent            = titulo;
    overlay.querySelector('.cm-mensaje').textContent              = mensaje;
    overlay.querySelector('[data-accion="cancelar"]').textContent = textoCancelar;
    overlay.querySelector('[data-accion="confirmar"]').textContent = textoConfirmar;

    function cerrar(resultado) {
      overlay.remove();
      document.removeEventListener('keydown', onKey);
      resolve(resultado);
    }
    function onKey(e) {
      if (e.key === 'Escape') cerrar(false);
    }

    overlay.addEventListener('click', e => { if (e.target === overlay) cerrar(false); });
    overlay.querySelector('[data-accion="cancelar"]').addEventListener('click', () => cerrar(false));
    overlay.querySelector('[data-accion="confirmar"]').addEventListener('click', () => cerrar(true));
    document.addEventListener('keydown', onKey);

    document.body.appendChild(overlay);
  });
}
