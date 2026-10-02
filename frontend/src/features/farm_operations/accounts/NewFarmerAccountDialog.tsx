import { UserPlus } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { FormSection, TextField } from '../components/fields'
import { textOrNull, useFormValues } from '../components/useFormValues'
import { createFarmerWithAccount } from '../services/farmerAccounts.api'

/**
 * Registrar un caficultor nuevo con su cuenta, en una sola operación:
 * persona, registro de caficultor y usuario `farmer`.
 */
export default function NewFarmerAccountDialog({
  onClose,
  onSaved,
}: {
  onClose: () => void
  onSaved: () => void
}) {
  const { values, bind, requireFields, setFieldError } = useFormValues({
    full_name: '',
    document: '',
    phone: '',
    email: '',
    farm_name: '',
    village: '',
    municipality: '',
    username: '',
    password: '',
    confirmation: '',
  })

  const handleSubmit = async () => {
    const complete = requireFields([
      'full_name', 'phone', 'farm_name', 'village', 'municipality',
      'username', 'password', 'confirmation',
    ])
    if (!complete) return
    if (values.password !== values.confirmation) {
      setFieldError('confirmation', 'Las contraseñas no coinciden')
      return
    }
    await createFarmerWithAccount({
      farm_name: values.farm_name.trim(),
      village: values.village.trim(),
      municipality: values.municipality.trim(),
      person: {
        full_name: values.full_name.trim(),
        document: textOrNull(values.document),
        phone: values.phone.trim(),
        email: textOrNull(values.email),
      },
      username: values.username.trim(),
      password: values.password,
    })
    onSaved()
  }

  return (
    <FormDialog
      wide
      title="Nuevo caficultor con cuenta"
      description="Queda registrado como caficultor (también para compras de pergamino) y con acceso a Cultivo."
      icon={UserPlus}
      submitLabel="Registrar"
      onClose={onClose}
      onSubmit={handleSubmit}
    >
      <FormSection title="Datos personales">
        <TextField label="Nombre completo" required wide {...bind('full_name')} />
        <TextField label="Documento" hint="Solo números." {...bind('document')} />
        <TextField label="Teléfono" type="tel" required hint="10 dígitos." {...bind('phone')} />
        <TextField label="Correo" type="email" wide {...bind('email')} />
      </FormSection>

      <FormSection title="Registro de caficultor">
        <TextField
          label="Finca principal"
          required
          wide
          hint="Mínimo 4 caracteres. Sus fincas de cultivo se registran después, en Fincas."
          {...bind('farm_name')}
        />
        <TextField label="Vereda" required {...bind('village')} />
        <TextField label="Municipio" required {...bind('municipality')} />
      </FormSection>

      <FormSection title="Acceso">
        <TextField label="Usuario" required wide hint="Mínimo 4 caracteres." {...bind('username')} />
        <TextField label="Contraseña" type="password" required hint="Mínimo 6 caracteres." {...bind('password')} />
        <TextField label="Confirmar contraseña" type="password" required {...bind('confirmation')} />
      </FormSection>
    </FormDialog>
  )
}
