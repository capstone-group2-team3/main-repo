"use client";

import { Activity, ArrowRight, ShieldCheck } from "lucide-react";

type HeaderProps = {
  backendOnline: boolean | null;
};

const navLinks = [
  ["Overview", "#overview"],
  ["Analysis", "#analysis"],
  ["Dashboard", "#dashboard"],
  ["Safety", "#safety"],
  ["Technical Details", "#technical-details"],
] as const;

export function Header({ backendOnline }: HeaderProps) {
  const statusLabel = backendOnline === true ? "Backend online" : backendOnline === false ? "Backend offline" : "Backend checking";
  const statusDot = backendOnline === true ? "bg-emerald-500" : backendOnline === false ? "bg-red-500" : "animate-pulse bg-amber-400";

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-white/78 shadow-[0_10px_35px_rgba(15,23,42,.06)] backdrop-blur-2xl">
      <div className="mx-auto flex h-[72px] max-w-[1440px] items-center justify-between gap-4 px-4 md:px-8">
        <a href="#overview" className="group flex min-w-0 items-center gap-3">
          <span className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-slate-950 via-blue-800 to-teal-600 text-white shadow-lg shadow-teal-900/15 transition group-hover:-translate-y-0.5">
            <Activity size={20} />
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm font-black tracking-tight text-slate-950 sm:text-base">MedDx Assistant</span>
            <span className="hidden truncate text-[11px] font-bold uppercase tracking-[.14em] text-teal-700 sm:block">Clinical Review Dashboard</span>
          </span>
        </a>

        <nav aria-label="Primary navigation" className="hidden items-center gap-1 rounded-full border border-slate-200 bg-white/75 p-1 shadow-sm lg:flex">
          {navLinks.map(([label, href]) => (
            <a
              key={href}
              href={href}
              className="rounded-full px-3.5 py-2 text-xs font-bold text-slate-600 transition hover:bg-teal-50 hover:text-teal-800"
            >
              {label}
            </a>
          ))}
        </nav>

        <div className="flex shrink-0 items-center gap-2">
          <span className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-[11px] font-bold text-slate-600 shadow-sm">
            <span className={`h-2.5 w-2.5 rounded-full ${statusDot}`} />
            <span className="hidden sm:inline">{statusLabel}</span>
            <span className="sm:hidden">{backendOnline === true ? "Online" : backendOnline === false ? "Offline" : "Checking"}</span>
          </span>
          <span className="hidden items-center gap-1.5 rounded-full border border-teal-100 bg-teal-50 px-3 py-2 text-[11px] font-bold text-teal-800 xl:inline-flex">
            <ShieldCheck size={14} /> Clinician-facing review
          </span>
          <a
            href="#analysis"
            className="hidden items-center gap-1.5 rounded-full bg-slate-950 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-slate-900/15 transition hover:-translate-y-0.5 hover:bg-teal-700 md:inline-flex"
          >
            Start Review <ArrowRight size={14} />
          </a>
        </div>
      </div>
    </header>
  );
}
