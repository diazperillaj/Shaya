import React from 'react'

/**
 * Renderizador de markdown ligero para las respuestas del asistente.
 *
 * Soporta lo que el system prompt permite emitir: negrilla, código inline,
 * listas, títulos pequeños y tablas. Sin dependencias externas y sin HTML
 * crudo (el texto siempre se renderiza como texto → sin riesgo XSS).
 */

/** Partes inline: **negrilla** y `código`. */
const renderInline = (text: string): React.ReactNode[] => {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code key={i} className="bg-gray-100 text-emerald-900 px-1 py-0.5 rounded text-[0.85em]">
          {part.slice(1, -1)}
        </code>
      )
    }
    return <React.Fragment key={i}>{part}</React.Fragment>
  })
}

const isTableRow = (line: string): boolean => line.trim().startsWith('|')
const isTableSeparator = (line: string): boolean =>
  /^\s*\|?[\s:-]+\|[\s|:-]*$/.test(line) && line.includes('-')

const splitRow = (line: string): string[] =>
  line
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((c) => c.trim())

interface Props {
  text: string
}

export default function Markdown({ text }: Props) {
  const lines = text.split('\n')
  const blocks: React.ReactNode[] = []
  let i = 0

  while (i < lines.length) {
    const line = lines[i]

    // Tabla: fila + separador
    if (isTableRow(line) && i + 1 < lines.length && isTableSeparator(lines[i + 1])) {
      const header = splitRow(line)
      i += 2
      const rows: string[][] = []
      while (i < lines.length && isTableRow(lines[i])) {
        rows.push(splitRow(lines[i]))
        i++
      }
      blocks.push(
        <div key={blocks.length} className="overflow-x-auto my-2">
          <table className="text-sm border-collapse w-full">
            <thead>
              <tr>
                {header.map((h, j) => (
                  <th
                    key={j}
                    className="text-left font-semibold text-gray-700 border-b border-gray-200 px-2 py-1.5 whitespace-nowrap"
                  >
                    {renderInline(h)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, r) => (
                <tr key={r} className="even:bg-gray-50">
                  {row.map((cell, c) => (
                    <td key={c} className="border-b border-gray-100 px-2 py-1.5 whitespace-nowrap">
                      {renderInline(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      )
      continue
    }

    // Lista
    if (/^\s*[-*•]\s+/.test(line)) {
      const items: string[] = []
      while (i < lines.length && /^\s*[-*•]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*•]\s+/, ''))
        i++
      }
      blocks.push(
        <ul key={blocks.length} className="list-disc pl-5 my-1.5 space-y-0.5">
          {items.map((item, j) => (
            <li key={j}>{renderInline(item)}</li>
          ))}
        </ul>,
      )
      continue
    }

    // Título pequeño (el asistente rara vez los usa)
    if (/^#{1,4}\s+/.test(line)) {
      blocks.push(
        <p key={blocks.length} className="font-semibold text-gray-900 mt-2 mb-1">
          {renderInline(line.replace(/^#{1,4}\s+/, ''))}
        </p>,
      )
      i++
      continue
    }

    // Párrafo (líneas vacías separan)
    if (line.trim() === '') {
      i++
      continue
    }
    const para: string[] = [line]
    i++
    while (i < lines.length && lines[i].trim() !== '' && !isTableRow(lines[i]) && !/^\s*[-*•]\s+/.test(lines[i]) && !/^#{1,4}\s+/.test(lines[i])) {
      para.push(lines[i])
      i++
    }
    blocks.push(
      <p key={blocks.length} className="my-1 leading-relaxed">
        {para.map((p, j) => (
          <React.Fragment key={j}>
            {j > 0 && <br />}
            {renderInline(p)}
          </React.Fragment>
        ))}
      </p>,
    )
  }

  return <>{blocks}</>
}
