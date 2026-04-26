"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string;
  sub?: string;
  trend?: number;
  loading?: boolean;
  className?: string;
}

export function StatCard({
  label,
  value,
  sub,
  trend,
  loading,
  className,
}: StatCardProps) {
  const isPositive = trend !== undefined && trend >= 0;

  return (
    <div
      className={cn(
        "rounded-2xl bg-card border border-border p-6 flex flex-col gap-3",
        className
      )}
    >
      <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
        {label}
      </p>

      {loading ? (
        <>
          <Skeleton className="h-9 w-36" />
          <Skeleton className="h-4 w-24" />
        </>
      ) : (
        <>
          <p className="text-3xl font-semibold tracking-tight text-foreground leading-none">
            {value}
          </p>
          {(sub !== undefined || trend !== undefined) && (
            <p
              className={cn(
                "text-sm font-medium",
                trend !== undefined
                  ? isPositive
                    ? "text-emerald-400"
                    : "text-red-400"
                  : "text-muted-foreground"
              )}
            >
              {trend !== undefined && (
                <span>{isPositive ? "▲" : "▼"} {Math.abs(trend).toFixed(2)}% </span>
              )}
              {sub}
            </p>
          )}
        </>
      )}
    </div>
  );
}
