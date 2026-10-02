import { KeyRound } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { FormSection, TextField } from '../components/fields'
import { useFormValues } from '../components/useFormValues'
import type { FarmerAccount } from '../models/types'
import { createFarmerAccount } from '../services/farmerAccounts.api'

/**
 * Dar acceso a un caficultor ya registrado: se le crea un usuario con rol
 * `farmer` sobre su misma persona.
 */
export default function GrantAccessDialog({
  account,
  onClose,
  onSaved,
}: {
  account: FarmerAccount
  onClose: () => void
  onSaved: () => void
}) {
  const { values, bind, requireFields, setFieldError } = useFormValues({
    username: '',
    password: '',
    confirmation: '',
  })

  const handleSubmit = async () => {
    if (!requireFields(['username', 'password', 'confirmation'])) return
    if (values.password !== values.confirmation) {
      setFieldError('confirmation', 'Las contraseñas no coinciden')
      return
    }
    await createFarmerAccount({
      farmer_id: account.farmer_id,
      username: values.username.trim(),
      password: values.password,
    })
    onSaved()
  }

  return (
    <FormDialog
      title={`Dar acceso a ${account.full_name}`}
      description="Entrega estas credenciales al caficultor: solo verá sus propias fincas."
      icon={KeyRound}
      submitLabel="Crear cuenta"
      onClose={onClose}
      onSubmit={handleSubmit}
    >
      <FormSection>
        <TextField label="Usuario" required wide hint="Mínimo 4 caracteres." {...bind('username')} />
        <TextField label="Contraseña" type="password" required hint="Mínimo 6 caracteres." {...bind('password')} />
        <TextField label="Confirmar contraseña" type="password" required {...bind('confirmation')} />
      </FormSection>
    </FormDialog>
  )
}
