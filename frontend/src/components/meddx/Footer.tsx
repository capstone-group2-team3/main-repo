import { Activity, ShieldCheck } from "lucide-react";

const safety = "For clinicians only — supports review, not diagnosis or prescribing.";

const productLinks = [
  ["Overview", "#overview"],
  ["Analysis", "#analysis"],
  ["Dashboard", "#dashboard"],
  ["Safety Notice", "#safety"],
] as const;

export function Footer() {
  return (
    <footer id="safety" className="relative scroll-mt-24 overflow-hidden rounded-t-[2rem] bg-slate-950 text-white shadow-[0_-24px_70px_rgba(15,23,42,.12)]">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_0%,rgba(6,182,212,.24),transparent_32%),radial-gradient(circle_at_92%_40%,rgba(15,118,110,.20),transparent_34%)]" />
      <div className="absolute inset-0 footer-grid opacity-40" />
      <div className="relative mx-auto max-w-[1440px] px-5 py-10 md:px-8 md:py-12">
        <div className="grid gap-8 md:grid-cols-[1.35fr_.75fr_.9fr]">
          <div>
            <a href="#overview" className="inline-flex items-center gap-3">
              <span className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-blue-700 to-teal-500 text-white shadow-lg shadow-cyan-900/20">
                <Activity size={20} />
              </span>
              <span>
                <span className="block font-black tracking-tight">MedDx Assistant</span>
                <span className="text-xs font-bold uppercase tracking-[.16em] text-cyan-200">Clinical Review Dashboard</span>
              </span>
            </a>
            <p className="mt-5 max-w-lg text-sm leading-6 text-slate-300">
              Doctor-facing clinical review support for lab findings, abnormal signals, safety notes, and missing evidence.
            </p>
          </div>

          <div>
            <h3 className="text-xs font-black uppercase tracking-[.18em] text-cyan-200">Product</h3>
            <div className="mt-4 grid gap-3">
              {productLinks.map(([label, href]) => (
                <a key={href} href={href} className="text-sm font-semibold text-slate-300 transition hover:text-cyan-200">
                  {label}
                </a>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-xs font-black uppercase tracking-[.18em] text-cyan-200">Project / Safety</h3>
            <div className="mt-4 flex flex-wrap gap-2">
              {["AISPIRE Capstone Project", "For clinicians only", "Not diagnosis or prescribing"].map((item) => (
                <span key={item} className="rounded-full border border-white/10 bg-white/[0.07] px-3 py-1.5 text-xs font-semibold text-slate-200 backdrop-blur">
                  {item}
                </span>
              ))}
            </div>
            <div className="mt-5 flex gap-3 rounded-2xl border border-teal-300/20 bg-teal-300/10 p-4 text-sm leading-6 text-teal-50">
              <ShieldCheck size={18} className="mt-0.5 shrink-0 text-cyan-200" />
              <span>{safety}</span>
            </div>
          </div>
        </div>

        <div className="mt-10 flex flex-col gap-3 border-t border-white/10 pt-5 text-xs text-slate-400 md:flex-row md:items-center md:justify-between">
          <p>© 2026 MedDx Assistant. Educational clinical decision support prototype.</p>
          <p>{safety}</p>
        </div>
      </div>
    </footer>
  );
}
