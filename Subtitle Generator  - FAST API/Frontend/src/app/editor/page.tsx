import Link from "next/link";
import {
  ChevronDown,
  ChevronLeft,
  Download,
  Plus,
  Trash,
  Upload,
} from "@/components/icons";

type Line = {
  id: string;
  start: string;
  end: string;
  text: string;
  active?: boolean;
};

const lines: Line[] = [
  { id: "1", start: "00:00:01,200", end: "00:00:03,500", text: "Welcome to our product demo." },
  { id: "2", start: "00:00:03,600", end: "00:00:06,800", text: "Today, we'll show you how it works.", active: true },
  { id: "3", start: "00:00:06,900", end: "00:00:09,500", text: "In this demo, we'll see how easy it is." },
  { id: "4", start: "00:00:09,600", end: "00:00:12,400", text: "First, get started by..." },
  { id: "5", start: "00:00:12,500", end: "00:00:15,500", text: "It's a comprehensive tool for subtitle generation." },
];

export default function EditorPage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#0d1320] text-white">
      <header className="flex items-center justify-between border-b border-white/10 px-6 py-4">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-white/80 hover:text-white"
        >
          <ChevronLeft className="h-4 w-4" />
          Back to Projects
        </Link>
        <div className="flex items-center gap-2">
          <button className="inline-flex items-center gap-2 rounded-lg border border-white/15 bg-white/5 px-4 py-2 text-sm font-medium text-white hover:bg-white/10">
            <Download className="h-4 w-4" />
            Download
          </button>
          <button className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700">
            <Upload className="h-4 w-4" />
            Export
          </button>
        </div>
      </header>

      <main className="grid flex-1 gap-6 px-6 py-6 lg:grid-cols-[1fr_360px]">
        <div className="flex flex-col gap-4">
          <VideoPlayer />
          <Timeline lines={lines} />
        </div>

        <aside className="space-y-6 rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <section>
            <h2 className="text-base font-semibold">Edit Subtitle</h2>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <Field label="Start Time" value="00:00:01,200" />
              <Field label="End Time" value="00:00:03,500" />
            </div>
            <div className="mt-3">
              <label className="mb-1.5 block text-xs font-medium text-white/70">
                Text
              </label>
              <textarea
                rows={4}
                defaultValue="Welcome to our product demo. Today, we'll show you how it works. It's a comprehensive tool for subtitle generation."
                className="w-full resize-none rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-white/40 focus:border-brand-400 focus:outline-none"
              />
              <div className="mt-1 text-right text-[11px] text-white/50">95 / 150</div>
            </div>
            <div className="mt-3 flex gap-2">
              <button className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-brand-600 px-3 py-2 text-sm font-semibold text-white hover:bg-brand-700">
                <Plus className="h-4 w-4" />
                Add Line
              </button>
              <button className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-danger-600/40 bg-danger-600/10 px-3 py-2 text-sm font-semibold text-red-300 hover:bg-danger-600/20">
                <Trash className="h-4 w-4" />
                Delete Line
              </button>
            </div>
          </section>

          <hr className="border-white/10" />

          <section>
            <h2 className="text-base font-semibold">Settings</h2>
            <div className="mt-4 space-y-3">
              <SelectField label="Font Size" value="16" />
              <SelectField label="Position" value="Bottom Center" />
            </div>
          </section>
        </aside>
      </main>
    </div>
  );
}

function VideoPlayer() {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-black">
      <div
        className="aspect-video w-full bg-cover bg-center"
        style={{
          backgroundImage:
            "linear-gradient(to bottom, rgba(0,0,0,0.0), rgba(0,0,0,0.2)), url('https://images.unsplash.com/photo-1506905925346-21bda4d32df4?auto=format&fit=crop&w=1200&q=60')",
        }}
      />
      <div className="absolute inset-x-0 bottom-0 flex items-center gap-3 bg-gradient-to-t from-black/70 to-transparent px-4 py-3">
        <button
          className="grid h-9 w-9 place-items-center rounded-full bg-white/95 text-black"
          aria-label="Play"
        >
          <svg viewBox="0 0 24 24" className="h-4 w-4 fill-black">
            <path d="M8 5v14l11-7z" />
          </svg>
        </button>
        <span className="text-xs tabular-nums text-white/80">0:03 / 3:25</span>
        <div className="relative h-1 flex-1 rounded-full bg-white/20">
          <div className="h-full w-[12%] rounded-full bg-brand-500" />
        </div>
        <span className="text-xs text-white/80">⛶</span>
      </div>
    </div>
  );
}

function Timeline({ lines }: { lines: Line[] }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
      <div className="mb-2 flex justify-between text-[10px] uppercase tracking-wider text-white/40">
        {["0", "0:30", "1:00", "1:30", "2:00", "2:30", "3:00"].map((t) => (
          <span key={t}>{t}</span>
        ))}
      </div>
      <div className="grid grid-cols-5 gap-2">
        {lines.map((l) => (
          <div
            key={l.id}
            className={`rounded-lg border px-3 py-2 text-xs ${
              l.active
                ? "border-brand-400 bg-brand-500/20 text-white"
                : "border-white/10 bg-white/5 text-white/80"
            }`}
          >
            <p className="line-clamp-2 leading-snug">{l.text}</p>
            <p className="mt-1 text-[10px] text-white/50">
              {l.start} → {l.end}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <label className="mb-1.5 block text-xs font-medium text-white/70">
        {label}
      </label>
      <input
        defaultValue={value}
        className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white tabular-nums focus:border-brand-400 focus:outline-none"
      />
    </div>
  );
}

function SelectField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <label className="mb-1.5 block text-xs font-medium text-white/70">
        {label}
      </label>
      <div className="relative">
        <select
          defaultValue={value}
          className="w-full appearance-none rounded-lg border border-white/10 bg-white/5 px-3 py-2 pr-9 text-sm text-white focus:border-brand-400 focus:outline-none"
        >
          <option>{value}</option>
        </select>
        <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/60" />
      </div>
    </div>
  );
}
