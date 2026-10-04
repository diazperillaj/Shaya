// Rendered once outside Recharts — SVG gradient IDs are global in the browser
export default function GlobalChartDefs() {
  return (
    <svg width="0" height="0" style={{ position: 'absolute', overflow: 'hidden' }} aria-hidden>
      <defs>
        <linearGradient id="gv0" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#10b981" stopOpacity={0.95} />
          <stop offset="100%" stopColor="#065f46" stopOpacity={1} />
        </linearGradient>
        <linearGradient id="gv1" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#34d399" stopOpacity={0.95} />
          <stop offset="100%" stopColor="#059669" stopOpacity={1} />
        </linearGradient>
        <linearGradient id="gv2" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#6ee7b7" stopOpacity={0.95} />
          <stop offset="100%" stopColor="#34d399" stopOpacity={1} />
        </linearGradient>
        <linearGradient id="gv3" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#a7f3d0" stopOpacity={0.95} />
          <stop offset="100%" stopColor="#6ee7b7" stopOpacity={1} />
        </linearGradient>
        <linearGradient id="gh1" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#34d399" stopOpacity={0.95} />
          <stop offset="100%" stopColor="#059669" stopOpacity={1} />
        </linearGradient>
      </defs>
    </svg>
  )
}
