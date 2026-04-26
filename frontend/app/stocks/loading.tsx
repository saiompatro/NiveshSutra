import { Navbar } from "@/components/Navbar";
import { Skeleton } from "@/components/ui/skeleton";

export default function StocksLoading() {
  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        <Skeleton className="h-8 w-24" />
        <div className="rounded-2xl bg-card border border-border p-6 space-y-3">
          {Array.from({ length: 12 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full rounded-lg" />
          ))}
        </div>
      </main>
    </>
  );
}
