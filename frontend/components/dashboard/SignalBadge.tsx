import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { SignalLabel } from "@/types";

const SIGNAL_CONFIG: Record<
  SignalLabel,
  { label: string; className: string }
> = {
  strong_buy: {
    label: "Strong Buy",
    className: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
  },
  buy: {
    label: "Buy",
    className: "bg-emerald-500/10 text-emerald-500 border-emerald-500/15",
  },
  hold: {
    label: "Hold",
    className: "bg-yellow-500/10 text-yellow-400 border-yellow-500/15",
  },
  sell: {
    label: "Sell",
    className: "bg-orange-500/10 text-orange-400 border-orange-500/15",
  },
  strong_sell: {
    label: "Strong Sell",
    className: "bg-red-500/15 text-red-400 border-red-500/20",
  },
};

interface SignalBadgeProps {
  signal: SignalLabel;
  className?: string;
}

export function SignalBadge({ signal, className }: SignalBadgeProps) {
  const config = SIGNAL_CONFIG[signal] ?? SIGNAL_CONFIG.hold;
  return (
    <Badge
      variant="outline"
      className={cn(
        "text-xs font-semibold px-2.5 py-0.5 rounded-full border",
        config.className,
        className
      )}
    >
      {config.label}
    </Badge>
  );
}
