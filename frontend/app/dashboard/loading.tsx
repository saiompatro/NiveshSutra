import { Navbar } from "@/components/Navbar";
import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardLoading() {
  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* Stat cards */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-2xl" />
          ))}
        </section>

        {/* Sparkline */}
        <Skeleton className="h-32 rounded-2xl" />

        {/* Signals table */}
        <div className="rounded-2xl bg-card border border-border p-6 space-y-3">
          <Skeleton className="h-4 w-32" />
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full rounded-lg" />
          ))}
        </div>
      </main>
    </>
  );
}
