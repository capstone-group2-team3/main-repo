import { AlertTriangle, BookOpen, CheckCircle2, FileWarning, ShieldCheck, Sparkles } from "lucide-react";
import type { AnalyzeResponse, ClinicalPattern, RetrievedSource } from "@/lib/types";
import { ChartsPanel } from "./ChartsPanel";
import { StatusBadge } from "./StatusBadge";

const safety = "For clinicians only — supports review, not diagnosis or prescribing.";

function list(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String) : [];
}

export function ResultsDashboard({ result }: { result: AnalyzeResponse }) {
  const patient = result.patient_summary || result.received || {};
  const labs = result.lab_results || result.labs || result.findings || [];
  const patterns = result.clinical_patterns || result.patterns || result.pattern_results || [];
  const caseId = result.report_case_id || result.case_id || result.id || "Not returned";

  return (
    <section id="dashboard" className="relative scroll-mt-24 space-y-5">
      <span id="results" className="absolute -top-24" aria-hidden="true" />
      <div className="overflow-hidden rounded-3xl bg-[linear-gradient(135deg,#0F172A,#164E63)] p-7 text-white shadow-xl">
        <div className="text-xs font-bold uppercase tracking-[.16em] text-cyan-200">Clinical Review</div>
        <h2 className="mt-2 text-3xl font-bold">Case {caseId}</h2>
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm text-slate-300">
          <span>Panel: {patient.selected_panel || "Not provided"}</span><span>Age: {patient.age ?? "Not provided"}</span>
          <span>Sex: {patient.sex || "Not provided"}</span><span>Symptoms: {patient.symptoms?.join(", ") || "Not provided"}</span>
        </div>
        <div className="mt-5 flex flex-wrap gap-2">
          {[`${labs.length} lab results`, `${result.abnormal_findings?.length || 0} abnormal findings`, `${patterns.length} clinical patterns`].map((text) => (
            <span key={text} className="rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs">{text}</span>
          ))}
        </div>
      </div>

      <div className="flex gap-3 rounded-2xl border border-teal-200 bg-teal-50 p-5 text-sm text-teal-900">
        <ShieldCheck className="shrink-0" size={20} /><div><strong>Clinical safety notice</strong><p className="mt-1">{safety}</p></div>
      </div>
      <ChartsPanel result={result} />

      <section className="dashboard-card">
        <div className="section-heading"><span>Lab Results</span><small>Reference-aware findings</small></div>
        {labs.length ? <div className="overflow-x-auto"><table className="clinical-table"><thead><tr><th>Test</th><th>Value</th><th>Unit</th><th>Reference Range</th><th>Status</th></tr></thead>
          <tbody>{labs.map((lab, index) => {
            const range = lab.reference_low != null && lab.reference_high != null ? `${lab.reference_low} – ${lab.reference_high}` : lab.reference_range || "Not configured";
            return <tr key={`${lab.name || lab.test_name}-${index}`}><td className="font-semibold">{lab.name || lab.test_name || "Unknown"}</td><td>{lab.value ?? "—"}</td><td>{lab.unit || "—"}</td><td>{range}</td><td><StatusBadge status={lab.status} /></td></tr>;
          })}</tbody></table></div> : <Empty text="No lab results returned yet." />}
      </section>

      <div className="grid gap-5 xl:grid-cols-2">
        <section className="dashboard-card">
          <div className="section-heading"><span>Abnormal Findings</span><FileWarning size={19} /></div>
          <div className="grid gap-3 sm:grid-cols-2">{result.abnormal_findings?.length ? result.abnormal_findings.map((finding, index) => typeof finding === "string"
            ? <Insight key={index} title="Finding" body={finding} />
            : <div key={index} className="mini-card"><div className="flex items-start justify-between gap-3"><strong>{finding.test || finding.name || finding.test_name || "Finding"}</strong><StatusBadge status={finding.status} /></div><p className="mt-3">{finding.value ?? "—"} {finding.unit}</p><p className="mt-2 text-xs leading-5 text-slate-500">{finding.evidence || "Requires clinician review."}</p></div>
          ) : <Empty text="No abnormal findings returned." />}</div>
        </section>
        <section className="dashboard-card">
          <div className="section-heading"><span>Clinical Warnings</span><AlertTriangle size={19} /></div>
          <div className="space-y-3">{result.clinical_warnings?.length ? result.clinical_warnings.map((warning, index) => <div key={index} className="flex gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950"><AlertTriangle size={17} className="shrink-0" />{warning}</div>) : <Empty text="No clinical warnings returned." />}</div>
        </section>
      </div>

      <section className="dashboard-card">
        <div className="section-heading"><span>Top Clinical Patterns</span><Sparkles size={19} /></div>
        {patterns.length ? <div className="grid gap-4 lg:grid-cols-2">{patterns.map((pattern, index) => {
          if (typeof pattern === "string") return <Insight key={index} title={`Pattern ${index + 1}`} body={pattern} />;
          const item = pattern as ClinicalPattern;
          return <div key={index} className="mini-card"><div className="flex items-center justify-between gap-3"><strong>{item.pattern_name || item.name || "Clinical pattern"}</strong><span className="rounded-full bg-blue-50 px-2 py-1 text-xs font-bold text-blue-700">Rank {item.rank ?? index + 1}</span></div>
            <p className="mt-3 text-sm">Confidence: <strong>{item.confidence_level || item.confidence || "Not provided"}</strong> · Score: <strong>{item.score ?? "Not provided"}</strong></p>
            <PatternList label="Evidence for" values={list(item.evidence_for || item.supporting_findings)} /><PatternList label="Missing evidence" values={list(item.missing_evidence)} /><PatternList label="Warnings" values={list(item.warnings)} />
          </div>;
        })}</div> : <Empty text="No clinical patterns matched this case yet." />}</section>

      <div className="grid gap-5 xl:grid-cols-2">
        <section className="dashboard-card"><div className="section-heading"><span>Missing Required Labs</span><CheckCircle2 size={19} /></div>
          {result.missing_required_labs?.length ? <div className="flex flex-wrap gap-2">{result.missing_required_labs.map((lab) => <span key={lab} className="rounded-full bg-amber-100 px-3 py-1 text-sm font-semibold text-amber-800">{lab}</span>)}</div> : <div className="rounded-2xl bg-green-50 p-4 text-sm text-green-800">No missing required labs reported.</div>}
        </section>
        <section className="dashboard-card"><div className="section-heading"><span>Retrieved Sources</span><BookOpen size={19} /></div>
          {result.retrieved_sources?.length ? <div className="space-y-3">{result.retrieved_sources.map((source, index) => {
            if (typeof source === "string") return <Insight key={index} title={`Source ${index + 1}`} body={source} />;
            const item = source as RetrievedSource;
            return <div key={index} className="mini-card"><strong>{item.title || "Evidence source"}</strong><p className="mt-2 text-xs leading-5 text-slate-500">{item.snippet || "No snippet available."}</p><div className="mt-3 flex gap-2 text-xs"><span className="rounded-full bg-slate-100 px-2 py-1">Similarity {item.similarity_score ?? "N/A"}</span>{(item.source_id || item.id) && <span className="rounded-full bg-slate-100 px-2 py-1">ID {item.source_id || item.id}</span>}</div></div>;
          })}</div> : <Empty text="No retrieved evidence sources available yet." />}</section>
      </div>

      <details id="technical-details" className="dashboard-card group scroll-mt-24"><summary className="cursor-pointer list-none font-semibold">Technical Details / Raw API Response <span className="float-right text-slate-400 group-open:rotate-180">⌄</span></summary><pre className="mt-5 max-h-[420px] overflow-auto rounded-2xl bg-slate-950 p-5 text-xs text-slate-200">{JSON.stringify(result, null, 2)}</pre></details>
    </section>
  );
}

function Empty({ text }: { text: string }) { return <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">{text}</div>; }
function Insight({ title, body }: { title: string; body: string }) { return <div className="mini-card"><strong>{title}</strong><p className="mt-2 text-sm text-slate-600">{body}</p></div>; }
function PatternList({ label, values }: { label: string; values: string[] }) { return values.length ? <div className="mt-3 text-xs leading-5 text-slate-500"><strong className="text-slate-700">{label}:</strong> {values.join(", ")}</div> : null; }
