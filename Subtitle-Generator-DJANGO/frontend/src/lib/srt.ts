// Tiny SRT parser. Splits cue blocks on blank lines, extracts the index,
// timecodes and text. Returns the list in source order; bad blocks are
// silently skipped so a partially malformed file still renders the rest.

export type SrtCue = {
  index: number;
  startMs: number;
  endMs: number;
  startLabel: string;
  endLabel: string;
  text: string;
};

function parseTimestamp(stamp: string): number | null {
  // Format: HH:MM:SS,mmm
  const m = stamp.trim().match(/^(\d+):(\d{2}):(\d{2})[,.](\d{1,3})$/);
  if (!m) return null;
  const h = Number(m[1]);
  const min = Number(m[2]);
  const s = Number(m[3]);
  const ms = Number(m[4].padEnd(3, "0").slice(0, 3));
  return ((h * 60 + min) * 60 + s) * 1000 + ms;
}

export function parseSrt(raw: string): SrtCue[] {
  // Normalise line endings, then split on one-or-more blank lines.
  const text = raw.replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
  if (!text) return [];

  const blocks = text.split(/\n{2,}/);
  const cues: SrtCue[] = [];
  for (const block of blocks) {
    const lines = block.split("\n").filter((l) => l.length > 0);
    if (lines.length < 2) continue;

    // Some encoders omit the index line. Look for the timecode line first.
    let cursor = 0;
    let index = cues.length + 1;
    if (/^\d+$/.test(lines[0].trim())) {
      index = Number(lines[0].trim());
      cursor = 1;
    }
    const timeLine = lines[cursor];
    if (!timeLine) continue;
    const tm = timeLine.match(/(\S+)\s*-->\s*(\S+)/);
    if (!tm) continue;
    const startMs = parseTimestamp(tm[1]);
    const endMs = parseTimestamp(tm[2]);
    if (startMs == null || endMs == null) continue;

    const body = lines.slice(cursor + 1).join("\n").trim();
    cues.push({
      index,
      startMs,
      endMs,
      startLabel: tm[1],
      endLabel: tm[2],
      text: body,
    });
  }
  return cues;
}

export function formatDuration(ms: number): string {
  const total = Math.max(0, Math.round(ms / 1000));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}
