import { RequireAuth } from "@/components/RequireAuth";
import { Sidebar } from "@/components/Sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RequireAuth>
      <div className="flex min-h-screen bg-white">
        <Sidebar />
        <main className="flex-1 overflow-x-hidden px-10 py-10">{children}</main>
      </div>
    </RequireAuth>
  );
}
