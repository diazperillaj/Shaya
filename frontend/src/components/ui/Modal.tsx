// src/components/ui/EditModal.tsx
import { useState } from 'react';
import type { TableField } from '../../models/common';
import { Pencil, X, Check, Trash2 } from 'lucide-react';

type ModalMode = 'add'|'edit';

interface ModalProps<T> {
  item: T;
  fields: TableField<T>[];
  onClose: () => void;
  onSave: (item: T) => void;
  onDelete?: (id: string | number) => void;
  idKey?: keyof T; // por defecto "id" para eliminar
  mode?: ModalMode;
}

export default function Modal<T>({
  item,
  fields,
  onClose,
  onSave,
  onDelete,
  idKey = 'id' as keyof T,
  mode = 'edit',

}: ModalProps<T>) {
  const [formData, setFormData] = useState<T>({ ...item });

  const isEdit = mode === 'edit';

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm z-50 p-4 animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md transform transition-all animate-slideUp">
        {/* Header */}
        <div className="bg-gradient-to-r from-emerald-900 via-emerald-800 to-emerald-900 rounded-t-2xl px-6 py-5 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white flex items-center gap-3">
            <div>
              <Pencil className="w-5 h-5" />
            </div>
            {isEdit ? 'Editar elemento' : 'Agregar elemento'}
          </h2>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white hover:bg-white/10 rounded-lg p-2 transition-all duration-200"
          >
            <div>
              <X className="w-5 h-5" />
            </div>
          </button>
        </div>

        {/* Body */}
        <div className="p-6">
          <div className="flex flex-col gap-4 max-h-[60vh] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-emerald-200 scrollbar-track-gray-100">
            {fields.map(field => (
              <div key={String(field.accessor)} className="flex flex-col gap-2">
                <label className="text-md font-semibold text-gray-700 flex ps-2">
                  {field.header}
                </label>
                <input
                  type="text"
                  value={formData[field.accessor] as string}
                  onChange={e =>
                    setFormData(prev => ({ ...prev, [field.accessor]: e.target.value } as T))
                  }
                  className="border border-gray-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200 hover:border-emerald-300"
                  placeholder={`Ingrese ${field.header.toLowerCase()}`}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 rounded-b-2xl border-t border-gray-100">
          
          <div className="flex flex-wrap gap-3 justify-end">
            {onDelete && isEdit && (
              <button
                onClick={() => onDelete(formData[idKey] as string | number)}
                className="bg-red-800 hover:bg-red-900 text-white px-5 py-2.5 rounded-xl font-medium shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200 flex items-center gap-2"
              >
                <div>
                  <Trash2 className="w-5 h-5" />
                </div>
                Eliminar
              </button>
            )}
            <button
              onClick={onClose}
              className="bg-white hover:bg-gray-100 text-gray-700 px-5 py-2.5 rounded-xl font-medium shadow-sm hover:shadow-md transform hover:scale-105 transition-all duration-200 border border-gray-200 flex items-center gap-2"
            >
              <div>
                <X className="w-5 h-5" />
              </div>
              Cancelar
            </button>
            <button
              onClick={() => onSave(formData)}
              className="bg-emerald-900 hover:bg-emerald-950 text-white px-5 py-2.5 rounded-xl font-medium shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200 flex items-center gap-2"
            >
              <div>
                <Check className="w-5 h-5" />
              </div>
              Guardar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}