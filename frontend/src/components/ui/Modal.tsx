// src/components/ui/EditModal.tsx
import { useEffect, useId, useState } from "react";
import type { TableField } from "../../models/common";
import { Pencil, X, Check, Trash2, Eye, EyeOff } from "lucide-react";

type ModalMode = "add" | "edit";

interface ModalProps<T> {
  item: T;
  fields: TableField<T>[];
  onClose: () => void;
  onSave: (item: T) => void;
  onDelete?: (id: string | number) => void;
  idKey?: keyof T; // por defecto "id" para eliminar
  mode?: ModalMode;
  title?: string;
}

export default function Modal<T>({
  item,
  fields,
  onClose,
  onSave,
  onDelete,
  idKey = "id" as keyof T,
  mode = "edit",
  title,
}: ModalProps<T>) {
  const [formData, setFormData] = useState<T>({ ...item });

  const isEdit = mode === "edit";
  const [isPasswordVisible, setIsPasswordVisible] = useState<boolean>(false);
  const titleId = useId();

  // Escape cierra el diálogo, como en cualquier ventana del sistema
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm z-50 p-4 animate-fadeIn">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="bg-white rounded-2xl shadow-2xl w-full max-w-md animate-slideUp text-left dark:ring-1 dark:ring-white/10"
      >
        {/* Header */}
        <div className="bg-emerald-900 dark:bg-emerald-950 rounded-t-2xl px-6 py-5 flex items-center justify-between">
          <h2 id={titleId} className="text-lg font-semibold text-white flex items-center gap-3">
            <div>
              <Pencil className="w-5 h-5" />
            </div>
            {isEdit ? `Editar ${title}` : `Agregar ${title}`}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="text-white/80 hover:text-white hover:bg-white/10 rounded-lg p-2 transition-colors duration-150 focus-visible:outline-white/70"
          >
            <div>
              <X className="w-5 h-5" />
            </div>
          </button>
        </div>

        {/* Body */}
        <div className="p-6">
          <div className="flex flex-col gap-4 max-h-[60vh] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-emerald-200 scrollbar-track-gray-100">
            {fields.map((field) => (
              <div
                key={String(field.accessor)}
                className="flex flex-col gap-2 relative"
              >
                <label className="flex text-md font-semibold text-gray-700 ps-2">
                  {field.header}
                </label>

                {/* SELECT */}
                {field.type === "select" && (
                  <select
                    value={formData[field.accessor] as string}
                    onChange={(e) =>
                      setFormData(
                        (prev) =>
                          ({
                            ...prev,
                            [field.accessor]: e.target.value,
                          }) as T,
                      )
                    }
                    className="text-sm border border-gray-200 rounded-xl px-4 py-3 bg-white focus:outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/20 transition-[border-color,box-shadow] duration-150"
                  >
                    {field.options?.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                )}

                {/* CHECK */}
                {field.type === "checkbox" && (
                  <input
                    type="checkbox"
                    checked={Boolean(formData[field.accessor])}
                    onChange={(e) =>
                      setFormData(
                        (prev) =>
                          ({
                            ...prev,
                            [field.accessor]: e.target.checked,
                          }) as T,
                      )
                    }
                    className="ms-2 h-5 w-5 rounded border-gray-300 accent-emerald-700"
                  />
                )}

                {/* TEXTAREA */}
                {field.type === "textarea" && (
                  <textarea
                    value={formData[field.accessor] as string}
                    onChange={(e) =>
                      setFormData(
                        (prev) =>
                          ({
                            ...prev,
                            [field.accessor]: e.target.value,
                          }) as T,
                      )
                    }
                    rows={5}
                    className="text-sm border border-gray-200 rounded-xl px-4 py-3 bg-white resize-none focus:outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/20 transition-[border-color,box-shadow] duration-150"
                    placeholder={`Ingrese ${field.header.toLowerCase()}`}
                  />
                )}

                {/* INPUT TEXT / PASSWORD / NUMBER / DATE */}
                {(field.type === "text" ||
                  field.type === "password" ||
                  field.type === "number" ||
                  field.type === "date" ||
                  field.type === "datetime-local") && (
                  <div className="relative">
                    <input
                      type={
                        field.type === "password"
                          ? isPasswordVisible
                            ? "text"
                            : "password"
                          : field.type
                      }
                      value={formData[field.accessor] as string | number}
                      onChange={(e) =>
                        setFormData(
                          (prev) =>
                            ({
                              ...prev,
                              [field.accessor]:
                                field.type === "number"
                                  ? Number(e.target.value)
                                  : e.target.value,
                            }) as T,
                        )
                      }
                      className="text-sm border border-gray-200 rounded-xl px-4 py-3 pr-12 bg-white w-full focus:outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/20 transition-[border-color,box-shadow] duration-150"
                      placeholder={`Ingrese ${field.header.toLowerCase()}`}
                    />

                    {/* ICONO PASSWORD */}
                    {field.type === "password" && (
                      <button
                        type="button"
                        className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg p-1"
                        onClick={() => setIsPasswordVisible((prev) => !prev)}
                        aria-label={isPasswordVisible ? "Ocultar contraseña" : "Mostrar contraseña"}
                      >
                        {isPasswordVisible ? (
                          <EyeOff className="w-5 h-5 text-gray-400" />
                        ) : (
                          <Eye className="w-5 h-5 text-gray-400" />
                        )}
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 rounded-b-2xl border-t border-gray-100">
          <div className="flex flex-wrap gap-3 justify-end">
            {onDelete && isEdit && (
              <button
                onClick={() => {
                  // Pregunta de confirmación
                  const confirmed = window.confirm(
                    `¿Eliminar este registro${title ? ` de ${title.toLowerCase()}` : ""}? Esta acción no se puede deshacer.`,
                  );
                  if (!confirmed) return; // si el usuario cancela, no hacemos nada

                  // Llamada a la función de delete, convirtiendo id a número
                  onDelete(Number(formData[idKey]));
                }}
                type="button"
                className="bg-red-800 hover:bg-red-900 text-white shadow-sm px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 transition-[transform,background-color,box-shadow] duration-150 ease-out active:scale-[0.97]"
              >
                <div>
                  <Trash2 className="w-5 h-5" />
                </div>
                Eliminar
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              className="bg-white hover:bg-gray-100 text-gray-700 border border-gray-200 shadow-sm px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 transition-[transform,background-color,box-shadow] duration-150 ease-out active:scale-[0.97]"
            >
              <div>
                <X className="w-5 h-5" />
              </div>
              Cancelar
            </button>
            <button
              type="button"
              onClick={() => onSave(formData)}
              className="bg-emerald-900 hover:bg-emerald-950 text-white shadow-sm px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 transition-[transform,background-color,box-shadow] duration-150 ease-out active:scale-[0.97]"
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
