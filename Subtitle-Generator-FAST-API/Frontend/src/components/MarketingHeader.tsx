import Link from "next/link";
import { Logo } from "./Logo";

export function MarketingHeader() {
  return (
    <header className="border-b border-ink-100 bg-white/80 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-6">
        <Logo />
        <nav className="hidden items-center gap-7 text-sm font-medium text-ink-700 md:flex">
          <Link href="#features" className="hover:text-ink-900">
            Features
          </Link>
          <Link href="#how" className="hover:text-ink-900">
            How It Works
          </Link>
          <Link href="#pricing" className="hover:text-ink-900">
            Pricing
          </Link>
          <Link href="#blog" className="hover:text-ink-900">
            Blog
          </Link>
        </nav>
        <div className="flex items-center gap-2">
          <Link href="/login" className="btn-ghost">
            Log in
          </Link>
          <Link href="/signup" className="btn-primary">
            Sign Up
          </Link>
        </div>
      </div>
    </header>
  );
}
