import React from "react";

export default function Spinner({ className = "" }) {
  return (
    <div className={className} aria-label="Loading">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-white/20 border-t-indigo-300" />
    </div>
  );
}

