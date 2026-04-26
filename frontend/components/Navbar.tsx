import Link from "next/link";
import { Separator } from "@/components/ui/separator";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/stocks", label: "Stocks" },
  { href: "/signals", label: "Signals" },
  { href: "/portfolio", label: "Portfolio" },
];

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center gap-8">
        {/* Brand */}
        <Link
          href="/dashboard"
          className="flex items-center gap-2.5 shrink-0"
        >
          <span className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center text-xs font-bold text-primary-foreground">
            N
          </span>
          <span className="font-semibold text-sm tracking-tight text-foreground hidden sm:block">
            NiveshSutra
          </span>
        </Link>

        <Separator orientation="vertical" className="h-4 hidden sm:block" />

        {/* Nav links */}
        <nav className="flex items-center gap-1">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="px-3 py-1.5 rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
