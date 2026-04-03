import React, { createContext, useCallback, useMemo, useState } from "react";

export const ToastContext = createContext(null);

let idCounter = 1;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback((toast) => {
    const id = idCounter++;
    const next = { id, type: toast.type || "info", message: toast.message || "", timeoutMs: toast.timeoutMs ?? 4000 };
    setToasts((prev) => [next, ...prev].slice(0, 5));
    if (next.timeoutMs > 0) {
      window.setTimeout(() => removeToast(id), next.timeoutMs);
    }
    return id;
  }, [removeToast]);

  const value = useMemo(() => ({ addToast }), [addToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed right-4 top-4 z-50 space-y-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={[
              "rounded-xl px-4 py-3 shadow-glow ring-1 ring-white/10 backdrop-blur",
              t.type === "success" ? "bg-emerald-900/50" : "",
              t.type === "error" ? "bg-rose-900/50" : "",
              t.type === "info" ? "bg-indigo-900/50" : "",
            ].join(" ")}
          >
            <div className="text-sm font-semibold">{t.type.toUpperCase()}</div>
            <div className="text-sm opacity-90">{t.message}</div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

