import React from "react";

export default function Card({ className = "", children }) {
  return (
    <div
      className={[
        "rounded-2xl bg-white/5 ring-1 ring-white/10 shadow-[0_0_0_1px_rgba(99,102,241,0.08)] backdrop-blur",
        className,
      ].join(" ")}
    >
      {children}
    </div>
  );
}

