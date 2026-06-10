"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { Logo } from "./Logo";
import {
  FilePlus,
  Folder,
  LayoutGrid,
  LogOut,
  Settings,
  Tag,
} from "./icons";

type Item = {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
};

const items: Item[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutGrid },
  { href: "/dashboard", label: "Projects", icon: Folder },
  { href: "/new-project", label: "New Project", icon: FilePlus },
  { href: "#pricing", label: "Pricing", icon: Tag },
  { href: "#settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { logout } = useAuth();
  async function handleLogout() {
    await logout();
    router.replace("/login");
  }
  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-ink-100 bg-white px-4 py-6">
      <div className="px-2">
        <Logo />
      </div>

      <nav className="mt-8 flex-1 space-y-1">
        {items.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
                active
                  ? "bg-brand-50 text-brand-700"
                  : "text-ink-700 hover:bg-ink-50"
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>

      <button
        type="button"
        onClick={handleLogout}
        className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm font-medium text-ink-700 hover:bg-ink-50"
      >
        <LogOut className="h-4 w-4" />
        Log out
      </button>
    </aside>
  );
}
