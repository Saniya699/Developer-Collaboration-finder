import React from "react";

export default function Input({
  label,
  value,
  onChange,
  placeholder = "",
  type = "text",
  className = "",
  ...props
}) {
  return (
    <label className="block">
      {label ? <div className="mb-2 text-sm font-semibold text-slate-200">{label}</div> : null}
      <input
        value={value ?? ""}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder={placeholder}
        type={type}
        className={[
          "w-full rounded-xl bg-white/5 px-4 py-2 text-sm outline-none ring-1 ring-white/10",
          "focus:ring-indigo-500/40",
          className,
        ].join(" ")}
        {...props}
      />
    </label>
  );
}

