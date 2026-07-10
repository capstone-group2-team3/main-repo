import { Activity, AlertTriangle, ClipboardList, CircleDashed } from "lucide-react";
import type { AnalyzeResponse, LabResult } from "@/lib/types";

function labsOf(result: AnalyzeResponse): LabResult[] {
  return result.lab_results || result.labs || result.findings || [];
}

export function ChartsPanel({ result }: { result: AnalyzeResponse }) {
  const labs = labsOf(result);
  const statuses = ["normal", "low", "high", "critical", "unknown"];
  const counts = Object.fromEntries(statuses.map((status) => [
    status,
    labs.filter((lab) => String(lab.status || "unknown").toLowerCase() === status).length,
  ]));
  const abnormal = labs.length - counts.normal - counts.unknown;
  const critical = counts.critical;
  const nonCriticalAbnormal = Math.max(abnormal - critical, 0);
  const total = Math.max(labs.length, 1);
  const normalDegrees = (counts.normal / total) * 360;
  const abnormalDegrees = (nonCriticalAbnormal / total) * 360;
  const maxCount = Math.max(...Object.values(counts), 1);
  const cards = [
    ["Total Labs", labs.length, ClipboardList],
    ["Abnormal Findings", result.abnormal_findings?.length || 0, Activity],
    ["Clinical Warnings", result.clinical_warnings?.length || 0, AlertTriangle],
    ["Missing Required Labs", result.missing_required_labs?.length || 0, CircleDashed],
  ] as const;

  return (
    <section className="dashboard-card">
      <div className="section-heading"><span>Visual Summary</span><small>At-a-glance review</small></div>
      <div className="grid gap-6 lg:grid-cols-[.7fr_1.3fr]">
        <div className="flex items-center justify-center">
          <div
            className="relative grid h-44 w-44 place-items-center rounded-full"
            style={{ background: `conic-gradient(#16A34A 0 ${normalDegrees}deg,#F59E0B ${normalDegrees}deg ${normalDegrees + abnormalDegrees}deg,#DC2626 ${normalDegrees + abnormalDegrees}deg ${normalDegrees + abnormalDegrees + (critical / total) * 360}deg,#E2E8F0 0)` }}
          >
            <div className="grid h-28 w-28 place-items-center rounded-full bg-white text-center shadow-inner">
              <div><strong className="block text-3xl text-slate-900">{labs.length}</strong><span className="text-xs text-slate-500">labs reviewed</span></div>
            </div>
          </div>
        </div>
        <div className="space-y-3">
          {statuses.map((status) => (
            <div key={status} className="grid grid-cols-[70px_1fr_24px] items-center gap-3 text-sm">
              <span className="capitalize text-slate-600">{status}</span>
              <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
                <div className={`h-full rounded-full status-bar-${status}`} style={{ width: `${(counts[status] / maxCount) * 100}%` }} />
              </div>
              <strong>{counts[status]}</strong>
            </div>
          ))}
        </div>
      </div>
      <div className="mt-7 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map(([label, count, Icon]) => (
          <div key={label} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <Icon size={18} className="mb-3 text-teal-700" /><strong className="text-2xl">{count}</strong><p className="mt-1 text-xs text-slate-500">{label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
