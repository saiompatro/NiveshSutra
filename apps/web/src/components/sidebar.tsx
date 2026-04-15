"use client";

import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  LayoutDashboard,
  BarChart3,
  Briefcase,
  Zap,
  Settings,
  LogOut,
  Menu,
  TrendingUp,
  User,
} from "lucide-react";
import { useState } from "react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/stocks", label: "Stocks", icon: BarChart3 },
  { href: "/portfolio", label: "Portfolio", icon: Briefcase },
  { href: "/signals", label: "Signals", icon: Zap },
  { href: "/settings", label: "Settings", icon: Settings },
];

function NavLinks({ onClick }: { onClick?: () => void }) {
  const pathname = usePathname();

  return (
    <nav className="flex flex-1 flex-col gap-1">
      {navItems.map((item) => {
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onClick}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              active
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

function UserSection() {
  const { user, signOut } = useAuth();
  const router = useRouter();

  async function handleSignOut() {
    await signOut();
    router.push("/login");
  }

  return (
    <div className="border-t border-border pt-4">
      <div className="flex items-center gap-3 px-3 pb-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
          <User className="h-4 w-4 text-muted-foreground" />
        </div>
        <div className="flex-1 truncate">
          <p className="truncate text-sm font-medium">
            {user?.email ?? "User"}
          </p>
        </div>
      </div>
      <Button
        variant="ghost"
        className="w-full justify-start gap-3 px-3 text-muted-foreground"
        onClick={handleSignOut}
      >
        <LogOut className="h-4 w-4" />
        Sign Out
      </Button>
    </div>
  );
}

export function DesktopSidebar() {
  return (
    <aside className="hidden lg:flex lg:w-64 lg:flex-col lg:border-r lg:border-border lg:bg-card">
      <div className="flex h-full flex-col p-4">
        <Link
          href="/dashboard"
          className="mb-6 flex items-center gap-2 px-3"
        >
          <TrendingUp className="h-6 w-6 text-primary" />
          <span className="text-lg font-bold">NiveshSutra</span>
        </Link>
        <NavLinks />
        <UserSection />
      </div>
    </aside>
  );
}

export function MobileSidebar() {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex items-center border-b border-border bg-card px-4 py-3 lg:hidden">
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger
          render={
            <Button variant="ghost" size="icon">
              <Menu className="h-5 w-5" />
              <span className="sr-only">Toggle menu</span>
            </Button>
          }
        />
        <SheetContent side="left" className="w-64 p-4">
          <SheetHeader>
            <SheetTitle>
              <Link
                href="/dashboard"
                className="flex items-center gap-2"
                onClick={() => setOpen(false)}
              >
                <TrendingUp className="h-6 w-6 text-primary" />
                <span className="text-lg font-bold">NiveshSutra</span>
              </Link>
            </SheetTitle>
          </SheetHeader>
          <div className="mt-4 flex h-[calc(100%-4rem)] flex-col">
            <NavLinks onClick={() => setOpen(false)} />
            <UserSection />
          </div>
        </SheetContent>
      </Sheet>
      <Link href="/dashboard" className="ml-3 flex items-center gap-2">
        <TrendingUp className="h-5 w-5 text-primary" />
        <span className="font-bold">NiveshSutra</span>
      </Link>
    </div>
  );
}
