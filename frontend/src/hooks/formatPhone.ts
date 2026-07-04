export const fmtPhone = (value?: number | string) => {
  if (!value) return '';

  // Convertir a string y quitar todo lo que no sea número
  const digits = value.toString().replace(/\D/g, '');

  // Limitar a 10 dígitos
  const clean = digits.slice(0, 10);

  // Formatear XXX XXX XXXX
  return clean.replace(
    /^(\d{3})(\d{3})(\d{4})$/,
    '$1 $2 $3'
  );
};