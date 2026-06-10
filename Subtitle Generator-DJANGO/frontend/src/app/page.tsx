import Link from "next/link";
import { MarketingHeader } from "@/components/MarketingHeader";
import {
  Bolt,
  CloudUpload,
  Lock,
  Target,
} from "@/components/icons";

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <MarketingHeader />

      <main className="flex-1">
        <section className="mx-auto w-full max-w-5xl px-6 pt-16 pb-12 text-center">
          <h1 className="text-balance text-5xl font-extrabold leading-tight tracking-tight text-brand-700 sm:text-6xl">
            Generate Accurate Subtitles in Minutes
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-pretty text-base text-ink-500">
            Upload your audio or video files and get accurate subtitles
            automatically. Save time and reach a wider audience.
          </p>

          <div className="mt-10 rounded-2xl bg-ink-50 p-10">
            <div className="flex flex-col items-center">
              <CloudUpload className="h-9 w-9 text-ink-500" />
              <p className="mt-3 text-base font-semibold text-ink-900">
                Drag &amp; drop your file here
              </p>
              <Link href="/new-project" className="btn-primary mt-5">
                Choose File
              </Link>
              <p className="mt-4 text-xs text-ink-500">
                Supports MP4, MOV, MP3, WAV and more
              </p>
            </div>
          </div>
        </section>

        <section
          id="features"
          className="mx-auto grid w-full max-w-5xl gap-10 px-6 py-12 sm:grid-cols-3"
        >
          <Feature
            icon={<Target className="h-7 w-7" />}
            title="High Accuracy"
            text="AI-powered accuracy up to 98%"
          />
          <Feature
            icon={<Bolt className="h-7 w-7" />}
            title="Fast Processing"
            text="Get subtitles in just minutes"
          />
          <Feature
            icon={<Lock className="h-7 w-7" />}
            title="Secure & Private"
            text="Your files are safe and encrypted"
          />
        </section>
      </main>
    </div>
  );
}

function Feature({
  icon,
  title,
  text,
}: {
  icon: React.ReactNode;
  title: string;
  text: string;
}) {
  return (
    <div className="flex flex-col items-center text-center">
      <div className="text-brand-600">{icon}</div>
      <h3 className="mt-3 text-base font-semibold text-ink-900">{title}</h3>
      <p className="mt-1 text-sm text-ink-500">{text}</p>
    </div>
  );
}
