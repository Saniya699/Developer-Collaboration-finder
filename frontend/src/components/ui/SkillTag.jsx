import React from "react";

export default function SkillTag({ skill, className = "" }) {
  return (
    <span
      className={[
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold",
        "bg-indigo-600/20 text-indigo-200 ring-1 ring-indigo-500/30",
        className,
      ].join(" ")}
    >
      {skill}
    </span>
  );
}

