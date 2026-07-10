import type { LabStatus } from "@/lib/types";

export function StatusBadge({ status }: { status?: LabStatus }) {
  const value = String(status || "unknown").toLowerCase();
  const styles: Record<string, string> = {
    normal: "bg-green-100 text-green-700 ring-green-600/15",
    low: "bg-amber-100 text-amber-800 ring-amber-600/15",
    high: "bg-amber-100 text-amber-800 ring-amber-600/15",
    critical: "bg-red-100 text-red-700 ring-red-600/15",
    unknown: "bg-slate-100 text-slate-600 ring-slate-500/15",
  };
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-bold capitalize ring-1 ${styles[value] || styles.unknown}`}>{value}</span>;
}
