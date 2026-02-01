"use client";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "error" | "info";
  size?: "sm" | "md";
  className?: string;
}

export function Badge({ children, variant = "default", size = "sm", className = "" }: BadgeProps) {
  const variants = {
    default: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300",
    success: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    warning: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
    error: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
    info: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
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
