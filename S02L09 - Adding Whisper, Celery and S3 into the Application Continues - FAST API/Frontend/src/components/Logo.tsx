import Link from "next/link";

type LogoProps = {
  href?: string;
  showWordmark?: boolean;
  variant?: "default" | "light";
  size?: "sm" | "md" | "lg";
};

const sizeMap = {
  sm: { box: "h-7 w-7", text: "text-base" },
  md: { box: "h-9 w-9", text: "text-lg" },
  lg: { box: "h-11 w-11", text: "text-xl" },
};

export function Logo({
  href = "/",
  showWordmark = true,
  variant = "default",
  size = "md",
}: LogoProps) {
  const s = sizeMap[size];
  const wordClass =
    variant === "light" ? "text-white" : "text-ink-900";
  return (
    <Link href={href} className="inline-flex items-center gap-2">
      <span
        className={`${s.box} grid place-items-center rounded-xl bg-brand-600 text-white shadow-sm`}
        aria-hidden
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          className="h-5 w-5"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M16 7c-1-1.5-2.5-2.2-4.5-2.2-2.6 0-4.5 1.4-4.5 3.5 0 2 1.7 2.9 4.4 3.5 3 .7 5.6 1.6 5.6 4.6 0 2.5-2.4 4.2-5.7 4.2-2.6 0-4.6-1-5.8-2.7"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
          />
        </svg>
      </span>
      {showWordmark && (
        <span className={`font-extrabold tracking-tight ${s.text} ${wordClass}`}>
          Subly
        </span>
      )}
    </Link>
  );
}
