/**
 * Reparte un total entre lotes en proporción a su área; en partes iguales
 * si a alguno le falta el área (o todos la tienen en cero).
 *
 * Cada parte se redondea a `decimals` y la última absorbe el redondeo, para
 * que la suma sea exactamente el total.
 */
export function splitByArea(
  total: number,
  plots: { id: number; area: number | null }[],
  decimals: number,
): Record<number, number> {
  if (plots.length === 0) return {}

  const byArea = plots.every((plot) => plot.area !== null && plot.area > 0)
  const weights = plots.map((plot) => (byArea ? (plot.area as number) : 1))
  const weightSum = weights.reduce((sum, weight) => sum + weight, 0)
  const factor = 10 ** decimals
  const round = (value: number) => Math.round(value * factor) / factor

  const shares: Record<number, number> = {}
  let assigned = 0
  plots.forEach((plot, index) => {
    const isLast = index === plots.length - 1
    const share = isLast ? round(total - assigned) : round((total * weights[index]) / weightSum)
    shares[plot.id] = share
    assigned += share
  })
  return shares
}

/** Si el reparto es por área o en partes iguales, para explicarlo al usuario */
export const splitsByArea = (plots: { area: number | null }[]): boolean =>
  plots.length > 0 && plots.every((plot) => plot.area !== null && plot.area > 0)
