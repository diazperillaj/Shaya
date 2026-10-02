import { useCallback, useState } from 'react'
import { KeyRound, UserPlus } from 'lucide-react'
import { Badge, Button, EmptyState, ErrorMessage, Loading, PageHeader } from '../components/ui'
import { useLoader } from '../components/useLoader'
import { plural } from '../format'
import type { FarmerAccount } from '../models/types'
import { fetchFarmerAccounts } from '../services/farmerAccounts.api'
import GrantAccessDialog from './GrantAccessDialog'
import NewFarmerAccountDialog from './NewFarmerAccountDialog'

/**
 * Cuentas de los caficultores (solo administradores).
 *
 * No hay autoregistro: el administrador da acceso a un caficultor ya
 * registrado o registra uno nuevo con su cuenta.
 */
export default function FarmerAccountsPage() {
  const load = useCallback(() => fetchFarmerAccounts(), [])
  const { data: accounts, error, loading, reload } = useLoader(load)

  const [dialog, setDialog] = useState<{ grant?: FarmerAccount } | null>(null)
  const closeAndReload = () => {
    setDialog(null)
    reload()
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        icon={KeyRound}
        title="Cuentas de caficultores"
        subtitle="Con su cuenta, cada caficultor registra sus fincas y solo ve lo suyo. Las cuentas las crea un administrador."
        actions={
          <Button variant="primary" icon={UserPlus} onClick={() => setDialog({})}>
            Nuevo caficultor con cuenta
          </Button>
        }
      />

      {error && <ErrorMessage message={error} />}
      {loading && <Loading />}

      {accounts && accounts.length === 0 && (
        <EmptyState icon={KeyRound} title="Aún no hay caficultores registrados" />
      )}

      {accounts && accounts.length > 0 && (
        <ul className="divide-y divide-gray-100 rounded-2xl border border-gray-100 bg-white shadow-sm">
          {accounts.map((account) => (
            <li key={account.farmer_id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
              <div>
                <p className="text-sm font-medium text-gray-900">{account.full_name}</p>
                <p className="text-xs text-gray-400">
                  {[account.document, account.phone].filter(Boolean).join(' · ') || 'Sin documento ni teléfono'}
                  {' · '}
                  {plural(account.farms, 'finca', 'fincas')}
                </p>
              </div>
              <AccountStatus account={account} onGrant={() => setDialog({ grant: account })} />
            </li>
          ))}
        </ul>
      )}

      {dialog?.grant && (
        <GrantAccessDialog account={dialog.grant} onClose={() => setDialog(null)} onSaved={closeAndReload} />
      )}
      {dialog && !dialog.grant && (
        <NewFarmerAccountDialog onClose={() => setDialog(null)} onSaved={closeAndReload} />
      )}
    </div>
  )
}

function AccountStatus({ account, onGrant }: { account: FarmerAccount; onGrant: () => void }) {
  if (account.account_role === 'farmer') {
    return <Badge tone="green">Con acceso · {account.username}</Badge>
  }
  if (account.account_role) {
    // La persona ya tiene una cuenta del personal de Shaya
    return <Badge tone="blue">Cuenta de personal · {account.username}</Badge>
  }
  return (
    <Button icon={KeyRound} onClick={onGrant}>
      Dar acceso
    </Button>
  )
}
