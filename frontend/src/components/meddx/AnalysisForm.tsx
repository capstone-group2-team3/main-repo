"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, Beaker, Check, ChevronRight, FlaskConical, LoaderCircle, RotateCcw, ShieldCheck, Stethoscope } from "lucide-react";
import { analyzeReport, fetchTemplate, fetchTemplates } from "@/lib/api";
import type { AnalyzePayload, AnalyzeResponse, PanelTemplate, Sex, TemplateOption } from "@/lib/types";

type Values = Record<string, string>;
type DemoCase = { title: string; panelHints: string[]; age: number; sex: Sex; symptoms: string[]; notes: string; labs: Record<string, number> };

const DEMOS: DemoCase[] = [
  { title: "CBC Sample", panelHints: ["CBC_Panel", "CBC"], age: 50, sex: "female", symptoms: ["pale skin", "fatigue", "dizziness"], notes: "Severe fatigue and pale skin. Educational synthetic case for demo.", labs: { Hemoglobin: 5, WBC: 6, Platelets: 8 } },
  { title: "Diabetic Sample", panelHints: ["Diabetic_Panel", "Diabetic"], age: 40, sex: "male", symptoms: ["increased thirst", "frequent urination", "blurred vision"], notes: "Increased thirst and frequent urination. Educational synthetic case for demo.", labs: { Glucose: 250, HbA1c: 8 } },
  { title: "Cardiac Sample", panelHints: ["Cardiac_Panel", "Cardiac_Enzymes_Panel", "Cardiac"], age: 58, sex: "male", symptoms: ["chest pain", "shortness of breath"], notes: "Chest discomfort with shortness of breath. Educational synthetic case for demo.", labs: { Troponin: 0.2, CPK: 450 } },
  { title: "Renal & Thyroid Sample", panelHints: ["Renal_Thyroid_Panel"], age: 62, sex: "female", symptoms: ["fatigue", "swelling"], notes: "Fatigue with swelling. Educational synthetic case for demo.", labs: { Creatinine: 1.8, TSH: 2.5 } },
  { title: "Lipids & Inflammation Sample", panelHints: ["Lipids_Inflammation_Panel"], age: 55, sex: "male", symptoms: ["joint pain"], notes: "Screening values for educational clinician review.", labs: { LDL: 150, HDL: 35, CRP: 12 } },
  { title: "Electrolytes & Calcium Sample", panelHints: ["Electrolytes_Calcium_Panel"], age: 47, sex: "female", symptoms: ["muscle weakness", "cramps"], notes: "Muscle symptoms with electrolyte values for educational review.", labs: { Sodium: 132, Potassium: 3.2, Calcium: 9.1 } },
  { title: "Albumin & Protein Sample", panelHints: ["Albumin_Protein_Panel"], age: 64, sex: "male", symptoms: ["swelling", "fatigue"], notes: "Low albumin demonstration for clinician review.", labs: { Albumin: 2.8 } },
];

export function AnalysisForm({ onResult }: { onResult: (result: AnalyzeResponse) => void }) {
  const [options, setOptions] = useState<TemplateOption[]>([]);
  const [panel, setPanel] = useState("");
  const [template, setTemplate] = useState<PanelTemplate | null>(null);
  const [age, setAge] = useState("");
  const [sex, setSex] = useState<Sex | "">("");
  const [symptoms, setSymptoms] = useState<string[]>([]);
  const [notes, setNotes] = useState("");
  const [values, setValues] = useState<Values>({});
  const [loading, setLoading] = useState(false);
  const [templateLoading, setTemplateLoading] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [selectedDemo, setSelectedDemo] = useState("");

  const loadTemplate = useCallback(async (name: string, preset?: DemoCase) => {
    setPanel(name);
    setTemplateLoading(true);
    setError("");
    try {
      const next = await fetchTemplate(name);
      setTemplate(next);
      setValues(preset ? Object.fromEntries(Object.entries(preset.labs).map(([key, value]) => [key.toLowerCase(), String(value)])) : {});
      const allowed = next.suggested_symptoms || [];
      setSymptoms(preset ? preset.symptoms.filter((item) => allowed.includes(item)) : []);
    } catch (cause) {
      setTemplate(null);
      setError(cause instanceof Error ? cause.message : "Unable to load this template.");
    } finally {
      setTemplateLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchTemplates()
      .then((items) => {
        setOptions(items);
        if (items[0]) void loadTemplate(items[0].name);
      })
      .catch((cause) => setError(cause instanceof Error ? cause.message : "Templates could not be loaded."));
  }, [loadTemplate]);

  const tests = useMemo(() => template?.tests || [], [template]);
  const required = tests.filter((test) => test.required);
  const optional = tests.filter((test) => !test.required);

  async function loadDemo(demo: DemoCase) {
    const match = options.find((option) =>
      demo.panelHints.some((hint) =>
        option.name.toLowerCase() === hint.toLowerCase() ||
        option.name.toLowerCase().includes(hint.toLowerCase()) ||
        option.display_name.toLowerCase().includes(hint.toLowerCase()),
      ),
    );
    if (!match) {
      setError(`${demo.title} panel is not available from the backend.`);
      return;
    }
    setAge(String(demo.age)); setSex(demo.sex); setNotes(demo.notes);
    await loadTemplate(match.name, demo);
    document.querySelector("#analysis")?.scrollIntoView({ behavior: "smooth" });
  }

  function clearForm() {
    setAge(""); setSex(""); setSymptoms([]); setNotes(""); setValues({});
    setSelectedDemo(""); setError(""); setFieldErrors({});
  }

  function toggleSymptom(symptom: string) {
    setSymptoms((current) => current.includes(symptom) ? current.filter((item) => item !== symptom) : [...current, symptom]);
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    const nextErrors: Record<string, string> = {};
    const numericAge = Number(age);
    if (!panel) nextErrors.panel = "Select a lab panel.";
    if (!age || !Number.isFinite(numericAge) || numericAge <= 0 || numericAge > 120) nextErrors.age = "Enter an age from 1 to 120.";
    if (!sex) nextErrors.sex = "Select sex for the configured educational context.";
    const missing = required.filter((test) => !values[String(test.name || test.test_name).toLowerCase()]);
    missing.forEach((test) => { nextErrors[`lab-${String(test.name || test.test_name).toLowerCase()}`] = "Enter this required lab value."; });
    const labs = tests.flatMap((test) => {
      const name = String(test.name || test.test_name || "Unknown");
      const raw = values[name.toLowerCase()];
      if (raw === "" || raw == null) return [];
      const value = Number(raw);
      if (!Number.isFinite(value)) {
        nextErrors[`lab-${name.toLowerCase()}`] = "Enter a valid numeric value.";
        return [];
      }
      return [{ name, value, unit: test.unit || "" }];
    });
    setFieldErrors(nextErrors);
    if (Object.keys(nextErrors).length || !sex) { setError("Review the highlighted required fields."); return; }
    const payload: AnalyzePayload = { age: numericAge, sex, selected_panel: panel, symptoms, clinical_notes: notes, labs };
    setLoading(true);
    try {
      onResult(await analyzeReport(payload));
      window.setTimeout(() => document.querySelector("#results")?.scrollIntoView({ behavior: "smooth" }), 50);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The clinical review could not be generated.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section id="analysis" className="scroll-mt-24 space-y-6">
      <div>
        <span className="eyebrow">Clinical workflow</span>
        <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-950 md:text-4xl">Generate a focused clinical review</h2>
        <p className="mt-3 max-w-2xl text-slate-600">Choose a lab panel to generate the correct clinical review form. The form updates automatically based on the selected panel.</p>
      </div>

      <div className="rounded-3xl border border-blue-100 bg-gradient-to-r from-blue-50 to-cyan-50 p-5">
        <label className="mb-2 flex items-center gap-2 font-semibold text-slate-900" htmlFor="sample-case"><FlaskConical size={19} className="text-blue-700" /> Load Sample Case</label>
        <p id="sample-help" className="mb-3 text-xs leading-5 text-slate-600">Populate a safe educational example without submitting it. You can edit every value afterward.</p>
        <div className="flex flex-col gap-3 sm:flex-row"><select id="sample-case" aria-describedby="sample-help" value={selectedDemo} onChange={(event) => { const value = event.target.value; setSelectedDemo(value); const demo = DEMOS.find((item) => item.title === value); if (demo) void loadDemo(demo); }} className="field-input flex-1"><option value="">Choose a sample case…</option>{DEMOS.map((demo) => <option key={demo.title} value={demo.title}>{demo.title}</option>)}</select><button type="button" onClick={clearForm} className="secondary-button" aria-label="Reset and clear analysis form"><RotateCcw size={16} />Reset / Clear Form</button></div>
      </div>

      <div className="flex gap-3 rounded-2xl border border-teal-300 bg-teal-50 p-5 text-sm text-teal-950" role="note"><ShieldCheck className="shrink-0 text-teal-700" size={22} aria-hidden="true" /><div><strong className="block">Clinical Safety Notice</strong><p className="mt-1">For clinicians only — supports review, not diagnosis or prescribing.</p></div></div>

      {error && <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>}

      <form onSubmit={submit} className="grid gap-6 xl:grid-cols-[.9fr_1.1fr]">
        <div className="space-y-6">
          <StepCard step="01" title="Select Analysis Template" icon={Beaker}>
            <label className="field-label" htmlFor="panel">Lab panel <span aria-label="required">*</span></label>
            <select id="panel" aria-describedby="panel-help" aria-invalid={Boolean(fieldErrors.panel)} value={panel} onChange={(event) => void loadTemplate(event.target.value)} className="field-input" disabled={!options.length}>
              {!options.length && <option>Templates unavailable</option>}
              {options.map((option) => <option key={option.name} value={option.name}>{option.display_name} · {option.name}</option>)}
            </select>
            <Helper id="panel-help">Selects the supported tests, units, and educational ranges for this review.</Helper>
            {templateLoading ? <div className="mt-5 flex items-center gap-2 text-sm text-slate-500"><LoaderCircle className="animate-spin" size={16} /> Loading template…</div> : template && <div className="mt-5 rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50 to-teal-50 p-5">
              <div className="flex items-center justify-between gap-4"><div><span className="text-xs font-bold uppercase tracking-wider text-teal-700">Selected panel</span><h3 className="mt-1 font-bold">{template.display_name || panel}</h3></div><Activity className="text-teal-700" /></div>
              <div className="mt-4 grid grid-cols-3 gap-2 text-center">{[[tests.length, "Tests"], [required.length, "Required"], [template.suggested_symptoms?.length || 0, "Symptoms"]].map(([count, label]) => <div key={label} className="rounded-xl bg-white/80 p-2"><strong className="block">{count}</strong><span className="text-[11px] text-slate-500">{label}</span></div>)}</div>
              <div className="mt-4 text-xs leading-5 text-slate-600"><strong>Required:</strong> {required.map((item) => item.name || item.test_name).join(", ") || "None"}<br /><strong>Optional:</strong> {optional.map((item) => item.name || item.test_name).join(", ") || "None"}</div>
            </div>}
          </StepCard>

          <StepCard step="02" title="Patient Context" icon={Stethoscope}>
            <div className="grid gap-4 sm:grid-cols-2"><div><label className="field-label" htmlFor="age">Age <span aria-label="required">*</span></label><input id="age" aria-describedby="age-help age-error" aria-invalid={Boolean(fieldErrors.age)} type="number" min="1" max="120" value={age} onChange={(event) => setAge(event.target.value)} className="field-input" placeholder="50" /><Helper id="age-help">Used only to present the submitted clinical context.</Helper>{fieldErrors.age && <FieldError id="age-error">{fieldErrors.age}</FieldError>}</div>
              <fieldset><legend className="field-label">Sex <span aria-label="required">*</span></legend><div className="grid grid-cols-2 gap-2">{(["male", "female"] as Sex[]).map((item) => <button key={item} type="button" aria-pressed={sex === item} onClick={() => setSex(item)} className={`rounded-xl border px-3 py-3 text-sm font-semibold capitalize transition ${sex === item ? "border-teal-600 bg-teal-50 text-teal-800" : "border-slate-200 hover:bg-slate-50"}`}>{item}</button>)}</div><Helper id="sex-help">Records the submitted context; configured ranges may not be sex-specific.</Helper>{fieldErrors.sex && <FieldError>{fieldErrors.sex}</FieldError>}</fieldset></div>
            <fieldset className="mt-5"><legend className="field-label">Symptoms</legend><Helper id="symptoms-help">Select only symptoms relevant to this educational clinician review.</Helper><div className="mt-2 flex flex-wrap gap-2">{template?.suggested_symptoms?.length ? template.suggested_symptoms.map((symptom) => <button key={symptom} type="button" aria-pressed={symptoms.includes(symptom)} onClick={() => toggleSymptom(symptom)} className={`inline-flex items-center gap-1 rounded-full border px-3 py-2 text-xs font-semibold transition ${symptoms.includes(symptom) ? "border-teal-600 bg-teal-600 text-white" : "border-slate-200 bg-white text-slate-600 hover:border-teal-300"}`}>{symptoms.includes(symptom) && <Check size={12} aria-hidden="true" />}{symptom}</button>) : <span className="text-sm text-slate-400">Select a panel to see suggested symptoms.</span>}</div></fieldset>
            <div className="mt-5"><label className="field-label" htmlFor="notes">Clinical notes</label><textarea id="notes" aria-describedby="notes-help" value={notes} onChange={(event) => setNotes(event.target.value)} rows={4} className="field-input resize-none" placeholder="Add concise context relevant to clinician review…" /><Helper id="notes-help">Add concise context without names, identifiers, diagnosis claims, or prescribing instructions.</Helper></div>
          </StepCard>
        </div>

        <StepCard step="03" title="Lab Values" icon={FlaskConical} className="h-fit">
          <p className="mb-2 text-sm text-slate-500">Required tests are marked with an asterisk. Units and ranges come from backend configuration.</p><p className="mb-5 rounded-xl bg-amber-50 p-3 text-xs leading-5 text-amber-900">{template?.educational_disclaimer || "Configured ranges are educational and may differ by laboratory, age, sex, method, and clinical context."}</p>
          <div className="grid gap-4 sm:grid-cols-2">{tests.map((test, index) => {
            const name = String(test.name || test.test_name || `Test ${index + 1}`);
            const errorKey = `lab-${name.toLowerCase()}`; const range = test.reference_low != null && test.reference_high != null ? `${test.reference_low}–${test.reference_high} ${test.unit || ""}` : "Not configured";
            return <div key={name} className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4 transition focus-within:border-cyan-400 focus-within:bg-white"><label className="field-label" htmlFor={`lab-${index}`}>{name} {test.required && <span aria-label="required">*</span>}</label><p id={`lab-meta-${index}`} className="mb-2 text-xs leading-5 text-slate-600">Reference range: {range}<br /><strong>{test.required ? "Required" : "Optional"}</strong></p><div className="relative"><input id={`lab-${index}`} aria-describedby={`lab-meta-${index} lab-help-${index}`} aria-invalid={Boolean(fieldErrors[errorKey])} type="number" step="any" value={values[name.toLowerCase()] || ""} onChange={(event) => setValues((current) => ({ ...current, [name.toLowerCase()]: event.target.value }))} className="field-input pr-20" placeholder="Enter value" /><span className="pointer-events-none absolute right-3 top-3 text-xs font-semibold text-slate-400">{test.unit}</span></div><Helper id={`lab-help-${index}`}>Enter the numeric result in the displayed unit; the range is educational context only.</Helper>{fieldErrors[errorKey] && <FieldError>{fieldErrors[errorKey]}</FieldError>}{test.description && <p className="mt-2 text-xs text-slate-500">{test.description}</p>}</div>;
          })}</div>
          {!tests.length && <div className="rounded-2xl bg-slate-50 p-8 text-center text-sm text-slate-500">Select an available template to display lab inputs.</div>}
          <button disabled={loading || !tests.length} aria-describedby="submit-help" className="premium-button mt-7 w-full justify-center disabled:cursor-not-allowed disabled:opacity-60">{loading ? <><LoaderCircle className="animate-spin" size={18} aria-hidden="true" /> Generating Clinical Review…</> : <>Generate Clinical Review <ChevronRight size={18} aria-hidden="true" /></>}</button>
          <p id="submit-help" className="mt-3 text-center text-xs text-slate-500">Submits the entered values for clinician-facing educational review. It does not produce a final diagnosis.</p>
        </StepCard>
      </form>
    </section>
  );
}

function Helper({ id, children }: { id?: string; children: React.ReactNode }) { return <p id={id} className="helper-text">{children}</p>; }
function FieldError({ id, children }: { id?: string; children: React.ReactNode }) { return <p id={id} className="field-error" role="alert">{children}</p>; }

function StepCard({ step, title, icon: Icon, children, className = "" }: { step: string; title: string; icon: typeof Beaker; children: React.ReactNode; className?: string }) {
  return <section className={`rounded-3xl border border-slate-200 bg-white p-5 shadow-[0_12px_40px_rgba(15,23,42,.06)] md:p-7 ${className}`}><div className="mb-6 flex items-center gap-3"><div className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-blue-600 to-teal-600 text-white shadow-lg"><Icon size={20} /></div><div><span className="text-[11px] font-bold uppercase tracking-[.16em] text-teal-700">Step {step}</span><h3 className="text-xl font-bold">{title}</h3></div></div>{children}</section>;
}
