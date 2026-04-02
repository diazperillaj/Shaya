/**
 * Ejecuta una acción asíncrona y muestra una alerta
 * según el resultado de la ejecución.
 *
 * Centraliza el manejo básico de éxito y error
 * para acciones que interactúan con la API.
 *
 * @param action Función asíncrona a ejecutar
 * @param successMessage Mensaje a mostrar si la acción es exitosa
 */
export const runWithAlert = async (
  action: () => Promise<void>,
  successMessage: string
): Promise<void> => {
  try {
    await action()
    alert(successMessage)
  } catch (err: any) {
    alert(err.message)
  }
}
