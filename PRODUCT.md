# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
- **Personal de Shaya Café** (administrador y personal): trabaja en computador, a diario, en la operación de una empresa cafetera: compra de café pergamino a caficultores, procesos de maquila y tostado, inventario de pergamino y de café tostado, ventas (incluidas ventas rápidas y ferias), clientes, gastos y costos de producción.
- **Caficultores** (rol `farmer`): entran desde el celular, a menudo en la finca, al módulo de cultivo. Registran labores, cosechas, beneficio y secado de sus lotes, y consultan su resumen, alertas y la proyección de calidad. Solo ven sus propias fincas.

## Product Purpose
Sistema interno de gestión de Shaya Café que cubre el ciclo completo del café: del cultivo en la finca (trazabilidad desde la siembra hasta el pergamino seco) a la compra, el proceso, el inventario y la venta. Éxito: el personal opera el negocio sin hojas de cálculo y el caficultor registra su operación desde el celular, con la trazabilidad de cada venta hasta sus lotes.

## Positioning
Une en un solo sistema la operación de campo del caficultor y la operación comercial de la tostadora: un pergamino del inventario se rastrea hasta los lotes, labores y cosechas que lo produjeron.

## Operating Context
- Uso diario y repetitivo: formularios de registro, tablas, filtros y dashboards de consulta.
- El personal trabaja en escritorio; el caficultor, en celular y con conexión que puede ser irregular en el campo.
- Asistente conversacional integrado para consultar los datos del negocio.
- El sistema informa y nunca obliga: alertas y proyecciones orientan, no bloquean.

## Capabilities and Constraints
- Frontend: React 19 + Vite + TypeScript + Tailwind CSS 3, rutas con react-router, tablas con TanStack Table, gráficas con Recharts, íconos de lucide-react.
- Módulos: ventas, ventas rápidas, ferias, clientes, caficultores, productos, inventario de pergamino, procesos, café tostado y sus movimientos, gastos, usuarios, asistente y cultivo (fincas, lotes, ciclos, labores, cosechas, beneficio, secado, trazabilidad, pagos, cuentas, resumen con alertas y proyección de calidad).
- Roles: `admin`, `user` (personal) y `farmer` (solo el módulo de cultivo).
- Idioma de la interfaz: español (Colombia), con formatos de número y fecha de es-CO.
- La proyección de calidad sale de un modelo entrenado con datos sintéticos y siempre lleva su descargo.

## Brand Commitments
- Nombre: **Shaya Café**. Logo en `frontend/public/shaya.svg` y `frontend/public/logo.png`.
- El usuario quiere conservar el diseño actual y su paleta de verdes (esmeralda); la mejora es de UI/UX, no un cambio de identidad.
- Debe haber un botón para alternar modo claro y modo oscuro. La primera vez sigue la preferencia del dispositivo; si el usuario elige, se recuerda su elección.

## Evidence on Hand
- Datos de demostración: el generador sintético puebla fincas, lotes, cosechas, beneficios, secados y evaluaciones (`backend/scripts/farm_ml/`).
- Sin testimonios, clientes ni cifras comerciales publicables: no se deben inventar.

## Product Principles
1. La tarea primero: registrar y consultar rápido pesa más que la expresión visual.
2. Dos contextos reales: escritorio para el personal, celular en la finca para el caficultor; ambos deben funcionar igual de bien.
3. Informar sin obligar: alertas, proyecciones y avisos ayudan a decidir y nunca bloquean.
4. Continuidad: mejorar sin romper la familiaridad del diseño que el equipo ya usa.

## Accessibility & Inclusion
Sin un estándar formal definido. Uso en exteriores desde el celular (luz solar, pantallas pequeñas): contraste y tamaños de toque suficientes en ambos temas.
