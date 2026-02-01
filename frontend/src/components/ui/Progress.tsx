"use client";

interface ProgressProps {
  value: number;
  max?: number;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  className?: string;
  gradient?: boolean;
}

export function Progress({
  value,
  max = 100,
  size = "md",
  showLabel = false,
  className = "",
  gradient = true,
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
        <div className="flex justify-between mb-2 text-sm">
          <span className="text-slate-400">Progress</span>
          <span className="text-white font-medium">
            {Math.round(percentage)}%
          </span>
        </div>
      )}
      <div
        className={`w-full bg-slate-800 rounded-full overflow-hidden ${sizes[size]}`}
      >
        <div
          className={`${sizes[size]} rounded-full transition-all duration-500 ease-out ${gradient ? 'bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500' : 'bg-blue-500'}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
