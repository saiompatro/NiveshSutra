"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { SignalBadge } from "./SignalBadge";
import type { Signal } from "@/types";

interface SignalsTableProps {
  signals: Signal[];
  loading?: boolean;
}

function fmt(n: number) {
  return (n >= 0 ? "+" : "") + n.toFixed(3);
}

export function SignalsTable({ signals, loading }: SignalsTableProps) {
  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (!signals.length) {
    return (
      <p className="text-sm text-muted-foreground py-8 text-center">
        No signals available — run the pipeline to generate today&apos;s signals.
      </p>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow className="border-border hover:bg-transparent">
          <TableHead className="text-muted-foreground font-medium">Symbol</TableHead>
          <TableHead className="text-muted-foreground font-medium">Signal</TableHead>
          <TableHead className="text-muted-foreground font-medium text-right">Score</TableHead>
          <TableHead className="text-muted-foreground font-medium text-right hidden md:table-cell">
            Confidence
          </TableHead>
          <TableHead className="text-muted-foreground font-medium text-right hidden lg:table-cell">
            Technical
          </TableHead>
          <TableHead className="text-muted-foreground font-medium text-right hidden lg:table-cell">
            Sentiment
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {signals.map((s) => (
          <TableRow
            key={s.symbol}
            className="border-border hover:bg-secondary/40 transition-colors cursor-default"
          >
            <TableCell className="font-mono font-semibold text-foreground">
              {s.symbol}
            </TableCell>
            <TableCell>
              <SignalBadge signal={s.signal} />
            </TableCell>
            <TableCell className="text-right font-mono text-sm text-foreground">
              {fmt(s.composite_score)}
            </TableCell>
            <TableCell className="text-right text-sm text-muted-foreground hidden md:table-cell">
              {(s.confidence * 100).toFixed(0)}%
            </TableCell>
            <TableCell className="text-right font-mono text-sm text-muted-foreground hidden lg:table-cell">
              {fmt(s.technical_score)}
            </TableCell>
            <TableCell className="text-right font-mono text-sm text-muted-foreground hidden lg:table-cell">
              {fmt(s.sentiment_score)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
