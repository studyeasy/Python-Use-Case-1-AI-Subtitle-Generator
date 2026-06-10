import { RequireAuth } from "@/components/RequireAuth";

export default function NewProjectLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <RequireAuth>{children}</RequireAuth>;
}
