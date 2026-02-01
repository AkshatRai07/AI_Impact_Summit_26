"use client";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "error" | "info";
  size?: "sm" | "md";
  className?: string;
}

export function Badge({ children, variant = "default", size = "sm", className = "" }: BadgeProps) {
  const variants = {
    default: "bg-slate-800 text-slate-300 border border-slate-700",
    success: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
    warning: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
    error: "bg-red-500/10 text-red-400 border border-red-500/20",
    info: "bg-blue-500/10 text-blue-400 border border-blue-500/20",
  };

  const sizes = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-2.5 py-1 text-sm",
  };

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full ${variants[variant]} ${sizes[size]} ${className}`}
    >
      {children}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const statusMap: Record<string, { variant: BadgeProps["variant"]; label: string }> = {
    queued: { variant: "default", label: "Queued" },
    submitted: { variant: "success", label: "Submitted" },
    failed: { variant: "error", label: "Failed" },
    retried: { variant: "warning", label: "Retried" },
    running: { variant: "info", label: "Running" },
    completed: { variant: "success", label: "Completed" },
    stopped: { variant: "warning", label: "Stopped" },
  };

  const config = statusMap[status] || { variant: "default", label: status };

  return <Badge variant={config.variant}>{config.label}</Badge>;
}
