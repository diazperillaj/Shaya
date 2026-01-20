export const runWithAlert = async (
  action: () => Promise<void>,
  successMessage: string
) => {
  try {
    await action()
    alert(successMessage)
  } catch (err: any) {
    alert(err.message)
  }
}