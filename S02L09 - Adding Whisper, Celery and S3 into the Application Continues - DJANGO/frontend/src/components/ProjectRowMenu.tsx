"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Eye, MoreVertical, Trash } from "@/components/icons";

type Props = {
  hasSrt: boolean;
  onViewSrt: () => void;
  onDelete: () => void;
  busy?: boolean;
};

// Three-dot popover menu for a project row. Stops click propagation so it
// doesn't trigger the row's "navigate to detail" handler.
export function ProjectRowMenu({ hasSrt, onViewSrt, onDelete, busy }: Props) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const menuId = useId();

  useEffect(() => {
    if (!open) return;
    function onDocClick(e: MouseEvent) {
      if (!wrapperRef.current) return;
      if (!wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div
      ref={wrapperRef}
      className="relative inline-block"
      onClick={(e) => e.stopPropagation()}
    >
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        aria-label="More actions"
        disabled={busy}
        onClick={() => setOpen((v) => !v)}
        className="rounded-md p-1 text-ink-500 hover:bg-ink-50 hover:text-ink-900 disabled:opacity-50"
      >
        <MoreVertical className="h-4 w-4" />
      </button>

      {open && (
        <div
          id={menuId}
          role="menu"
          className="absolute right-0 z-20 mt-1 w-44 overflow-hidden rounded-lg border border-ink-200 bg-white shadow-lg"
        >
          <MenuItem
            disabled={!hasSrt}
            title={hasSrt ? undefined : "Subtitle is not ready yet"}
            onClick={() => {
              setOpen(false);
              onViewSrt();
            }}
          >
            <Eye className="h-4 w-4" />
            View subtitle
          </MenuItem>
          <div className="border-t border-ink-100" />
          <MenuItem
            destructive
            onClick={() => {
              setOpen(false);
              onDelete();
            }}
          >
            <Trash className="h-4 w-4" />
            Delete project
          </MenuItem>
        </div>
      )}
    </div>
  );
}

function MenuItem({
  children,
  onClick,
  disabled,
  destructive,
  title,
}: {
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  destructive?: boolean;
  title?: string;
}) {
  const tone = destructive
    ? "text-danger-600 hover:bg-danger-50"
    : "text-ink-900 hover:bg-ink-50";
  return (
    <button
      type="button"
      role="menuitem"
      title={title}
      disabled={disabled}
      onClick={onClick}
      className={`flex w-full items-center gap-2 px-3 py-2 text-left text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-40 ${tone}`}
    >
      {children}
    </button>
  );
}
