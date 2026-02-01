"use client";

interface ProgressProps {
  value: number;
  max?: number;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  className?: string;
}

export function Progress({
  value,
  max = 100,
  size = "md",
  showLabel = false,
  className = "",
}: ProgressProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  const sizes = {
    sm: "h-1.5",
    md: "h-2.5",
    lg: "h-4",
  };

  return (
    <div className={`w-full ${className}`}>
      {showLabel && (
        <div className="flex justify-between mb-1 text-sm">
          <span className="text-gray-600 dark:text-gray-400">Progress</span>
          <span className="text-gray-900 dark:text-gray-100 font-medium">
            {Math.round(percentage)}%
          </span>
        </div>
      )}
      <div
        className={`w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden ${sizes[size]}`}
      >
        <div
          className={`bg-blue-600 ${sizes[size]} rounded-full transition-all duration-300 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
