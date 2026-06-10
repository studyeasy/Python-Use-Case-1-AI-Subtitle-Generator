type Variant = "login" | "signup";

export function AuthArtwork({ variant }: { variant: Variant }) {
  return (
    <div className="relative hidden flex-1 overflow-hidden rounded-3xl bg-brand-600 lg:block">
      <Sparkles />
      {variant === "login" ? <LoginArt /> : <SignupArt />}
    </div>
  );
}

function Sparkles() {
  const dots = [
    { x: "8%", y: "12%", s: 8 },
    { x: "85%", y: "18%", s: 12 },
    { x: "78%", y: "78%", s: 10 },
    { x: "12%", y: "82%", s: 14 },
    { x: "60%", y: "10%", s: 6 },
  ];
  return (
    <>
      {dots.map((d, i) => (
        <span
          key={i}
          className="absolute text-brand-300/70"
          style={{ left: d.x, top: d.y }}
          aria-hidden
        >
          <svg width={d.s} height={d.s} viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2l2 8 8 2-8 2-2 8-2-8-8-2 8-2z" />
          </svg>
        </span>
      ))}
    </>
  );
}

function LoginArt() {
  return (
    <div className="flex h-full items-center justify-center p-10">
      <div className="relative">
        {/* Document with play */}
        <div className="rounded-2xl bg-white/95 p-6 shadow-xl">
          <div className="grid h-44 w-36 place-items-center rounded-xl bg-brand-100">
            <div className="grid h-14 w-14 place-items-center rounded-full bg-white shadow">
              <svg viewBox="0 0 24 24" className="h-6 w-6 fill-brand-600">
                <path d="M8 5v14l11-7z" />
              </svg>
            </div>
          </div>
        </div>
        {/* Progress card */}
        <div className="absolute -bottom-6 -right-16 w-56 rounded-xl bg-white/95 p-4 shadow-xl">
          <div className="flex items-center justify-between text-xs font-medium text-ink-700">
            <span>Generating subtitles...</span>
            <span className="text-brand-600">90%</span>
          </div>
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-ink-100">
            <div className="h-full w-[90%] rounded-full bg-brand-600" />
          </div>
        </div>
        {/* CC chip */}
        <div className="absolute -bottom-2 right-4 grid h-8 w-12 place-items-center rounded-md bg-white text-[10px] font-bold text-brand-600 shadow">
          CC
        </div>
      </div>
    </div>
  );
}

function SignupArt() {
  return (
    <div className="flex h-full flex-col items-center justify-center p-10 text-white">
      <div className="w-full max-w-sm rounded-2xl bg-white/95 p-4 shadow-2xl">
        <div className="relative grid h-44 place-items-center overflow-hidden rounded-xl bg-gradient-to-br from-brand-400 to-brand-700">
          <div className="grid h-16 w-16 place-items-center rounded-full bg-white/95 shadow">
            <svg viewBox="0 0 24 24" className="h-7 w-7 fill-brand-600">
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
        </div>
        <div className="mt-3 flex items-center gap-2">
          <button
            type="button"
            className="grid h-7 w-7 place-items-center rounded-full bg-brand-600 text-white"
            aria-label="Play"
          >
            <svg viewBox="0 0 24 24" className="h-3 w-3 fill-white">
              <path d="M8 5v14l11-7z" />
            </svg>
          </button>
          <div className="h-1 flex-1 rounded-full bg-ink-100">
            <div className="h-full w-1/3 rounded-full bg-brand-600" />
          </div>
          <span className="text-[10px] font-medium text-ink-500">01:23</span>
        </div>
        <div className="mt-3 flex items-end gap-0.5">
          {Array.from({ length: 36 }).map((_, i) => (
            <span
              key={i}
              className="w-1 rounded-sm bg-brand-500/80"
              style={{ height: `${10 + Math.abs(Math.sin(i * 0.7)) * 26}px` }}
            />
          ))}
        </div>
      </div>
      <div className="mt-8 text-center">
        <p className="text-lg font-bold">Generate Accurate Subtitles in Minutes.</p>
        <p className="mt-1 text-sm text-white/80">
          AI-powered processing, fast delivery.
        </p>
      </div>
    </div>
  );
}
