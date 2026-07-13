import { AlertTriangle, BookOpen, CheckCircle2, CircleAlert, ExternalLink, FileDown, FileText, FileWarning, Printer, ShieldCheck, Sparkles } from "lucide-react";
import { buildApiUrl } from "@/lib/api";
import type { AnalyzeResponse, ClinicalPattern, ClinicalWarning, RetrievedSource, SeverityResult } from "@/lib/types";
import { ChartsPanel } from "./ChartsPanel";
import { StatusBadge } from "./StatusBadge";

const safety = "For clinicians only — supports review, not diagnosis or prescribing.";

function list(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String) : [];
}

function formatDate(value?: string): string {
  if (!value) return "Not provided";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone,
  }).format(date).replace(",", " •");
}

function sourceCount(pattern: ClinicalPattern): number {
  return pattern.retrieved_sources?.length || 0;
}

function formatPanelLabel(value?: string): string {
  if (!value) return "Not provided";
  const mapping: Record<string, string> = {
    Diabetic_Panel: "Diabetic / Rapid Glucose Panel",
    Cardiac_Enzymes_Panel: "Cardiac Enzymes Panel",
    Electrolytes_Calcium_Panel: "Electrolytes & Calcium Panel",
    Lipids_Inflammation_Panel: "Lipids & Inflammation Panel",
    Albumin_Protein_Panel: "Albumin & Protein Panel",
    Renal_Thyroid_Panel: "Renal & Thyroid Panel",
  };
  return mapping[value] || value;
}

export function ResultsDashboard({ result }: { result: AnalyzeResponse }) {
  const patient = result.patient_summary || result.received || {};
  const labs = result.lab_results || result.labs || result.findings || [];
  const patterns = result.clinical_patterns || result.patterns || result.pattern_results || [];
  const caseId = result.report_case_id || result.case_id || result.id || "Not returned";
  const notice = result.safety_notice || safety;
  const report = result.report;
  const htmlUrl = report?.html_download_url ? buildApiUrl(report.html_download_url) : null;
  const pdfUrl = report?.pdf_download_url ? buildApiUrl(report.pdf_download_url) : null;

  return (
    <section id="dashboard" className="relative scroll-mt-24 space-y-5">
      <span id="results" className="absolute -top-24" aria-hidden="true" />
      <div className="overflow-hidden rounded-3xl bg-[linear-gradient(135deg,#0F172A,#164E63)] p-7 text-white shadow-xl">
        <div className="text-xs font-bold uppercase tracking-[.16em] text-cyan-200">Clinical Review</div>
        <h2 className="mt-2 text-3xl font-bold">Case {caseId}</h2>
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm text-slate-300">
          <span>Panel: {formatPanelLabel(patient.selected_panel)}</span><span>Age: {patient.age ?? "Not provided"}</span>
          <span>Sex: {patient.sex || "Not provided"}</span><span>Symptoms: {patient.symptoms?.join(", ") || "Not provided"}</span>
        </div>
        <div className="mt-5 flex flex-wrap gap-2">
          {[`${labs.length} lab results`, `${result.abnormal_findings?.length || 0} abnormal findings`, `${patterns.length} clinical patterns`].map((text) => (
            <span key={text} className="rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs">{text}</span>
          ))}
        </div>
      </div>

      {result.severity && <SeverityBanner severity={result.severity} />}

      <div className="flex gap-3 rounded-2xl border border-teal-200 bg-teal-50 p-5 text-sm text-teal-900">
        <ShieldCheck className="shrink-0" size={20} /><div><strong>Clinical safety notice</strong><p className="mt-1">{notice}</p></div>
      </div>
      <ChartsPanel result={result} />

      <section className="dashboard-card">
        <div className="section-heading"><span>Patient Summary</span><small>Submitted case context</small></div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
          <SummaryItem label="Age" value={patient.age ?? "Not provided"} />
          <SummaryItem label="Sex" value={patient.sex || "Not provided"} />
          <SummaryItem label="Selected Panel" value={formatPanelLabel(patient.selected_panel)} />
          <SummaryItem label="Symptoms" value={patient.symptoms?.join(", ") || "Not provided"} />
          <SummaryItem label="Generated At" value={formatDate(result.generated_at)} />
        </div>
        <div className="mt-4 rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
          <strong className="text-slate-800">Clinical notes</strong>
          <p className="mt-2 leading-6">{patient.clinical_notes || "Not provided"}</p>
        </div>
      </section>

      <section className="dashboard-card">
        <div className="section-heading"><span>Lab Results</span><small>Reference-aware findings</small></div>
        {labs.length ? <div className="overflow-x-auto"><table className="clinical-table"><thead><tr><th>Test</th><th>Value</th><th>Unit</th><th>Reference Range</th><th>Status</th><th>Evidence</th></tr></thead>
          <tbody>{labs.map((lab, index) => {
            const range = lab.reference_low != null && lab.reference_high != null ? `${lab.reference_low} – ${lab.reference_high}` : lab.reference_range || "Not configured";
            return <tr key={`${lab.name || lab.test_name}-${index}`}><td className="font-semibold">{lab.name || lab.test_name || "Unknown"}</td><td>{lab.value ?? "—"}</td><td>{lab.unit || "—"}</td><td>{range}</td><td><StatusBadge status={lab.status} /></td><td className="min-w-64 text-xs leading-5 text-slate-500">{lab.evidence || "Requires clinician review."}</td></tr>;
          })}</tbody></table></div> : <Empty text="No lab results returned yet." />}
      </section>

      <div className="grid gap-5 xl:grid-cols-2">
        <section className="dashboard-card">
          <div className="section-heading"><span>Abnormal findings that may require clinician review</span><FileWarning size={19} /></div>
          <div className="grid gap-3 sm:grid-cols-2">{result.abnormal_findings?.length ? result.abnormal_findings.map((finding, index) => typeof finding === "string"
            ? <Insight key={index} title="Finding" body={finding} />
            : <div key={index} className="mini-card"><div className="flex items-start justify-between gap-3"><strong>{finding.test || finding.name || finding.test_name || "Finding"}</strong><StatusBadge status={finding.status} /></div><p className="mt-3">{finding.value ?? "—"} {finding.unit}</p><p className="mt-2 text-xs leading-5 text-slate-500">{finding.evidence || "Requires clinician review."}</p></div>
          ) : <Empty text="No abnormal findings returned." />}</div>
        </section>
        <section className="dashboard-card">
          <div className="section-heading"><span>Clinical Warnings</span><AlertTriangle size={19} /></div>
          <div className="space-y-3">{result.clinical_warnings?.length ? result.clinical_warnings.map((warning, index) => <WarningCard key={index} warning={warning} />) : <Empty text="No clinical warnings returned." />}</div>
        </section>
      </div>

      <section className="dashboard-card">
        <div className="section-heading"><span>Top Clinical Patterns</span><Sparkles size={19} /></div>
        {patterns.length ? <div className="grid gap-4 lg:grid-cols-2">{patterns.map((pattern, index) => {
          if (typeof pattern === "string") return <Insight key={index} title={`Pattern ${index + 1}`} body={pattern} />;
          const item = pattern as ClinicalPattern;
          return <div key={index} className="mini-card"><div className="flex flex-wrap items-center justify-between gap-3"><strong>{item.pattern_name || item.pattern || item.name || "Clinical pattern"}</strong><span className="rounded-full bg-blue-50 px-2 py-1 text-xs font-bold text-blue-700">Rank {item.rank ?? index + 1}</span></div>
            <div className="mt-3 flex flex-wrap gap-2 text-xs"><ConfidenceBadge value={item.confidence_level || item.confidence} /><span className="rounded-full bg-slate-100 px-2.5 py-1 font-bold text-slate-700">Score {item.score ?? "Not provided"}</span><span className="rounded-full bg-teal-50 px-2.5 py-1 font-bold text-teal-700">{sourceCount(item)} retrieved sources</span></div>
            <p className="mt-3 text-xs leading-5 text-slate-500">Requires clinician review and correlation with the full clinical context.</p>
            <PatternList label="Evidence for" values={list(item.evidence_for || item.supporting_findings)} /><PatternList label="Missing evidence" values={list(item.missing_evidence)} /><PatternList label="Warnings" values={list(item.warnings)} />
            {item.retrieved_sources?.length ? <div className="mt-4 space-y-2"><strong className="text-xs text-slate-700">Retrieved RAG sources</strong>{item.retrieved_sources.map((source, sourceIndex) => <SourceCard key={sourceIndex} source={source} index={sourceIndex} />)}</div> : null}
          </div>;
        })}</div> : <Empty text="No clinical patterns matched this case yet." />}</section>

      <div className="grid gap-5 xl:grid-cols-2">
        <section className="dashboard-card"><div className="section-heading"><span>Missing Required Labs</span><CheckCircle2 size={19} /></div>
          {result.missing_required_labs?.length ? <div className="space-y-4"><div className="text-sm font-semibold text-amber-900">{result.missing_required_labs.length} missing required labs</div><div className="flex flex-wrap gap-2">{result.missing_required_labs.map((lab) => <span key={lab} className="rounded-full bg-amber-100 px-3 py-1 text-sm font-semibold text-amber-800">{lab}</span>)}</div><p className="text-xs leading-5 text-slate-500">Interpretation may be limited until missing information is reviewed.</p></div> : <div className="flex gap-3 rounded-2xl bg-green-50 p-4 text-sm text-green-800"><CheckCircle2 size={18} className="shrink-0" />No missing required labs reported.</div>}
        </section>
        <section className="dashboard-card"><div className="section-heading"><span>Retrieved Sources</span><BookOpen size={19} /></div>
          {result.retrieved_sources?.length ? <div className="space-y-3">{result.retrieved_sources.map((source, index) => {
            if (typeof source === "string") return <Insight key={index} title={`Source ${index + 1}`} body={source} />;
            const item = source as RetrievedSource;
            return <SourceCard key={index} source={item} index={index} />;
          })}</div> : <Empty text="No retrieved evidence sources available yet." />}</section>
      </div>

      <section className="dashboard-card">
        <div className="section-heading"><span>Generated Clinical Review Report</span><FileText size={19} /></div>
        {report?.generated || result.report_file_path ? <div className="space-y-5">
          <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-green-200 bg-green-50 p-4 text-sm text-green-800"><CheckCircle2 size={18} />Report generated successfully</div>
          <div className="grid gap-3 md:grid-cols-2">
            <SummaryItem label="Case ID" value={String(caseId)} />
            <SummaryItem label="Generated" value={formatDate(result.generated_at)} />
          </div>
          <div className="flex flex-wrap gap-3">
            {pdfUrl && <a href={pdfUrl} className="report-button" download><FileDown size={17} aria-hidden="true" />Download PDF</a>}
            {htmlUrl && <a href={htmlUrl} className="report-button" target="_blank" rel="noreferrer"><ExternalLink size={17} />Open Printable Report</a>}
            {htmlUrl && <button type="button" className="report-button" onClick={() => window.open(htmlUrl, "_blank", "noopener,noreferrer")}><Printer size={17} />Print / Save as PDF</button>}
          </div>
          <p className="text-xs leading-5 text-slate-500">Download PDF uses the backend-generated ReportLab document. The printable report keeps the browser print flow available.</p>
        </div> : <Empty text="No generated report metadata returned." />}
      </section>

    </section>
  );
}

function Empty({ text }: { text: string }) { return <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">{text}</div>; }
function Insight({ title, body }: { title: string; body: string }) { return <div className="mini-card"><strong>{title}</strong><p className="mt-2 text-sm text-slate-600">{body}</p></div>; }
function PatternList({ label, values }: { label: string; values: string[] }) { return values.length ? <div className="mt-3 text-xs leading-5 text-slate-500"><strong className="text-slate-700">{label}:</strong> {values.join(", ")}</div> : null; }
function SummaryItem({ label, value }: { label: string; value: string | number }) { return <div className="rounded-2xl bg-slate-50 p-4"><span className="text-xs font-bold uppercase tracking-wider text-slate-400">{label}</span><p className="mt-2 text-sm font-semibold text-slate-800">{value}</p></div>; }
function SourceCard({ source, index }: { source: RetrievedSource | string; index: number }) {
  if (typeof source === "string") return <Insight title={`Source ${index + 1}`} body={source} />;
  const score = source.similarity_score == null ? "N/A" : Number(source.similarity_score).toFixed(2);
  return <div className="rounded-2xl border border-slate-200 bg-white p-3 text-xs"><div className="space-y-2"><div><strong className="text-sm text-slate-800">{source.title || "Evidence source"}</strong></div><div className="rounded-xl bg-slate-50 p-3"><div className="text-[11px] font-bold uppercase tracking-wide text-slate-500">Relevant Finding</div><p className="mt-1 leading-5 text-slate-600">{source.snippet || "No snippet available."}</p></div><div className="rounded-xl bg-slate-50 p-3"><div className="text-[11px] font-bold uppercase tracking-wide text-slate-500">Clinical Context</div><p className="mt-1 leading-5 text-slate-600">{source.pattern_code || "No pattern context available."}</p></div><div className="mt-2 flex flex-wrap gap-2"><span className="rounded-full bg-slate-100 px-2 py-1">Similarity Score {score}</span>{(source.source_id || source.id) && <span className="rounded-full bg-slate-100 px-2 py-1">Source ID {source.source_id || source.id}</span>}</div></div></div>;
}
function ConfidenceBadge({ value }: { value?: string }) {
  const key = String(value || "unknown").toLowerCase();
  const styles: Record<string, string> = {
    high: "bg-green-100 text-green-700",
    moderate: "bg-blue-100 text-blue-700",
    low: "bg-amber-100 text-amber-800",
    unknown: "bg-slate-100 text-slate-600",
  };
  return <span className={`rounded-full px-2.5 py-1 font-bold ${styles[key] || styles.unknown}`}>Confidence {value || "unknown"}</span>;
}
function WarningCard({ warning }: { warning: ClinicalWarning | string }) {
  const item = typeof warning === "string" ? { severity: "Review", text: warning } : warning;
  return <div className="flex gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950"><AlertTriangle size={17} className="shrink-0" /><div><strong>{item.severity || "Review"}</strong><p className="mt-1">{item.text || item.warning || "Requires clinician review."}</p>{item.associated_item && <p className="mt-1 text-xs text-amber-800">Associated item: {item.associated_item}</p>}</div></div>;
}

function SeverityBanner({ severity }: { severity: SeverityResult }) {
  const label = severity.label;
  const config = severityConfig(label);
  const Icon = config.icon;

  return (
    <section className={`flex flex-col gap-4 rounded-2xl border p-5 text-sm shadow-sm md:flex-row md:items-start md:justify-between ${config.wrapper}`}>
      <div className="flex min-w-0 gap-3">
        <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full ${config.iconClass}`}>
          <Icon size={22} aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-base font-bold">{config.heading}</h3>
            <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${config.badge}`}>
              Severity Alert: {label}
            </span>
          </div>
          <p className="mt-2 leading-6">{config.description}</p>
          <p className="mt-2 text-xs leading-5">
            This is a supportive AI alert for clinician prioritization only. It is not a diagnosis and does not replace clinical judgment.
          </p>
        </div>
      </div>
      <div className="grid shrink-0 grid-cols-2 gap-2 md:w-72">
        <SummaryPill label="Confidence" value={formatSeverityConfidence(severity.confidence)} />
        <SummaryPill label="Source" value={formatSeveritySource(severity.source)} />
      </div>
    </section>
  );
}

function SummaryPill({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl bg-white/70 p-3 ring-1 ring-black/5"><span className="text-[11px] font-bold uppercase tracking-wide text-slate-500">{label}</span><p className="mt-1 text-sm font-bold text-slate-900">{value}</p></div>;
}

function severityConfig(label: string) {
  if (label === "Critical") {
    return {
      heading: "Critical Review Alert",
      description: "One or more findings require immediate clinician attention and review in the full clinical context.",
      wrapper: "border-red-300 bg-red-50 text-red-950",
      badge: "bg-red-100 text-red-800",
      iconClass: "bg-red-100 text-red-700",
      icon: CircleAlert,
    };
  }
  if (label === "Urgent") {
    return {
      heading: "Urgent Review",
      description: "The submitted findings may require timely clinician review and correlation with the full clinical context.",
      wrapper: "border-amber-300 bg-amber-50 text-amber-950",
      badge: "bg-amber-100 text-amber-800",
      iconClass: "bg-amber-100 text-amber-700",
      icon: AlertTriangle,
    };
  }
  return {
    heading: "Routine Review",
    description: "The submitted findings support routine clinician review in the full clinical context.",
    wrapper: "border-green-300 bg-green-50 text-green-950",
    badge: "bg-green-100 text-green-800",
    iconClass: "bg-green-100 text-green-700",
    icon: CheckCircle2,
  };
}

function formatSeverityConfidence(value?: number) {
  if (typeof value !== "number" || Number.isNaN(value)) return "Not available";
  const clamped = Math.max(0, Math.min(1, value));
  return `${Math.round(clamped * 100)}%`;
}

function formatSeveritySource(value?: string) {
  const labels: Record<string, string> = {
    fine_tuned_model: "Fine-tuned DistilBERT model",
    rule_based_fallback: "Rule-based fallback",
    critical_override: "Critical lab override",
  };
  return labels[value || ""] || "Not available";
}
