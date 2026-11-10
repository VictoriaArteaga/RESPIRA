// Cierra la aplicación de escritorio. En el navegador (solo desarrollo) intenta cerrar la pestaña.
export async function quitApp(): Promise<void> {
  if (window.respiraDesktop) {
    await window.respiraDesktop.quit()
    return
  }
  window.close()
}
