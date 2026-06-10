import { Logo } from "@/components/Logo";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <header className="px-8 py-6">
        <Logo />
      </header>
      <main className="flex flex-1 gap-8 px-6 pb-8 lg:px-8">{children}</main>
    </div>
  );
}
