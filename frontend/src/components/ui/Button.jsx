import React from "react";

export default function Button({
  as: As = "button",
  variant = "primary",
  className = "",
  disabled = false,
  children,
  ...props
}) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed";

  const styles =
    variant === "primary"
      ? "bg-indigo-600 hover:bg-indigo-500 text-white shadow-glow"
      : variant === "secondary"
        ? "bg-white/5 hover:bg-white/10 text-indigo-200 ring-1 ring-white/10"
        : variant === "danger"
          ? "bg-rose-600/90 hover:bg-rose-500 text-white"
          : "bg-white/5 text-white ring-1 ring-white/10";

  if (As !== "button") {
    return (
      <As className={`${base} ${styles} ${className}`} aria-disabled={disabled ? "true" : undefined} {...props}>
        {children}
      </As>
    );
  }

  return (
    <button className={`${base} ${styles} ${className}`} disabled={disabled} {...props}>
      {children}
    </button>
  );
}

