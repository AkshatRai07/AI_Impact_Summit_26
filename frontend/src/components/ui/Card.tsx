"use client";

import { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: "none" | "sm" | "md" | "lg";
  glow?: boolean;
}

export function Card({ children, className = "", padding = "md", glow = false }: CardProps) {
  const paddings = {
    none: "",
    sm: "p-3",
    md: "p-4 sm:p-6",
    lg: "p-6 sm:p-8",
  };

  return (
    <div className={`relative ${glow ? 'group' : ''}`}>
      {glow && (
        <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-2xl blur opacity-0 group-hover:opacity-75 transition-opacity duration-500" />
      )}
      <div
        className={`relative bg-[#121214]/80 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl ${paddings[padding]} ${className}`}
      >
        {children}
      </div>
    </div>
  );
}

interface CardHeaderProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function CardHeader({ title, description, action }: CardHeaderProps) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h3 className="text-lg font-semibold text-white">
          {title}
        </h3>
        {description && (
          <p className="mt-1 text-sm text-slate-400">
            {description}
          </p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}
