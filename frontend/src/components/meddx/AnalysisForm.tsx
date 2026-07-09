"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, Beaker, Check, ChevronRight, FlaskConical, LoaderCircle, Stethoscope } from "lucide-react";
import { analyzeReport, fetchTemplate, fetchTemplates } from "@/lib/api";
import type { AnalyzePayload, AnalyzeResponse, PanelTemplate, Sex, TemplateOption } from "@/lib/types";

type Values = Record<string, string>;
type DemoCase = { title: string; panelHints: string[]; age: number; sex: Sex; symptoms: string[]; notes: string; labs: Record<string, number> };

const DEMOS: DemoCase[] = [
  { title: "CBC Sample", panelHints: ["CBC_Panel", "CBC"], age: 50, sex: "female", symptoms: ["pale skin", "fatigue", "dizziness"], notes: "Severe fatigue and pale skin. Educational synthetic case for demo.", labs: { Hemoglobin: 5, WBC: 6, Platelets: 8 } },
  { title: "Diabetic Sample", panelHints: ["Diabetic_Panel", "Diabetic"], age: 40, sex: "male", symptoms: ["increased thirst", "frequent urination", "blurred vision"], notes: "Increased thirst and frequent urination. Educational synthetic case for demo.", labs: { Glucose: 250, HbA1c: 8 } },
  { title: "Cardiac Sample", panelHints: ["Cardiac_Panel", "Cardiac_Enzymes_Panel", "Cardiac"], age: 58, sex: "male", symptoms: ["chest pain", "shortness of breath"], notes: "Chest discomfort with shortness of breath. Educational synthetic case for demo.", labs: { Troponin: 0.2, CPK: 450 } },
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

  function toggleSymptom(symptom: string) {
    setSymptoms((current) => current.includes(symptom) ? current.filter((item) => item !== symptom) : [...current, symptom]);
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    if (!panel || !age || !sex) { setError("Panel, age, and sex are required."); return; }
    const missing = required.filter((test) => !values[String(test.name || test.test_name).toLowerCase()]);
    if (missing.length) { setError(`Missing required lab values: ${missing.map((test) => test.name || test.test_name).join(", ")}`); return; }
    const labs = tests.flatMap((test) => {
      const name = String(test.name || test.test_name || "Unknown");
      const raw = values[name.toLowerCase()];
      if (raw === "" || raw == null) return [];
      return [{ name, value: Number(raw), unit: test.unit || "" }];
    });
    const payload: AnalyzePayload = { age: Number(age), sex, selected_panel: panel, symptoms, clinical_notes: notes, labs };
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
        <div className="mb-4 flex items-center gap-2 font-semibold text-slate-900"><FlaskConical size={19} className="text-blue-700" /> Load Demo Case</div>
        <div className="grid gap-3 md:grid-cols-3">{DEMOS.map((demo) => <button key={demo.title} type="button" onClick={() => void loadDemo(demo)} className="group rounded-2xl border border-white bg-white/80 p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-cyan-300 hover:shadow-md"><strong>{demo.title}</strong><span className="mt-2 flex items-center gap-1 text-xs text-slate-500">Educational synthetic case <ChevronRight size={13} className="transition group-hover:translate-x-1" /></span></button>)}</div>
      </div>

      {error && <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>}

      <form onSubmit={submit} className="grid gap-6 xl:grid-cols-[.9fr_1.1fr]">
        <div className="space-y-6">
          <StepCard step="01" title="Select Analysis Template" icon={Beaker}>
            <label className="field-label" htmlFor="panel">Lab panel <span>*</span></label>
            <select id="panel" value={panel} onChange={(event) => void loadTemplate(event.target.value)} className="field-input" disabled={!options.length}>
              {!options.length && <option>Templates unavailable</option>}
              {options.map((option) => <option key={option.name} value={option.name}>{option.display_name} · {option.name}</option>)}
            </select>
            {templateLoading ? <div className="mt-5 flex items-center gap-2 text-sm text-slate-500"><LoaderCircle className="animate-spin" size={16} /> Loading template…</div> : template && <div className="mt-5 rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50 to-teal-50 p-5">
              <div className="flex items-center justify-between gap-4"><div><span className="text-xs font-bold uppercase tracking-wider text-teal-700">Selected panel</span><h3 className="mt-1 font-bold">{template.display_name || panel}</h3></div><Activity className="text-teal-700" /></div>
              <div className="mt-4 grid grid-cols-3 gap-2 text-center">{[[tests.length, "Tests"], [required.length, "Required"], [template.suggested_symptoms?.length || 0, "Symptoms"]].map(([count, label]) => <div key={label} className="rounded-xl bg-white/80 p-2"><strong className="block">{count}</strong><span className="text-[11px] text-slate-500">{label}</span></div>)}</div>
              <div className="mt-4 text-xs leading-5 text-slate-600"><strong>Required:</strong> {required.map((item) => item.name || item.test_name).join(", ") || "None"}<br /><strong>Optional:</strong> {optional.map((item) => item.name || item.test_name).join(", ") || "None"}</div>
            </div>}
          </StepCard>

          <StepCard step="02" title="Patient Context" icon={Stethoscope}>
            <div className="grid gap-4 sm:grid-cols-2"><div><label className="field-label" htmlFor="age">Age <span>*</span></label><input id="age" type="number" min="0" max="120" value={age} onChange={(event) => setAge(event.target.value)} className="field-input" placeholder="50" /></div>
              <div><div className="field-label">Sex <span>*</span></div><div className="grid grid-cols-2 gap-2">{(["male", "female"] as Sex[]).map((item) => <button key={item} type="button" onClick={() => setSex(item)} className={`rounded-xl border px-3 py-3 text-sm font-semibold capitalize transition ${sex === item ? "border-teal-600 bg-teal-50 text-teal-800" : "border-slate-200 hover:bg-slate-50"}`}>{item}</button>)}</div></div></div>
            <div className="mt-5"><div className="field-label">Symptoms</div><div className="flex flex-wrap gap-2">{template?.suggested_symptoms?.length ? template.suggested_symptoms.map((symptom) => <button key={symptom} type="button" onClick={() => toggleSymptom(symptom)} className={`inline-flex items-center gap-1 rounded-full border px-3 py-2 text-xs font-semibold transition ${symptoms.includes(symptom) ? "border-teal-600 bg-teal-600 text-white" : "border-slate-200 bg-white text-slate-600 hover:border-teal-300"}`}>{symptoms.includes(symptom) && <Check size={12} />}{symptom}</button>) : <span className="text-sm text-slate-400">Select a panel to see suggested symptoms.</span>}</div></div>
            <div className="mt-5"><label className="field-label" htmlFor="notes">Clinical notes</label><textarea id="notes" value={notes} onChange={(event) => setNotes(event.target.value)} rows={4} className="field-input resize-none" placeholder="Add concise context relevant to clinician review…" /></div>
          </StepCard>
        </div>

        <StepCard step="03" title="Lab Values" icon={FlaskConical} className="h-fit">
          <p className="mb-5 text-sm text-slate-500">Required tests are marked with an asterisk. Units come directly from the selected template.</p>
          <div className="grid gap-4 sm:grid-cols-2">{tests.map((test, index) => {
            const name = String(test.name || test.test_name || `Test ${index + 1}`);
            return <div key={name} className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4 transition focus-within:border-cyan-400 focus-within:bg-white"><label className="field-label" htmlFor={`lab-${index}`}>{name} {test.required && <span>*</span>}</label><div className="relative"><input id={`lab-${index}`} type="number" step="any" value={values[name.toLowerCase()] || ""} onChange={(event) => setValues((current) => ({ ...current, [name.toLowerCase()]: event.target.value }))} className="field-input pr-20" placeholder="Enter value" /><span className="pointer-events-none absolute right-3 top-3 text-xs font-semibold text-slate-400">{test.unit}</span></div>{test.description && <p className="mt-2 text-xs text-slate-500">{test.description}</p>}</div>;
          })}</div>
          {!tests.length && <div className="rounded-2xl bg-slate-50 p-8 text-center text-sm text-slate-500">Select an available template to display lab inputs.</div>}
          <button disabled={loading || !tests.length} className="premium-button mt-7 w-full justify-center disabled:cursor-not-allowed disabled:opacity-60">{loading ? <><LoaderCircle className="animate-spin" size={18} /> Generating review…</> : <>Generate Clinical Review <ChevronRight size={18} /></>}</button>
          <p className="mt-3 text-center text-xs text-slate-500">Review abnormal findings, safety notes, and clinical patterns in seconds.</p>
        </StepCard>
      </form>
    </section>
  );
}

function StepCard({ step, title, icon: Icon, children, className = "" }: { step: string; title: string; icon: typeof Beaker; children: React.ReactNode; className?: string }) {
  return <section className={`rounded-3xl border border-slate-200 bg-white p-5 shadow-[0_12px_40px_rgba(15,23,42,.06)] md:p-7 ${className}`}><div className="mb-6 flex items-center gap-3"><div className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-blue-600 to-teal-600 text-white shadow-lg"><Icon size={20} /></div><div><span className="text-[11px] font-bold uppercase tracking-[.16em] text-teal-700">Step {step}</span><h3 className="text-xl font-bold">{title}</h3></div></div>{children}</section>;
}
