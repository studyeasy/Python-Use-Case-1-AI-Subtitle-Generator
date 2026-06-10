import { RequireAuth } from "@/components/RequireAuth";

export default function EditorLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <RequireAuth>{children}</RequireAuth>;
}
